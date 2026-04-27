import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

# ── Load .env ──────────────────────────────────────────────────────────────────
load_dotenv()

# ── Boot FastAPI backend (Streamlit Cloud single-process trick) ────────────────
# Streamlit Cloud only runs one process. This spawns the FastAPI backend as a
# child process on port 8000 the first time the app boots, then sets a flag so
# subsequent Streamlit re-runs don't spawn duplicate servers.
import subprocess
import time

if "BACKEND_STARTED" not in os.environ:
    print("[EquiGuard] Booting FastAPI backend…")
    subprocess.Popen(
        ["uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    os.environ["BACKEND_STARTED"] = "1"
    time.sleep(3)   # Allow uvicorn time to bind before Streamlit renders the UI
# ──────────────────────────────────────────────────────────────────────────────

# ── Custom Components ─────────────────────────────────────────────────────────
def render_gradual_blur(position='bottom', strength=2, height='6rem', divCount=5,
                        exponential=False, curve='linear', opacity=1, zIndex=9999):
    """
    Ports the React GradualBlur component to Streamlit by injecting HTML
    directly into window.parent.document.body via a JS bridge.
    backdrop-filter is blocked by Streamlit's nested containers, so this
    is the only approach that actually works.
    """
    import streamlit.components.v1 as _components

    direction_map = {
        "bottom": "to bottom", "top": "to top",
        "left": "to left",     "right": "to right"
    }
    direction = direction_map.get(position, "to bottom")

    curve_js = {
        'linear':       'function(p){ return p; }',
        'bezier':       'function(p){ return p*p*(3-2*p); }',
        'ease-in':      'function(p){ return p*p; }',
        'ease-out':     'function(p){ return 1-Math.pow(1-p,2); }',
        'ease-in-out':  'function(p){ return p<0.5?2*p*p:1-Math.pow(-2*p+2,2)/2; }',
    }.get(curve, 'function(p){ return p; }')

    js = """
(function() {
  var STYLE_ID = 'eq-gradual-blur-style';
  var EL_ID    = 'eq-gradual-blur-""" + position + """';
  var doc      = window.parent.document;

  // ── Inject CSS once ───────────────────────────────────────────────────────
  if (!doc.getElementById(STYLE_ID)) {
    var s = doc.createElement('style');
    s.id = STYLE_ID;
    s.textContent = [
      '.eq-gb { pointer-events:none; overflow:hidden; }',
      '.eq-gb-inner { position:relative; width:100%; height:100%; }',
      '@supports not (backdrop-filter:blur(1px)){',
      '  .eq-gb-inner > div { background:rgba(0,0,0,0.3); opacity:0.5; }',
      '}'
    ].join('');
    doc.head.appendChild(s);
  }

  // ── Remove previous instance so hot-reload doesn't stack ─────────────────
  var old = doc.getElementById(EL_ID);
  if (old) old.remove();

  // ── Config ────────────────────────────────────────────────────────────────
  var position   = '""" + position + """';
  var strength   = """ + str(strength) + """;
  var height     = '""" + height + """';
  var divCount   = """ + str(divCount) + """;
  var exponential= """ + ("true" if exponential else "false") + """;
  var opacity    = """ + str(opacity) + """;
  var zIndex     = """ + str(zIndex) + """;
  var direction  = '""" + direction + """';
  var curveFunc  = """ + curve_js + """;

  // ── Build blur layers ─────────────────────────────────────────────────────
  var increment = 100 / divCount;
  var inner = doc.createElement('div');
  inner.className = 'eq-gb-inner';

  for (var i = 1; i <= divCount; i++) {
    var progress = curveFunc(i / divCount);
    var blurValue;
    if (exponential) {
      blurValue = Math.pow(2, progress * 4) * 0.0625 * strength;
    } else {
      blurValue = 0.0625 * (progress * divCount + 1) * strength;
    }

    var p1 = Math.round((increment*i - increment)*10)/10;
    var p2 = Math.round(increment*i*10)/10;
    var p3 = Math.round((increment*i + increment)*10)/10;
    var p4 = Math.round((increment*i + increment*2)*10)/10;

    var stops = 'transparent '+p1+'%, black '+p2+'%';
    if (p3 <= 100) stops += ', black '+p3+'%';
    if (p4 <= 100) stops += ', transparent '+p4+'%';

    var mask = 'linear-gradient('+direction+', '+stops+')';
    var bv   = blurValue.toFixed(3)+'rem';

    var div = doc.createElement('div');
    div.style.cssText = [
      'position:absolute', 'inset:0',
      'mask-image:'+mask, '-webkit-mask-image:'+mask,
      'backdrop-filter:blur('+bv+')', '-webkit-backdrop-filter:blur('+bv+')',
      'opacity:'+opacity
    ].join(';');
    inner.appendChild(div);
  }

  // ── Build container & attach ──────────────────────────────────────────────
  var container = doc.createElement('div');
  container.id = EL_ID;
  container.className = 'eq-gb';

  var isVertical = (position === 'top' || position === 'bottom');
  var css = [
    'position:fixed',
    position+':0',
    isVertical ? 'left:0;right:0;height:'+height+';width:100%'
               : 'top:0;bottom:0;width:'+height+';height:100%',
    'pointer-events:none',
    'z-index:'+zIndex,
    'overflow:hidden'
  ].join(';');
  container.style.cssText = css;
  container.appendChild(inner);
  var target = doc.querySelector('.stApp') || doc.body;
  target.appendChild(container);
})();
"""
    st.iframe("<script>" + js + "</script>", height=1)



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
# ── Google AI feature state ─────────────────────────────────────────────────────────────
if "narrative" not in st.session_state:
    st.session_state.narrative = None          # Gemini Risk Narrative
if "narrative_model" not in st.session_state:
    st.session_state.narrative_model = "template"
if "mitigation_code" not in st.session_state:
    st.session_state.mitigation_code = None    # Vertex AI Remediation
if "mitigation_model" not in st.session_state:
    st.session_state.mitigation_model = "template"
if "mitigation_note" not in st.session_state:
    st.session_state.mitigation_note = ""
if "vision_result" not in st.session_state:
    st.session_state.vision_result = None      # Vision AI Scan result
if "pkg_bytes" not in st.session_state:
    st.session_state.pkg_bytes = None
if "intersectional_result" not in st.session_state:
    st.session_state.intersectional_result = None
if "ix_summary" not in st.session_state:
    st.session_state.ix_summary = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # [{"role": "user"|"assistant", "content": str}]
# ── New feature state
if "comparison_result" not in st.session_state:
    st.session_state.comparison_result = None
if "preflight_result" not in st.session_state:
    st.session_state.preflight_result = None
if "backend_status" not in st.session_state:
    st.session_state.backend_status = None
if "hero_dismissed" not in st.session_state:
    st.session_state.hero_dismissed = False


# ── Page Config ────────────────────────────────────────────────────────────────
try:
    from PIL import Image as _PILImage
    _icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_small.png")
    _page_icon = _PILImage.open(_icon_path)
except Exception:
    _page_icon = "⚖"

st.set_page_config(
    page_title="EquiGuard — AI Bias Firewall",
    page_icon=_page_icon,
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
    background-color: #050609;
    color: #c8cad4;
    /* Subtle dot-grid background */
    background-image:
        radial-gradient(rgba(99,102,241,0.12) 1px, transparent 1px);
    background-size: 28px 28px;
    background-attachment: fixed;
}
.block-container {
    padding: 0 2rem 10rem 2rem !important;
    max-width: 100% !important;
}

/* ── Hide default Streamlit chrome (without touching the sidebar toggle) ── */
#MainMenu, footer { visibility: hidden; }
[data-testid="stToolbar"]          { display: none !important; }
[data-testid="stAppDeployButton"]  { display: none !important; }
[data-testid="stStatusWidget"]     { visibility: hidden; }
header { background: transparent !important; }
section[data-testid="stSidebar"] > div { background: #0d0e14; border-right: 1px solid #1e2030; }

/* ── Hide the collapse (<<) button so the sidebar stays permanently open ── */
/* This prevents users getting trapped without navigation */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapseSidebarButton"],
section[data-testid="stSidebar"] button[aria-label="Collapse sidebar"],
section[data-testid="stSidebar"] button[title="Collapse sidebar"] {
    display: none !important;
}

/* ── Expand (>>) button — styled prominently as a fallback ── */
/* If the sidebar IS collapsed, this pill is always findable */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    position: fixed !important;
    top: 0.6rem !important;
    left: 0.6rem !important;
    z-index: 99999 !important;
    background: #6366f1 !important;
    border-radius: 8px !important;
    padding: 6px 10px !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.4) !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg {
    fill: #ffffff !important;
    color: #ffffff !important;
}


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
    border: 1px solid #2F293A;
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
    --glow-x: 50%;
    --glow-y: 50%;
    --glow-intensity: 0;
    --glow-radius: 250px;
}
.kpi-card::after {
    content: '';
    position: absolute;
    inset: 0;
    padding: 2px;
    background: radial-gradient(
        var(--glow-radius) circle at var(--glow-x) var(--glow-y),
        rgba(132, 0, 255, calc(var(--glow-intensity) * 0.8)) 0%,
        rgba(132, 0, 255, calc(var(--glow-intensity) * 0.3)) 30%,
        transparent 60%
    );
    border-radius: inherit;
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask-composite: exclude;
    pointer-events: none;
    opacity: 1;
    transition: opacity 0.3s ease;
    z-index: 1;
}

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

/* ── Section Cards (MagicBento Styled) ── */
.section-card {
    background: #0d0e14;
    border: 1px solid #2F293A;
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
    --glow-x: 50%;
    --glow-y: 50%;
    --glow-intensity: 0;
    --glow-radius: 300px;
}
.section-card::after {
    content: '';
    position: absolute;
    inset: 0;
    padding: 2px;
    background: radial-gradient(
        var(--glow-radius) circle at var(--glow-x) var(--glow-y),
        rgba(132, 0, 255, calc(var(--glow-intensity) * 0.8)) 0%,
        rgba(132, 0, 255, calc(var(--glow-intensity) * 0.3)) 30%,
        transparent 60%
    );
    border-radius: inherit;
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask-composite: exclude;
    pointer-events: none;
    opacity: 1;
    transition: opacity 0.3s ease;
    z-index: 1;
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
    min-width: 40px;
}
.history-filename {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: #a4b1cd;
    background: #151722;
    padding: 3px 8px;
    border-radius: 4px;
    border: 1px solid #1e2030;
    max-width: 140px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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

/* ── Audit Agent Chat Messages ── */
[data-testid="stChatMessage"] { background:#0d0e14 !important; border:1px solid #1a1c28 !important; border-radius:14px !important; margin-bottom:8px !important; }
[data-testid="stChatMessage"] p { font-size:13px !important; color:#c8cad4 !important; font-family:'DM Sans',sans-serif !important; line-height:1.65 !important; }
[data-testid="stBottom"], [data-testid="stBottomBlockContainer"] { z-index: 1001 !important; }
[data-testid="stChatInputContainer"] { background:#0d0e14 !important; border:1px solid #1e2030 !important; border-radius:12px !important; z-index: 1001 !important; position: relative; }
[data-testid="stChatInputContainer"]:focus-within { border-color:#6366f1 !important; }

/* ── Uiverse Search Input (Audit Agent) ── */
[data-testid="stTextInput"]:has(input[aria-label="Ask the agent"]),
[data-testid="stTextInput"]:has(input[id*="agent_input"]) {
  background: linear-gradient(135deg, rgba(30,32,48,1) 0%, rgba(20,22,35,1) 100%);
  border-radius: 1000px !important;
  padding: 7px !important;
  box-shadow: rgba(99,102,241,0.5) 3px 3px 5px 0px, rgba(99,102,241,0.4) 5px 5px 20px 0px;
  border: none !important;
  position: relative;
  z-index: 0;
}
[data-testid="stTextInput"]:has(input[aria-label="Ask the agent"]) div,
[data-testid="stTextInput"]:has(input[id*="agent_input"]) div {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 50px !important;
}
[data-testid="stTextInput"]:has(input[aria-label="Ask the agent"]) input,
[data-testid="stTextInput"]:has(input[id*="agent_input"]) input {
  background: linear-gradient(135deg, rgba(20,22,35,1) 0%, rgba(15,17,28,1) 100%) !important;
  border: none !important;
  border-radius: 50px !important;
  color: #818cf8 !important;
  font-size: 14px !important;
  font-family: 'DM Sans', sans-serif !important;
  padding: 10px 18px !important;
  box-shadow: none !important;
  transition: background 0.3s ease !important;
}
[data-testid="stTextInput"]:has(input[aria-label="Ask the agent"]) input:focus,
[data-testid="stTextInput"]:has(input[id*="agent_input"]) input:focus {
  background: linear-gradient(135deg, rgba(30,32,55,1) 0%, rgba(20,22,40,1) 100%) !important;
  outline: none !important;
  box-shadow: none !important;
}
/* ── Uiverse Send Button (Audit Agent) ── */
.uv-send-wrap { display:flex; justify-content:center; align-items:center; height:100%; }
.uv-send-container {
  position: relative;
  background: linear-gradient(135deg, rgb(99,102,241) 0%, rgb(79,82,221) 100%);
  border-radius: 1000px;
  padding: 7px;
  display: grid;
  place-content: center;
  z-index: 0;
  width: auto;
  height: 58px;
  cursor: pointer;
  transition: transform 0.15s ease;
}
.uv-send-container:active { transform: scale(0.91); }
.uv-send-inner {
  position: relative;
  border-radius: 50px;
  background: linear-gradient(135deg, rgb(25,27,48) 0%, rgb(15,17,32) 100%);
  min-width: 100px;
  height: 44px;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 16px;
}
.uv-send-inner::before {
  content: "";
  width: 100%; height: 100%;
  border-radius: inherit;
  position: absolute;
  top: -1px; left: -1px;
  background: linear-gradient(0deg, rgb(25,27,48) 0%, rgb(45,48,80) 100%);
  z-index: -1;
}
.uv-send-inner::after {
  content: "";
  width: 100%; height: 100%;
  border-radius: inherit;
  position: absolute;
  bottom: -1px; right: -1px;
  background: linear-gradient(0deg, rgb(79,82,221) 0%, rgb(99,102,241) 100%);
  box-shadow: rgba(99,102,241,0.7) 3px 3px 5px 0px, rgba(99,102,241,0.5) 5px 5px 20px 0px;
  z-index: -2;
}
.uv-send-icon {
  width: 18px; height: 18px;
  transition: transform 0.2s ease;
  fill: none;
  stroke: white;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex-shrink: 0;
}
.uv-send-label {
  color: #e0e2f0;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.5px;
  user-select: none;
}
.uv-send-container:hover .uv-send-icon { transform: translateX(2px) translateY(-2px); }
/* Hide the JS-bridge hidden buttons */
button[kind="primary"] { display: none !important; }

.gemini-narrative { background:#0d0e14; border:1px solid #1a1c28; border-radius:16px; padding:1.5rem 1.75rem; position:relative; }
.gemini-narrative.pass { border-left:4px solid #22c55e; }
.gemini-narrative.fail { border-left:4px solid #ef4444; }
.gemini-narrative-text { font-size:13px; color:#c8cad4; font-family:'DM Sans',sans-serif; line-height:1.8; }
.gemini-narrative-text p { margin:0 0 12px 0; }
.gemini-badge { position:absolute; bottom:1rem; right:1.25rem; font-size:10px; color:#6366f1; font-family:'DM Mono',monospace; letter-spacing:1px; }

/* ── Risk Level Box (Vision Scanner) ── */
.risk-box { border-radius:14px; padding:1.5rem; text-align:center; margin-bottom:1rem; }
.risk-box.critical { background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.4); animation:risk-pulse 1.5s infinite; }
.risk-box.high     { background:rgba(251,146,60,0.12); border:1px solid rgba(251,146,60,0.35); }
.risk-box.medium   { background:rgba(251,191,36,0.10); border:1px solid rgba(251,191,36,0.3); }
.risk-box.low      { background:rgba(74,222,128,0.10); border:1px solid rgba(74,222,128,0.3); }
@keyframes risk-pulse {
    0%,100% { box-shadow:0 0 0 0 rgba(239,68,68,0.3); }
    50%      { box-shadow:0 0 16px 4px rgba(239,68,68,0.2); }
}
.risk-label { font-size:10px; letter-spacing:2px; text-transform:uppercase; color:#6b7280; font-family:'DM Mono',monospace; margin-bottom:6px; }
.risk-level { font-family:'Syne',sans-serif; font-size:32px; font-weight:800; }

/* ── Pill badges ── */
.pill-red  { display:inline-block; background:rgba(239,68,68,0.12); color:#f87171; border:1px solid rgba(239,68,68,0.3); padding:3px 10px; border-radius:50px; font-size:11px; font-family:'DM Mono',monospace; margin:3px; }
.pill-amber{ display:inline-block; background:rgba(251,191,36,0.12); color:#fbbf24; border:1px solid rgba(251,191,36,0.3); padding:3px 10px; border-radius:50px; font-size:11px; font-family:'DM Mono',monospace; margin:3px; }

/* ── Vertex AI banner ── */
.vertex-banner { background:rgba(34,197,94,0.08); border:1px solid rgba(34,197,94,0.25); border-radius:12px; padding:10px 16px; display:flex; align-items:center; gap:10px; margin-bottom:1rem; }
.vertex-banner-icon { font-size:18px; }
.vertex-banner-text { font-size:12px; color:#4ade80; font-family:'DM Mono',monospace; line-height:1.4; }
.vertex-banner-sub  { font-size:11px; color:#4b5280; font-family:'DM Sans',sans-serif; margin-top:2px; }

/* ── Uiverse Download Component ── */
.uv-dl-container { padding: 0; margin: 0; display: flex; justify-content: center; align-items: center; width: 100%; }
.uv-dl-label {
  background-color: transparent; border: 2px solid rgb(91, 91, 240); display: flex; align-items: center;
  border-radius: 50px; width: 280px; cursor: pointer; transition: all 0.4s ease; padding: 5px; position: relative;
  overflow: hidden;
}
.uv-dl-label::before {
  content: ""; position: absolute; top: 0; bottom: 0; left: 0; right: 0; background-color: #fff; width: 8px; height: 8px;
  transition: all 0.4s ease; border-radius: 100%; margin: auto; opacity: 0; visibility: hidden;
}
.uv-dl-label .uv-dl-input { display: none; }

.uv-dl-label .uv-dl-title { 
  font-size: 13.5px; font-weight: 500; font-family: 'DM Sans', sans-serif; color: #fff; 
  transition: all 0.4s ease; position: absolute; top: 50%; transform: translateY(-50%); 
  text-align: center; pointer-events: none; white-space: nowrap; margin: 0;
}
/* First text: Executive Report */
.uv-dl-label .uv-dl-circle + .uv-dl-title { left: 45px; right: 15px; }

/* Second text: Downloaded */
.uv-dl-label .uv-dl-title + .uv-dl-title { left: 0; right: 0; opacity: 0; visibility: hidden; }
.uv-dl-label .uv-dl-circle {
  height: 35px; width: 35px; border-radius: 50%; background-color: rgb(91, 91, 240); display: flex; justify-content: center; align-items: center; transition: all 0.4s ease; position: relative; box-shadow: 0 0 0 0 rgb(255, 255, 255); overflow: hidden; flex-shrink: 0;
}
.uv-dl-label .uv-dl-circle .uv-dl-icon { color: #fff; width: 20px; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); transition: all 0.4s ease; }
.uv-dl-label .uv-dl-circle .uv-dl-square { aspect-ratio: 1; width: 12px; border-radius: 2px; background-color: #fff; opacity: 0; visibility: hidden; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); transition: all 0.4s ease; }
.uv-dl-label .uv-dl-circle::before { content: ""; position: absolute; left: 0; top: 0; background-color: #3333a8; width: 100%; height: 0; transition: all 0.4s ease; }

.uv-dl-label:has(.uv-dl-input:checked) { width: 49px; animation: installed 0.4s ease 1.2s forwards; }
.uv-dl-label:has(.uv-dl-input:checked)::before { animation: uv-dl-rotate 0.8s ease-in-out 0.4s forwards; }
.uv-dl-label .uv-dl-input:checked + .uv-dl-circle { animation: uv-dl-pulse 0.8s forwards, circleDelete 0.2s ease 1.2s forwards; rotate: 180deg; }
.uv-dl-label .uv-dl-input:checked + .uv-dl-circle::before { animation: installing 0.8s ease-in-out forwards; }
.uv-dl-label .uv-dl-input:checked + .uv-dl-circle .uv-dl-icon { opacity: 0; visibility: hidden; }
.uv-dl-label .uv-dl-input:checked ~ .uv-dl-circle .uv-dl-square { opacity: 1; visibility: visible; }
.uv-dl-label .uv-dl-input:checked ~ .uv-dl-circle + .uv-dl-title { opacity: 0; visibility: hidden; }
.uv-dl-label .uv-dl-input:checked ~ .uv-dl-title + .uv-dl-title { animation: showInstalledMessage 0.4s ease 1.2s forwards; }

@keyframes uv-dl-pulse { 0% { scale: 0.95; box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.7); } 70% { scale: 1; box-shadow: 0 0 0 16px rgba(255, 255, 255, 0); } 100% { scale: 0.95; box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); } }
@keyframes installing { from { height: 0; } to { height: 100%; } }
@keyframes uv-dl-rotate { 0% { transform: rotate(-90deg) translate(20px) rotate(0); opacity: 1; visibility: visible; } 99% { transform: rotate(270deg) translate(20px) rotate(270deg); opacity: 1; visibility: visible; } 100% { opacity: 0; visibility: hidden; } }
@keyframes installed { 100% { width: 280px; border-color: rgb(35, 174, 35); } }
@keyframes circleDelete { 100% { opacity: 0; visibility: hidden; } }
@keyframes showInstalledMessage { 100% { opacity: 1; visibility: visible; } }

/* ── Uiverse Pagination Buttons ── */
.uv-nav-btn {
  width: 130px; height: 34px; display: flex; align-items: center; justify-content: flex-start;
  cursor: pointer; border: 2px solid rgb(99, 102, 241); background-color: rgb(99, 102, 241); border-radius: 6px;
  box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.137); overflow: hidden; margin: 0 auto;
}
.uv-nav-text {
  flex: 1; height: 100%; display: flex; align-items: center; justify-content: center;
  background-color: #0d0e14; color: #f0f1f5; font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 500;
}
.uv-nav-arrow { width: 14px; flex-shrink: 0; }
.uv-nav-arrow path { fill: #ffffff; }

/* "Next" specific spacing and animation */
.uv-nav-btn.next { padding-right: 12px; gap: 12px; }
.uv-nav-btn.next:hover .uv-nav-arrow { animation: uv-slide-in-left 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) both; }

/* "Previous" specific spacing and animation */
.uv-nav-btn.prev { padding-left: 12px; gap: 12px; }
.uv-nav-btn.prev .uv-nav-arrow { transform: scaleX(-1); }
.uv-nav-btn.prev:hover .uv-nav-arrow { animation: uv-slide-in-right 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) both; }

.uv-nav-btn:active { transform: scale(0.97); }

@keyframes uv-slide-in-left { 0% { transform: translateX(-8px); opacity: 0; } 100% { transform: translateX(0px); opacity: 1; } }
@keyframes uv-slide-in-right { 0% { transform: translateX(8px) scaleX(-1); opacity: 0; } 100% { transform: translateX(0px) scaleX(-1); opacity: 1; } }

/* Hide the native Streamlit trigger buttons */
div[data-testid="stButton"] > button[kind="primary"]:has(p:contains("HiddenTrigger")) { display: none !important; }


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   EquiGuard  ·  Motion & Delight Layer
   Inspired by ReactBits text-animations / animations + Barba.js
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/* ── Aurora sidebar background ─────────────────────────────────────── */
@keyframes aurora-shift {
    0%   { background-position: 0% 50%;   }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%;   }
}
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(
        160deg,
        #0d0e14 0%,
        #0f1022 30%,
        #0d1228 60%,
        #0d0e14 100%
    ) !important;
    background-size: 300% 300% !important;
    animation: aurora-shift 12s ease infinite !important;
}

/* ── Shimmer brand name text (ReactBits: TextShimmer) ──────────────── */
@keyframes text-shimmer {
    0%   { background-position: -400% center; }
    100% { background-position:  400% center; }
}
.eq-brand-name {
    background: linear-gradient(
        90deg,
        #818cf8 0%,
        #f0f1f5 30%,
        #c7d2fe 50%,
        #6366f1 70%,
        #f0f1f5 90%
    ) !important;
    background-size: 400% auto !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    animation: text-shimmer 4s linear infinite !important;
}

/* ── BlurIn page section entrance (ReactBits: BlurIn) ──────────────── */
@keyframes blur-in {
    0%   { opacity: 0; filter: blur(18px); transform: translateY(14px); }
    100% { opacity: 1; filter: blur(0px);  transform: translateY(0);    }
}
.section-card {
    animation: blur-in 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}
/* Staggered entrance — each consecutive card slightly delayed */
.section-card:nth-child(1)  { animation-delay: 0.05s; }
.section-card:nth-child(2)  { animation-delay: 0.12s; }
.section-card:nth-child(3)  { animation-delay: 0.19s; }
.section-card:nth-child(4)  { animation-delay: 0.26s; }
.section-card:nth-child(5)  { animation-delay: 0.33s; }
.section-card:nth-child(n+6){ animation-delay: 0.40s; }

/* KPI cards: slide+fade in from bottom */
@keyframes kpi-rise {
    0%   { opacity: 0; transform: translateY(20px) scale(0.97); }
    100% { opacity: 1; transform: translateY(0)    scale(1);    }
}

/* ── Matrix Background ── */
.matrix-container {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    z-index: 0; /* behind main content but above default background */
    pointer-events: none;
    overflow: hidden;
    display: flex;
    justify-content: space-around;
    opacity: 0.15;
}
.matrix-pattern {
    display: flex;
    flex-direction: row;
    justify-content: space-around;
    flex-grow: 1;
}
.matrix-column {
    width: 20px;
    font-family: 'DM Mono', monospace;
    font-size: 14px;
    color: #4ade80;
    line-height: 1.2;
    word-break: break-all;
    position: relative;
    overflow: visible;
}
.matrix-column::before {
    content: "0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1";
    position: absolute;
    top: -100%;
    left: 0;
    width: 100%;
    text-shadow: 0 0 5px rgba(74,222,128,0.8);
    animation: matrixFall 12s linear infinite;
    display: block;
}
@keyframes matrixFall {
    0% { transform: translateY(-150%); opacity: 0; }
    5% { opacity: 1; }
    80% { opacity: 1; }
    100% { transform: translateY(200vh); opacity: 0; }
}
.matrix-column:nth-child(2n)::before { animation-duration: 14s; animation-delay: -3s; }
.matrix-column:nth-child(3n)::before { animation-duration: 9s; animation-delay: -7s; }
.matrix-column:nth-child(5n)::before { animation-duration: 16s; animation-delay: -1s; }
.matrix-column:nth-child(7n)::before { animation-duration: 11s; animation-delay: -9s; }
.matrix-column:nth-child(11n)::before { animation-duration: 13s; animation-delay: -5s; }
.matrix-column:nth-child(3n) { color: #818cf8; } /* Interstitial purple bits */
.matrix-column:nth-child(3n)::before { text-shadow: 0 0 5px rgba(129,140,248,0.8); }

.kpi-card {
    animation: kpi-rise 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.kpi-card:nth-child(1) { animation-delay: 0.08s; }
.kpi-card:nth-child(2) { animation-delay: 0.16s; }
.kpi-card:nth-child(3) { animation-delay: 0.24s; }
.kpi-card:nth-child(4) { animation-delay: 0.32s; }

/* ── Glowing card hover (MagicBento Overrides) ─────────────────── */
.section-card {
    transition: border-color 0.35s ease, box-shadow 0.35s ease, transform 0.2s ease !important;
    will-change: transform;
}
.section-card:hover {
    box-shadow:
        0 4px 20px rgba(46, 24, 78, 0.4),
        0 0 30px rgba(132, 0, 255, 0.2) !important;
    transform: translateY(-2px) !important;
}
.kpi-card:hover {
    box-shadow:
        0 4px 20px rgba(46, 24, 78, 0.4),
        0 0 30px rgba(132, 0, 255, 0.2) !important;
    transform: translateY(-2px) !important;
}

/* ── Animated gradient border on active nav item ────────────────────── */
@keyframes border-spin {
    0%   { background-position: 0% 50%;   }
    100% { background-position: 200% 50%; }
}
.nav-item.active {
    background:
        linear-gradient(#0d0e14, #0d0e14) padding-box,
        linear-gradient(90deg, #6366f1, #818cf8, #a5b4fc, #6366f1) border-box !important;
    background-size: auto, 300% auto !important;
    border: 1px solid transparent !important;
    animation: border-spin 3s linear infinite !important;
}

/* ── Nav item hover: lift + glow ───────────────────────────────────── */
.nav-item {
    transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1) !important;
}
.nav-item:hover {
    background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(129,140,248,0.05)) !important;
    color: #c8cad4 !important;
    transform: translateX(4px) !important;
    box-shadow: inset 3px 0 0 #6366f1 !important;
}

/* ── Barba.js-style page wipe overlay ──────────────────────────────── */
#eq-page-wipe {
    position: fixed;
    inset: 0;
    z-index: 99998;
    pointer-events: none;
    background: linear-gradient(135deg, #6366f1, #4338ca);
    clip-path: circle(0% at 50% 50%);
    transition: clip-path 0.45s cubic-bezier(0.76, 0, 0.24, 1);
}
#eq-page-wipe.in  { clip-path: circle(150% at 50% 50%); }
#eq-page-wipe.out {
    clip-path: circle(0% at 50% 50%);
    transition: clip-path 0.4s cubic-bezier(0.76, 0, 0.24, 1) 0.05s;
}

/* ── Cursor glow (follows mouse) ────────────────────────────────────── */
#eq-cursor-glow {
    position: fixed;
    pointer-events: none;
    z-index: 9997;
    width: 320px;
    height: 320px;
    border-radius: 50%;
    background: radial-gradient(
        circle,
        rgba(99,102,241,0.06) 0%,
        rgba(99,102,241,0.02) 40%,
        transparent 70%
    );
    transform: translate(-50%, -50%);
    transition: left 0.08s linear, top 0.08s linear;
    will-change: left, top;
}

/* ── Button micro-animations ────────────────────────────────────────── */
.stButton > button {
    transition: all 0.2s cubic-bezier(0.22,1,0.36,1) !important;
    position: relative !important;
    overflow: hidden !important;
}
.stButton > button::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.05), transparent);
    opacity: 0;
    transition: opacity 0.2s;
    pointer-events: none;
}
.stButton > button:hover::after { opacity: 1 !important; }
.stButton > button:hover {
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0px) scale(0.98) !important;
}

/* ── Section title scramble placeholder ────────────────────────────── */
.section-title { cursor: default; }

/* ── Eq-header blur-in ──────────────────────────────────────────────── */
@keyframes header-in {
    0%   { opacity: 0; transform: translateY(-8px); }
    100% { opacity: 1; transform: translateY(0);    }
}
.eq-header {
    animation: header-in 0.5s cubic-bezier(0.22, 1, 0.36, 1) both !important;
}

</style>
""", unsafe_allow_html=True)

# ── Motion JS & Global Components ────────────────────────────────────────────
render_gradual_blur() # Recreates the React component exactly in Python

st.markdown("""
<div id="eq-page-wipe"></div>
<div id="eq-cursor-glow"></div>


<script>
(function() {
    /* ── 1. Cursor glow ─────────────────────────────────────────────────── */
    const glow = document.getElementById('eq-cursor-glow');
    if (glow) {
        document.addEventListener('mousemove', e => {
            glow.style.left = e.clientX + 'px';
            glow.style.top  = e.clientY + 'px';
        });
    }

    /* ── 2. Barba.js-style page wipe on nav clicks ───────────────────── */
    function pageWipe(cb) {
        const wipe = document.getElementById('eq-page-wipe');
        if (!wipe) { cb && cb(); return; }
        wipe.classList.remove('out');
        wipe.classList.add('in');
        setTimeout(() => {
            cb && cb();
            wipe.classList.remove('in');
            wipe.classList.add('out');
            setTimeout(() => wipe.classList.remove('out'), 500);
        }, 420);
    }

    /* Wire nav items to trigger the wipe then let Streamlit handle routing */
    function wireNavItems() {
        document.querySelectorAll('.nav-item[data-page]').forEach(el => {
            if (el._wired) return;
            el._wired = true;
            el.addEventListener('click', () => pageWipe());
        });
    }

    /* ── 3. Scramble text on section-title hover (ReactBits: ScrambleText) ── */
    const CHARSET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789◎◈◉⬢';
    function scramble(el) {
        const original = el.dataset.original || el.textContent.trim();
        if (!el.dataset.original) el.dataset.original = original;
        let frame = 0;
        const total = 12;
        if (el._scramTimer) clearInterval(el._scramTimer);
        el._scramTimer = setInterval(() => {
            frame++;
            const progress = frame / total;
            el.textContent = original
                .split('')
                .map((ch, i) => {
                    if (ch === ' ') return ' ';
                    if (i / original.length < progress) return ch;
                    return CHARSET[Math.floor(Math.random() * CHARSET.length)];
                })
                .join('');
            if (frame >= total) {
                clearInterval(el._scramTimer);
                el.textContent = original;
            }
        }, 40);
    }

    function wireSectionTitles() {
        document.querySelectorAll('.section-title').forEach(el => {
            if (el._scramWired) return;
            el._scramWired = true;
            el.addEventListener('mouseenter', () => scramble(el));
        });
    }

    /* ── 4. Magnetic card hover (ReactBits: Magnet) ──────────────────── */
    function wireMagneticCards() {
        document.querySelectorAll('.kpi-card').forEach(card => {
            if (card._magWired) return;
            card._magWired = true;
            card.addEventListener('mousemove', e => {
                const r  = card.getBoundingClientRect();
                const cx = r.left + r.width  / 2;
                const cy = r.top  + r.height / 2;
                const dx = (e.clientX - cx) / (r.width  / 2);
                const dy = (e.clientY - cy) / (r.height / 2);
                card.style.transform =
                    'translateY(-3px) scale(1.01) rotateX(' + (-dy * 4) + 'deg) rotateY(' + (dx * 4) + 'deg)';
            });
            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
                card.style.transition = 'transform 0.4s cubic-bezier(0.22,1,0.36,1)';
            });
        });
    }

    /* ── 5. BlurIn for dynamically added section cards ───────────────── */
    let seenCards = new WeakSet();
    function animateNewCards() {
        document.querySelectorAll('.section-card').forEach(card => {
            if (seenCards.has(card)) return;
            seenCards.add(card);
            card.style.opacity = '0';
            card.style.filter  = 'blur(16px)';
            card.style.transform = 'translateY(12px)';
            card.style.transition = 'opacity 0.55s ease, filter 0.55s ease, transform 0.55s ease';
            requestAnimationFrame(() => requestAnimationFrame(() => {
                card.style.opacity   = '1';
                card.style.filter    = 'blur(0)';
                card.style.transform = 'translateY(0)';
            }));
        });
    }

    /* ── Run all wiringon DOM mutations (Streamlit re-renders) ───────── */
    function runAll() {
        wireNavItems();
        wireSectionTitles();
        wireMagneticCards();
        animateNewCards();
    }

    const observer = new MutationObserver(() => runAll());
    observer.observe(document.body, { childList: true, subtree: true });
    runAll();

    /* Trigger page-wipe on Streamlit internal navigation signals */
    window.addEventListener('message', e => {
        if (e.data && e.data.type === 'streamlit:render') {
            pageWipe();
        }
    });
})();
</script>
""", unsafe_allow_html=True)


# ── Hero landing page (shown once per session) ─────────────────────────────────
if not st.session_state.get("hero_dismissed", False):
    from frontend.hero import render_hero
    render_hero()
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:

    st.markdown("""
    <div style="padding: 1.2rem 1.2rem 0.5rem; border-bottom: 1px solid #1a1c28; margin-bottom: 0.5rem;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:36px;height:36px;display:flex;align-items:center;justify-content:center;">
                <svg width="36" height="36" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                  <path d="M100 20 L30 50 L30 110 C30 160 100 190 100 190 C100 190 170 160 170 110 L170 50 Z" fill="#0A2540" />
                  <path d="M100 35 L45 60 L45 105 C45 145 100 170 100 170 C100 170 155 145 155 105 L155 60 Z" fill="none" stroke="#20C997" stroke-width="6" />
                  <rect x="96" y="60" width="8" height="70" fill="#20C997" />
                  <circle cx="100" cy="60" r="8" fill="#20C997" />
                  <rect x="60" y="76" width="80" height="6" fill="#20C997" rx="3" />
                  <polygon points="64,82 44,115 84,115" fill="none" stroke="#20C997" stroke-width="4" stroke-linejoin="round" />
                  <path d="M44 115 Q64 130 84 115 Z" fill="#20C997" />
                  <polygon points="136,82 116,115 156,115" fill="none" stroke="#20C997" stroke-width="4" stroke-linejoin="round" />
                  <path d="M116 115 Q136 130 156 115 Z" fill="#20C997" />
                  <rect x="75" y="130" width="50" height="8" fill="#20C997" rx="4" />
                </svg>
            </div>
            <div>
                <div class="eq-brand-name" style="font-size:18px; line-height: 1.2;">EquiGuard</div>
                <div style="font-size:9px;color:#6366f1;letter-spacing:2px;text-transform:uppercase;font-family:'DM Mono',monospace;margin-top:2px;">AI Bias Firewall</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="nav-section-label">Navigation</div>', unsafe_allow_html=True)

    pages = [
        ("Dashboard",         "◈",  "Overview & compliance status"),
        ("Audit Engine",      "⬡",  "Run bias audits"),
        ("Bias Leaderboard",  "◉",  "Historical drift tracking"),
        ("Model Comparison",  "⧡",  "Pareto accuracy vs fairness"),
        ("Vision Scanner",    "◎",  "Image bias scanner"),
        ("Intersectional",    "⬢",  "Multi-attribute bias heatmap"),
    ]

    for page, icon, _ in pages:
        is_active = st.session_state.active_page == page
        cls = "nav-item active" if is_active else "nav-item"
        if st.sidebar.button(f"{icon}  {page}", key=f"nav_{page}", width="stretch"):
            st.session_state.active_page = page
            st.rerun()

    st.markdown('<div class="nav-section-label" style="margin-top:1rem;">System</div>', unsafe_allow_html=True)

    # Live backend health probe
    _backend_online = False
    try:
        from frontend.utils import api_get as _api_get
        _health_resp = _api_get("/health")
        _backend_online = _health_resp.status_code == 200
    except Exception:
        _backend_online = False
    st.session_state.backend_status = _backend_online

    _be_color  = "#4ade80" if _backend_online else "#f87171"
    _be_label  = "● Online" if _backend_online else "● Offline"

    # Webhook status
    _wh_enabled = os.getenv("WEBHOOK_ENABLED", "false").lower() == "true"
    _wh_color   = "#4ade80" if _wh_enabled else "#3a3d52"
    _wh_label   = "● Active" if _wh_enabled else "● Disabled"

    st.markdown(f"""
    <div style="padding: 0 8px;">
        <div style="background:#0a0b10;border:1px solid #1a1c28;border-radius:12px;padding:12px 14px;margin-top:4px;">
            <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">System Status</div>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:12px;color:#6b7280;">Backend API</span>
                <span style="font-size:11px;color:{_be_color};font-family:'DM Mono',monospace;">{_be_label}</span>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:12px;color:#6b7280;">EEOC Engine</span>
                <span style="font-size:11px;color:#4ade80;font-family:'DM Mono',monospace;">● Active</span>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                <span style="font-size:12px;color:#6b7280;">SHAP Explainer</span>
                <span style="font-size:11px;color:#4ade80;font-family:'DM Mono',monospace;">● Ready</span>
            </div>
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <span style="font-size:12px;color:#6b7280;">Alerting</span>
                <span style="font-size:11px;color:{_wh_color};font-family:'DM Mono',monospace;">{_wh_label}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _audit_pass = True
    if st.session_state.get("audit_result"):
        _audit_pass = st.session_state.audit_result.get("compliance_pass", True)

    _footer_text = "v1.0.0 · EEOC Compliant" if _audit_pass else "v1.0.0 · EEOC Non-Compliant"
    _footer_color = "#3a3d52" if _audit_pass else "#f87171"

    st.markdown(f"""
    <div style="padding: 0.75rem 1.2rem; margin-top: 0.75rem; border-top: 1px solid #1a1c28;">
        <div style="font-size:11px;color:{_footer_color};font-family:'DM Mono',monospace;">{_footer_text}</div>
    </div>
    """, unsafe_allow_html=True)
    # ── Global MagicBento Tracker ──
    st.iframe("""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
        <script>
            const parentDoc = window.parent.document;
            let spotlight = parentDoc.getElementById('global-spotlight');
            if (!spotlight) {
                spotlight = parentDoc.createElement('div');
                spotlight.id = 'global-spotlight';
                spotlight.style.cssText = `
                    mix-blend-mode: screen; will-change: transform, opacity; z-index: 9999;
                    pointer-events: none; position: fixed; width: 600px; height: 600px;
                    border-radius: 50%; opacity: 0; transform: translate(-50%, -50%);
                    background: radial-gradient(circle, rgba(132,0,255, 0.15) 0%, rgba(132,0,255, 0.08) 15%, rgba(132,0,255, 0.04) 25%, rgba(132,0,255, 0.02) 40%, rgba(132,0,255, 0.01) 65%, transparent 70%);
                `;
                parentDoc.body.appendChild(spotlight);
            }

            const RADIUS = 300, GLOW_COLOR = '132, 0, 255', PARTICLE_COUNT = 8;
            
            function initTracker() {
                if (typeof gsap === 'undefined' || !parentDoc) {
                    setTimeout(initTracker, 50); return;
                }
                
                parentDoc.body.addEventListener('mousemove', (e) => {
                    const cards = parentDoc.querySelectorAll('.section-card, .kpi-card');
                    const proximity = RADIUS * 0.5, fadeDistance = RADIUS * 0.75;
                    let minDistance = Infinity;

                    cards.forEach(card => {
                        const rect = card.getBoundingClientRect();
                        const cx = rect.left + rect.width / 2, cy = rect.top + rect.height / 2;
                        const dist = Math.hypot(e.clientX - cx, e.clientY - cy) - Math.max(rect.width, rect.height) / 2;
                        const effDist = Math.max(0, dist);
                        minDistance = Math.min(minDistance, effDist);

                        let intensity = 0;
                        if (effDist <= proximity) intensity = 1;
                        else if (effDist <= fadeDistance) intensity = (fadeDistance - effDist) / (fadeDistance - proximity);

                        card.style.setProperty('--glow-x', `${((e.clientX - rect.left) / rect.width) * 100}%`);
                        card.style.setProperty('--glow-y', `${((e.clientY - rect.top) / rect.height) * 100}%`);
                        card.style.setProperty('--glow-intensity', intensity);
                        
                        // Attach hover/tilt natively exactly once
                        if (!card.dataset.bentoInit) {
                            card.dataset.bentoInit = "true";
                            card.addEventListener('mousemove', (ce) => {
                                const cRect = card.getBoundingClientRect();
                                const x = ce.clientX - cRect.left, y = ce.clientY - cRect.top;
                                const tcx = cRect.width / 2, tcy = cRect.height / 2;
                                gsap.to(card, {
                                    rotateX: ((y - tcy) / tcy) * -2, rotateY: ((x - tcx) / tcx) * 2,
                                    duration: 0.1, ease: 'power2.out', transformPerspective: 1000
                                });
                            });
                            card.addEventListener('mouseleave', () => {
                                gsap.to(card, { rotateX: 0, rotateY: 0, duration: 0.5, ease: 'power2.out' });
                                if (card._particles) {
                                    card._particles.forEach(p => gsap.to(p, { scale: 0, opacity: 0, duration: 0.3, onComplete: () => p.remove() }));
                                    card._particles = null;
                                }
                            });
                            card.addEventListener('mouseenter', () => {
                                if (card._particles) return;
                                card._particles = [];
                                for (let i = 0; i < PARTICLE_COUNT; i++) {
                                    setTimeout(() => {
                                        if (!card.matches(':hover')) return;
                                        const p = parentDoc.createElement('div');
                                        p.style.cssText = `
                                            position: absolute; width: 3px; height: 3px; border-radius: 50%;
                                            background: rgba(${GLOW_COLOR}, 1); box-shadow: 0 0 6px rgba(${GLOW_COLOR}, 0.6);
                                            pointer-events: none; z-index: 100; left: ${Math.random() * card.offsetWidth}px; top: ${Math.random() * card.offsetHeight}px;
                                        `;
                                        card.appendChild(p); card._particles.push(p);
                                        gsap.fromTo(p, {scale:0, opacity:0}, {scale:1, opacity:1, duration:0.3, ease:'back.out(1.7)'});
                                        gsap.to(p, { x: (Math.random() - 0.5)*100, y: (Math.random() - 0.5)*100, rotation: Math.random()*360, duration: 2 + Math.random()*2, ease: 'none', repeat: -1, yoyo: true });
                                        gsap.to(p, { opacity: 0.3, duration: 1.5, ease: 'power2.inOut', repeat: -1, yoyo: true });
                                    }, i * 150);
                                }
                            });
                        }
                    });

                    gsap.to(spotlight, { left: e.clientX, top: e.clientY, duration: 0.1, ease: 'power2.out' });
                    const targetOpacity = minDistance <= proximity ? 0.8 : (minDistance <= fadeDistance ? ((fadeDistance - minDistance) / (fadeDistance - proximity)) * 0.8 : 0);
                    gsap.to(spotlight, { opacity: targetOpacity, duration: targetOpacity > 0 ? 0.2 : 0.5, ease: 'power2.out' });
                });

                parentDoc.body.addEventListener('mouseleave', () => {
                    gsap.to(spotlight, { opacity: 0, duration: 0.3 });
                    parentDoc.querySelectorAll('.section-card, .kpi-card').forEach(c => c.style.setProperty('--glow-intensity', '0'));
                });
            }
            initTracker();
        </script>
    """, height=1)



# ── Routing ────────────────────────────────────────────────────────────────────
from frontend.views.dashboard import render_dashboard
from frontend.views.audit_engine import render_audit_engine
from frontend.views.bias_leaderboard import render_bias_leaderboard
from frontend.views.vision_scanner import render_vision_scanner
from frontend.views.intersectional import render_intersectional
from frontend.views.comparison import render_comparison

if st.session_state.active_page == "Dashboard":
    render_dashboard()
elif st.session_state.active_page == "Audit Engine":
    render_audit_engine()
elif st.session_state.active_page == "Bias Leaderboard":
    render_bias_leaderboard()
elif st.session_state.active_page == "Model Comparison":
    render_comparison()
elif st.session_state.active_page == "Vision Scanner":
    render_vision_scanner()
elif st.session_state.active_page == "Intersectional":
    render_intersectional()
elif st.session_state.active_page == "Vision Scanner":
    render_vision_scanner()
elif st.session_state.active_page == "Intersectional":
    render_intersectional()
