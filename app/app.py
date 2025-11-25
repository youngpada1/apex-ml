import streamlit as st
import pandas as pd
import snowflake.connector
import os
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from ai_assistant import get_ai_response, generate_sql_from_question, answer_question_from_data

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
                "Session"
            ],
            default=["Driver"]
        )

    # Filters section - load available drivers and teams
    try:
        drivers_teams_query = """
        SELECT DISTINCT driver_number, full_name, team_name
        FROM dim_drivers
        ORDER BY full_name
        """
        drivers_df = query_snowflake(drivers_teams_query)
        available_drivers = drivers_df['FULL_NAME'].tolist()
        available_teams = sorted(drivers_df['TEAM_NAME'].unique().tolist())
    except Exception as e:
        st.error(f"Error loading drivers/teams: {e}")
        available_drivers = []
        available_teams = []

    st.subheader("Filters")
    filter_col1, filter_col2 = st.columns(2)

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
                if "Driver" in dimensions:
                    dim_sql.append("d.full_name as driver")
                    group_by.append("d.full_name")
                if "Team" in dimensions:
                    dim_sql.append("d.team_name as team")
                    group_by.append("d.team_name")
                if "Session" in dimensions:
                    dim_sql.append("l.session_key as session")
                    group_by.append("l.session_key")

                # Build WHERE clause with filters
                where_conditions = ["l.lap_duration > 0"]
                if selected_driver != "All":
                    where_conditions.append(f"d.full_name = '{selected_driver}'")
                if selected_team != "All":
                    where_conditions.append(f"d.team_name = '{selected_team}'")

                query = f"""
                SELECT
                    {', '.join(dim_sql)},
                    {', '.join(metric_sql)}
                FROM fct_lap_times l
                JOIN dim_drivers d ON l.driver_number = d.driver_number
                LEFT JOIN fct_race_results r ON l.driver_number = r.driver_number AND l.session_key = r.session_key
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
    st.header("💬 AI Assistant")
    st.markdown("Ask questions about F1 data and get insights, charts, and predictions")

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

                # Check if question requires SQL query
                if any(keyword in prompt.lower() for keyword in ["who", "what", "which", "how many", "fastest", "slowest", "average", "last", "latest"]):
                    # Try to generate and execute SQL behind the scenes
                    sql = generate_sql_from_question(prompt)

                    if sql:
                        # TEMPORARY DEBUG: Show SQL query
                        with st.expander("🔍 Debug: View generated SQL"):
                            st.code(sql, language="sql")

                        try:
                            # Execute the generated SQL
                            result_df = query_snowflake(sql)

                            if not result_df.empty:
                                # Get plain English answer from the data
                                response = answer_question_from_data(prompt, result_df)

                                # Show table ONLY if explicitly requested
                                if show_table:
                                    st.dataframe(result_df, use_container_width=True)

                                # Show chart ONLY if explicitly requested
                                if show_chart and len(result_df.columns) >= 2:
                                    fig = px.bar(result_df, x=result_df.columns[0], y=result_df.columns[1])
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                response = "I couldn't find any data to answer that question. Try asking something else!"

                        except Exception as e:
                            # Fall back to general response on error
                            response = get_ai_response(prompt)
                    else:
                        response = get_ai_response(prompt)
                else:
                    # General question - get direct AI response
                    response = get_ai_response(prompt)

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Data Source:** {os.getenv('SNOWFLAKE_DATABASE', 'APEXML_DEV')}.{os.getenv('SNOWFLAKE_SCHEMA', 'ANALYTICS')}")
st.sidebar.markdown("**Updated:** Real-time via dbt transformations")
