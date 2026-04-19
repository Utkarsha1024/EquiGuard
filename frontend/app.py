import os
import json
import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

# ── Load .env ──────────────────────────────────────────────────────────────────
load_dotenv()

# ── API Config ─────────────────────────────────────────────────────────────────
API_BASE    = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
_API_KEY    = os.getenv("EQUIGUARD_API_KEY", "")
API_HEADERS = {"X-API-Key": _API_KEY} if _API_KEY else {}

def api_get(path: str):
    return requests.get(f"{API_BASE}{path}", headers=API_HEADERS)

def api_post(path: str, json: dict):
    return requests.post(f"{API_BASE}{path}", json=json, headers=API_HEADERS)

# ── Session State ──────────────────────────────────────────────────────────────
if "audit_result" not in st.session_state:
    st.session_state.audit_result = None
if "flagged_columns" not in st.session_state:
    st.session_state.flagged_columns = []
if "active_page" not in st.session_state:
    st.session_state.active_page = "Dashboard"
if "report_bytes" not in st.session_state:
    st.session_state.report_bytes = None
if "cert_bytes" not in st.session_state:
    st.session_state.cert_bytes = None
if "sim_result" not in st.session_state:
    st.session_state.sim_result = None
if "pkg_bytes" not in st.session_state:
    st.session_state.pkg_bytes = None
if "intersectional_result" not in st.session_state:
    st.session_state.intersectional_result = None
if "ix_summary" not in st.session_state:
    st.session_state.ix_summary = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # [{"role": "user"|"assistant", "content": str}]

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EquiGuard — AI Bias Firewall",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Master CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Reset & Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.stApp {
    background-color: #080910;
    color: #c8cad4;
}
.block-container {
    padding: 0 2rem 2rem 2rem !important;
    max-width: 100% !important;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
section[data-testid="stSidebar"] > div { background: #0d0e14; border-right: 1px solid #1e2030; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0d0e14 !important;
    border-right: 1px solid #1a1c28 !important;
}

/* ── Top Header Bar ── */
.eq-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.1rem 2rem 1.1rem 0;
    border-bottom: 1px solid #1a1c28;
    margin-bottom: 2rem;
    background: transparent;
}
.eq-brand {
    display: flex;
    align-items: center;
    gap: 12px;
}
.eq-logo {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #6366f1, #818cf8);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    box-shadow: 0 0 20px rgba(99,102,241,0.4);
}
.eq-brand-name {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 22px;
    letter-spacing: -0.5px;
    color: #f0f1f5;
}
.eq-brand-tag {
    font-size: 11px;
    color: #6366f1;
    font-weight: 500;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-family: 'DM Mono', monospace;
}
.eq-status-dot {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-size: 12px;
    color: #6b7280;
    font-family: 'DM Mono', monospace;
}
.eq-status-dot::before {
    content: '';
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 8px rgba(34,197,94,0.6);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ── Sidebar Nav ── */
.nav-section-label {
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #3a3d52;
    font-family: 'DM Mono', monospace;
    padding: 1.2rem 1.2rem 0.4rem;
    font-weight: 500;
}
.nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 1.2rem;
    border-radius: 8px;
    margin: 2px 8px;
    cursor: pointer;
    font-size: 13.5px;
    color: #6b7280;
    transition: all 0.2s ease;
    font-weight: 400;
    text-decoration: none;
}
.nav-item:hover {
    background: #12141f;
    color: #c8cad4;
}
.nav-item.active {
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(129,140,248,0.08));
    color: #818cf8;
    border: 1px solid rgba(99,102,241,0.2);
    font-weight: 500;
}
.nav-icon { font-size: 15px; width: 20px; text-align: center; }

/* ── KPI Cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 1.5rem;
}
.kpi-card {
    background: #0d0e14;
    border: 1px solid #1a1c28;
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.kpi-card.indigo::before { background: linear-gradient(90deg, #6366f1, #818cf8); }
.kpi-card.green::before  { background: linear-gradient(90deg, #22c55e, #4ade80); }
.kpi-card.red::before    { background: linear-gradient(90deg, #ef4444, #f87171); }
.kpi-card.amber::before  { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.kpi-card:hover { border-color: #2a2d40; }

.kpi-label {
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #4b5280;
    font-family: 'DM Mono', monospace;
    margin-bottom: 8px;
}
.kpi-value {
    font-family: 'Syne', sans-serif;
    font-size: 28px;
    font-weight: 700;
    color: #f0f1f5;
    line-height: 1;
    margin-bottom: 6px;
}
.kpi-value.indigo { color: #818cf8; }
.kpi-value.green  { color: #4ade80; }
.kpi-value.red    { color: #f87171; }
.kpi-value.amber  { color: #fbbf24; }
.kpi-sub {
    font-size: 12px;
    color: #4b5280;
}

/* ── Section Cards ── */
.section-card {
    background: #0d0e14;
    border: 1px solid #1a1c28;
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 15px;
    font-weight: 600;
    color: #e0e1ea;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1a1c28;
    margin-left: 8px;
}

/* ── Compliance Badge ── */
.badge-pass {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(34,197,94,0.1);
    color: #4ade80;
    padding: 7px 18px;
    border-radius: 50px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid rgba(34,197,94,0.25);
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.5px;
}
.badge-fail {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(239,68,68,0.1);
    color: #f87171;
    padding: 7px 18px;
    border-radius: 50px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid rgba(239,68,68,0.25);
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.5px;
}
.badge-pending {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(107,114,128,0.1);
    color: #6b7280;
    padding: 7px 18px;
    border-radius: 50px;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid rgba(107,114,128,0.2);
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.5px;
}

