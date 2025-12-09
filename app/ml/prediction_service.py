"""ML Prediction Service for F1 Analytics.

This module provides clean service interfaces for ML predictions,
separating ML logic from UI presentation.
"""
from dataclasses import dataclass
from typing import Optional, List
import pandas as pd
from .ml_predictions import RaceWinnerPredictor, PerformanceAnalyzer


@dataclass
class PredictionRequest:
    """Request for race winner prediction."""
    circuit: Optional[str] = None
    prompt: Optional[str] = None


@dataclass
class PredictionResult:
    """Structured prediction result."""
    predictions: pd.DataFrame
    top_5_formatted: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class PerformanceComparisonRequest:
    """Request for driver performance comparison."""
    driver_name: str
    seasons: List[int]


@dataclass
class PerformanceComparisonResult:
    """Structured performance comparison result."""
    comparison_data: pd.DataFrame
    formatted_summary: str
    success: bool
    error_message: Optional[str] = None


class RacePredictionService:
    """Service for ML-based race predictions."""

    def __init__(self):
        """Initialize the prediction service."""
        self._predictor: Optional[RaceWinnerPredictor] = None

    @property
    def predictor(self) -> RaceWinnerPredictor:
        """Lazy load the predictor."""
        if self._predictor is None:
            self._predictor = RaceWinnerPredictor()
        return self._predictor

    def predict_race_winner(self, request: PredictionRequest) -> PredictionResult:
        """Predict race winner with error handling.

        Args:
            request: Prediction request with circuit information

        Returns:
            PredictionResult with predictions and formatted output
        """
        try:
            # Use provided circuit or default to generic circuit
            circuit = request.circuit or 'monza'

            # Get predictions
            predictions_df = self.predictor.predict_next_race(circuit)

            if predictions_df.empty:
                return PredictionResult(
                    predictions=pd.DataFrame(),
                    top_5_formatted="",
                    success=False,
                    error_message="Not enough data available for predictions"
                )

            # Format top 5 predictions
            top_5 = predictions_df.head(5)
            formatted = self._format_predictions(top_5)

            return PredictionResult(
                predictions=predictions_df,
                top_5_formatted=formatted,
                success=True
            )

        except Exception as e:
            return PredictionResult(
                predictions=pd.DataFrame(),
                top_5_formatted="",
                success=False,
                error_message=f"Prediction failed: {str(e)}"
            )

    def _format_predictions(self, predictions: pd.DataFrame) -> str:
        """Format predictions for display.

        Args:
            predictions: DataFrame with prediction results

        Returns:
            Formatted string for display
        """
        result = "Based on ML analysis of historical performance:\n\n"

        for idx, row in predictions.iterrows():
            prob_pct = row['win_probability'] * 100
            result += f"- **{row['driver_name']}** ({row['team_name']}): {prob_pct:.1f}% chance\n"

        result += "\n*Predictions based on recent race performance, lap times, and historical circuit data.*"

        return result


class PerformanceAnalysisService:
    """Service for driver performance analysis."""

    def __init__(self):
        """Initialize the performance analysis service."""
        self._analyzer: Optional[PerformanceAnalyzer] = None

    @property
    def analyzer(self) -> PerformanceAnalyzer:
        """Lazy load the analyzer."""
        if self._analyzer is None:
            self._analyzer = PerformanceAnalyzer()
        return self._analyzer

    def compare_driver_seasons(
        self,
        request: PerformanceComparisonRequest
    ) -> PerformanceComparisonResult:
        """Compare driver performance across seasons.

        Args:
            request: Comparison request with driver and seasons

        Returns:
            PerformanceComparisonResult with analysis data
        """
        try:
            # Get comparison data
            comparison_df = self.analyzer.compare_driver_seasons(
                request.driver_name,
                request.seasons
            )

            if comparison_df.empty:
                return PerformanceComparisonResult(
                    comparison_data=pd.DataFrame(),
                    formatted_summary="",
                    success=False,
                    error_message=f"No data available for {request.driver_name} in those seasons"
                )

            # Format summary
            formatted = self._format_comparison(request.driver_name, comparison_df)

            return PerformanceComparisonResult(
                comparison_data=comparison_df,
                formatted_summary=formatted,
                success=True
            )

        except Exception as e:
            return PerformanceComparisonResult(
                comparison_data=pd.DataFrame(),
                formatted_summary="",
                success=False,
                error_message=f"Performance analysis failed: {str(e)}"
            )

    def _format_comparison(self, driver_name: str, comparison: pd.DataFrame) -> str:
        """Format performance comparison for display.

        Args:
            driver_name: Name of the driver
            comparison: DataFrame with comparison data

        Returns:
            Formatted string for display
        """
        result = f"**{driver_name}'s Performance Comparison:**\n\n"

        for _, row in comparison.iterrows():
            result += f"**{int(row['YEAR'])} ({row['TEAM_NAME']})**:\n"
            result += f"- Races: {int(row['RACES'])}, Wins: {int(row['WINS'])}, Podiums: {int(row['PODIUMS'])}\n"
            result += f"- Average position: {row['AVG_POSITION']:.2f}\n"

            if row['AVG_LAP_TIME']:
                result += f"- Average lap time: {row['AVG_LAP_TIME']:.2f}s\n"

            result += "\n"

        return result
