import streamlit as st
import requests
import plotly.graph_objects as go

if "audit_result" not in st.session_state:
    st.session_state.audit_result = None
if "flagged_columns" not in st.session_state:
    st.session_state.flagged_columns = []

# 1. Enforce Page Config
st.set_page_config(page_title="EquiGuard", layout="wide", initial_sidebar_state="collapsed")

# 2. Inject Custom CSS for Material You styling
st.markdown("""
    <style>
    /* Dark Mode Background */
    .stApp {
        background-color: #0f0f11;
        color: #e0e0e0;
    }
    
    /* Pill-shaped Buttons */
    .stButton > button {
        border-radius: 50px !important;
        background: linear-gradient(135deg, #2c2c2e 0%, #1c1c1e 100%) !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.6) !important;
        border-color: #666 !important;
        background: linear-gradient(135deg, #3c3c3e 0%, #2c2c2e 100%) !important;
    }
    
    /* Pill-shaped Compliance Badges */
    .badge-pass {
        background: linear-gradient(135deg, #1b3a20 0%, #122b16 100%);
        color: #81c784;
        padding: 8px 24px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 15px;
        display: inline-block;
        margin: 4px 0px;
        box-shadow: 0 4px 12px rgba(27, 58, 32, 0.4);
        border: 1px solid #2e5a35;
    }
    .badge-fail {
        background: linear-gradient(135deg, #4a1a1a 0%, #301010 100%);
        color: #e57373;
        padding: 8px 24px;
        border-radius: 50px;
        font-weight: 700;
        font-size: 15px;
        display: inline-block;
        margin: 4px 0px;
        box-shadow: 0 4px 12px rgba(74, 26, 26, 0.4);
        border: 1px solid #6b2626;
    }
    
    /* Heavy Rounded Container Cards & Metrics */
    div[data-testid="stMetric"], div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] {
        background-color: #18181a;
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 12px 32px rgba(0,0,0,0.5);
        border: 1px solid #2a2a2c;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Helper for Gauge Chart
def render_fairness_gauge(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Fairness Ratio", 'font': {'color': 'white', 'size': 20}},
        number={'font': {'color': 'white'}},
        gauge={
            'axis': {'range': [0.0, 1.0], 'tickcolor': "white"},
            'bar': {'color': "rgba(255, 255, 255, 0.8)", 'thickness': 0.3},
            'bgcolor': "rgba(0,0,0,0)",
            'steps': [
                {'range': [0.0, 0.79], 'color': "#e57373"},
                {'range': [0.8, 1.0], 'color': "#81c784"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white"},
        margin=dict(l=20, r=20, t=50, b=20),
        height=300
    )
    return fig

# 4. Build the UI Layout
st.title("EquiGuard Bias Firewall")
st.markdown("Intercept and audit automated decisions before deployment.")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Compliance Status")
    
    # True Traffic Light Badges
    if st.session_state.audit_result is None:
        st.markdown('<div class="badge-pass" style="background-color: #333333; color: #aaaaaa;">US EEOC: Pending Audit</div>', unsafe_allow_html=True)
        fairness_ratio = 0.0
        top_feature = "N/A"
    else:
        res = st.session_state.audit_result
        fairness_ratio = res.get('fairness_ratio', 0.0)
        top_feature = res.get("top_biased_feature", "N/A")
        
        if res.get("compliance_pass"):
            st.markdown('<div class="badge-pass">US EEOC: Pass</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="badge-fail">US EEOC: Fail</div>', unsafe_allow_html=True)
            
    # Dynamic Plotly Gauge
    st.plotly_chart(render_fairness_gauge(fairness_ratio), use_container_width=True)
    
    if st.session_state.audit_result is not None:
        st.metric("Top Biased Feature", top_feature)

with col2:
    st.markdown("### Control Panel")
    uploaded_file = st.file_uploader("Upload Dataset (CSV)")
    
    if uploaded_file is not None:
        import pandas as pd
        
        # Auto-detect delimiter and read the file
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        
        # Normalize and save locally as a standard CSV
        df.to_csv("uploaded_data.csv", index=False)
        
        st.session_state.data_path = "uploaded_data.csv"
        
        columns = df.columns.tolist()
        
        st.session_state.target_col = st.selectbox("Select Target Column", columns)
        st.session_state.protected_col = st.selectbox("Select Protected Column", columns)
    else:
        st.info("Using default: golden_demo_dataset.csv")
        st.session_state.data_path = "golden_demo_dataset.csv"
        st.session_state.target_col = "loan_approved"
        st.session_state.protected_col = "race"
        
    api_payload = {
        "data_path": st.session_state.data_path,
        "target_col": st.session_state.target_col,
        "protected_col": st.session_state.protected_col
    }
    
    if st.button("Run Pre-Processing Audit"):
        with st.spinner("Hunting for Proxy Variables..."):
            try:
                response = requests.post("http://127.0.0.1:8000/audit/preprocess", json=api_payload)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("proxies_detected"):
                        flagged_cols = data.get("flagged_columns", [])
                        st.session_state.flagged_columns = flagged_cols
                        cols_str = ", ".join(flagged_cols)
                        st.warning(f"⚠️ **Proxy Variables Detected!** The following columns strongly correlate with protected attributes and should be removed or decorrelated: {cols_str}")
                    else:
                        st.session_state.flagged_columns = []
                        st.success("✅ No hidden proxies detected.")
                else:
                    try:
                        err = response.json().get('detail', f"Error {response.status_code}")
                    except:
                        err = f"Error {response.status_code}"
                    st.error(f"Audit failed: {err}")
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")
                
    if st.button("Run Full Compliance Audit"):
        with st.spinner("Running Audit..."):
            try:
                response = requests.post("http://127.0.0.1:8000/audit/compliance", json=api_payload)
                if response.status_code == 200:
                    st.session_state.audit_result = response.json()
                    st.rerun()
                else:
                    try:
                        err = response.json().get('detail', f"Error {response.status_code}")
                    except:
                        err = f"Error {response.status_code}"
                    st.error(f"Audit failed: {err}")
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")
                
    if st.button("Apply Mitigation (Drop Proxies)"):
        with st.spinner('Retraining Model...'):
            try:
                mitigation_payload = api_payload.copy()
                mitigation_payload["flagged_columns"] = st.session_state.flagged_columns
                response = requests.post("http://127.0.0.1:8000/audit/mitigate", json=mitigation_payload)
                if response.status_code == 200:
                    st.session_state.audit_result = response.json()
                    st.rerun()
                else:
                    try:
                        err = response.json().get('detail', f"Error {response.status_code}")
                    except:
                        err = f"Error {response.status_code}"
                    st.error(f"Mitigation failed: {err}")
            except Exception as e:
                st.error(f"Error connecting to backend: {e}")
                
    if st.session_state.audit_result:
        try:
            export_payload = st.session_state.audit_result.copy()
            export_payload["flagged_proxies"] = st.session_state.flagged_columns
            
            pdf_response = requests.post("http://127.0.0.1:8000/audit/export", json=export_payload)
            if pdf_response.status_code == 200:
                st.download_button(
                    label="Export CEO Report",
                    data=pdf_response.content,
                    file_name="EquiGuard_Executive_Report.pdf",
                    mime="application/pdf"
                )
            else:
                try:
                    err = pdf_response.json().get('detail', "Report generation failed.")
                except:
                    err = "Report generation failed."
                st.error(err)
                st.button("Export CEO Report", disabled=True)
        except Exception as e:
            st.error("Backend unreachable.")
            st.button("Export CEO Report", disabled=True)
    else:
        st.button("Export CEO Report", disabled=True, help="Run an audit first.")

# 4. Bias Leaderboard
st.markdown("---")
with st.container():
    st.markdown("### Bias Leaderboard")
    try:
        history_response = requests.get("http://127.0.0.1:8000/audit/history")
        if history_response.status_code == 200:
            history_data = history_response.json().get("history", [])
            if history_data:
                import pandas as pd
                df_history = pd.DataFrame(history_data)
                df_history["timestamp"] = pd.to_datetime(df_history["timestamp"])
                df_history.set_index("timestamp", inplace=True)
                
                # Plot fairness ratio over time
                import plotly.express as px
                max_y = max(1.05, df_history['fairness_ratio'].max() * 1.1)
                
                fig = px.line(
                    df_history, 
                    y="fairness_ratio", 
                    markers=True,
                    title="Temporal Bias Drift"
                )
                
                # Style for dark mode
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)", 
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="white",
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                
                # Dynamic Y-axis
                fig.update_yaxes(
                    range=[0, max_y],
                    gridcolor="#333",
                    zerolinecolor="#555"
                )
                fig.update_xaxes(gridcolor="#333")
                
                # Add EEOC 0.8 Threshold Line
                fig.add_hline(y=0.8, line_dash="dash", line_color="#e57373", annotation_text="EEOC Minimum (0.8)")
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No audit history available yet. Run a compliance audit to see the leaderboard.")
        else:
            st.error("Failed to fetch audit history.")
    except Exception as e:
        st.error(f"Could not connect to backend to fetch audit history: {e}")
