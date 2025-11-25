"""ML-powered predictions for F1 race outcomes and performance analytics."""
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder
from pathlib import Path
import snowflake.connector
import pickle
from typing import Optional, Dict, Tuple
from datetime import datetime


def get_snowflake_connection():
    """Get Snowflake connection for ML training data."""
    account = os.getenv('SNOWFLAKE_ACCOUNT')
    user = os.getenv('SNOWFLAKE_USER')

    if not account:
        raise ValueError("SNOWFLAKE_ACCOUNT environment variable is not set")
    if not user:
        raise ValueError("SNOWFLAKE_USER environment variable is not set")

    return snowflake.connector.connect(
        user=user,
        account=account,
        authenticator='SNOWFLAKE_JWT',
        private_key_file=str(Path.home() / '.ssh' / 'snowflake_key.p8'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
        database=os.getenv('SNOWFLAKE_DATABASE', 'APEXML_DEV'),
        schema='ANALYTICS',
        role=os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')
    )


class RaceWinnerPredictor:
    """Predicts race winners based on historical performance."""

    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.driver_encoder = LabelEncoder()
        self.circuit_encoder = LabelEncoder()
        self.trained = False

    def fetch_training_data(self) -> pd.DataFrame:
        """Fetch historical race results for training."""
        conn = get_snowflake_connection()

        query = """
        WITH driver_stats AS (
            SELECT
                r.driver_number,
                r.driver_name,
                r.team_name,
                r.circuit_short_name,
                r.year,
                r.final_position,
                AVG(l.lap_duration) as avg_lap_time,
                MIN(l.lap_duration) as best_lap_time,
                COUNT(l.lap_number) as total_laps,
                AVG(l.position) as avg_position_during_race
            FROM fct_race_results r
            LEFT JOIN fct_lap_times l
                ON r.session_key = l.session_key
                AND r.driver_number = l.driver_number
                AND l.lap_duration > 0
            WHERE r.session_name = 'Race'
                AND r.final_position IS NOT NULL
            GROUP BY r.driver_number, r.driver_name, r.team_name,
                     r.circuit_short_name, r.year, r.final_position
        )
        SELECT * FROM driver_stats
        ORDER BY year, circuit_short_name
        """

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def train(self):
        """Train the model on historical data."""
        df = self.fetch_training_data()

        if df.empty:
            raise ValueError("No training data available")

        # Create binary target: 1 if won (position 1), 0 otherwise
        df['won'] = (df['FINAL_POSITION'] == 1).astype(int)

        # Encode categorical features
        df['driver_encoded'] = self.driver_encoder.fit_transform(df['DRIVER_NAME'])
        df['circuit_encoded'] = self.circuit_encoder.fit_transform(df['CIRCUIT_SHORT_NAME'])

        # Prepare features
        feature_cols = ['driver_encoded', 'circuit_encoded', 'AVG_LAP_TIME',
                       'BEST_LAP_TIME', 'TOTAL_LAPS', 'AVG_POSITION_DURING_RACE']

        X = df[feature_cols].fillna(df[feature_cols].median())
        y = df['won']

        self.model.fit(X, y)
        self.trained = True

    def predict_next_race(self, circuit: str) -> pd.DataFrame:
        """
        Predict winner for next race at given circuit.

        Args:
            circuit: Circuit short name

        Returns:
            DataFrame with drivers and their win probabilities
        """
        if not self.trained:
            self.train()

        # Fetch recent driver performance
        conn = get_snowflake_connection()

        query = f"""
        WITH recent_performance AS (
            SELECT
                r.driver_number,
                r.driver_name,
                r.team_name,
                AVG(l.lap_duration) as avg_lap_time,
                MIN(l.lap_duration) as best_lap_time,
                COUNT(l.lap_number) as total_laps,
                AVG(l.position) as avg_position_during_race
            FROM fct_race_results r
            LEFT JOIN fct_lap_times l
                ON r.session_key = l.session_key
                AND r.driver_number = l.driver_number
                AND l.lap_duration > 0
            WHERE r.session_name = 'Race'
                AND r.year >= YEAR(CURRENT_DATE()) - 1
            GROUP BY r.driver_number, r.driver_name, r.team_name
        )
        SELECT * FROM recent_performance
        """

        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return pd.DataFrame()

        # Prepare features for prediction
        df['driver_encoded'] = df['DRIVER_NAME'].apply(
            lambda x: self.driver_encoder.transform([x])[0]
            if x in self.driver_encoder.classes_ else -1
        )

        if circuit in self.circuit_encoder.classes_:
            circuit_encoded = self.circuit_encoder.transform([circuit])[0]
        else:
            circuit_encoded = -1

        df['circuit_encoded'] = circuit_encoded

        feature_cols = ['driver_encoded', 'circuit_encoded', 'AVG_LAP_TIME',
                       'BEST_LAP_TIME', 'TOTAL_LAPS', 'AVG_POSITION_DURING_RACE']

        X = df[feature_cols].fillna(df[feature_cols].median())

        # Predict probabilities
        probabilities = self.model.predict_proba(X)[:, 1]

        # Prepare results
        results = pd.DataFrame({
            'driver_name': df['DRIVER_NAME'],
            'team_name': df['TEAM_NAME'],
            'win_probability': probabilities
        })

        return results.sort_values('win_probability', ascending=False)


class PerformanceAnalyzer:
    """Analyzes and compares driver performance across seasons."""

    @staticmethod
    def compare_driver_seasons(driver_name: str, seasons: list) -> pd.DataFrame:
        """
        Compare a driver's performance across multiple seasons.

        Args:
            driver_name: Full name of driver
            seasons: List of years to compare

        Returns:
            DataFrame with season-by-season statistics
        """
        conn = get_snowflake_connection()

        seasons_str = ','.join(map(str, seasons))

        query = f"""
        WITH season_stats AS (
            SELECT
                r.year,
                r.driver_name,
                r.team_name,
                COUNT(DISTINCT r.session_key) as races,
                SUM(CASE WHEN r.final_position = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN r.final_position <= 3 THEN 1 ELSE 0 END) as podiums,
                AVG(r.final_position) as avg_position,
                MIN(r.final_position) as best_position,
                AVG(l.lap_duration) as avg_lap_time,
                MIN(l.lap_duration) as best_lap_time
            FROM fct_race_results r
            LEFT JOIN fct_lap_times l
                ON r.session_key = l.session_key
                AND r.driver_number = l.driver_number
                AND l.lap_duration > 0
            WHERE r.driver_name = '{driver_name}'
                AND r.session_name = 'Race'
                AND r.year IN ({seasons_str})
            GROUP BY r.year, r.driver_name, r.team_name
        )
        SELECT * FROM season_stats
        ORDER BY year
        """

        df = pd.read_sql(query, conn)
        conn.close()
        return df

    @staticmethod
    def predict_season_performance(driver_name: str, current_year: int) -> Dict[str, float]:
        """
        Predict end-of-season statistics for a driver.

        Args:
            driver_name: Full name of driver
            current_year: Year to predict for

        Returns:
            Dictionary with predicted wins, podiums, avg position
        """
        conn = get_snowflake_connection()

        # Get historical season data
        query = f"""
        WITH historical_seasons AS (
            SELECT
                r.year,
                COUNT(DISTINCT r.session_key) as races,
                SUM(CASE WHEN r.final_position = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN r.final_position <= 3 THEN 1 ELSE 0 END) as podiums,
                AVG(r.final_position) as avg_position
            FROM fct_race_results r
            WHERE r.driver_name = '{driver_name}'
                AND r.session_name = 'Race'
                AND r.year < {current_year}
            GROUP BY r.year
        ),
        current_progress AS (
            SELECT
                COUNT(DISTINCT r.session_key) as races_so_far,
                SUM(CASE WHEN r.final_position = 1 THEN 1 ELSE 0 END) as wins_so_far,
                SUM(CASE WHEN r.final_position <= 3 THEN 1 ELSE 0 END) as podiums_so_far,
                AVG(r.final_position) as avg_position_so_far
            FROM fct_race_results r
            WHERE r.driver_name = '{driver_name}'
                AND r.session_name = 'Race'
                AND r.year = {current_year}
        )
        SELECT * FROM historical_seasons
        UNION ALL
        SELECT {current_year} as year, * FROM current_progress
        ORDER BY year
        """

        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return {"predicted_wins": 0, "predicted_podiums": 0, "predicted_avg_position": 15}

        # Simple linear projection based on current pace
        current_data = df[df['YEAR'] == current_year].iloc[0]

        # Assume 24 races in a season (F1 2024/2025 standard)
        total_races = 24
        races_completed = current_data['RACES'] if 'RACES_SO_FAR' not in current_data else current_data['RACES_SO_FAR']

        if races_completed > 0:
            win_rate = current_data['WINS'] / races_completed
            podium_rate = current_data['PODIUMS'] / races_completed

            predicted_wins = win_rate * total_races
            predicted_podiums = podium_rate * total_races
            predicted_avg_position = current_data['AVG_POSITION']
        else:
            # Fall back to historical average
            historical = df[df['YEAR'] < current_year]
            predicted_wins = historical['WINS'].mean() if not historical.empty else 0
            predicted_podiums = historical['PODIUMS'].mean() if not historical.empty else 0
            predicted_avg_position = historical['AVG_POSITION'].mean() if not historical.empty else 15

        return {
            "predicted_wins": round(predicted_wins, 1),
            "predicted_podiums": round(predicted_podiums, 1),
            "predicted_avg_position": round(predicted_avg_position, 2)
        }


def detect_question_type(question: str) -> str:
    """
    Detect whether question is prediction, analysis, or historical.

    Returns:
        'prediction', 'analysis', or 'historical'
    """
    question_lower = question.lower()

    # Prediction keywords
    prediction_keywords = ['predict', 'will', 'next race', 'future', 'who will win',
                          'going to', 'forecast', 'expect', 'likely']

    # Analysis keywords
    analysis_keywords = ['compare', 'performance', 'across seasons', 'vs', 'versus',
                        'trend', 'improvement', 'decline', 'season by season']

    if any(keyword in question_lower for keyword in prediction_keywords):
        return 'prediction'
    elif any(keyword in question_lower for keyword in analysis_keywords):
        return 'analysis'
    else:
        return 'historical'
