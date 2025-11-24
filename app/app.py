import streamlit as st
import pandas as pd
import snowflake.connector
import os
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="ApexML – F1 Analytics", layout="wide")

# Snowflake connection
@st.cache_resource
def get_snowflake_connection():
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    # Read private key from environment variable
    private_key_str = os.getenv("SNOWFLAKE_PRIVATE_KEY")
    if not private_key_str:
        raise ValueError("SNOWFLAKE_PRIVATE_KEY environment variable is not set")

    # Parse the private key
    private_key = serialization.load_pem_private_key(
        private_key_str.encode('utf-8'),
        password=None,
        backend=default_backend()
    )

    pkb = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        private_key=pkb,
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

# Sidebar
st.sidebar.header("Filters")

# Get available drivers
try:
    drivers_query = """
    SELECT DISTINCT driver_number, full_name, team_name
    FROM dim_drivers
    ORDER BY full_name
    """
    drivers_df = query_snowflake(drivers_query)

    selected_driver = st.sidebar.selectbox(
        "Select Driver",
        options=["All"] + drivers_df['FULL_NAME'].tolist()
    )
except Exception as e:
    st.sidebar.error(f"Error loading drivers: {e}")
    drivers_df = pd.DataFrame()
    selected_driver = "All"

# Main Dashboard
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🏎️ Driver Performance", "⏱️ Lap Analysis", "🔧 Custom Analysis", "💬 AI Assistant"])

with tab1:
    st.header("Race Overview")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    try:
        with col1:
            total_drivers = query_snowflake("SELECT COUNT(*) as cnt FROM dim_drivers")
            st.metric("Total Drivers", total_drivers['CNT'].iloc[0])

        with col2:
            total_laps = query_snowflake("SELECT COUNT(*) as cnt FROM fct_lap_times")
            st.metric("Total Laps", total_laps['CNT'].iloc[0])

        with col3:
            avg_lap = query_snowflake("SELECT AVG(lap_duration) as avg FROM fct_lap_times WHERE lap_duration > 0")
            avg_value = avg_lap['AVG'].iloc[0]
            st.metric("Avg Lap Time", f"{avg_value:.2f}s" if avg_value else "N/A")

        with col4:
            total_races = query_snowflake("SELECT COUNT(DISTINCT session_key) as cnt FROM fct_race_results")
            st.metric("Sessions", total_races['CNT'].iloc[0])

        # Driver standings
        st.subheader("Driver Standings")
        standings_query = """
        SELECT
            d.driver_number,
            d.full_name,
            d.team_name,
            COUNT(DISTINCT r.session_key) as races,
            AVG(r.final_position) as avg_position
        FROM fct_race_results r
        JOIN dim_drivers d ON r.driver_number = d.driver_number
        GROUP BY d.driver_number, d.full_name, d.team_name
        ORDER BY avg_position
        LIMIT 10
        """
        standings_df = query_snowflake(standings_query)
        st.dataframe(standings_df, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading overview data: {e}")

with tab2:
    st.header("Driver Performance")

    if selected_driver != "All" and not drivers_df.empty:
        try:
            driver_num = drivers_df[drivers_df['FULL_NAME'] == selected_driver]['DRIVER_NUMBER'].iloc[0]

            # Driver info
            driver_info_query = f"""
            SELECT * FROM dim_drivers WHERE driver_number = {driver_num}
            """
            driver_info = query_snowflake(driver_info_query)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Driver", driver_info['FULL_NAME'].iloc[0])
            with col2:
                st.metric("Team", driver_info['TEAM_NAME'].iloc[0])
            with col3:
                st.metric("Number", driver_info['DRIVER_NUMBER'].iloc[0])

            # Lap times
            st.subheader("Lap Times Distribution")
            lap_times_query = f"""
            SELECT
                lap_number,
                lap_duration
            FROM fct_lap_times
            WHERE driver_number = {driver_num}
            AND lap_duration > 0
            ORDER BY lap_number
            """
            lap_times_df = query_snowflake(lap_times_query)

            if not lap_times_df.empty:
                st.line_chart(lap_times_df.set_index('LAP_NUMBER')['LAP_DURATION'])

                # Stats
                st.subheader("Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Best Lap", f"{lap_times_df['LAP_DURATION'].min():.2f}s")
                with col2:
                    st.metric("Average Lap", f"{lap_times_df['LAP_DURATION'].mean():.2f}s")
                with col3:
                    st.metric("Total Laps", len(lap_times_df))
            else:
                st.info("No lap data available for this driver")
        except Exception as e:
            st.error(f"Error loading driver performance: {e}")
    else:
        st.info("Please select a driver from the sidebar")

with tab3:
    st.header("Lap Analysis")

    try:
        # Fastest laps
        st.subheader("Top 10 Fastest Laps")
        fastest_laps_query = """
        SELECT
            l.session_key,
            d.full_name,
            d.team_name,
            l.lap_number,
            l.lap_duration
        FROM fct_lap_times l
        JOIN dim_drivers d ON l.driver_number = d.driver_number
        WHERE l.lap_duration > 0
        ORDER BY l.lap_duration
        LIMIT 10
        """
        fastest_laps_df = query_snowflake(fastest_laps_query)
        st.dataframe(fastest_laps_df, use_container_width=True)

        # Lap time comparison
        st.subheader("Team Comparison")
        team_comparison_query = """
        SELECT
            d.team_name,
            COUNT(*) as total_laps,
            AVG(l.lap_duration) as avg_lap_time,
            MIN(l.lap_duration) as best_lap
        FROM fct_lap_times l
        JOIN dim_drivers d ON l.driver_number = d.driver_number
        WHERE l.lap_duration > 0
        GROUP BY d.team_name
        ORDER BY avg_lap_time
        """
        team_comparison_df = query_snowflake(team_comparison_query)
        st.dataframe(team_comparison_df, use_container_width=True)
    except Exception as e:
        st.error(f"Error loading lap analysis: {e}")

with tab4:
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

                query = f"""
                SELECT
                    {', '.join(dim_sql)},
                    {', '.join(metric_sql)}
                FROM fct_lap_times l
                JOIN dim_drivers d ON l.driver_number = d.driver_number
                LEFT JOIN fct_race_results r ON l.driver_number = r.driver_number AND l.session_key = r.session_key
                WHERE l.lap_duration > 0
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

with tab5:
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

        # Generate response (placeholder for now - will integrate LLM next)
        with st.chat_message("assistant"):
            response = "🤖 AI Assistant coming soon! I'll be able to:\n\n"
            response += "- Answer questions about driver performance\n"
            response += "- Generate custom charts and visualizations\n"
            response += "- Predict race outcomes using ML models\n"
            response += "- Provide insights from historical data\n\n"
            response += "For now, use the Custom Analysis tab to explore the data!"
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Data Source:** {os.getenv('SNOWFLAKE_DATABASE', 'APEXML_DEV')}.{os.getenv('SNOWFLAKE_SCHEMA', 'ANALYTICS')}")
st.sidebar.markdown("**Updated:** Real-time via dbt transformations")
