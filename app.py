import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta, timezone
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

# --- Custom CSS (Light Theme) ---
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
html, body, [class*="css"] { -webkit-font-smoothing: antialiased; }
.block-container { padding-top: 1.5rem; padding-bottom: 1rem; max-width: 1200px; }

.dashboard-header {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
    border-radius: 12px;
    padding: 1.25rem 1.75rem;
    margin-bottom: 1.25rem;
    display: flex; align-items: center; justify-content: space-between;
}
.dashboard-header .header-left h1 {
    font-size: 1.5rem; font-weight: 700; color: #FFFFFF; margin: 0; letter-spacing: -0.02em;
}
.dashboard-header .header-left .subtitle {
    font-size: 0.8rem; color: rgba(255,255,255,0.75); margin-top: 0.2rem;
}
.status-badge {
    padding: 0.3rem 0.85rem; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.03em;
}
.status-online { background: rgba(255,255,255,0.2); color: #FFFFFF; }
.status-offline { background: rgba(239,68,68,0.2); color: #FEE2E2; }

.kpi-card {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
    padding: 1rem 1.2rem; text-align: center;
    min-height: 120px; display: flex; flex-direction: column; justify-content: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.kpi-label { font-size: 0.68rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.15rem; line-height: 1.4; }
.kpi-label-ko { font-size: 0.68rem; color: #94A3B8; margin-bottom: 0.35rem; }
.kpi-value { font-size: 1.7rem; font-weight: 700; color: #1E293B; line-height: 1.2; }
.kpi-delta { font-size: 0.78rem; margin-top: 0.25rem; }
.delta-up { color: #16A34A; }
.delta-down { color: #DC2626; }
.delta-neutral { color: #94A3B8; }

.kpi-status { display: inline-block; padding: 0.2rem 0.7rem; border-radius: 12px; font-size: 0.78rem; font-weight: 600; }
.kpi-status-normal { background: #F0FDF4; color: #16A34A; }
.kpi-status-low { background: #FEFCE8; color: #CA8A04; }
.kpi-status-critical { background: #FEF2F2; color: #DC2626; }

.section-title {
    font-size: 0.82rem; font-weight: 600; color: #64748B;
    text-transform: uppercase; letter-spacing: 0.05em;
    margin-bottom: 0.75rem; padding-bottom: 0.5rem;
    border-bottom: 1px solid #E2E8F0; line-height: 1.5;
}
.section-title-ko { font-size: 0.75rem; color: #94A3B8; text-transform: none; letter-spacing: 0; }

.streamlit-expanderHeader { font-weight: 600; font-size: 0.85rem; }

.footer-text {
    text-align: center; color: #94A3B8; font-size: 0.72rem;
    margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #E2E8F0;
}

div[data-testid="stRadio"] { margin-bottom: -0.5rem; }

/* Roadmap */
.roadmap-phase {
    background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
    padding: 1.25rem 1.5rem; margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.roadmap-phase h4 { margin: 0 0 0.5rem 0; color: #1E293B; font-size: 1rem; }
.roadmap-phase p { margin: 0.25rem 0; color: #64748B; font-size: 0.85rem; line-height: 1.6; }
.roadmap-badge {
    display: inline-block; padding: 0.15rem 0.6rem; border-radius: 10px;
    font-size: 0.7rem; font-weight: 600; margin-bottom: 0.5rem;
}
.badge-current { background: #DBEAFE; color: #2563EB; }
.badge-next { background: #FEF3C7; color: #D97706; }
.badge-future { background: #F1F5F9; color: #64748B; }

.no-data-msg {
    text-align: center; color: #94A3B8; font-size: 0.9rem;
    padding: 3rem 1rem;
}
/* === Mobile Responsive === */
@media (max-width: 768px) {
    .block-container { padding-top: 1rem; padding-left: 1rem; padding-right: 1rem; }
    .dashboard-header { flex-direction: column; align-items: flex-start; gap: 0.5rem; padding: 1rem 1.25rem; }
    .dashboard-header .header-left h1 { font-size: 1.2rem; }
    .kpi-card { min-height: 100px; padding: 0.8rem; }
    .kpi-value { font-size: 1.4rem; }
    .kpi-label { font-size: 0.62rem; }
    .kpi-label-ko { font-size: 0.62rem; }
    .section-title { font-size: 0.75rem; }
    .roadmap-phase { padding: 1rem; }
    .roadmap-phase h4 { font-size: 0.9rem; }
    .roadmap-phase p { font-size: 0.8rem; }
    .footer-text { font-size: 0.65rem; }
}

@media (max-width: 480px) {
    .dashboard-header .header-left h1 { font-size: 1.05rem; }
    .dashboard-header .header-left .subtitle { font-size: 0.7rem; }
    .kpi-value { font-size: 1.2rem; }
    .kpi-card { min-height: 90px; }
}
</style>
""", unsafe_allow_html=True)

# --- Data Filtering ---
def filter_water_level(df):
    """Remove sensor outliers: replace 0% with last valid reading, then smooth with rolling median."""
    df = df.sort_values('created_at').copy()
    df.loc[df['water_level'] == 0, 'water_level'] = pd.NA
    df['water_level'] = df['water_level'].ffill().bfill()
    df['water_level'] = df['water_level'].rolling(window=5, min_periods=1, center=True).median()
    return df.sort_values('created_at', ascending=False).reset_index(drop=True)

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
                return filter_water_level(df)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def fetch_all_data():
    try:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?order=created_at.desc&limit=10000"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            if not df.empty:
                df['created_at'] = pd.to_datetime(df['created_at'])
                return filter_water_level(df)
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# --- Helper Functions ---
def get_freshness(ts):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
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
        return "Critical", "kpi-status-critical", "위험"
    elif level <= 20:
        return "Low", "kpi-status-low", "부족"
    else:
        return "Normal", "kpi-status-normal", "정상"

def render_kpi(label_en, label_ko, value_html, delta_html=""):
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label_en}</div>
        <div class="kpi-label-ko">{label_ko}</div>
        <div class="kpi-value">{value_html}</div>
        {f'<div class="kpi-delta">{delta_html}</div>' if delta_html else ''}
    </div>
    """

def compute_daily_summary(df_all):
    """Compute daily consumption: max(usage_volume) per day."""
    df_all = df_all.copy()
    df_all['date'] = df_all['created_at'].dt.date
    daily = df_all.groupby('date').agg(
        daily_max=('usage_volume', 'max'),
        daily_min=('usage_volume', 'min'),
        avg_level=('water_level', 'mean'),
        records=('id', 'count')
    ).reset_index()
    daily['consumption'] = daily['daily_max']
    daily['date'] = pd.to_datetime(daily['date'])
    daily['dow'] = daily['date'].dt.dayofweek  # 0=Mon, 6=Sun
    daily['dow_name'] = daily['date'].dt.strftime('%a')
    daily = daily.sort_values('date')
    return daily

DOW_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
DOW_LABELS_KO = ['월', '화', '수', '목', '금', '토', '일']

# --- Plotly themes (Light) ---
BAR_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#64748B', size=12),
    xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=11, color='#64748B')),
    yaxis=dict(gridcolor='#E2E8F0', gridwidth=0.5, showline=False, zeroline=False,
               tickfont=dict(size=11, color='#94A3B8')),
    height=350,
    margin=dict(l=50, r=20, t=30, b=40),
    showlegend=False,
)

PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#64748B', size=12),
    xaxis=dict(
        gridcolor='#E2E8F0', gridwidth=0.5,
        showline=False, zeroline=False,
        tickfont=dict(size=11, color='#94A3B8'),
        title=None,
    ),
    yaxis=dict(
        gridcolor='#E2E8F0', gridwidth=0.5,
        showline=False, zeroline=False,
        tickfont=dict(size=11, color='#94A3B8'),
    ),
    height=350,
    margin=dict(l=50, r=20, t=20, b=40),
    hovermode='x unified',
    hoverlabel=dict(
        bgcolor='#FFFFFF', bordercolor='#E2E8F0',
        font=dict(color='#1E293B', size=12)
    ),
    legend=dict(
        orientation='h', yanchor='bottom', y=1.02,
        xanchor='right', x=1,
        font=dict(color='#64748B', size=11),
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
            <div class="subtitle">Real-time water tank monitoring & analytics · 실시간 물탱크 모니터링</div>
        </div>
        <span class="status-badge status-offline">● Offline · 오프라인</span>
    </div>
    """, unsafe_allow_html=True)
    st.warning("데이터가 없습니다. MQTT 수신기가 실행 중인지 확인하세요.")
    if st.button("새로고침"):
        st.rerun()
else:
    latest = df.iloc[0]
    has_prev = len(df) > 1
    prev = df.iloc[1] if has_prev else None

    # --- Header Banner ---
    freshness_text, freshness_class = get_freshness(latest['created_at'])
    is_online = freshness_class != "delta-down"
    badge_class = "status-online" if is_online else "status-offline"
    badge_label = "● Online · 온라인" if is_online else "● Offline · 오프라인"

    st.markdown(f"""
    <div class="dashboard-header">
        <div class="header-left">
            <h1>💧 Smart Water Manager</h1>
            <div class="subtitle">Real-time water tank monitoring & analytics · 실시간 물탱크 모니터링</div>
        </div>
        <span class="status-badge {badge_class}">{badge_label}</span>
    </div>
    """, unsafe_allow_html=True)

    # --- KPI Row ---
    k1, k2, k3, k4 = st.columns(4)

    level_val = latest['water_level']
    usage_val = latest['usage_volume']
    status_text, status_class, status_ko = get_status(level_val)

    # Level delta
    if has_prev:
        level_delta = level_val - prev['water_level']
        level_arrow = "▲" if level_delta >= 0 else "▼"
        level_delta_class = "delta-up" if level_delta >= 0 else "delta-down"
        level_delta_html = f'<span class="{level_delta_class}">{level_arrow} {abs(level_delta):.1f}%</span>'
    else:
        level_delta_html = '<span class="delta-neutral">—</span>'

    with k1:
        st.markdown(render_kpi("Water Level", "수위", f"{level_val:.0f}%", level_delta_html), unsafe_allow_html=True)
    with k2:
        st.markdown(render_kpi("Today's Usage", "금일 사용량", f"{usage_val:,.0f} L"), unsafe_allow_html=True)
    with k3:
        st.markdown(render_kpi("Last Update", "최근 갱신", freshness_text, f'<span class="{freshness_class}">{latest["created_at"].strftime("%H:%M UTC")}</span>'), unsafe_allow_html=True)
    with k4:
        st.markdown(render_kpi("System Status", "시스템 상태", f'<span class="kpi-status {status_class}">{status_text} · {status_ko}</span>'), unsafe_allow_html=True)

    st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)

    # ========================================
    # TABS
    # ========================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Real-time · 실시간",
        "📅 Day-of-Week · 요일별",
        "📈 Period Trends · 기간별",
        "🗺️ Roadmap · 로드맵"
    ])

    # --- Tab 1: Real-time ---
    with tab1:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown('<div class="section-title">Tank Gauge <span class="section-title-ko">· 탱크 수위</span></div>', unsafe_allow_html=True)
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=level_val,
                number={'font': {'size': 42, 'color': '#1E293B'}, 'suffix': '%'},
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Water Level · 수위", 'font': {'size': 13, 'color': '#94A3B8'}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1,
                             'tickcolor': '#E2E8F0', 'tickfont': {'color': '#94A3B8', 'size': 11}},
                    'bar': {'color': '#2563EB', 'thickness': 0.75},
                    'bgcolor': '#F1F5F9',
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0, 10], 'color': 'rgba(220, 38, 38, 0.15)'},
                        {'range': [10, 20], 'color': 'rgba(202, 138, 4, 0.1)'},
                        {'range': [20, 100], 'color': 'rgba(37, 99, 235, 0.05)'}
                    ],
                    'threshold': {
                        'line': {'color': '#DC2626', 'width': 3},
                        'thickness': 0.8, 'value': 10
                    }
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font={'color': '#1E293B'}, height=280,
                margin=dict(l=30, r=30, t=40, b=20)
            )
            st.plotly_chart(fig_gauge, width="stretch")

        with col2:
            st.markdown('<div class="section-title">Trends <span class="section-title-ko">· 추이</span></div>', unsafe_allow_html=True)
            view_option = st.radio(
                "Metric:", ["사용량 Usage Volume (L)", "수위 Water Level (%)"],
                horizontal=True, label_visibility="collapsed"
            )
            fig_trend = go.Figure()
            if "Water Level" in view_option:
                fig_trend.add_trace(go.Scatter(
                    x=df['created_at'], y=df['water_level'],
                    mode='lines', name='Water Level · 수위',
                    line=dict(color='#2563EB', width=2.5, shape='spline'),
                    fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.06)',
                    hovertemplate='%{y:.1f}%<extra></extra>'
                ))
                fig_trend.update_layout(**PLOTLY_LAYOUT, yaxis_title="Level · 수위 (%)")
            else:
                fig_trend.add_trace(go.Scatter(
                    x=df['created_at'], y=df['usage_volume'],
                    mode='lines', name='Usage Volume · 사용량',
                    line=dict(color='#EA580C', width=2.5, shape='spline'),
                    fill='tozeroy', fillcolor='rgba(234, 88, 12, 0.06)',
                    hovertemplate='%{y:,.0f} L<extra></extra>'
                ))
                fig_trend.update_layout(**PLOTLY_LAYOUT, yaxis_title="Volume · 사용량 (L)")
            st.plotly_chart(fig_trend, width="stretch")

        with st.expander("View Raw Data · 원시 데이터 보기"):
            st.dataframe(df, width="stretch", hide_index=True)

    # --- Tab 2: Day-of-Week Analysis ---
    with tab2:
        df_all = fetch_all_data()
        if df_all.empty:
            st.markdown('<div class="no-data-msg">데이터가 부족합니다. 데이터가 축적되면 요일별 분석이 표시됩니다.</div>', unsafe_allow_html=True)
        else:
            daily = compute_daily_summary(df_all)

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown('<div class="section-title">Avg. by Day-of-Week <span class="section-title-ko">· 요일별 평균 사용량</span></div>', unsafe_allow_html=True)

                dow_avg = daily.groupby('dow').agg(avg_consumption=('consumption', 'mean'), count=('consumption', 'count')).reindex(range(7)).fillna(0).reset_index()
                dow_avg['label'] = [f"{DOW_LABELS[i]}\n{DOW_LABELS_KO[i]}" for i in range(7)]
                colors = ['#2563EB'] * 5 + ['#F97316'] * 2  # weekday blue, weekend orange

                fig_dow = go.Figure(go.Bar(
                    x=dow_avg['label'], y=dow_avg['avg_consumption'],
                    marker_color=colors,
                    text=[f"{v:,.0f}L" if v > 0 else "" for v in dow_avg['avg_consumption']],
                    textposition='outside',
                    hovertemplate='%{x}: %{y:,.0f} L<extra></extra>'
                ))
                fig_dow.update_layout(**BAR_LAYOUT, yaxis_title="Volume · 사용량 (L)")
                st.plotly_chart(fig_dow, width="stretch")

                if len(daily) < 7:
                    st.caption(f"현재 {len(daily)}일치 데이터. 7일 이상 축적되면 요일별 비교가 의미있어집니다.")

            with col_b:
                st.markdown('<div class="section-title">Hourly Pattern (Today) <span class="section-title-ko">· 시간대별 사용 패턴 (오늘)</span></div>', unsafe_allow_html=True)

                today = df_all['created_at'].dt.date.max()
                df_today = df_all[df_all['created_at'].dt.date == today].copy()
                df_today['hour'] = df_today['created_at'].dt.hour
                hourly = df_today.groupby('hour').agg(usage=('usage_volume', 'max')).reset_index()
                # Calculate per-hour increment
                hourly = hourly.sort_values('hour')
                hourly['increment'] = hourly['usage'].diff().fillna(0).clip(lower=0)

                fig_hourly = go.Figure(go.Bar(
                    x=[f"{h:02d}:00" for h in hourly['hour']],
                    y=hourly['increment'],
                    marker_color='#06B6D4',
                    text=[f"{v:,.0f}" if v > 0 else "" for v in hourly['increment']],
                    textposition='outside',
                    hovertemplate='%{x}: %{y:,.0f} L<extra></extra>'
                ))
                fig_hourly.update_layout(**BAR_LAYOUT, yaxis_title="Volume · 시간당 사용량 (L)")
                fig_hourly.update_layout(
                    xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10, color='#64748B'), tickangle=-45),
                    margin=dict(l=50, r=20, t=30, b=60),
                )
                st.plotly_chart(fig_hourly, width="stretch")

    # --- Tab 3: Period Trends ---
    with tab3:
        df_all = fetch_all_data()
        if df_all.empty:
            st.markdown('<div class="no-data-msg">데이터가 부족합니다.</div>', unsafe_allow_html=True)
        else:
            daily = compute_daily_summary(df_all)

            period = st.radio(
                "기간 선택:",
                ["일간 Daily", "월간 Monthly", "연간 Yearly"],
                horizontal=True
            )

            if "Daily" in period:
                st.markdown('<div class="section-title">Daily Usage Trend <span class="section-title-ko">· 일별 사용량 추이</span></div>', unsafe_allow_html=True)
                recent = daily.tail(30)
                fig_daily = go.Figure()
                fig_daily.add_trace(go.Bar(
                    x=recent['date'], y=recent['consumption'],
                    marker_color='#2563EB',
                    text=[f"{v:,.0f}" for v in recent['consumption']],
                    textposition='outside',
                    hovertemplate='%{x|%Y-%m-%d}: %{y:,.0f} L<extra></extra>'
                ))
                fig_daily.update_layout(**BAR_LAYOUT, yaxis_title="Volume · 사용량 (L)")
                fig_daily.update_layout(xaxis=dict(gridcolor='#E2E8F0', showline=False, zeroline=False,
                               tickformat='%m/%d', tickfont=dict(size=11, color='#94A3B8')))
                st.plotly_chart(fig_daily, width="stretch")

                # Summary stats
                if len(daily) > 1:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("평균 일일 사용량 Avg Daily", f"{daily['consumption'].mean():,.0f} L")
                    c2.metric("최대 일일 사용량 Max Daily", f"{daily['consumption'].max():,.0f} L")
                    c3.metric("총 사용량 Total", f"{daily['consumption'].sum():,.0f} L")

            elif "Monthly" in period:
                st.markdown('<div class="section-title">Monthly Usage Trend <span class="section-title-ko">· 월별 사용량 추이</span></div>', unsafe_allow_html=True)
                daily_c = daily.copy()
                daily_c['month'] = daily_c['date'].dt.to_period('M')
                monthly = daily_c.groupby('month').agg(total=('consumption', 'sum'), days=('consumption', 'count')).reset_index()
                monthly['month_str'] = monthly['month'].astype(str)

                fig_monthly = go.Figure()
                fig_monthly.add_trace(go.Bar(
                    x=monthly['month_str'], y=monthly['total'],
                    marker_color='#7C3AED',
                    text=[f"{v:,.0f}L" for v in monthly['total']],
                    textposition='outside',
                    hovertemplate='%{x}: %{y:,.0f} L<extra></extra>'
                ))
                fig_monthly.update_layout(**BAR_LAYOUT, yaxis_title="Volume · 사용량 (L)")
                st.plotly_chart(fig_monthly, width="stretch")

                if len(monthly) < 2:
                    st.caption("월간 비교는 2개월 이상 데이터 축적 시 의미있어집니다.")

            else:  # Yearly
                st.markdown('<div class="section-title">Yearly Usage Trend <span class="section-title-ko">· 연별 사용량 추이</span></div>', unsafe_allow_html=True)
                daily_c = daily.copy()
                daily_c['year'] = daily_c['date'].dt.year
                yearly = daily_c.groupby('year').agg(total=('consumption', 'sum'), days=('consumption', 'count')).reset_index()

                fig_yearly = go.Figure()
                fig_yearly.add_trace(go.Bar(
                    x=yearly['year'].astype(str), y=yearly['total'],
                    marker_color='#059669',
                    text=[f"{v:,.0f}L" for v in yearly['total']],
                    textposition='outside',
                    hovertemplate='%{x}: %{y:,.0f} L<extra></extra>'
                ))
                fig_yearly.update_layout(**BAR_LAYOUT, yaxis_title="Volume · 사용량 (L)")
                fig_yearly.update_layout(xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=14, color='#64748B')))
                st.plotly_chart(fig_yearly, width="stretch")

                if len(yearly) < 2:
                    st.caption("연간 비교는 2년 이상 데이터 축적 시 의미있어집니다.")

    # --- Tab 4: Roadmap ---
    with tab4:
        st.markdown('<div class="section-title">System Roadmap <span class="section-title-ko">· 시스템 로드맵</span></div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="roadmap-phase">
            <span class="roadmap-badge badge-current">● Current · 현재</span>
            <h4>Phase 0 — 단일 탱크 모니터링</h4>
            <p>심정(Ground Water Well) → 물탱크 1개 → IoT 센서(LoRa) → MQTT → Supabase → Dashboard</p>
            <p>수위 실시간 모니터링, 일일/요일별 사용량 분석 가능</p>
        </div>

        <div class="roadmap-phase">
            <span class="roadmap-badge badge-next">◐ Next · 다음 단계</span>
            <h4>Phase 1 — 다중 탱크 모니터링</h4>
            <p>Receiving Tank(수수 탱크) + Supply Tank(공급 탱크) 3개 이상 센서 설치</p>
            <p>각 탱크별 수위 독립 모니터링, node_id 기반 멀티 노드 대시보드</p>
        </div>

        <div class="roadmap-phase">
            <span class="roadmap-badge badge-next">◐ Next · 다음 단계</span>
            <h4>Phase 2 — 펌프 & 밸브 자동 제어</h4>
            <p>심정 펌프 ON/OFF 원격 제어, Receiving Tank 컨트롤 밸브 자동 조절</p>
            <p>야간 충수(22:00~06:00) → 주간 배수(06:00~22:00) 패턴 자동 운영</p>
            <p>수위 임계치 기반 펌프 자동 가동 (예: 수위 20% 이하 시 펌프 ON, 90% 이상 시 OFF)</p>
        </div>

        <div class="roadmap-phase">
            <span class="roadmap-badge badge-future">○ Future · 장기 계획</span>
            <h4>Phase 3 — Water Distribution Network</h4>
            <p>Receiving Tank → Supply Tank 간 분배 네트워크 구축</p>
            <p>각 Supply Tank의 펌프, 컨트롤 밸브를 지능적으로 제어하여 수요 예측 기반 배수</p>
            <p>머신러닝 기반 사용 패턴 학습 → 최적 충수/배수 스케줄 자동 생성</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="section-title" style="margin-top: 1.5rem;">System Architecture (Target) <span class="section-title-ko">· 목표 시스템 구성도</span></div>
        """, unsafe_allow_html=True)

        st.code("""
    ┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
    │  Ground     │     │  Receiving Tank   │     │  Supply Tank A  │
    │  Water Well │────▶│  (수수 탱크)       │────▶│  (공급 탱크 A)   │──▶ Building A
    │  (심정)     │     │  [Sensor][Valve]  │     │  [Sensor][Pump] │
    └─────────────┘     └──────────────────┘     ├─────────────────┤
          │              [Pump Control]      ├────▶│  Supply Tank B  │──▶ Building B
          │                                  │     │  [Sensor][Pump] │
          ▼                                  │     ├─────────────────┤
    ┌─────────────┐                          └────▶│  Supply Tank C  │──▶ Building C
    │  IoT/LoRa   │◀── Sensor Data                 │  [Sensor][Pump] │
    │  Gateway    │──▶ MQTT ──▶ Supabase ──▶ Dashboard + AI Control
    └─────────────┘
        """, language=None)

# --- Footer ---
st.markdown(
    '<div class="footer-text">10분 간격 자동 갱신 · Auto-refreshes every 10 minutes · Data sourced from IoT sensors via MQTT</div>',
    unsafe_allow_html=True
)
time.sleep(600)
st.rerun()
