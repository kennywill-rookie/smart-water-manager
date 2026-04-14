import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()
from config import SUPABASE_URL, SUPABASE_KEY, TABLE_NAME

# --- Configuration ---
st.set_page_config(page_title="Smart Water Manager", layout="wide")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# --- Data Fetching ---
@st.cache_data(ttl=600) # Refresh data every 10 minutes (matches MQTT data interval)
def fetch_data():
    try:
        # Fetch last 100 records
        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?order=created_at.desc&limit=100"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            if not df.empty:
                df['created_at'] = pd.to_datetime(df['created_at'])
                return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# --- UI Layout ---
st.title("🚰 Smart Water Management System")
st.markdown("Real-time monitoring of water tank levels and consumption trends.")

df = fetch_data()

if df.empty:
    st.warning("No data found in Supabase. Ensure the MQTT subscriber is running and publishing data.")
    if st.button("Refresh"):
        st.rerun()
else:
    # Latest Data
    latest = df.iloc[0]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Current Status")
        
        # Water Level Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = latest['water_level'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Water Level (%)", 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [0, 20], 'color': "red"},
                    {'range': [20, 50], 'color': "orange"},
                    {'range': [50, 100], 'color': "green"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 10}
            }
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        st.metric("Total Usage Volume", f"{latest['usage_volume']} L", delta_color="inverse")
        st.caption(f"Last updated: {latest['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")

    with col2:
        st.subheader("Trends")
        
        # Trend Selection
        view_option = st.radio("View Trend for:", ["Usage Volume (L)", "Water Level (%)"], horizontal=True)
        # ["Water Level (%)", "Usage Volume (L)"]
        
        if view_option == "Water Level (%)":
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=df['created_at'], y=df['water_level'], mode='lines+markers', name='Level'))
            fig_trend.update_layout(yaxis_title="Percentage (%)", xaxis_title="Time")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(x=df['created_at'], y=df['usage_volume'], mode='lines+markers', name='Usage', line=dict(color='orange')))
            fig_trend.update_layout(yaxis_title="Volume (L)", xaxis_title="Time")
            st.plotly_chart(fig_trend, use_container_width=True)

    # Raw Data Table
    with st.expander("View Raw Data"):
        st.dataframe(df)

# Auto-refresh
st.info("The dashboard auto-refreshes every 10 minutes.")
time.sleep(600)
st.rerun()
