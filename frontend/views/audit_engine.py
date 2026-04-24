import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from frontend.utils import api_get, api_post, get_kpi_values, suggest_columns
from frontend.components import render_fairness_gauge, render_shap_waterfall, render_bias_drift
import json


def render_audit_engine():
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
                                        'background: rgba(153,27,27,0.22) !important',
                                        'border: 1px solid rgba(239,68,68,0.6) !important',
                                        'color: #f87171 !important',
                                        'transition: background 0.2s, border-color 0.2s, color 0.2s'
                                    ].join(';');
                                    btn.addEventListener('mouseenter', function() {
                                        this.style.background = 'rgba(220,38,38,0.35)';
                                        this.style.borderColor = 'rgba(248,113,113,0.85)';
                                        this.style.color = '#fca5a5';
                                    });
                                    btn.addEventListener('mouseleave', function() {
                                        this.style.background = 'rgba(153,27,27,0.22)';
                                        this.style.borderColor = 'rgba(239,68,68,0.6)';
                                        this.style.color = '#f87171';
                                    });
                                }
                            }
                        });
                    }, 200);
                } catch(e) { /* cross-origin guard */ }
            })();
            </script>
            """, height=0)

        else:
            uploaded_file = st.file_uploader("Upload Dataset (CSV)", type=["csv"], label_visibility="collapsed")
            
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
                st.download_button(
                    label="↓  Export Executive Report (PDF)",
                    data=st.session_state.report_bytes,
                    file_name="EquiGuard_Executive_Report.pdf",
                    mime="application/pdf",
                    width="stretch",
                    key="dl_report",
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
                    st.download_button(
                        label="⬡  Download EEOC Compliance Certificate",
                        data=st.session_state.cert_bytes,
                        file_name="EquiGuard_EEOC_Certificate.pdf",
                        mime="application/pdf",
                        width="stretch",
                        help="One-page compliance certificate — issue to auditors or executives.",
                        key="dl_cert",
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
                    st.download_button(
                        label="↓  Download Regulatory Package (ZIP)",
                        data=st.session_state.pkg_bytes,
                        file_name="EquiGuard_Regulatory_Package.zip",
                        mime="application/zip",
                        width="stretch",
                        help="Full package: executive PDF, certificate, methodology, raw JSON.",
                        key="dl_pkg",
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
    
    
    # ── Vertex AI Remediation Agent ────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("""
    <div class="section-title">◈ Vertex AI Remediation Agent</div>
    <div style="font-size:11px;color:#3a3d52;font-family:'DM Mono',monospace;margin-bottom:1rem;margin-top:-0.8rem;">
        Enterprise-grade · Zero data retention · Powered by Google Vertex AI
    </div>
    """, unsafe_allow_html=True)
    
    # Zero-retention badge
    st.markdown("""
    <div class="vertex-banner">
        <div class="vertex-banner-icon">🔒</div>
        <div>
            <div class="vertex-banner-text">Zero Data Retention — Powered by Google Vertex AI</div>
            <div class="vertex-banner-sub">Your audit data is processed in an enterprise VPC and never used to train base models.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    _rem_disabled = st.session_state.audit_result is None
    _rem_btn_lbl  = "◈  Generate Mitigation Code" if not st.session_state.mitigation_code else "↺  Regenerate Mitigation Code"
    
    if st.button(_rem_btn_lbl, key="btn_remediate", disabled=_rem_disabled):
        with st.spinner("Vertex AI generating remediation strategies..."):
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
        _model_color = "#4ade80" if "vertex" in _rem_model else "#fbbf24"
        st.markdown(f"""
        <div style="margin:1rem 0 0.5rem;display:flex;align-items:center;gap:10px;">
            <span style="font-size:11px;color:{_model_color};font-family:'DM Mono',monospace;">
                ◉ {_rem_model}
            </span>
            <span style="font-size:11px;color:#3a3d52;font-family:'DM Sans',monospace;">{_rem_note}</span>
        </div>
        """, unsafe_allow_html=True)
        st.code(st.session_state.mitigation_code, language="python")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    
    # ══════════════════════════════════════════════════════════════════════════════
