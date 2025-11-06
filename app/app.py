import streamlit as st
import pandas as pd
import snowflake.connector
import os
from pathlib import Path

st.set_page_config(page_title="ApexML – F1 Analytics", layout="wide")

# Snowflake connection
@st.cache_resource
def get_snowflake_connection():
    return snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        authenticator='SNOWFLAKE_JWT',
        private_key_file=str(Path.home() / '.ssh' / 'snowflake_key.p8'),
        warehouse='COMPUTE_WH',
        database='APEXML_DEV',
        schema='RAW_ANALYTICS'
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

# Main Dashboard
tab1, tab2, tab3 = st.tabs(["📊 Overview", "🏎️ Driver Performance", "⏱️ Lap Analysis"])

with tab1:
    st.header("Race Overview")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_drivers = query_snowflake("SELECT COUNT(*) as cnt FROM dim_drivers")
        st.metric("Total Drivers", total_drivers['CNT'].iloc[0])

    with col2:
        total_laps = query_snowflake("SELECT COUNT(*) as cnt FROM fct_lap_times")
        st.metric("Total Laps", total_laps['CNT'].iloc[0])

    with col3:
        avg_lap = query_snowflake("SELECT AVG(lap_duration_seconds) as avg FROM fct_lap_times WHERE lap_duration_seconds > 0")
        st.metric("Avg Lap Time", f"{avg_lap['AVG'].iloc[0]:.2f}s")

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
        AVG(r.position) as avg_position
    FROM fct_race_results r
    JOIN dim_drivers d ON r.driver_number = d.driver_number
    GROUP BY d.driver_number, d.full_name, d.team_name
    ORDER BY avg_position
    LIMIT 10
    """
    standings_df = query_snowflake(standings_query)
    st.dataframe(standings_df, use_container_width=True)

with tab2:
    st.header("Driver Performance")

    if selected_driver != "All":
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
            lap_duration_seconds
        FROM fct_lap_times
        WHERE driver_number = {driver_num}
        AND lap_duration_seconds > 0
        ORDER BY lap_number
        """
        lap_times_df = query_snowflake(lap_times_query)

        if not lap_times_df.empty:
            st.line_chart(lap_times_df.set_index('LAP_NUMBER')['LAP_DURATION_SECONDS'])

            # Stats
            st.subheader("Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Best Lap", f"{lap_times_df['LAP_DURATION_SECONDS'].min():.2f}s")
            with col2:
                st.metric("Average Lap", f"{lap_times_df['LAP_DURATION_SECONDS'].mean():.2f}s")
            with col3:
                st.metric("Total Laps", len(lap_times_df))
        else:
            st.info("No lap data available for this driver")
    else:
        st.info("Please select a driver from the sidebar")

with tab3:
    st.header("Lap Analysis")

    # Fastest laps
    st.subheader("Top 10 Fastest Laps")
    fastest_laps_query = """
    SELECT
        l.session_key,
        d.full_name,
        d.team_name,
        l.lap_number,
        l.lap_duration_seconds
    FROM fct_lap_times l
    JOIN dim_drivers d ON l.driver_number = d.driver_number
    WHERE l.lap_duration_seconds > 0
    ORDER BY l.lap_duration_seconds
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
        AVG(l.lap_duration_seconds) as avg_lap_time,
        MIN(l.lap_duration_seconds) as best_lap
    FROM fct_lap_times l
    JOIN dim_drivers d ON l.driver_number = d.driver_number
    WHERE l.lap_duration_seconds > 0
    GROUP BY d.team_name
    ORDER BY avg_lap_time
    """
    team_comparison_df = query_snowflake(team_comparison_query)
    st.dataframe(team_comparison_df, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**Data Source:** Snowflake ANALYTICS schema")
st.sidebar.markdown("**Updated:** Real-time via dbt transformations")
