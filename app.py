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
st.set_page_config(
    page_title="Smart Water Manager",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# --- Custom CSS ---
st.markdown("""
<style>
/* Hide Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Global typography */
html, body, [class*="css"] {
    -webkit-font-smoothing: antialiased;
}

/* Tighten page padding */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 1rem;
    max-width: 1200px;
}

/* --- Header Banner --- */
.dashboard-header {
    background: linear-gradient(135deg, #1B1F2B 0%, #141720 100%);
    border: 1px solid #2D3348;
    border-radius: 12px;
    padding: 1.25rem 1.75rem;
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.dashboard-header .header-left h1 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #FAFAFA;
    margin: 0;
    letter-spacing: -0.02em;
}
.dashboard-header .header-left .subtitle {
    font-size: 0.8rem;
    color: #8B8FA3;
    margin-top: 0.2rem;
}
.status-badge {
    padding: 0.3rem 0.85rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}
.status-online {
    background: rgba(34, 197, 94, 0.15);
    color: #22C55E;
}
.status-offline {
    background: rgba(239, 68, 68, 0.15);
    color: #EF4444;
}

/* --- KPI Cards --- */
.kpi-card {
    background: #1B1F2B;
    border: 1px solid #2D3348;
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.kpi-label {
    font-size: 0.7rem;
    color: #8B8FA3;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.35rem;
}
.kpi-value {
    font-size: 1.7rem;
    font-weight: 700;
    color: #FAFAFA;
    line-height: 1.2;
}
.kpi-delta {
    font-size: 0.78rem;
    margin-top: 0.25rem;
}
.delta-up { color: #22C55E; }
.delta-down { color: #EF4444; }
.delta-neutral { color: #8B8FA3; }

/* Status badge inside KPI */
.kpi-status {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 600;
}
.kpi-status-normal { background: rgba(34,197,94,0.15); color: #22C55E; }
.kpi-status-low { background: rgba(234,179,8,0.15); color: #EAB308; }
.kpi-status-critical { background: rgba(239,68,68,0.15); color: #EF4444; }

/* --- Section titles --- */
.section-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #8B8FA3;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #2D3348;
}

/* --- Expander styling --- */
.streamlit-expanderHeader {
    font-weight: 600;
    font-size: 0.85rem;
}

/* --- Footer --- */
.footer-text {
    text-align: center;
    color: #8B8FA3;
    font-size: 0.72rem;
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #2D3348;
}

/* Reduce gap between radio and chart */
div[data-testid="stRadio"] {
    margin-bottom: -0.5rem;
}
</style>
""", unsafe_allow_html=True)

# --- Data Fetching ---
@st.cache_data(ttl=600)
def fetch_data():
    try:
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

# --- Helper Functions ---
def get_freshness(ts):
    now = datetime.utcnow()
    ts_naive = ts.to_pydatetime().replace(tzinfo=None)
    diff = now - ts_naive
    minutes = diff.total_seconds() / 60
    if minutes < 1:
        return "Just now", "delta-up"
    elif minutes < 60:
        return f"{int(minutes)} min ago", "delta-up" if minutes < 15 else "delta-neutral"
    elif minutes < 1440:
        return f"{int(minutes // 60)} hr ago", "delta-down"
    else:
        return f"{int(minutes // 1440)} days ago", "delta-down"

def get_status(level):
    if level <= 10:
        return "Critical", "kpi-status-critical"
    elif level <= 20:
        return "Low", "kpi-status-low"
    else:
        return "Normal", "kpi-status-normal"

def render_kpi(label, value_html, delta_html=""):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value_html}</div>
        {f'<div class="kpi-delta">{delta_html}</div>' if delta_html else ''}
    </div>
    """

# --- Plotly theme helpers ---
PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#8B8FA3', size=12),
    xaxis=dict(
        gridcolor='#2D3348', gridwidth=0.5,
        showline=False, zeroline=False,
        tickformat='%m/%d %H:%M',
        tickfont=dict(size=11, color='#8B8FA3'),
        title=None,
    ),
    yaxis=dict(
        gridcolor='#2D3348', gridwidth=0.5,
        showline=False, zeroline=False,
        tickfont=dict(size=11, color='#8B8FA3'),
    ),
    height=350,
    margin=dict(l=50, r=20, t=20, b=40),
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor='#1B1F2B', bordercolor='#2D3348',
        font=dict(color='#FAFAFA', size=12)
    ),
    legend=dict(
        orientation='h', yanchor='bottom', y=1.02,
        xanchor='right', x=1,
        font=dict(color='#8B8FA3', size=11),
        bgcolor='rgba(0,0,0,0)'
    ),
)

# --- Load Data ---
df = fetch_data()

if df.empty:
    st.markdown("""
    <div class="dashboard-header">
        <div class="header-left">
            <h1>💧 Smart Water Manager</h1>
            <div class="subtitle">Real-time water tank monitoring & analytics</div>
        </div>
        <span class="status-badge status-offline">● Offline</span>
    </div>
    """, unsafe_allow_html=True)
    st.warning("No data found. Ensure the MQTT subscriber is running and publishing data.")
    if st.button("Refresh"):
        st.rerun()
else:
    latest = df.iloc[0]
    has_prev = len(df) > 1
    prev = df.iloc[1] if has_prev else None

    # --- Header Banner ---
    freshness_text, freshness_class = get_freshness(latest['created_at'])
    is_online = freshness_class != "delta-down"
    badge_class = "status-online" if is_online else "status-offline"
    badge_label = "● Online" if is_online else "● Offline"

    st.markdown(f"""
    <div class="dashboard-header">
        <div class="header-left">
            <h1>💧 Smart Water Manager</h1>
            <div class="subtitle">Real-time water tank monitoring & analytics</div>
        </div>
        <span class="status-badge {badge_class}">{badge_label}</span>
    </div>
    """, unsafe_allow_html=True)

    # --- KPI Row ---
    k1, k2, k3, k4 = st.columns(4)

    level_val = latest['water_level']
    usage_val = latest['usage_volume']
    status_text, status_class = get_status(level_val)

    # Level delta
    if has_prev:
        level_delta = level_val - prev['water_level']
        level_arrow = "▲" if level_delta >= 0 else "▼"
        level_delta_class = "delta-up" if level_delta >= 0 else "delta-down"
        level_delta_html = f'<span class="{level_delta_class}">{level_arrow} {abs(level_delta):.1f}%</span>'
    else:
        level_delta_html = '<span class="delta-neutral">—</span>'

    # Usage delta
    if has_prev:
        usage_delta = usage_val - prev['usage_volume']
        usage_arrow = "▲" if usage_delta >= 0 else "▼"
        usage_delta_class = "delta-neutral" if usage_delta >= 0 else "delta-down"
        usage_delta_html = f'<span class="{usage_delta_class}">{usage_arrow} {abs(usage_delta):.0f} L</span>'
    else:
        usage_delta_html = '<span class="delta-neutral">—</span>'

    with k1:
        st.markdown(render_kpi("Water Level", f"{level_val:.0f}%", level_delta_html), unsafe_allow_html=True)
    with k2:
        st.markdown(render_kpi("Usage Volume", f"{usage_val:,.0f} L", usage_delta_html), unsafe_allow_html=True)
    with k3:
        st.markdown(render_kpi("Last Update", freshness_text, f'<span class="{freshness_class}">{latest["created_at"].strftime("%H:%M UTC")}</span>'), unsafe_allow_html=True)
    with k4:
        st.markdown(render_kpi("System Status", f'<span class="kpi-status {status_class}">{status_text}</span>'), unsafe_allow_html=True)

    st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)

    # --- Main Content ---
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<div class="section-title">Tank Gauge</div>', unsafe_allow_html=True)

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=level_val,
            number={'font': {'size': 42, 'color': '#FAFAFA'}, 'suffix': '%'},
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Water Level", 'font': {'size': 14, 'color': '#8B8FA3'}},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1,
                         'tickcolor': '#2D3348', 'tickfont': {'color': '#8B8FA3', 'size': 11}},
                'bar': {'color': '#06B6D4', 'thickness': 0.75},
                'bgcolor': '#242938',
                'borderwidth': 0,
                'steps': [
                    {'range': [0, 10], 'color': 'rgba(239, 68, 68, 0.3)'},
                    {'range': [10, 20], 'color': 'rgba(234, 179, 8, 0.2)'},
                    {'range': [20, 100], 'color': 'rgba(6, 182, 212, 0.08)'}
                ],
                'threshold': {
                    'line': {'color': '#EF4444', 'width': 3},
                    'thickness': 0.8,
                    'value': 10
                }
            }
        ))
        fig_gauge.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': '#FAFAFA'},
            height=280,
            margin=dict(l=30, r=30, t=40, b=20)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Trends</div>', unsafe_allow_html=True)

        view_option = st.radio(
            "Metric:",
            ["Usage Volume (L)", "Water Level (%)"],
            horizontal=True,
            label_visibility="collapsed"
        )

        fig_trend = go.Figure()

        if view_option == "Water Level (%)":
            fig_trend.add_trace(go.Scatter(
                x=df['created_at'], y=df['water_level'],
                mode='lines', name='Water Level',
                line=dict(color='#3B82F6', width=2.5, shape='spline'),
                fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.08)',
                hovertemplate='%{y:.1f}%<extra></extra>'
            ))
            fig_trend.update_layout(**PLOTLY_LAYOUT, yaxis_title="Level (%)")
        else:
            fig_trend.add_trace(go.Scatter(
                x=df['created_at'], y=df['usage_volume'],
                mode='lines', name='Usage Volume',
                line=dict(color='#F97316', width=2.5, shape='spline'),
                fill='tozeroy', fillcolor='rgba(249, 115, 22, 0.08)',
                hovertemplate='%{y:,.0f} L<extra></extra>'
            ))
            fig_trend.update_layout(**PLOTLY_LAYOUT, yaxis_title="Volume (L)")

        st.plotly_chart(fig_trend, use_container_width=True)

    # --- Raw Data ---
    with st.expander("View Raw Data"):
        st.dataframe(df, use_container_width=True, hide_index=True)

# --- Footer ---
st.markdown(
    '<div class="footer-text">Auto-refreshes every 10 minutes · Data sourced from IoT sensors via MQTT</div>',
    unsafe_allow_html=True
)
time.sleep(600)
st.rerun()
