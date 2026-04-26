import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from frontend.utils import api_get, api_post, get_kpi_values, suggest_columns
from frontend.components import render_fairness_gauge, render_shap_waterfall, render_bias_drift, render_uiverse_download
import json


def render_audit_engine():
    # Matrix animated background
    matrix_html = '<div class="matrix-container">' + ''.join(
        '<div class="matrix-pattern">' + ''.join('<div class="matrix-column"></div>' for _ in range(40)) + '</div>'
        for _ in range(5)
    ) + '</div>'
    st.markdown(matrix_html, unsafe_allow_html=True)

    # PAGE: AUDIT ENGINE
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
    
        if st.session_state.get("data_path") == "data/uploaded_data.csv" and os.path.exists("data/uploaded_data.csv"):
            fname = st.session_state.get("uploaded_file_name", "data/uploaded_data.csv")
            st.markdown(f"""
            <div class="info-chip">✓ {fname} (Persisted)</div>
            """, unsafe_allow_html=True)

            columns = st.session_state.get("uploaded_file_cols", [])
            if not columns:
                df = pd.read_csv("data/uploaded_data.csv", nrows=0, sep=None, engine='python')
                columns = df.columns.tolist()
                st.session_state.uploaded_file_cols = columns

            # ── ✨ Gemini Auto-detect button (hidden if no API key) ────────────
            _gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
            if _gemini_key:
                if st.button("✨  Auto-detect columns", key="btn_autodetect"):
                    with st.spinner("Asking Gemini to identify columns…"):
                        try:
                            _df_sample = pd.read_csv("data/uploaded_data.csv", sep=None, engine="python", nrows=100)
                            _suggestion = suggest_columns(_df_sample)
                            if _suggestion["target_col"] in columns:
                                st.session_state.target_col = _suggestion["target_col"]
                            if _suggestion["protected_col"] in columns:
                                st.session_state.protected_col = _suggestion["protected_col"]
                            st.session_state["_suggest_target_reason"]    = _suggestion.get("target_reason", "")
                            st.session_state["_suggest_protected_reason"] = _suggestion.get("protected_reason", "")
                            st.rerun()
                        except Exception as _ae:
                            st.warning(f"Auto-detect failed: {_ae}")

            current_target = st.session_state.get("target_col", columns[0])
            if current_target not in columns: current_target = columns[0]
            current_protected = st.session_state.get("protected_col", columns[0])
            if current_protected not in columns: current_protected = columns[0]

            st.session_state.target_col = st.selectbox("Target Column", columns, index=columns.index(current_target), key="target_sel")

            # Show Gemini reasoning chip below the target selectbox
            _tr = st.session_state.get("_suggest_target_reason", "")
            if _tr:
                st.markdown(f'<div class="info-chip" style="margin-top:4px;margin-bottom:6px;">✦ {_tr}</div>', unsafe_allow_html=True)

            st.session_state.protected_col = st.selectbox("Protected Attribute", columns, index=columns.index(current_protected), key="protected_sel")

            # Show Gemini reasoning chip below the protected selectbox
            _pr = st.session_state.get("_suggest_protected_reason", "")
            if _pr:
                st.markdown(f'<div class="info-chip" style="margin-top:4px;margin-bottom:6px;">✦ {_pr}</div>', unsafe_allow_html=True)

            st.markdown("<div style='margin-top:6px;'>", unsafe_allow_html=True)
            if st.button("✕  Remove Uploaded File", key="btn_remove_file"):
                st.session_state.data_path = "data/golden_demo_dataset.csv"
                st.session_state.target_col = "loan_approved"
                st.session_state.protected_col = "race"
                st.session_state.pop("_suggest_target_reason", None)
                st.session_state.pop("_suggest_protected_reason", None)
                if os.path.exists("data/uploaded_data.csv"):
                    os.remove("data/uploaded_data.csv")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            # Style the Remove button red via JS — the only reliable approach.
            # Uses window.parent.document (same-origin) to find and style the button.
            components.html("""
            <script>
            (function applyDangerStyle() {
                try {
                    var parentDoc = window.parent.document;
                    // Streamlit re-renders components, which can wipe inline styles.
                    // We run an interval to continually ensure the style is applied.
                    setInterval(function() {
                        var btns = parentDoc.querySelectorAll('button');
                        btns.forEach(function(btn) {
                            var txt = btn.innerText || btn.textContent || '';
                            if (txt.indexOf('Remove Uploaded File') !== -1) {
                                // Only attach if not already attached
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
                } catch(e) { /* cross-origin guard */ }
            })();
            </script>
            """, height=0)

        else:
            st.markdown("""
            <style>
            .uiverse-container-audit {
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
            .uiverse-folder-audit {
                position: absolute;
                top: -20px;
                left: calc(50% - 60px);
                animation: float 2.5s infinite ease-in-out;
                transition: transform var(--transition) ease;
            }
            .uiverse-container-audit.is-hovered .uiverse-folder-audit { transform: scale(1.05); }

            .uiverse-folder-audit .front-side, .uiverse-folder-audit .back-side {
                position: absolute;
                transition: transform var(--transition);
                transform-origin: bottom center;
            }
            .uiverse-folder-audit .back-side::before, .uiverse-folder-audit .back-side::after {
                content: ""; display: block; background-color: white; opacity: 0.5;
                z-index: 0; width: var(--folder-W); height: var(--folder-H);
                position: absolute; transform-origin: bottom center;
                border-radius: 15px; transition: transform 350ms; z-index: 0;
            }
            .uiverse-container-audit.is-hovered .back-side::before { transform: rotateX(-5deg) skewX(5deg); }
            .uiverse-container-audit.is-hovered .back-side::after { transform: rotateX(-15deg) skewX(12deg); }

            .uiverse-folder-audit .front-side { z-index: 1; }
            .uiverse-container-audit.is-hovered .front-side { transform: rotateX(-40deg) skewX(15deg); }

            .uiverse-folder-audit .tip {
                background: linear-gradient(135deg, #ff9a56, #ff6f56);
                width: 80px; height: 20px; border-radius: 12px 12px 0 0;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
                position: absolute; top: -10px; z-index: 2;
            }
            .uiverse-folder-audit .cover {
                background: linear-gradient(135deg, #ffe563, #ffc663);
                width: var(--folder-W); height: var(--folder-H);
                box-shadow: 0 15px 30px rgba(0, 0, 0, 0.3);
                border-radius: 10px;
            }
            .uiverse-custom-file-upload-audit {
                font-size: 1.1em; color: #ffffff; text-align: center;
                background: rgba(255, 255, 255, 0.2); border: none;
                border-radius: 10px; box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
                display: inline-block; width: 100%; padding: 10px 35px;
                position: relative; transition: background var(--transition) ease;
            }
            .uiverse-container-audit.is-hovered .uiverse-custom-file-upload-audit { background: rgba(255, 255, 255, 0.4); }

            /* OVERLAY STREAMLIT UPLOADER - Removed global absolute positioning */
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

            <div class="uploader-wrapper-audit" id="uploader-wrap-audit">
                <div class="uiverse-container-audit" id="uiverse-ui-audit">
                    <div class="uiverse-folder-audit">
                        <div class="front-side"><div class="tip"></div><div class="cover"></div></div>
                        <div class="back-side cover"></div>
                    </div>
                    <div class="uiverse-custom-file-upload-audit">Drop dataset (CSV) here or click</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            uploaded_file = st.file_uploader("Upload Dataset (CSV)", type=["csv"], label_visibility="collapsed")

            components.html("""
                <script>
                    const parentDoc = window.parent.document;
                    function init() {
                        const wrapper = parentDoc.getElementById('uploader-wrap-audit');
                        const ui = parentDoc.getElementById('uiverse-ui-audit');
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
            """, height=0)
            
            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file, sep=None, engine='python')
                df.to_csv("data/uploaded_data.csv", index=False)
                st.session_state.data_path = "data/uploaded_data.csv"
                st.session_state.uploaded_file_name = uploaded_file.name
                columns = df.columns.tolist()
                st.session_state.uploaded_file_cols = columns
                st.session_state.target_col = columns[0]
                st.session_state.protected_col = columns[0]
                st.rerun()
            else:
                st.markdown("""
                <div class="info-chip">◌ Using default: data/golden_demo_dataset.csv</div>
                """, unsafe_allow_html=True)
                st.session_state.data_path = "data/golden_demo_dataset.csv"
                st.session_state.uploaded_file_name = "golden_demo_dataset.csv"
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
            "file_name": st.session_state.get("uploaded_file_name", "golden_demo_dataset.csv"),
            "target_col": st.session_state.target_col,
            "protected_col": st.session_state.protected_col
        }

        # ── Pre-flight Dataset Check
        if st.button("⚡  Pre-flight Dataset Check", key="btn_preflight", width="stretch"):
            with st.spinner("Running Gemini pre-flight analysis…"):
                try:
                    _pf_resp = api_post("/audit/preflight", {"data_path": st.session_state.data_path})
                    if _pf_resp.status_code == 200:
                        st.session_state.preflight_result = _pf_resp.json()
                        st.rerun()
                    else:
                        st.error(f"Pre-flight failed: {_pf_resp.status_code}")
                except Exception as _pfe:
                    st.error(f"Cannot reach backend: {_pfe}")

        # ── Show pre-flight result if available
        _pf = st.session_state.preflight_result
        if _pf:
            _risk = _pf.get("overall_risk", "UNKNOWN")
            _risk_colors = {"CRITICAL": "#ef4444", "HIGH": "#fb923c", "MEDIUM": "#fbbf24", "LOW": "#4ade80"}
            _risk_color = _risk_colors.get(_risk, "#6b7280")
            _hr_cols = _pf.get("high_risk_columns", [])
            _px_cols = _pf.get("proxy_candidates", [])
            _engine  = _pf.get("engine", "heuristic")
            _engine_badge = "✦ Gemini" if "gemini" in _engine else "◌ Heuristic"

            # Build HTML string cleanly — avoids blank-line / code-block parser bugs
            _hr_section = ""
            if _hr_cols:
                _hr_pills = "".join(f'<span class="pill-red">{c}</span>' for c in _hr_cols)
                _hr_section = (
                    '<div style="margin-bottom:6px;">'
                    '<span style="font-size:10px;color:#f87171;font-family:\'DM Mono\',monospace;letter-spacing:1px;">HIGH-RISK COLUMNS</span>'
                    f"<br>{_hr_pills}</div>"
                )

            _px_section = ""
            if _px_cols:
                _px_pills = "".join(f'<span class="pill-amber">{c}</span>' for c in _px_cols)
                _px_section = (
                    '<div style="margin-bottom:6px;">'
                    '<span style="font-size:10px;color:#fbbf24;font-family:\'DM Mono\',monospace;letter-spacing:1px;">PROXY CANDIDATES</span>'
                    f"<br>{_px_pills}</div>"
                )

            _summary_text = _pf.get("summary", "")
            _pf_html = (
                '<div style="background:#0a0b10;border:1px solid #1a1c28;border-radius:12px;padding:12px 14px;margin-bottom:1rem;">'
                '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
                '<div style="font-size:10px;color:#3a3d52;font-family:\'DM Mono\',monospace;letter-spacing:1px;text-transform:uppercase;">Pre-flight Risk</div>'
                f'<div style="font-size:13px;font-weight:700;color:{_risk_color};font-family:\'Syne\',sans-serif;">{_risk}</div>'
                f'<div style="font-size:10px;color:#3a3d52;font-family:\'DM Mono\',monospace;margin-left:auto;">{_engine_badge}</div>'
                "</div>"
                + _hr_section
                + _px_section
                + f'<div style="font-size:12px;color:#6b7280;line-height:1.5;margin-top:6px;">{_summary_text}</div>'
                "</div>"
            )
            st.markdown(_pf_html, unsafe_allow_html=True)

        st.markdown('<div style="border-top:1px solid #1a1c28;margin:10px 0;"></div>', unsafe_allow_html=True)


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
    
        _has_proxies = bool(st.session_state.flagged_columns)
        _mitigate_help = (
            "Run ⬡ Pre-Processing Audit above first to detect proxy variables."
            if not _has_proxies
            else f"Will remove: {', '.join(st.session_state.flagged_columns)}"
        )

        # Show what will be dropped (only when proxies are detected)
        if _has_proxies:
            _proxy_pills = "".join(
                f'<span class="pill-red">{c}</span>'
                for c in st.session_state.flagged_columns
            )
            st.markdown(
                f'<div style="margin-bottom:6px;"><span style="font-size:10px;color:#f87171;'
                f'font-family:\'DM Mono\',monospace;letter-spacing:1px;">WILL REMOVE</span>'
                f'<br>{_proxy_pills}</div>',
                unsafe_allow_html=True,
            )

        if st.button(
            "⟳  Apply Mitigation & Retrain",
            key="btn_mitigate",
            disabled=not _has_proxies,
            help=_mitigate_help,
        ):
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
                        try:
                            _detail = response.json().get("detail", response.text[:200])
                        except Exception:
                            _detail = response.text[:200]
                        st.error(f"Mitigation failed ({response.status_code}): {_detail}")
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
                render_uiverse_download(
                    file_bytes=st.session_state.report_bytes,
                    file_name="EquiGuard_Executive_Report.pdf",
                    mime_type="application/pdf",
                    label="Executive Report",
                    completed_label="Downloaded"
                )
            else:
                st.button("↓  Export Executive Report (PDF)", disabled=True,
                          width="stretch", key="dl_report_disabled")
    
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
                    render_uiverse_download(
                        file_bytes=st.session_state.cert_bytes,
                        file_name="EquiGuard_EEOC_Certificate.pdf",
                        mime_type="application/pdf",
                        label="Compliance Cert",
                        completed_label="Downloaded"
                    )
                else:
                    st.button("⬡  Download EEOC Compliance Certificate",
                              disabled=True, width="stretch", key="dl_cert_disabled")
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
                    render_uiverse_download(
                        file_bytes=st.session_state.pkg_bytes,
                        file_name="EquiGuard_Regulatory_Package.zip",
                        mime_type="application/zip",
                        label="Regulatory ZIP",
                        completed_label="Downloaded"
                    )
                else:
                    st.button("↓  Download Regulatory Package (ZIP)", disabled=True,
                              width="stretch", key="dl_pkg_disabled")
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
                      help="Run a compliance audit first.", width="stretch",
                      key="dl_report_none")
            st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
            st.button("⬡  Download EEOC Compliance Certificate", disabled=True,
                      help="Run a compliance audit first.", width="stretch",
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
        "data_path": st.session_state.get("data_path", "data/golden_demo_dataset.csv"),
        "target_col": st.session_state.get("target_col", "loan_approved"),
        "protected_col": st.session_state.get("protected_col", "race"),
    }
    
    if st.button("⬡  Simulate Mitigation Options", key="btn_simulate", width="stretch"):
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
    
    
    # ── Gemini Remediation Agent ────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-title">◈ Gemini Remediation Agent</div>
    <div style="font-size:11px;color:#3a3d52;font-family:'DM Mono',monospace;margin-bottom:1rem;margin-top:-0.8rem;">
        Powered by Google Gemini · AI-generated mitigation strategies
    </div>
    """, unsafe_allow_html=True)
    
    # Gemini badge
    st.markdown("""
    <div class="vertex-banner">
        <div class="vertex-banner-icon">✨</div>
        <div>
            <div class="vertex-banner-text">Powered by Google Gemini AI</div>
            <div class="vertex-banner-sub">Generates three production-ready bias mitigation strategies for your model.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    _rem_disabled = st.session_state.audit_result is None
    _rem_btn_lbl  = "◈  Generate Mitigation Code" if not st.session_state.mitigation_code else "↺  Regenerate Mitigation Code"
    
    if st.button(_rem_btn_lbl, key="btn_remediate", disabled=_rem_disabled):
        with st.spinner("Gemini generating remediation strategies..."):
            try:
                _rem_payload = {
                    "top_biased_feature": st.session_state.audit_result.get("top_biased_feature", ""),
                    "flagged_columns":    st.session_state.flagged_columns,
                    "fairness_ratio":     st.session_state.audit_result.get("fairness_ratio", 0.0),
                    "data_path":          st.session_state.get("data_path", "data/golden_demo_dataset.csv"),
                    "target_col":         st.session_state.get("target_col", "loan_approved"),
                    "protected_col":      st.session_state.get("protected_col", "race"),
                }
                _rem_resp = api_post("/audit/remediate", _rem_payload)
                if _rem_resp.status_code == 200:
                    _rem_data = _rem_resp.json()
                    st.session_state.mitigation_code  = _rem_data.get("mitigation_code", "")
                    st.session_state.mitigation_model = _rem_data.get("model", "template")
                    st.session_state.mitigation_note  = _rem_data.get("note", "")
                    st.rerun()
                else:
                    st.error(f"Remediation failed: {_rem_resp.status_code}")
            except Exception as _re:
                st.error(f"Could not reach backend: {_re}")
    
    if _rem_disabled:
        st.markdown("""
        <div style="font-size:12px;color:#3a3d52;font-family:'DM Mono',monospace;padding:0.5rem 0;">
            Run a compliance audit first to enable remediation code generation.
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.mitigation_code:
        _rem_model = getattr(st.session_state, "mitigation_model", "template")
        _rem_note  = getattr(st.session_state, "mitigation_note", "")
        _model_color = "#4ade80" if "gemini" in _rem_model else "#fbbf24"
        # Show warning banner if Gemini fell back to template due to an error
        if _rem_model == "template" and ("\u26a0" in _rem_note or "rate limit" in _rem_note.lower() or "error" in _rem_note.lower()):
            st.markdown(f"""
            <div style="background:#1a1208;border:1px solid #854d0e;border-radius:8px;padding:10px 14px;margin-bottom:0.75rem;display:flex;align-items:flex-start;gap:10px;">
                <span style="font-size:16px;">⚠️</span>
                <div>
                    <div style="font-size:12px;font-weight:600;color:#fbbf24;font-family:'DM Mono',monospace;margin-bottom:2px;">Gemini Unavailable</div>
                    <div style="font-size:11px;color:#a16207;font-family:'DM Sans',sans-serif;">{_rem_note}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="margin:1rem 0 0.5rem;display:flex;align-items:center;gap:10px;">
                <span style="font-size:11px;color:{_model_color};font-family:'DM Mono',monospace;">&#9689; {_rem_model}</span>
                <span style="font-size:11px;color:#3a3d52;font-family:'DM Sans',monospace;">{_rem_note}</span>
            </div>
            """, unsafe_allow_html=True)
        st.code(st.session_state.mitigation_code, language="python")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    
    # ══════════════════════════════════════════════════════════════════════════════
