import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from frontend.utils import api_get, api_post, get_kpi_values
from frontend.components import render_fairness_gauge, render_shap_waterfall, render_bias_drift
import json


def render_dashboard():
    # Header
    st.markdown("""
    <div class="eq-header">
        <div class="eq-brand">
            <div class="eq-logo" style="background:transparent;box-shadow:none;">
                <svg width="40" height="40" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
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

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card {ratio_color}">
            <div class="kpi-label" style="margin-bottom:8px;">Fairness Ratio</div>
            <div class="kpi-value {ratio_color}">{ratio_val}</div>
            <div class="kpi-sub" style="margin-top:8px;">EEOC threshold ≥ 0.80</div>
        </div>
        <div class="kpi-card {status_color}">
            <div class="kpi-label" style="margin-bottom:8px;">Compliance Status</div>
            <div class="kpi-value {status_color}">{status_val}</div>
            <div class="kpi-sub" style="margin-top:8px;">US EEOC 4/5ths Rule</div>
        </div>
        <div class="kpi-card indigo">
            <div class="kpi-label" style="margin-bottom:8px;">Top Bias Driver</div>
            <div class="kpi-value indigo" style="font-size:18px;">{feature_val}</div>
            <div class="kpi-sub" style="margin-top:8px;">Highest SHAP impact</div>
        </div>
        <div class="kpi-card amber">
            <div class="kpi-label" style="margin-bottom:8px;">Audit Engine</div>
            <div class="kpi-value amber" style="font-size:18px;">aif360 + SHAP</div>
            <div class="kpi-sub" style="margin-top:8px;">IBM Fairness 360 active</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


    # ── Additional aif360 metrics (shown when available)
    _res = st.session_state.audit_result
    if _res:
        _eod = _res.get("equal_opportunity_diff")
        _aod = _res.get("avg_odds_diff")
        if _eod is not None or _aod is not None:
            _chips = ""
            if _eod is not None:
                _eod_color = "#4ade80" if abs(_eod) <= 0.1 else "#f87171"
                _chips += f'<span class="info-chip" style="color:{_eod_color};">◌ Equal Opportunity Diff: {_eod:.4f}</span>'
            if _aod is not None:
                _aod_color = "#4ade80" if abs(_aod) <= 0.1 else "#f87171"
                _chips += f'<span class="info-chip" style="color:{_aod_color};margin-left:8px;">◌ Avg Odds Diff: {_aod:.4f}</span>'
            st.markdown(f'<div style="margin-bottom:1.5rem;display:flex;flex-wrap:wrap;gap:8px;">{_chips}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">⬡ Fairness Gauge</div>', unsafe_allow_html=True)
        fairness_ratio = 0.0
        if st.session_state.audit_result:
            fairness_ratio = st.session_state.audit_result.get('fairness_ratio', 0.0)
        st.plotly_chart(render_fairness_gauge(fairness_ratio), width="stretch")
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
                    st.plotly_chart(fig_shap, width="stretch")
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
                st.markdown('<div style="display:flex;align-items:center;justify-content:center;height:180px;"><div style="font-size:12px;color:#3a3d52;font-family:\'DM Mono\',monospace;">SHAP data unavailable.</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="display:flex;align-items:center;justify-content:center;height:220px;"><div style="font-size:13px;color:#3a3d52;text-align:center;font-family:\'DM Mono\',monospace;">No audit data yet.<br>Run an audit from the Audit Engine.</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Legal Risk Narrative (template-based)
    if st.session_state.audit_result:
        _r  = st.session_state.audit_result
        _cp = _r.get("compliance_pass", False)
        _fr = _r.get("fairness_ratio", 0.0)
        _ga = _r.get("group_a_rate", 0.0)
        _gb = _r.get("group_b_rate", 0.0)
        _tf = _r.get("top_biased_feature", "N/A")
        _px = st.session_state.flagged_columns
        _cls   = "pass" if _cp else "fail"
        _verb  = "passes" if _cp else "fails"
        _tcolor = "#4ade80" if _cp else "#f87171"
        _legal = ("This model would likely survive disparate impact scrutiny under 29 CFR § 1607." if _cp
                  else "This disparity constitutes potential adverse impact under 29 CFR § 1607 and may not survive regulatory scrutiny.")
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
                <span class="nh">{_tf}</span>.{_proxy_sent}</p>
                <p style="margin-top:12px;padding:10px 14px;background:rgba({'34,197,94' if _cp else '239,68,68'},0.07);border-radius:8px;border-left:3px solid {'#22c55e' if _cp else '#ef4444'};">
                {_legal}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Bias Drift Chart
    st.markdown('<div class="section-card" style="margin-top:0;">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">◉ Bias Drift Over Time</div>', unsafe_allow_html=True)
    try:
        history_response = api_get("/audit/history")
        if history_response.status_code == 200:
            history_data = history_response.json().get("history", [])
            if history_data:
                fig_drift = render_bias_drift(history_data)
                if fig_drift:
                    st.plotly_chart(fig_drift, width="stretch")
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
                st.markdown('<div style="display:flex;align-items:center;justify-content:center;height:160px;"><div style="font-size:12px;color:#3a3d52;font-family:\'DM Mono\',monospace;text-align:center;">No audit history yet.<br>Run a compliance audit to see drift.</div></div>', unsafe_allow_html=True)
        else:
            st.error("Could not fetch audit history from backend.")
    except Exception:
        st.markdown('<div style="padding:1rem;background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.15);border-radius:10px;font-size:13px;color:#f87171;font-family:\'DM Mono\',monospace;">Backend unreachable — start the FastAPI server to see live drift data.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Gemini Legal Risk Narrative
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">⚖ Gemini Legal Risk Narrative</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#3a3d52;font-family:\'DM Mono\',monospace;margin-bottom:1rem;margin-top:-0.8rem;">Generated by Google Gemini 2.5 Flash · Legal analysis for compliance teams</div>', unsafe_allow_html=True)
    if st.session_state.audit_result is None:
        st.markdown('<div style="text-align:center;padding:1.5rem;font-size:13px;color:#3a3d52;font-family:\'DM Mono\',monospace;">Run a compliance audit first to generate a legal risk narrative.</div>', unsafe_allow_html=True)
    else:
        _narr_result  = st.session_state.audit_result
        _narr_cp      = _narr_result.get("compliance_pass", False)
        _narr_cls     = "pass" if _narr_cp else "fail"
        _narr_btn_lbl = "↺  Regenerate" if st.session_state.narrative else "⚖  Generate Narrative"
        if st.button(_narr_btn_lbl, key="btn_narrative"):
            with st.spinner("Consulting Gemini 2.5 Flash..."):
                try:
                    _narr_payload = _narr_result.copy()
                    _narr_payload["flagged_proxies"] = st.session_state.flagged_columns
                    _narr_resp = api_post("/audit/narrative", _narr_payload)
                    if _narr_resp.status_code == 200:
                        _narr_data = _narr_resp.json()
                        st.session_state.narrative = _narr_data.get("narrative", "")
                        st.session_state.narrative_model = _narr_data.get("model", "template")
                        st.rerun()
                    else:
                        st.error(f"Narrative generation failed: {_narr_resp.status_code}")
                except Exception as _ne:
                    st.error(f"Could not reach backend: {_ne}")
        if st.session_state.narrative:
            _narr_model = getattr(st.session_state, "narrative_model", "template")
            _narr_badge = ("✦ Powered by Google Gemini 2.5 Flash" if _narr_model != "template"
                           else "✦ Template narrative (set GEMINI_API_KEY to enable AI)")
            _narr_paras = [p.strip() for p in st.session_state.narrative.split("\n") if p.strip()]
            _narr_html  = "".join(f"<p>{p}</p>" for p in _narr_paras)
            st.markdown(f'<div class="gemini-narrative {_narr_cls}"><div class="gemini-narrative-text">{_narr_html}</div><div class="gemini-badge">{_narr_badge}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Conversational Audit Agent
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🤖 EquiGuard Audit Agent</div>', unsafe_allow_html=True)
    _gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not _gemini_key:
        st.markdown('<div class="info-chip">◌ Set <span style="color:#f0f1f5;">GEMINI_API_KEY</span> in your .env to activate the Audit Agent.</div>', unsafe_allow_html=True)
    elif st.session_state.audit_result is None:
        st.markdown('<div style="text-align:center;padding:2rem;font-size:13px;color:#3a3d52;font-family:\'DM Mono\',monospace;">Run a compliance audit first — the agent reads your live audit results.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:12px;color:#4b5280;font-family:\'DM Mono\',monospace;margin-bottom:1rem;">Ask anything about this audit in plain English.</div>', unsafe_allow_html=True)
        for _msg in st.session_state.chat_history:
            with st.chat_message(_msg["role"]):
                st.markdown(_msg["content"])
        
        if "agent_input_key" not in st.session_state:
            st.session_state.agent_input_key = 0
            
        # Inline input — avoids st.chat_input which is always fixed to the bottom viewport
        _col_input, _col_send = st.columns([5, 1])
        with _col_input:
            _user_input = st.text_input(
                "Ask the agent",
                placeholder="e.g. Why did we fail the EEOC check?",
                key=f"agent_input_{st.session_state.agent_input_key}",
                label_visibility="collapsed"
            )
        with _col_send:
            # Custom Uiverse send button (pill with paper-plane icon)
            st.markdown("""
            <div class="uv-send-wrap">
              <div class="uv-send-container" id="uv-send-btn">
                <div class="uv-send-inner">
                  <span class="uv-send-label">Send</span>
                  <svg class="uv-send-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M22 2L11 13"/>
                    <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
                  </svg>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            # Hide the real button visually; it's triggered by JS
            st.markdown('<style>#uv-agent-send-hidden { display:none !important; }</style>', unsafe_allow_html=True)
            _send_clicked = st.button("HiddenSend", type="primary", key="agent_send")

        # JS bridge — forwards click on custom button to the hidden Streamlit button
        st.iframe("""
        <script>
        (function() {
          try {
            var doc = window.parent.document;
            var btn = doc.getElementById('uv-send-btn');
            if (btn && !btn.dataset.attached) {
              btn.addEventListener('click', function() {
                var triggers = Array.from(doc.querySelectorAll('button[kind="primary"]'));
                var target = triggers.find(function(b) { return b.innerText.includes('HiddenSend'); });
                if (target) target.click();
              });
              btn.dataset.attached = 'true';
            }
          } catch(e) {}
        })();
        </script>
        """, height=1)
        
        if _send_clicked and _user_input.strip():
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
                            "You are the EquiGuard Audit Agent — an AI expert in EEOC compliance and algorithmic bias detection.\n\n"
                            f"Live audit results:\n{json.dumps(_res, indent=2)}\n\n"
                            f"Flagged proxy variables: {_prox if _prox else 'None detected'}\n\n"
                            "CRITICAL INSTRUCTIONS:\n"
                            "1. Act as a helpful, conversational chatbot.\n"
                            "2. ONLY answer the user's specific question. Do NOT proactively dump a summary of the entire audit unless explicitly asked to 'summarize'.\n"
                            "3. If the user simply greets you (e.g., 'hello', 'hi'), just greet them back and ask how you can help them interpret the current audit results.\n"
                            "4. When answering questions about the data, be concise, cite specific numbers from the JSON above, and never fabricate values. Explain things simply for a business executive."
                        )
                        _gemini_hist = []
                        for _m in st.session_state.chat_history[:-1]:
                            _role = "model" if _m["role"] == "assistant" else "user"
                            _gemini_hist.append(_gtypes.Content(role=_role, parts=[_gtypes.Part(text=_m["content"])]))
                        _reply = None
                        _agent_models = ["gemini-3.0-flash", "gemini-2.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]
                        for _am in _agent_models:
                            try:
                                _chat_session = _client.chats.create(
                                    model=_am,
                                    config=_gtypes.GenerateContentConfig(system_instruction=_sys),
                                    history=_gemini_hist,
                                )
                                _reply = _chat_session.send_message(_user_input).text
                                break
                            except Exception as _me:
                                _ms = str(_me)
                                if any(c in _ms for c in ("429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND", "503", "UNAVAILABLE")):
                                    continue
                                raise
                        if _reply is None:
                            raise Exception("All Gemini models exhausted quota. Please enable billing at console.cloud.google.com/billing")
                        st.markdown(_reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": _reply})
                        st.session_state.agent_input_key += 1
                        st.rerun()
                    except Exception as _e:
                        _err = f"Agent error: {_e}"
                        st.error(_err)
                        st.session_state.chat_history.append({"role": "assistant", "content": _err})
                        st.session_state.agent_input_key += 1
                        st.rerun()
        if st.session_state.chat_history:
            if st.button("✕  Clear conversation", key="btn_clear_chat"):
                st.session_state.chat_history = []
                st.session_state.agent_input_key += 1
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
