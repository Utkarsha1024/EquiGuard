import os
import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from frontend.utils import api_get, api_post, get_kpi_values
from frontend.components import render_fairness_gauge, render_shap_waterfall, render_bias_drift
import json


def render_intersectional():
    # PAGE: INTERSECTIONAL
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
        "data_path": st.session_state.get("data_path", "data/golden_demo_dataset.csv"),
        "target_col": st.session_state.get("target_col", "loan_approved"),
    }

    if st.button("⬢  Run Intersectional Audit", key="btn_ix", width="stretch"):
        with st.spinner("Scanning all protected attributes…"):
            try:
                ix_resp = api_post("/audit/intersectional", ix_payload)
                if ix_resp.status_code == 200:
                    st.session_state.intersectional_result = ix_resp.json()
                    st.session_state.ix_summary = None
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
                xaxis=dict(
                    title=dict(
                        text="Protected Attributes",
                        font=dict(color="#818cf8", size=13, family="Syne")
                    ),
                    side="top", 
                    tickfont=dict(color="#c8cad4", size=12)
                ),
                yaxis=dict(
                    title=dict(
                        text="Features",
                        font=dict(color="#818cf8", size=13, family="Syne")
                    ),
                    tickfont=dict(color="#c8cad4", size=11), 
                    autorange="reversed"
                ),
            )

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">⬢ Feature × Protected Attribute Correlation</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="info-chip">◌ Cells above 0.15 (proxy hunter threshold) indicate potential proxy bias. Cells above 0.5 indicate high correlation risk.</div>
            """, unsafe_allow_html=True)
            st.plotly_chart(fig_ix, width="stretch")
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
                        with st.spinner("Analyzing correlation matrix…"):
                            from google import genai as _genai
                            from google.genai import types as _gtypes
                            _client = _genai.Client(api_key=_gemini_key)

                            _sys_prompt = (
                                "You are an AI bias detection expert conducting a detailed intersectional audit. "
                                "Analyze the following Pearson correlation matrix between dataset features and protected demographic attributes.\n\n"
                                "Correlation Matrix JSON:\n" + json.dumps(corrs, indent=2) + "\n\n"
                                "Please provide a comprehensive, multi-paragraph analysis with the following structure:\n"
                                "1. **High-Risk Proxies (|r| > 0.5):** Detail any features strongly correlated with protected attributes.\n"
                                "2. **Moderate-Risk Proxies (0.15 < |r| <= 0.5):** List features showing moderate correlation.\n"
                                "3. **Safe Features (|r| <= 0.15):** Briefly summarize which features appear independent.\n"
                                "4. **Actionable Recommendations:** Suggest 2-3 specific mitigation strategies.\n\n"
                                "Use Markdown formatting. If no features cross a threshold, explicitly state that."
                            )

                            _reply = None
                            _last_err = None
                            _ix_models = ["gemini-3.0-flash", "gemini-2.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]
                            for _ix_model in _ix_models:
                                try:
                                    _chat = _client.chats.create(
                                        model=_ix_model,
                                        config=_gtypes.GenerateContentConfig(system_instruction=_sys_prompt)
                                    )
                                    _reply = _chat.send_message("Please summarize the proxy risks in this correlation table.").text
                                    break  # success
                                except Exception as _e:
                                    _last_err = _e
                                    _err_str = str(_e)
                                    if any(c in _err_str for c in ("429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND", "503", "UNAVAILABLE")):
                                        continue  # try next model
                                    else:
                                        break  # non-retryable error

                            if _reply:
                                st.session_state.ix_summary = _reply
                                st.rerun()
                            else:
                                _err_str = str(_last_err)
                                if any(c in _err_str for c in ("429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND", "503", "UNAVAILABLE")):
                                    st.warning(
                                        "⏳ Gemini is experiencing high demand right now. "
                                        "Please wait a moment and click **✨ Generate AI Summary** again."
                                    )
                                elif "429" in _err_str or "quota" in _err_str.lower():
                                    st.warning(
                                        "⚠ Gemini API quota exceeded. Check your usage at "
                                        "[aistudio.google.com](https://aistudio.google.com) or try again shortly."
                                    )
                                else:
                                    st.error(f"Failed to generate summary: {_last_err}")
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
