import os
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from frontend.utils import api_get, api_post, get_kpi_values, API_BASE, API_HEADERS
from frontend.components import render_fairness_gauge, render_shap_waterfall, render_bias_drift
import json


def render_vision_scanner():
    # PAGE: VISION SCANNER
    st.markdown("""
    <div class="eq-header">
        <div>
            <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#f0f1f5;">◎ Visual Bias Scanner</div>
            <div style="font-size:12px;color:#4b5280;font-family:'DM Mono',monospace;margin-top:2px;">
                Powered by Gemini 1.5 Flash Multimodal AI · Detects demographic data leaks in images
            </div>
        </div>
        <div class="eq-status-dot">Gemini Vision Active</div>
    </div>
    """, unsafe_allow_html=True)

    vis_col1, vis_col2 = st.columns([1, 1], gap="large")

    with vis_col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">◎ Image Upload</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-chip">◌ Upload an image to scan for demographic data leakage (faces, ID cards, demographic text)</div>
        """, unsafe_allow_html=True)

        if "vision_image" not in st.session_state:
            st.session_state.vision_image = None
        if "vision_image_name" not in st.session_state:
            st.session_state.vision_image_name = None
        if "vision_image_type" not in st.session_state:
            st.session_state.vision_image_type = None

        if st.session_state.vision_image is None:
            # Uiverse UI and logic
            st.markdown("""
            <style>
            .uiverse-container {
                --transition: 350ms;
                --folder-W: 120px;
                --folder-H: 80px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: flex-end;
                padding: 10px;
                background: linear-gradient(135deg, #6dd5ed, #2193b0);
                border-radius: 15px;
                box-shadow: 0 15px 30px rgba(0, 0, 0, 0.2);
                height: calc(var(--folder-H) * 1.7);
                position: relative;
                width: 100%;
                margin-top: 1rem;
            }
            .uiverse-folder {
                position: absolute;
                top: -20px;
                left: calc(50% - 60px);
                animation: float 2.5s infinite ease-in-out;
                transition: transform var(--transition) ease;
            }
            .uiverse-container.is-hovered .uiverse-folder { transform: scale(1.05); }

            .uiverse-folder .front-side, .uiverse-folder .back-side {
                position: absolute;
                transition: transform var(--transition);
                transform-origin: bottom center;
            }
            .uiverse-folder .back-side::before, .uiverse-folder .back-side::after {
                content: ""; display: block; background-color: white; opacity: 0.5;
                z-index: 0; width: var(--folder-W); height: var(--folder-H);
                position: absolute; transform-origin: bottom center;
                border-radius: 15px; transition: transform 350ms; z-index: 0;
            }
            .uiverse-container.is-hovered .back-side::before { transform: rotateX(-5deg) skewX(5deg); }
            .uiverse-container.is-hovered .back-side::after { transform: rotateX(-15deg) skewX(12deg); }

            .uiverse-folder .front-side { z-index: 1; }
            .uiverse-container.is-hovered .front-side { transform: rotateX(-40deg) skewX(15deg); }

            .uiverse-folder .tip {
                background: linear-gradient(135deg, #ff9a56, #ff6f56);
                width: 80px; height: 20px; border-radius: 12px 12px 0 0;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                position: absolute; top: -10px; z-index: 2;
            }
            .uiverse-folder .cover {
                background: linear-gradient(135deg, #ffe563, #ffc663);
                width: var(--folder-W); height: var(--folder-H);
                box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
                border-radius: 10px;
            }
            .uiverse-custom-file-upload {
                font-size: 1.1em; color: #ffffff; text-align: center;
                background: rgba(255, 255, 255, 0.2); border: none;
                border-radius: 10px; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
                display: inline-block; width: 100%; padding: 10px 35px;
                position: relative; transition: background var(--transition) ease;
            }
            .uiverse-container.is-hovered .uiverse-custom-file-upload { background: rgba(255, 255, 255, 0.4); }

            @keyframes float {
                0% { transform: translateY(0px); }
                50% { transform: translateY(-20px); }
                100% { transform: translateY(0px); }
            }

            /* OVERLAY STREAMLIT UPLOADER - Removed global absolute positioning to prevent bugs */
            [data-testid="stFileUploader"] {
                opacity: 0.01 !important;
                height: 100% !important;
                cursor: pointer;
            }
            [data-testid="stFileUploader"] section {
                height: 100% !important;
                padding: 0 !important;
            }
            </style>

            <div class="uploader-wrapper" id="uploader-wrap">
                <div class="uiverse-container" id="uiverse-ui">
                    <div class="uiverse-folder">
                        <div class="front-side"><div class="tip"></div><div class="cover"></div></div>
                        <div class="back-side cover"></div>
                    </div>
                    <div class="uiverse-custom-file-upload">Drop image here or click</div>
                </div>
            </div>
            <div style="font-size:12px;color:#818cf8;margin-top:8px;text-align:center;font-family:'Syne',sans-serif;">PDF, JPG, PNG, JPEG</div>
            """, unsafe_allow_html=True)

            _vis_file = st.file_uploader(
                "Upload image or PDF", type=["pdf", "jpg", "png", "jpeg"],
                label_visibility="collapsed", key="vision_uploader"
            )

            # Sync hover state from invisible uploader to the Uiverse UI and overlay perfectly via negative margin
            st.iframe("""
                <script>
                    const parentDoc = window.parent.document;
                    function init() {
                        const wrapper = parentDoc.getElementById('uploader-wrap');
                        const ui = parentDoc.getElementById('uiverse-ui');
                        const uploader = parentDoc.querySelector('[data-testid="stFileUploader"]');
                        
                        if (wrapper && ui && uploader) {
                            const uploaderParent = uploader.parentElement;
                            
                            // Perfect overlay via CSS negative margin instead of DOM reparenting
                            const wrapperHeight = wrapper.offsetHeight;
                            uploaderParent.style.marginTop = "-" + wrapperHeight + "px";
                            uploaderParent.style.height = wrapperHeight + "px";
                            uploaderParent.style.position = "relative";
                            uploaderParent.style.zIndex = "100";
                            
                            uploader.addEventListener('mouseenter', () => ui.classList.add('is-hovered'));
                            uploader.addEventListener('mouseleave', () => ui.classList.remove('is-hovered'));
                        } else {
                            setTimeout(init, 50);
                        }
                    }
                    init();
                </script>
            """, height=1)

            if _vis_file is not None:
                st.session_state.vision_image = _vis_file.getvalue()
                st.session_state.vision_image_name = _vis_file.name
                st.session_state.vision_image_type = _vis_file.type
                st.rerun()

        if st.session_state.vision_image is not None:
            if st.session_state.vision_image_type == "application/pdf":
                st.markdown(f"""
                <div style="padding:1rem;background:#12141f;border:1px solid #1e2030;border-radius:12px;margin-bottom:1rem;display:flex;align-items:center;gap:12px;">
                    <span style="font-size:24px;">📄</span>
                    <div style="font-size:14px;color:#f0f1f5;font-family:'Syne',sans-serif;">{st.session_state.vision_image_name}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.image(st.session_state.vision_image, use_container_width=True)

            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                if st.button("◎  Scan for Bias Risk", key="btn_vision_scan", use_container_width=True):
                    with st.spinner("Scanning with Gemini Vision..."):
                        try:
                            _vis_files   = {"file": (st.session_state.vision_image_name, st.session_state.vision_image, st.session_state.vision_image_type)}
                            _vis_headers = {"X-API-Key": os.getenv("EQUIGUARD_API_KEY", "")}
                            _vis_resp    = requests.post(
                                f"{API_BASE}/audit/vision",
                                files=_vis_files,
                                headers=_vis_headers,
                            )
                            if _vis_resp.status_code == 200:
                                st.session_state.vision_result = _vis_resp.json()
                                st.rerun()
                            else:
                                st.error(f"Vision scan failed: {_vis_resp.status_code} — {_vis_resp.text[:200]}")
                        except Exception as _ve:
                            st.error(f"Could not reach backend: {_ve}")
            
            with btn_col2:
                if st.button("✕ Remove Image", key="btn_vision_remove", use_container_width=True):
                    st.session_state.vision_image = None
                    st.session_state.vision_image_name = None
                    st.session_state.vision_image_type = None
                    st.session_state.vision_result = None
                    st.rerun()
                
                st.iframe("""
                <script>
                (function applyDangerStyle() {
                    try {
                        var parentDoc = window.parent.document;
                        setInterval(function() {
                            var btns = parentDoc.querySelectorAll('button');
                            btns.forEach(function(btn) {
                                var txt = btn.innerText || btn.textContent || '';
                                if (txt.indexOf('Remove Image') !== -1) {
                                    if (btn.getAttribute('data-eq-styled') !== 'true') {
                                        btn.setAttribute('data-eq-styled', 'true');
                                        btn.style.cssText = [
                                            'background: rgba(220,38,38,0.35) !important',
                                            'border: 1px solid rgba(248,113,113,0.85) !important',
                                            'color: #fca5a5 !important'
                                        ].join(';');
                                    }
                                }
                            });
                        }, 200);
                    } catch(e) { }
                })();
                </script>
                """, height=1)
        else:
            st.markdown("""
            <div style="height:200px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px;">
                <div style="font-size:48px;opacity:0.08;">◎</div>
                <div style="font-size:12px;color:#3a3d52;font-family:'DM Mono',monospace;text-align:center;">
                    Upload an image to begin scanning
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:1.5rem;padding:1rem;background:#0a0b10;border:1px solid #1a1c28;border-radius:12px;">
            <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;">Why this matters</div>
            <div style="font-size:12px;color:#4b5280;line-height:1.6;">
                Resume scanners, KYC systems, and hiring tools that process photos risk encoding demographic bias.
                EquiGuard detects this <em>before</em> deployment using Gemini 1.5 Flash Multimodal AI — scanning for faces,
                sensitive labels, and demographic text.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with vis_col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">◉ Scan Results</div>', unsafe_allow_html=True)

        _vr = st.session_state.vision_result

        if _vr is None:
            st.markdown("""
            <div style="height:300px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:12px;">
                <div style="font-size:48px;opacity:0.08;">◉</div>
                <div style="font-size:12px;color:#3a3d52;font-family:'DM Mono',monospace;text-align:center;">
                    Upload and scan an image to see results here.
                </div>
            </div>
            """, unsafe_allow_html=True)

        elif _vr.get("risk_level") == "UNKNOWN":
            st.markdown(f"""
            <div style="padding:1rem;background:rgba(107,114,128,0.08);border:1px solid rgba(107,114,128,0.2);
            border-radius:12px;font-size:13px;color:#6b7280;font-family:'DM Mono',monospace;">
                ◌ Gemini Vision not configured — {_vr.get('error', 'Check GEMINI_API_KEY')}
            </div>
            """, unsafe_allow_html=True)

        else:
            _rl    = _vr.get("risk_level", "LOW")
            _rs    = _vr.get("risk_score", 0)
            _faces = _vr.get("faces_detected", 0)
            _lbls  = _vr.get("flagged_labels", [])
            _txt   = _vr.get("flagged_text", [])
            _rec   = _vr.get("recommendation", "")
            _warn  = _vr.get("compliance_warning", "")

            _rl_colors = {
                "CRITICAL": ("#ef4444", "critical"),
                "HIGH":     ("#fb923c", "high"),
                "MEDIUM":   ("#fbbf24", "medium"),
                "LOW":      ("#4ade80", "low"),
            }
            _rl_color, _rl_css = _rl_colors.get(_rl, ("#6b7280", "low"))

            st.markdown(f"""
            <div class="risk-box {_rl_css}">
                <div class="risk-label">Risk Level</div>
                <div class="risk-level" style="color:{_rl_color};">{_rl}</div>
                <div style="font-size:12px;color:#6b7280;font-family:'DM Mono',monospace;margin-top:4px;">
                    Score: {_rs}/100
                </div>
            </div>
            """, unsafe_allow_html=True)

            _gauge_score = _rs / 100.0
            _gauge_color = "#ef4444" if _rs >= 70 else ("#fb923c" if _rs >= 40 else ("#fbbf24" if _rs >= 20 else "#4ade80"))
            _risk_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=_rs,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Risk Score", 'font': {'color': '#6b7280', 'size': 13, 'family': 'DM Mono'}},
                number={'font': {'color': _gauge_color, 'size': 36, 'family': 'Syne'}, 'suffix': '/100'},
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': "#2a2d40", 'tickfont': {'color': '#3a3d52', 'size': 10}},
                    'bar': {'color': _gauge_color, 'thickness': 0.25},
                    'bgcolor': "rgba(0,0,0,0)", 'borderwidth': 0,
                    'steps': [
                        {'range': [0, 20],  'color': "rgba(74,222,128,0.08)"},
                        {'range': [20, 40], 'color': "rgba(251,191,36,0.08)"},
                        {'range': [40, 70], 'color': "rgba(251,146,60,0.08)"},
                        {'range': [70, 100],'color': "rgba(239,68,68,0.08)"},
                    ],
                    'threshold': {'line': {'color': "#6366f1", 'width': 2}, 'thickness': 0.75, 'value': 70}
                }
            ))
            _risk_fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font={'color': "white", 'family': 'DM Sans'},
                margin=dict(l=20, r=20, t=40, b=10), height=200
            )
            st.plotly_chart(_risk_fig, width="stretch")

            st.markdown(f"""
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:1rem;">
                <div style="background:#12141f;border:1px solid #1e2030;border-radius:10px;padding:10px;text-align:center;">
                    <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1px;margin-bottom:4px;">FACES</div>
                    <div style="font-size:20px;font-weight:700;font-family:'Syne',sans-serif;color:{'#f87171' if _faces > 0 else '#4ade80'};">{_faces}</div>
                </div>
                <div style="background:#12141f;border:1px solid #1e2030;border-radius:10px;padding:10px;text-align:center;">
                    <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1px;margin-bottom:4px;">LABELS</div>
                    <div style="font-size:20px;font-weight:700;font-family:'Syne',sans-serif;color:{'#f87171' if _lbls else '#4ade80'};">{len(_lbls)}</div>
                </div>
                <div style="background:#12141f;border:1px solid #1e2030;border-radius:10px;padding:10px;text-align:center;">
                    <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1px;margin-bottom:4px;">DEMO TEXT</div>
                    <div style="font-size:20px;font-weight:700;font-family:'Syne',sans-serif;color:{'#f87171' if _txt else '#4ade80'};">{len(_txt)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if _lbls or _txt:
                _pills_html = "".join(f'<span class="pill-red">{l}</span>' for l in _lbls)
                _pills_html += "".join(f'<span class="pill-amber">{t}</span>' for t in _txt)
                st.markdown(f"""
                <div style="margin-bottom:1rem;">
                    <div style="font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:6px;">Flagged Items</div>
                    <div>{_pills_html}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="background:#0a0b10;border:1px solid #1a1c28;border-left:3px solid #fbbf24;border-radius:10px;padding:10px 14px;margin-bottom:1rem;">
                <div style="font-size:10px;color:#fbbf24;font-family:'DM Mono',monospace;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;">Recommendation</div>
                <div style="font-size:12px;color:#c8cad4;">{_rec}</div>
            </div>
            """, unsafe_allow_html=True)

            if _rl in ("HIGH", "CRITICAL"):
                st.markdown(f"""
                <div style="background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.2);border-radius:10px;padding:10px 14px;">
                    <div style="font-size:12px;color:#f87171;font-weight:500;margin-bottom:4px;">⚠ GDPR Article 9 & EEOC Risk</div>
                    <div style="font-size:12px;color:#c8cad4;">{_warn}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
