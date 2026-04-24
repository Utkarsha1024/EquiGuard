import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from frontend.utils import api_get, api_post, get_kpi_values
from frontend.components import render_fairness_gauge, render_shap_waterfall, render_bias_drift
import json


def render_bias_leaderboard():
    # PAGE: BIAS LEADERBOARD
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
                    st.plotly_chart(fig_drift, width="stretch")
                st.markdown('</div>', unsafe_allow_html=True)

                # Table
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">◈ Audit History</div>', unsafe_allow_html=True)
                
                df_history_desc = df_history.iloc[::-1]
                total_audits = len(df_history_desc)
                
                for i, (ts, row) in enumerate(df_history_desc.iterrows()):
                    ratio = row.get('fairness_ratio', 0)
                    passed = ratio >= 0.8
                    badge_html = (
                        '<span class="badge-pass" style="font-size:11px;padding:3px 10px;">PASS</span>'
                        if passed else
                        '<span class="badge-fail" style="font-size:11px;padding:3px 10px;">FAIL</span>'
                    )
                    st.markdown(f"""
                    <div class="leaderboard-row">
                        <span class="rank-num">#{total_audits - i}</span>
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
