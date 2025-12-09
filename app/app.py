import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from ml.ai_assistant import get_ai_response, generate_sql_from_question, answer_question_from_data
from ml.ml_predictions import detect_question_type
from ml.prediction_service import (
    RacePredictionService,
    PerformanceAnalysisService,
    PredictionRequest,
    PerformanceComparisonRequest
)
from query_builder import F1QueryBuilder, QueryFilters
from visualizations import display_visualization
from constants import (
    METRIC_OPTIONS, METRIC_HELP_TEXT, DEFAULT_METRICS,
    DIMENSION_OPTIONS, DIMENSION_HELP_TEXT, DEFAULT_DIMENSIONS,
    VISUALIZATION_OPTIONS, AI_ASSISTANT_DESCRIPTION,
    CHART_KEYWORDS, TABLE_KEYWORDS, HISTORICAL_KEYWORDS,
    PREDICTION_KEYWORDS, DRIVER_NAME_MAPPING,
    DEFAULT_PREDICTION_CIRCUIT, CURRENT_YEAR, PERFORMANCE_SEASONS_LOOKBACK,
    APP_TITLE, APP_DESCRIPTION, TAB_CUSTOM_ANALYSIS, TAB_AI_ASSISTANT,
    WARNING_NO_METRICS_DIMENSIONS, WARNING_NO_SEASONS,
    ERROR_INSUFFICIENT_DATA, ERROR_NO_DATA_FOR_DRIVER,
    PREDICTION_FALLBACK_MESSAGE, SPINNER_THINKING, SPINNER_TRAINING_MODEL,
    SPINNER_ANALYZING_PERFORMANCE, CACHE_TTL_SECONDS,
    SIDEBAR_ML_MODELS, SIDEBAR_AI_INFO, SIDEBAR_DATA_UPDATE, SIDEBAR_GITHUB_BADGE
)

# Add parent directory to path for library imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from library.connection import connection_manager
from library.error_handling import (
    setup_logger, format_user_error, validate_dataframe,
    retry, DatabaseError, DataNotFoundError
)

# Load environment variables from .env file
load_dotenv()

# Setup logger
logger = setup_logger(__name__, level=os.getenv("LOG_LEVEL", "INFO"))

st.set_page_config(page_title="ApexML – F1 Analytics", layout="wide")

# Snowflake connection and query
@st.cache_data(ttl=CACHE_TTL_SECONDS)
@retry(max_attempts=3, delay=1.0, exceptions=(DatabaseError,), logger=logger)
def query_snowflake(query: str) -> pd.DataFrame:
    """Query Snowflake with automatic retry on failures."""
    try:
        with connection_manager.get_connection(schema="ANALYTICS") as conn:
            df = pd.read_sql(query, conn)
            if df.empty:
                logger.warning(f"Query returned no results: {query[:100]}...")
            return df
    except Exception as e:
        logger.error(f"Database query failed: {e}", exc_info=True)
        raise DatabaseError(
            f"Failed to execute query: {e}",
            user_message="Unable to connect to database. Please try again later."
        )

@st.cache_resource
def get_prediction_service() -> RacePredictionService:
    """Initialize and cache prediction service."""
    return RacePredictionService()

@st.cache_resource
def get_performance_service() -> PerformanceAnalysisService:
    """Initialize and cache performance analysis service."""
    return PerformanceAnalysisService()

@st.cache_resource
def get_query_builder() -> F1QueryBuilder:
    """Initialize and cache query builder."""
    return F1QueryBuilder()

# Title
st.title(APP_TITLE)
st.markdown(APP_DESCRIPTION)

# Main Dashboard
tab1, tab2 = st.tabs([TAB_CUSTOM_ANALYSIS, TAB_AI_ASSISTANT])

with tab1:
    st.header("🔧 Custom Analysis Builder")
    st.markdown("Build your own custom analysis by selecting metrics and dimensions")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Select Metrics")
        metrics = st.multiselect(
            "Choose metrics to analyze",
            options=METRIC_OPTIONS,
            default=DEFAULT_METRICS,
            help=METRIC_HELP_TEXT
        )

    with col2:
        st.subheader("Select Dimensions")
        dimensions = st.multiselect(
            "Choose dimensions to group by",
            options=DIMENSION_OPTIONS,
            default=DEFAULT_DIMENSIONS,
            help=DIMENSION_HELP_TEXT
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
        validate_dataframe(drivers_df, required_columns=['FULL_NAME', 'TEAM_NAME'], min_rows=1)

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
        validate_dataframe(seasons_df, required_columns=['YEAR', 'CIRCUIT_SHORT_NAME', 'LOCATION'], min_rows=1)

        available_seasons = sorted(seasons_df['YEAR'].unique().tolist(), reverse=True)
        available_circuits = sorted(seasons_df['CIRCUIT_SHORT_NAME'].unique().tolist())

        # Create circuit display names with location
        circuit_display = {}
        for _, row in seasons_df.iterrows():
            circuit_key = row['CIRCUIT_SHORT_NAME']
            if circuit_key not in circuit_display:
                circuit_display[circuit_key] = f"{row['CIRCUIT_SHORT_NAME']} ({row['LOCATION']})"

    except (DatabaseError, DataNotFoundError) as e:
        logger.error(f"Failed to load filter options: {e}", exc_info=True)
        st.error(format_user_error(e))
        available_drivers = []
        available_teams = []
        available_seasons = []
        available_circuits = []
        circuit_display = {}
    except Exception as e:
        logger.error(f"Unexpected error loading filters: {e}", exc_info=True)
        st.error(format_user_error(e))
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
        options=VISUALIZATION_OPTIONS
    )

    if st.button("Generate Analysis", type="primary"):
        if not metrics or not dimensions:
            st.warning(WARNING_NO_METRICS_DIMENSIONS)
        elif not selected_seasons:
            st.warning(WARNING_NO_SEASONS)
        else:
            try:
                # Build query using query builder
                query_builder = get_query_builder()
                filters = QueryFilters(
                    seasons=selected_seasons,
                    drivers=selected_drivers if selected_drivers else None,
                    teams=selected_teams if selected_teams else None,
                    circuits=selected_circuits if selected_circuits else None
                )

                query = query_builder.build_analytics_query(metrics, dimensions, filters)
                result_df = query_snowflake(query)

                # Validate results
                validate_dataframe(result_df, min_rows=1)

                st.subheader("Analysis Results")
                st.write(f"**Rows returned:** {len(result_df)}")

                # Display visualization using visualization module
                display_visualization(result_df, viz_type)

            except (DatabaseError, DataNotFoundError) as e:
                logger.error(f"Analysis generation failed: {e}", exc_info=True)
                st.error(format_user_error(e))
            except Exception as e:
                logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
                st.error(format_user_error(e))

