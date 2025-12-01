import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from ml.ai_assistant import get_ai_response, generate_sql_from_question, answer_question_from_data
from ml.ml_predictions import RaceWinnerPredictor, PerformanceAnalyzer, detect_question_type

# Add parent directory to path for library imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from library.connection import connection_manager

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="ApexML – F1 Analytics", layout="wide")

# Snowflake connection and query
@st.cache_data(ttl=300)
def query_snowflake(query):
    with connection_manager.get_connection(schema="ANALYTICS") as conn:
        return pd.read_sql(query, conn)

@st.cache_resource
def get_ml_predictor():
    """Initialize and cache ML predictor."""
    return RaceWinnerPredictor()

@st.cache_resource
def get_performance_analyzer():
    """Initialize and cache performance analyzer."""
    return PerformanceAnalyzer()

# Title
st.title("🏁 ApexML – F1 Race Analytics")
st.markdown("Real-time F1 data analytics powered by Snowflake, dbt, and OpenF1 API")

# Main Dashboard
tab1, tab2 = st.tabs(["🔧 Custom Analysis", "💬 AI Assistant"])

with tab1:
    st.header("🔧 Custom Analysis Builder")
    st.markdown("Build your own custom analysis by selecting metrics and dimensions")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Select Metrics")
        metrics = st.multiselect(
            "Choose metrics to analyze",
            options=[
                "Average Lap Time",
                "Best Lap Time",
                "Total Laps",
                "Fastest Laps Count",
                "Average Sector 1",
                "Average Sector 2",
                "Average Sector 3",
                "Average Position",
                "Best Position",
                "Worst Position",
                "Pit Stop Laps",
                "Total Sessions"
            ],
            default=["Average Lap Time", "Total Laps"],
            help="""
            📊 LAP PERFORMANCE
            • Average Lap Time: Mean lap duration in seconds
            • Best Lap Time: Fastest lap recorded
            • Total Laps: Count of laps completed
            • Fastest Laps Count: Number of times driver achieved fastest lap

            ⏱️ SECTOR TIMES
            • Average Sector 1/2/3: Mean sector times (track is divided into 3 sectors)

            🏁 RACE POSITION
            • Average/Best/Worst Position: Race finishing positions

            🔧 PIT STRATEGY
            • Pit Stop Laps: Laps where driver exited pit lane (first lap after pit stop)

            📅 GENERAL
            • Total Sessions: Number of race sessions
            """
        )

    with col2:
        st.subheader("Select Dimensions")
        dimensions = st.multiselect(
            "Choose dimensions to group by",
            options=[
                "Driver",
                "Team",
                "Season",
                "Circuit",
                "Laps"
            ],
            default=["Driver"],
            help="""
            👤 CORE DIMENSIONS
            • Driver: Group by individual driver (e.g., Max Verstappen, Lewis Hamilton)
            • Team: Group by constructor/team (e.g., Red Bull Racing, Mercedes)

            📍 TIME & LOCATION
            • Season: Group by year (e.g., 2023, 2024, 2025)
            • Circuit: Group by race track (e.g., Monaco, Silverstone, Monza)

            🔍 DETAILED ANALYSIS
            • Laps: Show lap-by-lap details including lap number, position during lap, and pit stops

            💡 TIP: Combine dimensions for detailed analysis
            Example: Driver + Circuit shows performance per driver at each track
            """
        )

    # Filters section - load available drivers, teams, seasons, and circuits
    try:
        # Load drivers and teams
        drivers_teams_query = """
        SELECT DISTINCT driver_number, full_name, team_name
        FROM dim_drivers
        ORDER BY full_name
        """
        drivers_df = query_snowflake(drivers_teams_query)
        available_drivers = drivers_df['FULL_NAME'].tolist()
        available_teams = sorted(drivers_df['TEAM_NAME'].unique().tolist())

        # Load seasons and circuits from race results
        seasons_circuits_query = """
        SELECT DISTINCT
            year,
            circuit_short_name,
            location,
            date_start
        FROM fct_race_results
        WHERE session_name = 'Race'
        ORDER BY year DESC, date_start DESC
        """
        seasons_df = query_snowflake(seasons_circuits_query)
        available_seasons = sorted(seasons_df['YEAR'].unique().tolist(), reverse=True)
        available_circuits = sorted(seasons_df['CIRCUIT_SHORT_NAME'].unique().tolist())

        # Create circuit display names with location
        circuit_display = {}
        for _, row in seasons_df.iterrows():
            circuit_key = row['CIRCUIT_SHORT_NAME']
            if circuit_key not in circuit_display:
                circuit_display[circuit_key] = f"{row['CIRCUIT_SHORT_NAME']} ({row['LOCATION']})"

    except Exception as e:
        st.error(f"Error loading filter options: {e}")
        available_drivers = []
        available_teams = []
        available_seasons = []
        available_circuits = []
        circuit_display = {}

    # Smart filters - only show relevant filters based on selected dimensions
    st.divider()

    # REQUIRED: Season filter (multi-select)
    st.markdown("**📅 Season (Required)**")
    selected_seasons = st.multiselect(
        "Select one or more seasons to analyze",
        options=available_seasons,
        default=[available_seasons[0]] if available_seasons else [],
        key="season_filter_required",
        help="Select seasons to compare. Required to provide temporal context for analysis."
    )

    # Build filter columns dynamically based on selected dimensions
    active_filters = []
    if "Driver" in dimensions:
        active_filters.append("driver")
    if "Team" in dimensions:
        active_filters.append("team")
    if "Circuit" in dimensions:
        active_filters.append("circuit")

    if active_filters:
        # Create columns only for active filters
        filter_cols = st.columns(len(active_filters))

        selected_drivers = []
        selected_teams = []
        selected_circuits = []

        for idx, filter_type in enumerate(active_filters):
            with filter_cols[idx]:
                if filter_type == "driver":
                    selected_drivers = st.multiselect(
                        "🏎️ Driver",
                        options=available_drivers,
                        default=[],
                        key="driver_filter",
                        help="Select one or more drivers to compare. Leave empty for all drivers."
                    )
                elif filter_type == "team":
                    selected_teams = st.multiselect(
                        "🏁 Team",
                        options=available_teams,
                        default=[],
                        key="team_filter",
                        help="Select one or more teams to compare. Leave empty for all teams."
                    )
                elif filter_type == "circuit":
                    circuit_options = [circuit_display.get(c, c) for c in available_circuits]
                    selected_circuits_display = st.multiselect(
                        "🏟️ Circuit",
                        options=circuit_options,
                        default=[],
                        key="circuit_filter",
                        help="Select one or more circuits to compare. Leave empty for all circuits."
                    )
                    # Extract just the circuit short names
                    selected_circuits = [c.split(" (")[0] for c in selected_circuits_display]
    else:
        selected_drivers = []
        selected_teams = []
        selected_circuits = []

    st.subheader("Visualization Type")
    viz_type = st.selectbox(
        "Choose chart type",
        options=["Table", "Bar Chart", "Line Chart", "Scatter Plot"]
    )

    if st.button("Generate Analysis", type="primary"):
        if not metrics or not dimensions:
            st.warning("Please select at least one metric and one dimension")
        elif not selected_seasons:
            st.warning("⚠️ Please select at least one season to analyze")
        else:
            try:
                # Build query based on selections
                metric_sql = []
                if "Average Lap Time" in metrics:
                    metric_sql.append("AVG(l.lap_duration) as avg_lap_time")
                if "Best Lap Time" in metrics:
                    metric_sql.append("MIN(l.lap_duration) as best_lap_time")
                if "Total Laps" in metrics:
                    metric_sql.append("COUNT(*) as total_laps")
                if "Average Position" in metrics:
                    metric_sql.append("AVG(r.final_position) as avg_position")
                if "Best Position" in metrics:
                    metric_sql.append("MIN(r.final_position) as best_position")
                if "Worst Position" in metrics:
                    metric_sql.append("MAX(r.final_position) as worst_position")
                if "Total Sessions" in metrics:
                    metric_sql.append("COUNT(DISTINCT l.session_key) as total_sessions")
                if "Pit Stop Laps" in metrics:
                    metric_sql.append("SUM(CASE WHEN rl.is_pit_out_lap THEN 1 ELSE 0 END) as pit_stop_laps")
                if "Average Sector 1" in metrics:
                    metric_sql.append("AVG(l.segment_1_duration) as avg_sector_1")
                if "Average Sector 2" in metrics:
                    metric_sql.append("AVG(l.segment_2_duration) as avg_sector_2")
                if "Average Sector 3" in metrics:
                    metric_sql.append("AVG(l.segment_3_duration) as avg_sector_3")
                if "Fastest Laps Count" in metrics:
                    metric_sql.append("SUM(CASE WHEN l.is_driver_fastest_lap THEN 1 ELSE 0 END) as fastest_laps_count")

                dim_sql = []
                group_by = []
                needs_race_results = False
                needs_raw_laps = "Pit Stop Laps" in metrics

                if "Driver" in dimensions:
                    dim_sql.append("d.full_name as driver")
                    group_by.append("d.full_name")
                if "Team" in dimensions:
                    dim_sql.append("d.team_name as team")
                    group_by.append("d.team_name")
                if "Season" in dimensions:
                    dim_sql.append("l.year as season")
                    group_by.append("l.year")
                if "Circuit" in dimensions:
                    dim_sql.append("l.circuit_short_name as circuit")
                    group_by.append("l.circuit_short_name")
                if "Laps" in dimensions:
                    dim_sql.append("l.lap_number as lap")
                    dim_sql.append("l.lap_position as position_during_lap")
                    dim_sql.append("CASE WHEN rl.is_pit_out_lap THEN 'Yes' ELSE 'No' END as is_pit_lap")
                    group_by.append("l.lap_number")
                    group_by.append("l.lap_position")
                    group_by.append("rl.is_pit_out_lap")
                    needs_raw_laps = True

                # Build WHERE clause with filters
                where_conditions = ["l.lap_duration > 0"]

                # Season filter (required - always applied)
                if selected_seasons:
                    if len(selected_seasons) == 1:
                        where_conditions.append(f"l.year = {selected_seasons[0]}")
                    else:
                        season_list = ', '.join(map(str, selected_seasons))
                        where_conditions.append(f"l.year IN ({season_list})")

                # Driver filter (multi-select)
                if selected_drivers:
                    if len(selected_drivers) == 1:
                        where_conditions.append(f"d.full_name = '{selected_drivers[0]}'")
                    else:
                        driver_list = "', '".join(selected_drivers)
                        where_conditions.append(f"d.full_name IN ('{driver_list}')")

                # Team filter (multi-select)
                if selected_teams:
                    if len(selected_teams) == 1:
                        where_conditions.append(f"d.team_name = '{selected_teams[0]}'")
                    else:
                        team_list = "', '".join(selected_teams)
                        where_conditions.append(f"d.team_name IN ('{team_list}')")

                # Circuit filter (multi-select)
                if selected_circuits:
                    if len(selected_circuits) == 1:
                        where_conditions.append(f"l.circuit_short_name = '{selected_circuits[0]}'")
                    else:
                        circuit_list = "', '".join(selected_circuits)
                        where_conditions.append(f"l.circuit_short_name IN ('{circuit_list}')'")

                # Build JOIN clauses
                join_clauses = ["JOIN dim_drivers d ON l.driver_number = d.driver_number"]

                # Add raw laps join for pit stop data
                if needs_raw_laps:
                    join_clauses.append("LEFT JOIN APEXML_DEV.RAW.LAPS rl ON l.session_key = rl.session_key AND l.driver_number = rl.driver_number AND l.lap_number = rl.lap_number")

                # Add race results join if needed (for position metrics)
                if "Average Position" in metrics or "Best Position" in metrics or "Worst Position" in metrics:
                    join_clauses.append("LEFT JOIN fct_race_results r ON l.driver_number = r.driver_number AND l.session_key = r.session_key")

                query = f"""
                SELECT
                    {', '.join(dim_sql)},
                    {', '.join(metric_sql)}
                FROM fct_lap_times l
                {chr(10).join(join_clauses)}
                WHERE {' AND '.join(where_conditions)}
                GROUP BY {', '.join(group_by)}
                ORDER BY {metric_sql[0].split(' as ')[1]}
                LIMIT 100
                """

                # Debug: Show the generated query
                with st.expander("🔍 Debug: View Generated SQL Query"):
                    st.code(query, language="sql")

                result_df = query_snowflake(query)

                st.subheader("Analysis Results")
                st.write(f"**Rows returned:** {len(result_df)}")

                if viz_type == "Table":
                    st.dataframe(result_df, use_container_width=True)
                elif viz_type == "Bar Chart" and not result_df.empty:
                    fig = px.bar(result_df, x=result_df.columns[0], y=result_df.columns[-1])
                    st.plotly_chart(fig, use_container_width=True)
                elif viz_type == "Line Chart" and not result_df.empty:
                    fig = px.line(result_df, x=result_df.columns[0], y=result_df.columns[-1])
                    st.plotly_chart(fig, use_container_width=True)
                elif viz_type == "Scatter Plot" and not result_df.empty and len(result_df.columns) >= 3:
                    fig = px.scatter(result_df, x=result_df.columns[1], y=result_df.columns[2])
                    st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Error generating analysis: {e}")

