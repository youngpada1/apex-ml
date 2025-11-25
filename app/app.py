import streamlit as st
import pandas as pd
import snowflake.connector
import os
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from ai_assistant import get_ai_response, generate_sql_from_question, answer_question_from_data
from ml_predictions import RaceWinnerPredictor, PerformanceAnalyzer, detect_question_type

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="ApexML – F1 Analytics", layout="wide")

# Snowflake connection
@st.cache_resource
def get_snowflake_connection():
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
        schema=os.getenv('SNOWFLAKE_SCHEMA', 'ANALYTICS'),
        role=os.getenv('SNOWFLAKE_ROLE', 'ACCOUNTADMIN')
    )

@st.cache_data(ttl=300)
def query_snowflake(query):
    conn = get_snowflake_connection()
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
                "Average Position",
                "Best Position",
                "Worst Position",
                "Total Sessions"
            ],
            default=["Average Lap Time", "Total Laps"]
        )

    with col2:
        st.subheader("Select Dimensions")
        dimensions = st.multiselect(
            "Choose dimensions to group by",
            options=[
                "Driver",
                "Team",
                "Season",
                "Circuit"
            ],
            default=["Driver"]
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

    st.subheader("Filters")
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        # Show driver filter only if Driver dimension is selected
        if "Driver" in dimensions:
            selected_driver = st.selectbox(
                "Filter by Driver",
                options=["All"] + available_drivers,
                key="driver_filter"
            )
        else:
            selected_driver = "All"

    with filter_col2:
        # Show team filter only if Team dimension is selected
        if "Team" in dimensions:
            selected_team = st.selectbox(
                "Filter by Team",
                options=["All"] + available_teams,
                key="team_filter"
            )
        else:
            selected_team = "All"

    with filter_col3:
        # Show season filter only if Season dimension is selected
        if "Season" in dimensions:
            selected_season = st.selectbox(
                "Filter by Season",
                options=["All"] + available_seasons,
                key="season_filter"
            )
        else:
            selected_season = "All"

    # Additional row for circuit filter
    if "Circuit" in dimensions:
        selected_circuit = st.selectbox(
            "Filter by Circuit",
            options=["All"] + [circuit_display.get(c, c) for c in available_circuits],
            key="circuit_filter"
        )
        # Extract just the circuit short name if not "All"
        if selected_circuit != "All":
            selected_circuit = selected_circuit.split(" (")[0]
    else:
        selected_circuit = "All"

    st.subheader("Visualization Type")
    viz_type = st.selectbox(
        "Choose chart type",
        options=["Table", "Bar Chart", "Line Chart", "Scatter Plot"]
    )

    if st.button("Generate Analysis", type="primary"):
        if not metrics or not dimensions:
            st.warning("Please select at least one metric and one dimension")
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

                dim_sql = []
                group_by = []
                needs_race_results = False

                if "Driver" in dimensions:
                    dim_sql.append("d.full_name as driver")
                    group_by.append("d.full_name")
                if "Team" in dimensions:
                    dim_sql.append("d.team_name as team")
                    group_by.append("d.team_name")
                if "Season" in dimensions:
                    dim_sql.append("r.year as season")
                    group_by.append("r.year")
                    needs_race_results = True
                if "Circuit" in dimensions:
                    dim_sql.append("r.circuit_short_name as circuit")
                    dim_sql.append("r.location as location")
                    group_by.append("r.circuit_short_name")
                    group_by.append("r.location")
                    needs_race_results = True

                # Build WHERE clause with filters
                where_conditions = ["l.lap_duration > 0"]
                if selected_driver != "All":
                    where_conditions.append(f"d.full_name = '{selected_driver}'")
                if selected_team != "All":
                    where_conditions.append(f"d.team_name = '{selected_team}'")
                if selected_season != "All":
                    where_conditions.append(f"r.year = {selected_season}")
                    needs_race_results = True
                if selected_circuit != "All":
                    where_conditions.append(f"r.circuit_short_name = '{selected_circuit}'")
                    needs_race_results = True

                # Ensure we join with race_results if needed
                join_clause = "LEFT JOIN fct_race_results r ON l.driver_number = r.driver_number AND l.session_key = r.session_key"
                if needs_race_results:
                    # Require race_results to be present for Season/Circuit filtering
                    where_conditions.append("r.session_key IS NOT NULL")

                query = f"""
                SELECT
                    {', '.join(dim_sql)},
                    {', '.join(metric_sql)}
                FROM fct_lap_times l
                JOIN dim_drivers d ON l.driver_number = d.driver_number
                {join_clause}
                WHERE {' AND '.join(where_conditions)}
                GROUP BY {', '.join(group_by)}
                ORDER BY {metric_sql[0].split(' as ')[1]}
                LIMIT 20
                """

                result_df = query_snowflake(query)

                st.subheader("Analysis Results")

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