with tab2:
    st.header("💬 AI Assistant (ML-Powered)")
    st.markdown(AI_ASSISTANT_DESCRIPTION)

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
            with st.spinner(SPINNER_THINKING):
                # Check if user wants visualizations
                show_chart = any(word in prompt.lower() for word in CHART_KEYWORDS)
                show_table = any(word in prompt.lower() for word in TABLE_KEYWORDS)

                # Detect question type: prediction, analysis, or historical
                question_type = detect_question_type(prompt)

                if question_type == 'prediction':
                    # Handle ML predictions
                    prediction_service = get_prediction_service()

                    # Check if asking about next race winner
                    if any(keyword in prompt.lower() for keyword in PREDICTION_KEYWORDS):
                        with st.spinner(SPINNER_TRAINING_MODEL):
                            request = PredictionRequest(circuit=DEFAULT_PREDICTION_CIRCUIT, prompt=prompt)
                            result = prediction_service.predict_race_winner(request)

                            if result.success:
                                response = result.top_5_formatted

                                if show_table:
                                    st.dataframe(result.predictions, use_container_width=True)
                            else:
                                response = result.error_message or ERROR_INSUFFICIENT_DATA
                    else:
                        response = PREDICTION_FALLBACK_MESSAGE

                elif question_type == 'analysis':
                    # Handle performance analysis (compare across seasons)
                    performance_service = get_performance_service()

                    # Simple pattern matching for driver name
                    driver = None
                    for key, value in DRIVER_NAME_MAPPING.items():
                        if key in prompt.lower():
                            driver = value
                            break

                    if driver:
                        # Compare last 2-3 seasons
                        seasons = [CURRENT_YEAR - i for i in range(PERFORMANCE_SEASONS_LOOKBACK - 1, -1, -1)]

                        with st.spinner(SPINNER_ANALYZING_PERFORMANCE.format(driver=driver)):
                            request = PerformanceComparisonRequest(driver_name=driver, seasons=seasons)
                            result = performance_service.compare_driver_seasons(request)

                            if result.success:
                                response = result.formatted_summary

                                if show_table:
                                    st.dataframe(result.comparison_data, use_container_width=True)

                                if show_chart:
                                    fig = px.line(result.comparison_data, x='YEAR', y='WINS',
                                                 title=f"{driver} - Wins by Season",
                                                 markers=True)
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                response = result.error_message or ERROR_NO_DATA_FOR_DRIVER.format(driver=driver)
                    else:
                        # Fall back to SQL query for other analysis questions
                        sql = generate_sql_from_question(prompt)
                        if sql:
                            result_df = query_snowflake(sql)
                            response = answer_question_from_data(prompt, result_df)
                        else:
                            response = get_ai_response(prompt)

                else:
                    # Historical data questions - use existing SQL pipeline
                    if any(keyword in prompt.lower() for keyword in HISTORICAL_KEYWORDS):
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

                            except (DatabaseError, DataNotFoundError) as e:
                                logger.warning(f"Query failed for user question, falling back to AI: {e}")
                                response = get_ai_response(prompt)
                            except Exception as e:
                                logger.error(f"Unexpected error in AI assistant query: {e}", exc_info=True)
                                response = get_ai_response(prompt)
                        else:
                            response = get_ai_response(prompt)
                    else:
                        response = get_ai_response(prompt)

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Data Source:** {os.getenv('SNOWFLAKE_DATABASE', 'APEXML_DEV')}.{os.getenv('SNOWFLAKE_SCHEMA', 'ANALYTICS')}")
st.sidebar.markdown(SIDEBAR_DATA_UPDATE)
st.sidebar.markdown(SIDEBAR_ML_MODELS)
st.sidebar.markdown(SIDEBAR_AI_INFO)
st.sidebar.markdown("---")
st.sidebar.markdown(SIDEBAR_GITHUB_BADGE)