with tab2:
    st.header("💬 AI Assistant (ML-Powered)")
    st.markdown("""
    Ask questions about F1 data and get ML-powered predictions and analytics:
    - **Predictions**: "Who will win the next race?" (ML model trained on historical performance)
    - **Analysis**: "Compare Verstappen's performance across 2023-2025" (Multi-season trends)
    - **Historical**: "Who won the last race?" (Real-time data queries)
    """)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask me anything about F1 data..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Check if user wants visualizations
                show_chart = any(word in prompt.lower() for word in ["chart", "plot", "graph", "visualize", "show"])
                show_table = any(word in prompt.lower() for word in ["table", "show data", "raw data"])

                # Detect question type: prediction, analysis, or historical
                question_type = detect_question_type(prompt)

                if question_type == 'prediction':
                    # Handle ML predictions
                    try:
                        predictor = get_ml_predictor()

                        # Check if asking about next race winner
                        if 'next race' in prompt.lower() or 'will win' in prompt.lower():
                            # Extract circuit if mentioned, otherwise use default
                            # For now, predict for a generic upcoming race
                            with st.spinner("Training ML model and generating predictions..."):
                                predictions_df = predictor.predict_next_race('monza')  # Default circuit

                                if not predictions_df.empty:
                                    top_5 = predictions_df.head(5)

                                    response = f"Based on ML analysis of historical performance:\n\n"
                                    for idx, row in top_5.iterrows():
                                        prob_pct = row['win_probability'] * 100
                                        response += f"- **{row['driver_name']}** ({row['team_name']}): {prob_pct:.1f}% chance\n"

                                    response += "\n*Predictions based on recent race performance, lap times, and historical circuit data.*"

                                    if show_table:
                                        st.dataframe(predictions_df, use_container_width=True)
                                else:
                                    response = "I don't have enough data yet to make predictions. Try asking once historical data is loaded!"
                        else:
                            # Other prediction questions
                            response = "I can predict race winners and performance trends. Try asking 'Who will win the next race?'"

                    except Exception as e:
                        response = f"ML prediction is still warming up. Historical data may still be loading. Error: {str(e)}"

                elif question_type == 'analysis':
                    # Handle performance analysis (compare across seasons)
                    try:
                        analyzer = get_performance_analyzer()

                        # Simple pattern matching for driver name
                        # In production, would use NER or better parsing
                        driver = None
                        if 'verstappen' in prompt.lower():
                            driver = 'Max Verstappen'
                        elif 'hamilton' in prompt.lower():
                            driver = 'Lewis Hamilton'
                        elif 'leclerc' in prompt.lower():
                            driver = 'Charles Leclerc'

                        if driver:
                            # Compare last 2-3 seasons
                            current_year = 2025
                            seasons = [current_year - 2, current_year - 1, current_year]

                            with st.spinner(f"Analyzing {driver}'s performance across seasons..."):
                                comparison_df = analyzer.compare_driver_seasons(driver, seasons)

                                if not comparison_df.empty:
                                    response = f"**{driver}'s Performance Comparison:**\n\n"

                                    for _, row in comparison_df.iterrows():
                                        response += f"**{int(row['YEAR'])} ({row['TEAM_NAME']})**:\n"
                                        response += f"- Races: {int(row['RACES'])}, Wins: {int(row['WINS'])}, Podiums: {int(row['PODIUMS'])}\n"
                                        response += f"- Average position: {row['AVG_POSITION']:.2f}\n"
                                        if row['AVG_LAP_TIME']:
                                            response += f"- Average lap time: {row['AVG_LAP_TIME']:.2f}s\n"
                                        response += "\n"

                                    if show_table:
                                        st.dataframe(comparison_df, use_container_width=True)

                                    if show_chart:
                                        fig = px.line(comparison_df, x='YEAR', y='WINS',
                                                     title=f"{driver} - Wins by Season",
                                                     markers=True)
                                        st.plotly_chart(fig, use_container_width=True)
                                else:
                                    response = f"No data available for {driver} in those seasons."
                        else:
                            # Fall back to SQL query for other analysis questions
                            sql = generate_sql_from_question(prompt)
                            if sql:
                                result_df = query_snowflake(sql)
                                response = answer_question_from_data(prompt, result_df)
                            else:
                                response = get_ai_response(prompt)

                    except Exception as e:
                        response = f"Performance analysis failed: {str(e)}"

                else:
                    # Historical data questions - use existing SQL pipeline
                    if any(keyword in prompt.lower() for keyword in ["who", "what", "which", "how many", "fastest", "slowest", "average", "last", "latest"]):
                        sql = generate_sql_from_question(prompt)

                        if sql:
                            try:
                                result_df = query_snowflake(sql)

                                if not result_df.empty:
                                    response = answer_question_from_data(prompt, result_df)

                                    if show_table:
                                        st.dataframe(result_df, use_container_width=True)

                                    if show_chart and len(result_df.columns) >= 2:
                                        fig = px.bar(result_df, x=result_df.columns[0], y=result_df.columns[1])
                                        st.plotly_chart(fig, use_container_width=True)
                                else:
                                    response = "I couldn't find any data to answer that question. Try asking something else!"

                            except Exception as e:
                                response = get_ai_response(prompt)
                        else:
                            response = get_ai_response(prompt)
                    else:
                        response = get_ai_response(prompt)

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Data Source:** {os.getenv('SNOWFLAKE_DATABASE', 'APEXML_DEV')}.{os.getenv('SNOWFLAKE_SCHEMA', 'ANALYTICS')}")
st.sidebar.markdown("**Updated:** Real-time via dbt transformations")
st.sidebar.markdown("**ML Models:** Random Forest (Win Prediction), Gradient Boosting (Performance)")
st.sidebar.markdown("**AI:** OpenRouter (GPT-4o-mini) + scikit-learn")