/* ── Buttons ── */
.stButton > button {
    width: 100% !important;
    background: #12141f !important;
    color: #c8cad4 !important;
    border: 1px solid #1e2030 !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    font-family: 'DM Sans', sans-serif !important;
    transition: all 0.2s !important;
    letter-spacing: 0.3px !important;
}
.stButton > button:hover {
    background: #1a1d2e !important;
    border-color: #6366f1 !important;
    color: #818cf8 !important;
    transform: none !important;
    box-shadow: 0 0 16px rgba(99,102,241,0.15) !important;
}
.stButton > button:first-child {
    background: linear-gradient(135deg, #6366f1, #4f52c8) !important;
    color: #fff !important;
    border: none !important;
}
.stButton > button:first-child:hover {
    box-shadow: 0 0 24px rgba(99,102,241,0.4) !important;
    color: #fff !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: #0d0e14 !important;
    border: 1.5px dashed #1e2030 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #6366f1 !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: #12141f !important;
    border: 1px solid #1e2030 !important;
    border-radius: 10px !important;
    color: #c8cad4 !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #0d0e14 !important;
    border: 1px solid #1a1c28 !important;
    border-radius: 14px !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricLabel"] { color: #4b5280 !important; font-size: 11px !important; }
[data-testid="stMetricValue"] { color: #f0f1f5 !important; font-family: 'Syne', sans-serif !important; }

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: none !important;
    font-size: 13px !important;
}

/* ── Divider ── */
hr { border-color: #1a1c28 !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #6366f1 !important; }

/* ── Info box ── */
.info-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
    color: #818cf8;
    font-family: 'DM Mono', monospace;
    margin-bottom: 1rem;
}

/* ── Leaderboard table ── */
.leaderboard-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid #1a1c28;
    font-size: 13px;
}
.leaderboard-row:last-child { border-bottom: none; }
.rank-num {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #3a3d52;
    width: 24px;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #080910; }
::-webkit-scrollbar-thumb { background: #1e2030; border-radius: 4px; }

/* ── Risk Narrative ── */
.narrative-card { background:#0d0e14; border:1px solid #1a1c28; border-radius:20px; padding:1.5rem; margin-bottom:1rem; }
.narrative-card.pass { border-left:4px solid #22c55e; }
.narrative-card.fail { border-left:4px solid #ef4444; }
.narrative-text { font-size:13px; color:#c8cad4; font-family:'DM Sans',sans-serif; line-height:1.75; }
.narrative-text p { margin:0 0 10px 0; }
.nh { color:#818cf8; font-family:'DM Mono',monospace; }

/* ── What-If Simulator Table ── */
.sim-table { width:100%; border-collapse:collapse; }
.sim-table th { font-size:10px; letter-spacing:1.5px; text-transform:uppercase; color:#3a3d52; font-family:'DM Mono',monospace; padding:8px 12px; border-bottom:1px solid #1a1c28; text-align:left; }
.sim-table td { padding:9px 12px; border-bottom:1px solid #0f1018; font-size:13px; color:#c8cad4; }
.sim-table tr.best-row td { background:rgba(99,102,241,0.07); }
.rec-drop { display:inline-flex; align-items:center; background:rgba(34,197,94,0.1); color:#4ade80; padding:2px 10px; border-radius:50px; font-size:11px; border:1px solid rgba(34,197,94,0.2); font-family:'DM Mono',monospace; }
.rec-keep { display:inline-flex; align-items:center; background:rgba(107,114,128,0.1); color:#6b7280; padding:2px 10px; border-radius:50px; font-size:11px; border:1px solid rgba(107,114,128,0.2); font-family:'DM Mono',monospace; }

/* ── Mitigation Comparison ── */
.compare-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.compare-side { background:#0a0b10; border:1px solid #1a1c28; border-radius:14px; padding:1.2rem; }
.compare-label { font-size:9px; letter-spacing:2px; text-transform:uppercase; color:#3a3d52; font-family:'DM Mono',monospace; margin-bottom:12px; }
.compare-metric { margin-bottom:10px; }
.compare-metric-label { font-size:10px; color:#4b5280; font-family:'DM Mono',monospace; letter-spacing:1px; text-transform:uppercase; margin-bottom:3px; }
.compare-metric-value { font-size:22px; font-weight:700; font-family:'Syne',sans-serif; color:#f0f1f5; }

/* ── Intersectional badge row ── */
.ix-badge { display:inline-flex; flex-direction:column; align-items:center; background:#0d0e14; border:1px solid #1a1c28; border-radius:12px; padding:10px 18px; margin:0 6px 8px 0; min-width:90px; }
.ix-badge-label { font-size:10px; color:#4b5280; font-family:'DM Mono',monospace; letter-spacing:1px; text-transform:uppercase; margin-bottom:5px; }
.ix-badge-val { font-size:16px; font-weight:700; font-family:'Syne',sans-serif; }

/* ── Audit Agent Chat ── */
[data-testid="stChatMessage"] { background:#0d0e14 !important; border:1px solid #1a1c28 !important; border-radius:14px !important; margin-bottom:8px !important; }
[data-testid="stChatMessage"] p { font-size:13px !important; color:#c8cad4 !important; font-family:'DM Sans',sans-serif !important; line-height:1.65 !important; }
[data-testid="stChatInputContainer"] { background:#0d0e14 !important; border:1px solid #1e2030 !important; border-radius:12px !important; }
[data-testid="stChatInputContainer"]:focus-within { border-color:#6366f1 !important; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 1.2rem 1.2rem 0.5rem; border-bottom: 1px solid #1a1c28; margin-bottom: 0.5rem;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:32px;height:32px;background:linear-gradient(135deg,#6366f1,#818cf8);border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:16px;box-shadow:0 0 16px rgba(99,102,241,0.4);">⚖</div>
            <div>
                <div style="font-family:'Syne',sans-serif;font-weight:800;font-size:17px;color:#f0f1f5;letter-spacing:-0.3px;">EquiGuard</div>
                <div style="font-size:9px;color:#6366f1;letter-spacing:2px;text-transform:uppercase;font-family:'DM Mono',monospace;">AI Bias Firewall</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="nav-section-label">Navigation</div>', unsafe_allow_html=True)

    pages = [
        ("Dashboard", "◈", "Overview & compliance status"),
        ("Audit Engine", "⬡", "Run bias audits"),
        ("Bias Leaderboard", "◉", "Historical drift tracking"),
        ("Intersectional", "⬢", "Multi-attribute bias heatmap"),
    ]

    for page, icon, _ in pages:
        is_active = st.session_state.active_page == page
        cls = "nav-item active" if is_active else "nav-item"
        if st.sidebar.button(f"{icon}  {page}", key=f"nav_{page}", use_container_width=True):
            st.session_state.active_page = page
            st.rerun()

    st.markdown('<div class="nav-section-label" style="margin-top:1rem;">System</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="padding: 0 8px;">
        <div style="background:#0a0b10;border:1px solid #1a1c28;border-radius:12px;padding:12px 14px;margin-top:4px;">
            <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">System Status</div>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:12px;color:#6b7280;">Backend API</span>
                <span style="font-size:11px;color:#4ade80;font-family:'DM Mono',monospace;">● Online</span>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:12px;color:#6b7280;">EEOC Engine</span>
                <span style="font-size:11px;color:#4ade80;font-family:'DM Mono',monospace;">● Active</span>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <span style="font-size:12px;color:#6b7280;">SHAP Explainer</span>
                <span style="font-size:11px;color:#4ade80;font-family:'DM Mono',monospace;">● Ready</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="padding: 1rem 1.2rem; margin-top: auto; border-top: 1px solid #1a1c28; position: absolute; bottom: 0; left: 0; right: 0;">
        <div style="font-size:11px;color:#3a3d52;font-family:'DM Mono',monospace;">v1.0.0 · EEOC Compliant</div>
    </div>
    """, unsafe_allow_html=True)


# ── Gauge Chart ────────────────────────────────────────────────────────────────
def render_fairness_gauge(score):
    color = "#4ade80" if score >= 0.8 else ("#fbbf24" if score >= 0.6 else "#f87171")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Fairness Ratio", 'font': {'color': '#6b7280', 'size': 13, 'family': 'DM Mono'}},
        number={'font': {'color': color, 'size': 42, 'family': 'Syne'}, 'valueformat': '.2f'},
        gauge={
            'axis': {'range': [0.0, 1.0], 'tickcolor': "#2a2d40", 'tickfont': {'color': '#3a3d52', 'size': 10}},
            'bar': {'color': color, 'thickness': 0.25},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [
                {'range': [0.0, 0.6],  'color': "rgba(239,68,68,0.08)"},
                {'range': [0.6, 0.8],  'color': "rgba(251,191,36,0.08)"},
                {'range': [0.8, 1.0],  'color': "rgba(74,222,128,0.08)"}
            ],
            'threshold': {
                'line': {'color': "#6366f1", 'width': 2},
                'thickness': 0.75,
                'value': 0.8
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white", 'family': 'DM Sans'},
        margin=dict(l=20, r=20, t=40, b=10),
        height=240
    )
    return fig


# ── SHAP Waterfall Chart ───────────────────────────────────────────────────────
def render_shap_waterfall(shap_summary: dict):
    """
    Renders a horizontal waterfall bar chart from shap_summary dict
    {feature: mean_abs_shap_value} — top 5 features, sorted by impact.
    """
    if not shap_summary:
        return None

    items = sorted(shap_summary.items(), key=lambda x: x[1])  # ascending for bottom-up display
    features = [i[0] for i in items]
    values   = [i[1] for i in items]

    # Color: highest bar gets red accent, rest get indigo gradient
    colors = ["#6366f1"] * len(values)
    colors[-1] = "#f87171"   # top driver = red warning
    colors[-2] = "#fb923c" if len(values) > 1 else colors[-2]  # second = amber

    fig = go.Figure()

    # Invisible base bars (waterfall effect)
    cumulative = [0] + list(values[:-1])
    for i in range(len(features)):
        c = cumulative[i] if i == 0 else sum(values[:i])
        _ = c  # kept for clarity

    # Simple horizontal bar (mean abs SHAP — the standard presentation)
    fig.add_trace(go.Bar(
        x=values,
        y=features,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(width=0),
        ),
        text=[f"{v:.4f}" for v in values],
        textposition='outside',
        textfont=dict(color='#6b7280', size=11, family='DM Mono'),
        hovertemplate='<b>%{y}</b><br>SHAP Impact: %{x:.4f}<extra></extra>',
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#6b7280", family="DM Sans", size=12),
        margin=dict(l=10, r=60, t=10, b=10),
        height=260,
        xaxis=dict(
            showgrid=True,
            gridcolor="#1a1c28",
            zeroline=True,
            zerolinecolor="#2a2d40",
            zerolinewidth=1,
            showline=False,
            tickfont=dict(color="#3a3d52", size=10, family="DM Mono"),
            title=dict(text="Mean |SHAP| Value", font=dict(color="#3a3d52", size=11)),
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            tickfont=dict(color="#c8cad4", size=12, family="DM Sans"),
        ),
        bargap=0.35,
        showlegend=False,
    )

    # Vertical reference line at x=0
    fig.add_vline(x=0, line_color="#2a2d40", line_width=1)

    return fig


# ── Bias Drift Chart ───────────────────────────────────────────────────────────
def render_bias_drift(history_data: list):
    """
    Renders a Plotly area+line chart of fairness_ratio over time.
    Marks PASS/FAIL points with colored markers.
    """
    if not history_data:
        return None

    df = pd.DataFrame(history_data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    pass_df = df[df["fairness_ratio"] >= 0.8]
    fail_df = df[df["fairness_ratio"] < 0.8]

    fig = go.Figure()

    # Shaded area under the line
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["fairness_ratio"],
        mode="lines",
        line=dict(color="rgba(99,102,241,0)", width=0),
        fill='tozeroy',
        fillcolor="rgba(99,102,241,0.06)",
        showlegend=False,
        hoverinfo='skip',
    ))

    # Main line
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["fairness_ratio"],
        mode="lines",
        line=dict(color="#6366f1", width=2.5, shape='spline', smoothing=0.8),
        showlegend=False,
        hovertemplate='<b>%{x|%Y-%m-%d %H:%M}</b><br>Fairness Ratio: <b>%{y:.3f}</b><extra></extra>',
    ))

    # PASS markers (green dots)
    if not pass_df.empty:
        fig.add_trace(go.Scatter(
            x=pass_df["timestamp"],
            y=pass_df["fairness_ratio"],
            mode="markers",
            name="PASS",
            marker=dict(color="#4ade80", size=9, line=dict(color="#080910", width=2)),
            hovertemplate='<b>PASS</b><br>%{x|%Y-%m-%d %H:%M}<br>Ratio: %{y:.3f}<extra></extra>',
        ))

    # FAIL markers (red dots)
    if not fail_df.empty:
        fig.add_trace(go.Scatter(
            x=fail_df["timestamp"],
            y=fail_df["fairness_ratio"],
            mode="markers",
            name="FAIL",
            marker=dict(color="#f87171", size=9, symbol="x", line=dict(color="#080910", width=2)),
            hovertemplate='<b>FAIL</b><br>%{x|%Y-%m-%d %H:%M}<br>Ratio: %{y:.3f}<extra></extra>',
        ))

    # EEOC threshold line
    fig.add_hline(
        y=0.8,
        line_dash="dot",
        line_color="rgba(239,68,68,0.45)",
        line_width=1.5,
        annotation_text="EEOC Minimum (0.80)",
        annotation_font_color="#f87171",
        annotation_font_size=10,
        annotation_font_family="DM Mono",
        annotation_position="top right",
    )

    # Compliance zone shading
    fig.add_hrect(
        y0=0.8, y1=1.05,
        fillcolor="rgba(34,197,94,0.03)",
        line_width=0,
    )
    fig.add_hrect(
        y0=0, y1=0.8,
        fillcolor="rgba(239,68,68,0.03)",
        line_width=0,
    )

    max_y = max(1.05, df["fairness_ratio"].max() * 1.1)

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#6b7280", family="DM Sans", size=12),
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        xaxis=dict(
            gridcolor="#1a1c28",
            showline=False,
            zeroline=False,
            tickfont=dict(color="#3a3d52", size=10, family="DM Mono"),
        ),
        yaxis=dict(
            range=[0, max_y],
            gridcolor="#1a1c28",
            showline=False,
            zeroline=False,
            tickfont=dict(color="#3a3d52", size=10, family="DM Mono"),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(color="#6b7280", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
    )

    return fig


# ── Helper: derive KPI values ──────────────────────────────────────────────────
def get_kpi_values():
    res = st.session_state.audit_result
    if res is None:
        return {"ratio": "—", "status": "Pending", "feature": "—", "passed": "—"}
    return {
        "ratio": f"{res.get('fairness_ratio', 0):.2f}",
        "status": "PASS" if res.get("compliance_pass") else "FAIL",
        "feature": res.get("top_biased_feature", "N/A"),
        "passed": "Yes" if res.get("compliance_pass") else "No"
    }


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.active_page == "Dashboard":

    # Header
    st.markdown("""
    <div class="eq-header">
        <div class="eq-brand">
            <div class="eq-logo">⚖</div>
            <div>
                <div class="eq-brand-name">EquiGuard</div>
                <div class="eq-brand-tag">AI Bias Firewall · EEOC Compliance Suite</div>
            </div>
        </div>
        <div class="eq-status-dot">System Operational</div>
    </div>
    """, unsafe_allow_html=True)

    kpi = get_kpi_values()
    ratio_val = kpi["ratio"]
    status_val = kpi["status"]
    feature_val = kpi["feature"]

    ratio_color = "green" if status_val == "PASS" else ("amber" if ratio_val == "—" else "red")
    status_color = "green" if status_val == "PASS" else ("indigo" if status_val == "Pending" else "red")

    # KPI Row
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card {ratio_color}">
            <div class="kpi-label">Fairness Ratio</div>
            <div class="kpi-value {ratio_color}">{ratio_val}</div>
            <div class="kpi-sub">EEOC threshold ≥ 0.80</div>
        </div>
        <div class="kpi-card {status_color}">
            <div class="kpi-label">Compliance Status</div>
            <div class="kpi-value {status_color}">{status_val}</div>
            <div class="kpi-sub">US EEOC 4/5ths Rule</div>
        </div>
        <div class="kpi-card indigo">
            <div class="kpi-label">Top Bias Driver</div>
            <div class="kpi-value indigo" style="font-size:18px;margin-top:4px;">{feature_val}</div>
            <div class="kpi-sub">Highest SHAP impact</div>
        </div>
        <div class="kpi-card amber">
            <div class="kpi-label">Audit Engine</div>
            <div class="kpi-value amber" style="font-size:18px;margin-top:4px;">aif360 + SHAP</div>
            <div class="kpi-sub">IBM Fairness 360 active</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Main content
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">⬡ Fairness Gauge</div>', unsafe_allow_html=True)

        fairness_ratio = 0.0
        if st.session_state.audit_result:
            fairness_ratio = st.session_state.audit_result.get('fairness_ratio', 0.0)

        st.plotly_chart(render_fairness_gauge(fairness_ratio), use_container_width=True)

        # Compliance badge
        if st.session_state.audit_result is None:
            st.markdown('<div style="text-align:center;"><span class="badge-pending">◌ Pending Audit</span></div>', unsafe_allow_html=True)
        elif st.session_state.audit_result.get("compliance_pass"):
            st.markdown('<div style="text-align:center;"><span class="badge-pass">✓ US EEOC: Compliant</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center;"><span class="badge-fail">✗ US EEOC: Non-Compliant</span></div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">◈ SHAP Feature Impact</div>', unsafe_allow_html=True)

        if st.session_state.audit_result:
            res = st.session_state.audit_result
            shap_summary = res.get("shap_summary", {})

            if shap_summary:
                fig_shap = render_shap_waterfall(shap_summary)
                if fig_shap:
                    st.plotly_chart(fig_shap, use_container_width=True)

                # Legend chips
                st.markdown("""
                <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:4px;">
                    <span style="font-size:11px;font-family:'DM Mono',monospace;color:#f87171;">■ Top driver</span>
                    <span style="font-size:11px;font-family:'DM Mono',monospace;color:#fb923c;">■ 2nd driver</span>
                    <span style="font-size:11px;font-family:'DM Mono',monospace;color:#6366f1;">■ Other features</span>
                    <span style="font-size:11px;font-family:'DM Mono',monospace;color:#3a3d52;margin-left:auto;">Mean |SHAP| — higher = more bias influence</span>
                </div>
                """, unsafe_allow_html=True)

                # Quick stats row
                top_feat = res.get("top_biased_feature", "N/A")
                top_val  = shap_summary.get(top_feat, 0)
                st.markdown(f"""
                <div style="display:flex;gap:10px;margin-top:14px;">
                    <div style="flex:1;background:#12141f;border:1px solid #1e2030;border-radius:10px;padding:10px 14px;">
                        <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1px;margin-bottom:4px;">TOP DRIVER</div>
                        <div style="font-size:14px;color:#f87171;font-weight:500;">{top_feat}</div>
                    </div>
                    <div style="flex:1;background:#12141f;border:1px solid #1e2030;border-radius:10px;padding:10px 14px;">
                        <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1px;margin-bottom:4px;">SHAP SCORE</div>
                        <div style="font-size:14px;color:#818cf8;font-family:'DM Mono',monospace;">{top_val:.4f}</div>
                    </div>
                    <div style="flex:1;background:#12141f;border:1px solid #1e2030;border-radius:10px;padding:10px 14px;">
                        <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1px;margin-bottom:4px;">FEATURES TRACKED</div>
                        <div style="font-size:14px;color:#c8cad4;font-family:'DM Mono',monospace;">{len(shap_summary)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.session_state.flagged_columns:
                    st.markdown(f"""
                    <div style="margin-top:12px;background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.15);border-radius:10px;padding:10px 14px;">
                        <div style="font-size:10px;color:#f87171;font-family:'DM Mono',monospace;letter-spacing:1px;margin-bottom:4px;">PROXY VARIABLES DETECTED</div>
                        <div style="font-size:13px;color:#c8cad4;">{", ".join(st.session_state.flagged_columns)}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:180px;gap:10px;">
                    <div style="font-size:32px;opacity:0.12;">◈</div>
                    <div style="font-size:12px;color:#3a3d52;text-align:center;font-family:'DM Mono',monospace;">SHAP data unavailable for this audit.</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:220px;gap:12px;">
                <div style="font-size:36px;opacity:0.1;">◈</div>
                <div style="font-size:13px;color:#3a3d52;text-align:center;font-family:'DM Mono',monospace;">No audit data yet.<br>Run an audit from the Audit Engine.</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── Risk Narrative ────────────────────────────────────────────────────────
    if st.session_state.audit_result:
        _r  = st.session_state.audit_result
        _cp = _r.get("compliance_pass", False)
        _fr = _r.get("fairness_ratio", 0.0)
        _ga = _r.get("group_a_rate", 0.0)
        _gb = _r.get("group_b_rate", 0.0)
        _tf = _r.get("top_biased_feature", "N/A")
        _px = st.session_state.flagged_columns
        _cls    = "pass" if _cp else "fail"
        _verb   = "passes" if _cp else "fails"
        _tcolor = "#4ade80" if _cp else "#f87171"
        _legal  = (
            "This model would likely survive disparate impact scrutiny under 29 CFR § 1607."
            if _cp else
            "This disparity constitutes potential adverse impact under 29 CFR § 1607 and may not survive regulatory scrutiny."
        )
        _proxy_sent = ""
        if _px:
            _plist = ", ".join(f'<span class="nh">{p}</span>' for p in _px)
            _proxy_sent = f' Additionally, <span class="nh">{len(_px)}</span> proxy variable(s) — {_plist} — were detected as statistically correlated with the protected attribute and are flagged for removal.'
        st.markdown(f"""
        <div class="narrative-card {_cls}">
            <div class="section-title">⚖ Legal Risk Narrative</div>
            <div class="narrative-text">
                <p>The submitted model <strong style="color:#f0f1f5;">{_verb}</strong> the EEOC 4/5ths (80%) adverse impact rule.
                The privileged group achieves a selection rate of <span class="nh">{_ga*100:.1f}%</span>,
                while the unprivileged group achieves <span class="nh">{_gb*100:.1f}%</span>.</p>
                <p>The resulting disparate impact ratio is <span class="nh">{_fr:.4f}</span>, compared against the
                regulatory minimum threshold of <span style="color:{_tcolor};font-family:'DM Mono',monospace;">0.80</span>.
                {'The ratio meets or exceeds this threshold.' if _cp else 'The ratio falls <strong style="color:#f87171;">below</strong> this threshold.'}</p>
                <p>The feature with the highest SHAP-attributed influence on model outcomes is
                <span class="nh">{_tf}</span>, indicating it is the primary statistical driver of model decisions.{_proxy_sent}</p>
                <p style="margin-top:12px;padding:10px 14px;background:rgba({'34,197,94' if _cp else '239,68,68'},0.07);border-radius:8px;border-left:3px solid {'#22c55e' if _cp else '#ef4444'};">
                {_legal}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Bias Drift Chart (full width below) ─────────────────────────────────

    st.markdown('<div class="section-card" style="margin-top:0;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">◉ Bias Drift Over Time</div>', unsafe_allow_html=True)

    try:
        history_response = api_get("/audit/history")
        if history_response.status_code == 200:
            history_data = history_response.json().get("history", [])
            if history_data:
                fig_drift = render_bias_drift(history_data)
                if fig_drift:
                    st.plotly_chart(fig_drift, use_container_width=True)

                # Summary row below chart
                df_h = pd.DataFrame(history_data)
                total   = len(df_h)
                passing = int((pd.to_numeric(df_h["fairness_ratio"], errors="coerce") >= 0.8).sum())
                avg_r   = pd.to_numeric(df_h["fairness_ratio"], errors="coerce").mean()
                latest  = pd.to_numeric(df_h["fairness_ratio"], errors="coerce").iloc[-1] if total > 0 else 0
                trend_icon = "↑" if total > 1 and pd.to_numeric(df_h["fairness_ratio"], errors="coerce").iloc[-1] > pd.to_numeric(df_h["fairness_ratio"], errors="coerce").iloc[-2] else "↓"
                trend_color = "#4ade80" if trend_icon == "↑" else "#f87171"

                st.markdown(f"""
                <div style="display:flex;gap:10px;margin-top:12px;">
                    <div style="flex:1;background:#12141f;border:1px solid #1e2030;border-radius:10px;padding:10px 14px;text-align:center;">
                        <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1px;margin-bottom:4px;">TOTAL AUDITS</div>
                        <div style="font-size:18px;color:#818cf8;font-family:'Syne',sans-serif;font-weight:700;">{total}</div>
                    </div>
                    <div style="flex:1;background:#12141f;border:1px solid #1e2030;border-radius:10px;padding:10px 14px;text-align:center;">
                        <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1px;margin-bottom:4px;">PASSING</div>
                        <div style="font-size:18px;color:#4ade80;font-family:'Syne',sans-serif;font-weight:700;">{passing}/{total}</div>
                    </div>
                    <div style="flex:1;background:#12141f;border:1px solid #1e2030;border-radius:10px;padding:10px 14px;text-align:center;">
                        <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1px;margin-bottom:4px;">AVG RATIO</div>
                        <div style="font-size:18px;color:#c8cad4;font-family:'Syne',sans-serif;font-weight:700;">{avg_r:.3f}</div>
                    </div>
                    <div style="flex:1;background:#12141f;border:1px solid #1e2030;border-radius:10px;padding:10px 14px;text-align:center;">
                        <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1px;margin-bottom:4px;">TREND</div>
                        <div style="font-size:18px;font-family:'Syne',sans-serif;font-weight:700;color:{trend_color};">{trend_icon} {latest:.3f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:160px;gap:10px;">
                    <div style="font-size:32px;opacity:0.1;">◉</div>
                    <div style="font-size:12px;color:#3a3d52;font-family:'DM Mono',monospace;text-align:center;">No audit history yet.<br>Run a compliance audit to see drift.</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error("Could not fetch audit history from backend.")
    except Exception as e:
        st.markdown(f"""
        <div style="padding:1rem;background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.15);border-radius:10px;font-size:13px;color:#f87171;font-family:'DM Mono',monospace;">
            Backend unreachable — start the FastAPI server to see live drift data.
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


    # ── Conversational Audit Agent ─────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🤖 EquiGuard Audit Agent</div>', unsafe_allow_html=True)

    _gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not _gemini_key:
        st.markdown("""
        <div class="info-chip">◌ Set <span style="color:#f0f1f5;">GEMINI_API_KEY</span> in your .env to activate the Audit Agent.</div>
        """, unsafe_allow_html=True)
    elif st.session_state.audit_result is None:
        st.markdown("""
        <div style="text-align:center;padding:2rem;font-size:13px;color:#3a3d52;font-family:'DM Mono',monospace;">
            Run a compliance audit first — the agent reads your live audit results.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="font-size:12px;color:#4b5280;font-family:'DM Mono',monospace;margin-bottom:1rem;">
            Ask anything about this audit in plain English.
        </div>
        """, unsafe_allow_html=True)

        for _msg in st.session_state.chat_history:
            with st.chat_message(_msg["role"]):
                st.markdown(_msg["content"])

        if _user_input := st.chat_input("e.g. Why did we fail the EEOC check?", key="agent_input"):
            st.session_state.chat_history.append({"role": "user", "content": _user_input})
            with st.chat_message("user"):
                st.markdown(_user_input)

            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    try:
                        from google import genai as _genai
                        from google.genai import types as _gtypes

                        _client = _genai.Client(api_key=_gemini_key)

                        _res  = st.session_state.audit_result
                        _prox = st.session_state.flagged_columns or []
                        _sys  = (
                            "You are the EquiGuard Audit Agent — an AI expert in EEOC compliance "
                            "and algorithmic bias detection embedded inside the EquiGuard platform.\n\n"
                            "The following JSON contains the live audit results for the model under review:\n\n"
                            f"{json.dumps(_res, indent=2)}\n\n"
                            f"Flagged proxy variables: {_prox if _prox else 'None detected'}\n\n"
                            "Key definitions:\n"
                            "- fairness_ratio: EEOC 4/5ths disparate impact ratio (must be >= 0.80 to pass)\n"
                            "- group_a_rate: privileged group selection rate\n"
                            "- group_b_rate: unprivileged group selection rate\n"
                            "- shap_summary: mean |SHAP| per feature (higher = more influential)\n"
                            "- compliance_pass: True = model passed the EEOC 4/5ths rule\n\n"
                            "Answer in plain English suitable for a business executive or legal team. "
                            "Be concise, cite specific numbers from the audit data, "
                            "and never fabricate values not present in the JSON."
                        )

                        # Build typed history for the new SDK
                        _gemini_hist = []
                        for _m in st.session_state.chat_history[:-1]:
                            _role = "model" if _m["role"] == "assistant" else "user"
                            _gemini_hist.append(
                                _gtypes.Content(
                                    role=_role,
                                    parts=[_gtypes.Part(text=_m["content"])],
                                )
                            )

                        _chat_session = _client.chats.create(
                            model="gemini-2.5-flash",
                            config=_gtypes.GenerateContentConfig(
                                system_instruction=_sys,
                            ),
                            history=_gemini_hist,
                        )
                        _reply = _chat_session.send_message(_user_input).text

                        st.markdown(_reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": _reply})

                    except Exception as _e:
                        _err = f"Agent error: {_e}"
                        st.error(_err)
                        st.session_state.chat_history.append({"role": "assistant", "content": _err})

        if st.session_state.chat_history:
            if st.button("✕  Clear conversation", key="btn_clear_chat"):
                st.session_state.chat_history = []
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AUDIT ENGINE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_page == "Audit Engine":

    st.markdown("""
    <div class="eq-header">
        <div>
            <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#f0f1f5;">Audit Engine</div>
            <div style="font-size:12px;color:#4b5280;font-family:'DM Mono',monospace;margin-top:2px;">Upload data · Select columns · Run compliance checks</div>
        </div>
        <div class="eq-status-dot">EEOC Engine Active</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">◈ Data Configuration</div>', unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload Dataset (CSV)", type=["csv"], label_visibility="collapsed")

        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
            df.to_csv("uploaded_data.csv", index=False)
            st.session_state.data_path = "uploaded_data.csv"
            columns = df.columns.tolist()
            st.markdown(f"""
            <div class="info-chip">✓ {uploaded_file.name} · {len(df):,} rows · {len(columns)} columns</div>
            """, unsafe_allow_html=True)
            st.session_state.target_col = st.selectbox("Target Column", columns, key="target_sel")
            st.session_state.protected_col = st.selectbox("Protected Attribute", columns, key="protected_sel")
        else:
            st.markdown("""
            <div class="info-chip">◌ Using default: golden_demo_dataset.csv</div>
            """, unsafe_allow_html=True)
            st.session_state.data_path = "golden_demo_dataset.csv"
            st.session_state.target_col = "loan_approved"
            st.session_state.protected_col = "race"
            st.markdown("""
            <div style="font-size:12px;color:#3a3d52;margin-top:8px;">
                Target: <span style="color:#818cf8;font-family:'DM Mono',monospace;">loan_approved</span> &nbsp;·&nbsp;
                Protected: <span style="color:#818cf8;font-family:'DM Mono',monospace;">race</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">⬡ Run Audits</div>', unsafe_allow_html=True)

        api_payload = {
            "data_path": st.session_state.data_path,
            "target_col": st.session_state.target_col,
            "protected_col": st.session_state.protected_col
        }

        if st.button("⬡  Run Pre-Processing Audit", key="btn_preprocess"):
            with st.spinner("Scanning for proxy variables..."):
                try:
                    response = api_post("/audit/preprocess", api_payload)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("proxies_detected"):
                            flagged_cols = data.get("flagged_columns", [])
                            st.session_state.flagged_columns = flagged_cols
                            st.warning(f"⚠ Proxy variables detected: {', '.join(flagged_cols)}")
                        else:
                            st.session_state.flagged_columns = []
                            st.success("✓ No hidden proxy variables detected.")
                    else:
                        st.error(f"Audit failed: {response.status_code}")
                except Exception as e:
                    st.error(f"Cannot reach backend: {e}")

        if st.button("◉  Run Full Compliance Audit", key="btn_compliance"):
            with st.spinner("Running EEOC compliance audit..."):
                try:
                    response = api_post("/audit/compliance", api_payload)
                    if response.status_code == 200:
                        st.session_state.audit_result = response.json()
                        # Reset cached PDFs so they are regenerated for the new audit
                        st.session_state.report_bytes = None
                        st.session_state.cert_bytes = None
                        st.session_state.sim_result = None
                        st.session_state.pkg_bytes = None
                        st.success("✓ Audit complete.")
                        st.rerun()
                    else:
                        st.error(f"Audit failed: {response.status_code}")
                except Exception as e:
                    st.error(f"Cannot reach backend: {e}")

        if st.button("⟳  Apply Mitigation & Retrain", key="btn_mitigate"):
            with st.spinner("Retraining model with bias mitigation..."):
                try:
                    mitigation_payload = api_payload.copy()
                    mitigation_payload["flagged_columns"] = st.session_state.flagged_columns
                    response = api_post("/audit/mitigate", mitigation_payload)
                    if response.status_code == 200:
                        st.session_state.audit_result = response.json()
                        # Reset cached PDFs so they are regenerated for the new result
                        st.session_state.report_bytes = None
                        st.session_state.cert_bytes = None
                        st.success("✓ Mitigation applied. Model retrained.")
                        st.rerun()
                    else:
                        st.error(f"Mitigation failed: {response.status_code}")
                except Exception as e:
                    st.error(f"Cannot reach backend: {e}")

        st.markdown("<div style='margin-top:1rem;'>", unsafe_allow_html=True)
        if st.session_state.audit_result:

            # ── Fetch Executive Report PDF exactly once, cache in session_state ──
            if st.session_state.report_bytes is None:
                try:
                    export_payload = st.session_state.audit_result.copy()
                    export_payload["flagged_proxies"] = st.session_state.flagged_columns
                    pdf_response = api_post("/audit/export", export_payload)
                    if pdf_response.status_code == 200:
                        st.session_state.report_bytes = pdf_response.content
                except Exception:
                    pass  # stays None — button will render disabled

            if st.session_state.report_bytes:
                st.download_button(
                    label="↓  Export Executive Report (PDF)",
                    data=st.session_state.report_bytes,
                    file_name="EquiGuard_Executive_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_report",
                )
            else:
                st.button("↓  Export Executive Report (PDF)", disabled=True,
                          use_container_width=True, key="dl_report_disabled")

            # ── Compliance Certificate (only shown on PASS) ──────────────────
            if st.session_state.audit_result.get("compliance_pass"):

                # Fetch certificate PDF exactly once, cache in session_state
                if st.session_state.cert_bytes is None:
                    try:
                        cert_payload = st.session_state.audit_result.copy()
                        cert_response = api_post("/audit/certificate", cert_payload)
                        if cert_response.status_code == 200:
                            st.session_state.cert_bytes = cert_response.content
                        else:
                            st.warning(
                                f"Certificate generation failed (HTTP {cert_response.status_code}): "
                                f"{cert_response.text[:200]}"
                            )
                    except Exception as e:
                        st.error(f"Certificate request error: {e}")

                st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
                if st.session_state.cert_bytes:
                    st.download_button(
                        label="⬡  Download EEOC Compliance Certificate",
                        data=st.session_state.cert_bytes,
                        file_name="EquiGuard_EEOC_Certificate.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        help="One-page compliance certificate — issue to auditors or executives.",
                        key="dl_cert",
                    )
                else:
                    st.button("⬡  Download EEOC Compliance Certificate",
                              disabled=True, use_container_width=True, key="dl_cert_disabled")
                st.markdown("</div>", unsafe_allow_html=True)

                # ── Regulatory Package ZIP ───────────────────────────────────
                if st.session_state.pkg_bytes is None:
                    try:
                        pkg_payload = st.session_state.audit_result.copy()
                        pkg_payload["flagged_proxies"] = st.session_state.flagged_columns
                        pkg_resp = api_post("/audit/package", pkg_payload)
                        if pkg_resp.status_code == 200:
                            st.session_state.pkg_bytes = pkg_resp.content
                    except Exception:
                        pass

                st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
                if st.session_state.pkg_bytes:
                    st.download_button(
                        label="↓  Download Regulatory Package (ZIP)",
                        data=st.session_state.pkg_bytes,
                        file_name="EquiGuard_Regulatory_Package.zip",
                        mime="application/zip",
                        use_container_width=True,
                        help="Full package: executive PDF, certificate, methodology, raw JSON.",
                        key="dl_pkg",
                    )
                else:
                    st.button("↓  Download Regulatory Package (ZIP)", disabled=True,
                              use_container_width=True, key="dl_pkg_disabled")
                st.markdown("</div>", unsafe_allow_html=True)

            else:
                st.markdown("""
                <div style="margin-top:8px;background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.15);
                border-radius:10px;padding:10px 14px;font-size:12px;color:#f87171;font-family:'DM Mono',monospace;">
                    ✗  Certificate unavailable — model did not pass EEOC audit.<br>
                    <span style="color:#4b5280;">Apply mitigation and re-run to unlock.</span>
                </div>
                """, unsafe_allow_html=True)


        else:
            st.button("↓  Export Executive Report (PDF)", disabled=True,
                      help="Run a compliance audit first.", use_container_width=True,
                      key="dl_report_none")
            st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
            st.button("⬡  Download EEOC Compliance Certificate", disabled=True,
                      help="Run a compliance audit first.", use_container_width=True,
                      key="dl_cert_none")
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── What-If Simulator ─────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">⬡ What-If Mitigation Simulator</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-chip">◌ Simulates dropping each feature individually and retraining — projects the resulting EEOC ratio and accuracy cost.</div>
    """, unsafe_allow_html=True)

    sim_payload = {
        "data_path": st.session_state.get("data_path", "golden_demo_dataset.csv"),
        "target_col": st.session_state.get("target_col", "loan_approved"),
        "protected_col": st.session_state.get("protected_col", "race"),
    }

    if st.button("⬡  Simulate Mitigation Options", key="btn_simulate", use_container_width=True):
        with st.spinner("Running simulations — this may take 30–60 seconds…"):
            try:
                sim_resp = api_post("/audit/simulate", sim_payload)
                if sim_resp.status_code == 200:
                    st.session_state.sim_result = sim_resp.json().get("simulations", [])
                else:
                    st.error(f"Simulation failed: {sim_resp.status_code}")
            except Exception as e:
                st.error(f"Cannot reach backend: {e}")

    if st.session_state.sim_result:
        sims = st.session_state.sim_result
        best_idx = 0  # already sorted by projected_ratio desc

        rows_html = ""
        for i, s in enumerate(sims):
            pr   = s["projected_ratio"]
            ad   = s["accuracy_delta"]
            rec  = s["recommendation"]
            feat = s["feature"]
            acc_after = s["accuracy_after"]

            # Colour: ratio
            if pr >= 0.8:
                ratio_color = "#4ade80"
            elif pr >= 0.6:
                ratio_color = "#fbbf24"
            else:
                ratio_color = "#f87171"

            # Colour: accuracy delta
            if ad > -0.01:
                delta_color = "#4ade80"
            elif ad >= -0.05:
                delta_color = "#fbbf24"
            else:
                delta_color = "#f87171"

            delta_sign = "+" if ad >= 0 else ""
            rec_badge = '<span class="rec-drop">✓ Drop</span>' if rec == "drop" else '<span class="rec-keep">Keep</span>'
            row_cls = "best-row" if i == best_idx else ""

            rows_html += f"""
            <tr class="{row_cls}">
                <td>{feat}</td>
                <td><span style="color:{ratio_color};font-family:'DM Mono',monospace;font-weight:600;">{pr:.4f}</span></td>
                <td><span style="color:{delta_color};font-family:'DM Mono',monospace;">{delta_sign}{ad:.4f}</span></td>
                <td>{rec_badge}</td>
            </tr>"""

        st.markdown(f"""
        <table class="sim-table">
            <thead><tr>
                <th>Feature</th>
                <th>Drop → Projected Ratio</th>
                <th>Accuracy Cost</th>
                <th>Recommendation</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        <div style="margin-top:10px;font-size:11px;color:#3a3d52;font-family:'DM Mono',monospace;">
            * Projections are estimates based on held-out test set retraining. Highlighted row = best single feature to drop.
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: BIAS LEADERBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_page == "Bias Leaderboard":

    st.markdown("""
    <div class="eq-header">
        <div>
            <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#f0f1f5;">Bias Leaderboard</div>
            <div style="font-size:12px;color:#4b5280;font-family:'DM Mono',monospace;margin-top:2px;">Temporal drift tracking · Historical compliance records</div>
        </div>
        <div class="eq-status-dot">Live Data</div>
    </div>
    """, unsafe_allow_html=True)

    try:
        history_response = api_get("/audit/history")
        if history_response.status_code == 200:
            history_data = history_response.json().get("history", [])
            if history_data:
                df_history = pd.DataFrame(history_data)
                df_history["timestamp"] = pd.to_datetime(df_history["timestamp"])
                df_history.set_index("timestamp", inplace=True)

                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">◉ Temporal Bias Drift</div>', unsafe_allow_html=True)
                fig_drift = render_bias_drift(history_data)
                if fig_drift:
                    st.plotly_chart(fig_drift, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # Table
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">◈ Audit History</div>', unsafe_allow_html=True)
                for i, (ts, row) in enumerate(df_history.iterrows()):
                    ratio = row.get('fairness_ratio', 0)
                    passed = ratio >= 0.8
                    badge_html = (
                        '<span class="badge-pass" style="font-size:11px;padding:3px 10px;">PASS</span>'
                        if passed else
                        '<span class="badge-fail" style="font-size:11px;padding:3px 10px;">FAIL</span>'
                    )
                    st.markdown(f"""
                    <div class="leaderboard-row">
                        <span class="rank-num">#{i+1}</span>
                        <span style="font-size:12px;color:#4b5280;font-family:'DM Mono',monospace;">{ts.strftime('%Y-%m-%d %H:%M')}</span>
                        <span style="font-size:13px;color:#818cf8;font-family:'DM Mono',monospace;">{ratio:.4f}</span>
                        {badge_html}
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # ── Mitigation Impact Comparison ──────────────────────────────
                if len(history_data) >= 2:
                    _before = history_data[-2]
                    _after  = history_data[-1]
                    _br = _before.get("fairness_ratio", 0.0)
                    _ar = _after.get("fairness_ratio", 0.0)
                    _delta = _ar - _br
                    _delta_color = "#4ade80" if _delta >= 0 else "#f87171"
                    _delta_sign  = "+" if _delta >= 0 else ""
                    _bpass = _before.get("compliance_pass", False)
                    _apass = _after.get("compliance_pass", False)
                    _bbadge = '<span class="badge-pass" style="font-size:11px;padding:3px 10px;">PASS</span>' if _bpass else '<span class="badge-fail" style="font-size:11px;padding:3px 10px;">FAIL</span>'
                    _abadge = '<span class="badge-pass" style="font-size:11px;padding:3px 10px;">PASS</span>' if _apass else '<span class="badge-fail" style="font-size:11px;padding:3px 10px;">FAIL</span>'
                    _net_word = "improved" if _delta >= 0 else "worsened"
                    _net_color = "#4ade80" if _delta >= 0 else "#f87171"

                    st.markdown('<div class="section-card">', unsafe_allow_html=True)
                    st.markdown('<div class="section-title">⟳ Mitigation Impact</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="compare-grid">
                        <div class="compare-side">
                            <div class="compare-label">Before Mitigation</div>
                            <div class="compare-metric">
                                <div class="compare-metric-label">Fairness Ratio</div>
                                <div class="compare-metric-value">{_br:.4f}</div>
                            </div>
                            <div class="compare-metric">
                                <div class="compare-metric-label">EEOC Status</div>
                                <div style="margin-top:4px;">{_bbadge}</div>
                            </div>
                            <div class="compare-metric">
                                <div class="compare-metric-label">Top Feature</div>
                                <div style="font-size:13px;color:#818cf8;font-family:'DM Mono',monospace;margin-top:4px;">{_before.get('top_feature','—')}</div>
                            </div>
                        </div>
                        <div class="compare-side">
                            <div class="compare-label">After Mitigation</div>
                            <div class="compare-metric">
                                <div class="compare-metric-label">Fairness Ratio</div>
                                <div class="compare-metric-value" style="color:{_delta_color};">
                                    {_ar:.4f}
                                    <span style="font-size:14px;font-family:'DM Mono',monospace;margin-left:8px;">
                                        {_delta_sign}{_delta:.4f} {'↑' if _delta >= 0 else '↓'}
                                    </span>
                                </div>
                            </div>
                            <div class="compare-metric">
                                <div class="compare-metric-label">EEOC Status</div>
                                <div style="margin-top:4px;">{_abadge}</div>
                            </div>
                            <div class="compare-metric">
                                <div class="compare-metric-label">Top Feature</div>
                                <div style="font-size:13px;color:#818cf8;font-family:'DM Mono',monospace;margin-top:4px;">{_after.get('top_feature','—')}</div>
                            </div>
                        </div>
                    </div>
                    <div style="margin-top:14px;padding:10px 14px;background:#0a0b10;border-radius:10px;border:1px solid #1a1c28;font-size:13px;color:#c8cad4;">
                        Net result: Fairness ratio <strong style="color:{_net_color};">{_net_word} by {_delta_sign}{_delta:.4f}</strong> after proxy removal.
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.markdown("""
                <div class="section-card" style="text-align:center;padding:3rem;">
                    <div style="font-size:48px;opacity:0.1;margin-bottom:1rem;">◉</div>
                    <div style="font-size:14px;color:#3a3d52;font-family:'DM Mono',monospace;">No audit history yet.<br>Run a compliance audit to populate the leaderboard.</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error("Failed to fetch audit history from backend.")
    except Exception as e:
        st.error(f"Could not connect to backend: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: INTERSECTIONAL
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_page == "Intersectional":

    st.markdown("""
    <div class="eq-header">
        <div>
            <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#f0f1f5;">Intersectional Audit</div>
            <div style="font-size:12px;color:#4b5280;font-family:'DM Mono',monospace;margin-top:2px;">
                A model can pass for one group while failing another. This view audits all detected demographic attributes simultaneously.
            </div>
        </div>
        <div class="eq-status-dot">Multi-Attribute</div>
    </div>
    """, unsafe_allow_html=True)

    ix_payload = {
        "data_path": st.session_state.get("data_path", "golden_demo_dataset.csv"),
        "target_col": st.session_state.get("target_col", "loan_approved"),
    }

    if st.button("⬢  Run Intersectional Audit", key="btn_ix", use_container_width=False):
        with st.spinner("Scanning all protected attributes…"):
            try:
                ix_resp = api_post("/audit/intersectional", ix_payload)
                if ix_resp.status_code == 200:
                    st.session_state.intersectional_result = ix_resp.json()
                    st.session_state.ix_summary = None  # Reset AI summary for new audit
                else:
                    st.error(f"Intersectional audit failed: {ix_resp.status_code}")
            except Exception as e:
                st.error(f"Cannot reach backend: {e}")

    ix = st.session_state.intersectional_result
    if ix:
        prot_cols = ix.get("protected_columns", [])
        ratios    = ix.get("ratios", {})
        corrs     = ix.get("correlations", {})

        # ── Compliance badge row ─────────────────────────────────────────────
        if prot_cols:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">◈ Compliance Status per Attribute</div>', unsafe_allow_html=True)
            badges_html = ""
            for col in prot_cols:
                r = ratios.get(col)
                if r is None:
                    badge_color = "#6b7280"; badge_text = "N/A"
                elif r >= 0.8:
                    badge_color = "#4ade80"; badge_text = "PASS"
                else:
                    badge_color = "#f87171"; badge_text = "FAIL"
                badges_html += f"""
                <div class="ix-badge">
                    <div class="ix-badge-label">{col}</div>
                    <div class="ix-badge-val" style="color:{badge_color};">{badge_text}</div>
                    <div style="font-size:11px;color:#4b5280;font-family:'DM Mono',monospace;margin-top:4px;">{f'{r:.4f}' if r is not None else '—'}</div>
                </div>"""
            st.markdown(f'<div style="display:flex;flex-wrap:wrap;margin-top:8px;">{badges_html}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Correlation heatmap ──────────────────────────────────────────────
        if prot_cols and corrs:
            features = list(corrs.keys())
            z_matrix = [[corrs[f].get(c, 0.0) for c in prot_cols] for f in features]

            fig_ix = go.Figure(go.Heatmap(
                z=z_matrix,
                x=prot_cols,
                y=features,
                colorscale=[
                    [0.0,  "#0d0e14"],
                    [0.15, "#1a1c40"],
                    [0.5,  "#6b21a8"],
                    [1.0,  "#ef4444"],
                ],
                zmin=0, zmax=1,
                hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>|r| = %{z:.4f}<extra></extra>",
                colorbar=dict(
                    title=dict(
                        text="| Pearson r |",
                        font=dict(color="#6b7280", size=10, family="DM Mono"),
                    ),
                    tickfont=dict(color="#6b7280", size=10, family="DM Mono"),
                ),

            ))
            # Threshold annotation line
            fig_ix.add_shape(
                type="line", x0=-0.5, x1=len(prot_cols)-0.5,
                y0=-0.5, y1=-0.5,
                line=dict(color="rgba(0,0,0,0)", width=0),
            )
            fig_ix.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#6b7280", family="DM Sans", size=12),
                margin=dict(l=10, r=10, t=30, b=10),
                height=max(260, len(features) * 36),
                xaxis=dict(side="top", tickfont=dict(color="#c8cad4", size=12)),
                yaxis=dict(tickfont=dict(color="#c8cad4", size=11), autorange="reversed"),
            )

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">⬢ Feature × Protected Attribute Correlation</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="info-chip">◌ Cells above 0.15 (proxy hunter threshold) indicate potential proxy bias. Cells above 0.5 indicate high correlation risk.</div>
            """, unsafe_allow_html=True)
            st.plotly_chart(fig_ix, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            # ── AI Correlation Summary ──────────────────────────────────────────
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">✨ AI Correlation Summary</div>', unsafe_allow_html=True)
            
            _gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
            if not _gemini_key:
                st.markdown('<div class="info-chip">◌ Set <span style="color:#f0f1f5;">GEMINI_API_KEY</span> in your .env to enable AI summaries.</div>', unsafe_allow_html=True)
            else:
                if st.session_state.ix_summary:
                    st.markdown(f'<div style="font-size:13px;color:#c8cad4;font-family:\'DM Sans\',sans-serif;line-height:1.6;">{st.session_state.ix_summary}</div>', unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="font-size:12px;color:#4b5280;font-family:'DM Mono',monospace;margin-bottom:1rem;">
                        Analyze the correlation matrix above for hidden proxy variables using Gemini.
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("✨ Generate AI Summary", key="btn_ix_summary"):
                        with st.spinner("Analyzing correlation matrix..."):
                            try:
                                from google import genai as _genai
                                from google.genai import types as _gtypes
                                _client = _genai.Client(api_key=_gemini_key)
                                
                                _sys_prompt = (
                                    "You are an AI bias detection expert conducting a detailed intersectional audit. "
                                    "Analyze the following Pearson correlation matrix between dataset features and protected demographic attributes.\n\n"
                                    "Correlation Matrix JSON:\n" + json.dumps(corrs, indent=2) + "\n\n"
                                    "Please provide a comprehensive, multi-paragraph analysis with the following structure:\n"
                                    "1. **High-Risk Proxies (|r| > 0.5):** Detail any features strongly correlated with protected attributes. Explain why this poses a severe legal or ethical risk.\n"
                                    "2. **Moderate-Risk Proxies (0.15 < |r| <= 0.5):** List features showing moderate correlation. Provide a brief hypothesis on how these variables might unintentionally encode demographic data.\n"
                                    "3. **Safe Features (|r| <= 0.15):** Briefly summarize which features appear statistically independent of protected attributes.\n"
                                    "4. **Actionable Recommendations:** Suggest 2-3 specific mitigation strategies for the data science team (e.g., feature dropping, orthogonalization, or re-weighting).\n\n"
                                    "Ensure the tone is professional and objective. Use Markdown formatting (bolding, bullet points) to make the report highly readable. "
                                    "If no features cross a threshold, explicitly state that."
                                )
                                
                                _chat = _client.chats.create(
                                    model="gemini-2.5-flash",
                                    config=_gtypes.GenerateContentConfig(system_instruction=_sys_prompt)
                                )
                                _reply = _chat.send_message("Please summarize the proxy risks in this correlation table.").text
                                
                                st.session_state.ix_summary = _reply
                                st.rerun()
                            except Exception as _e:
                                st.error(f"Failed to generate summary: {_e}")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="section-card" style="text-align:center;padding:3rem;">
            <div style="font-size:48px;opacity:0.08;margin-bottom:1rem;">⬢</div>
            <div style="font-size:14px;color:#3a3d52;font-family:'DM Mono',monospace;">
                Click "Run Intersectional Audit" to scan all detected demographic attributes simultaneously.
            </div>
        </div>
        """, unsafe_allow_html=True)