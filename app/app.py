import streamlit as st
import httpx
import pandas as pd

st.set_page_config(page_title="ApexML – F1 Sessions", layout="wide")

st.title("🏁 ApexML – 2025 F1 Sessions")

API_URL = "https://api.openf1.org/v1/sessions?year=2025"

@st.cache_data(ttl=3600)
def load_sessions():
    try:
        response = httpx.get(API_URL, timeout=10)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except Exception as e:
        st.error(f"Error fetching session data: {e}")
        return pd.DataFrame()

df = load_sessions()

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.warning("No session data available.")
