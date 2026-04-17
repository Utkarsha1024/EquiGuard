import streamlit as st

# 1. Enforce Page Config
st.set_page_config(page_title="EquiGuard", layout="wide", initial_sidebar_state="collapsed")

# 2. Inject Custom CSS for Material You styling
st.markdown("""
    <style>
    /* Dark Mode Background */
    .stApp {
        background-color: #121212;
        color: #e0e0e0;
    }
    
    /* Pill-shaped Buttons */
    .stButton > button {
        border-radius: 24px;
        background-color: #2c2c2c;
        color: #ffffff;
        border: 1px solid #444444;
        padding: 10px 24px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #3d3d3d;
        border-color: #888888;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }
    
    /* Pill-shaped Compliance Badges */
    .badge-pass {
        background-color: #1b3a20;
        color: #81c784;
        padding: 8px 20px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;
        display: inline-block;
        margin: 4px 0px;
    }
    .badge-fail {
        background-color: #4a1a1a;
        color: #e57373;
        padding: 8px 20px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;
        display: inline-block;
        margin: 4px 0px;
    }
    
    /* Rounded Container Cards */
    div[data-testid="stVerticalBlock"] div[style*="flex-direction: column"] {
        background-color: #1e1e1e;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# 3. Build the UI Layout
st.title("EquiGuard Bias Firewall")
st.markdown("Intercept and audit automated decisions before deployment.")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Compliance Status")
    # Mocking the traffic light system for now
    st.markdown('<div class="badge-pass">US EEOC: Pass</div>', unsafe_allow_html=True)
    st.markdown('<div class="badge-fail">EU AI ACT: Warning</div>', unsafe_allow_html=True)

with col2:
    st.markdown("### Control Panel")
    st.button("Upload Dataset (CSV)")
    st.button("Run Pre-Processing Audit")
    st.button("Export CEO Report")
