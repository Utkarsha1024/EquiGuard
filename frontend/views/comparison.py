"""
frontend/views/comparison.py
Multi-model Pareto comparison page: accuracy vs. fairness scatter chart.
"""
import streamlit as st
import plotly.graph_objects as go
from frontend.utils import api_post


def render_comparison():
    # PAGE: MODEL COMPARISON
    st.markdown("""
    <div class="eq-header">
        <div>
            <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:700;color:#f0f1f5;">⧡ Model Comparison</div>
            <div style="font-size:12px;color:#4b5280;font-family:'DM Mono',monospace;margin-top:2px;">
                Pareto frontier: accuracy vs. fairness across 4 classifier families
            </div>
        </div>
        <div class="eq-status-dot">Multi-Model</div>
    </div>
    """, unsafe_allow_html=True)

    _payload = {
        "data_path":    st.session_state.get("data_path", "data/golden_demo_dataset.csv"),
        "target_col":   st.session_state.get("target_col", "loan_approved"),
        "protected_col": st.session_state.get("protected_col", "race"),
    }

    if st.button("⧡  Run Multi-Model Comparison", key="btn_compare", width="stretch"):
        with st.spinner("Training 4 models and running EEOC audits…"):
            try:
                resp = api_post("/audit/compare", _payload)
                if resp.status_code == 200:
                    st.session_state.comparison_result = resp.json().get("results", [])
                    st.rerun()
                else:
                    st.error(f"Comparison failed: {resp.status_code} — {resp.text[:200]}")
            except Exception as e:
                st.error(f"Cannot reach backend: {e}")

    results = st.session_state.comparison_result
    if not results:
        st.markdown("""
        <div class="section-card" style="text-align:center;padding:3rem;">
            <div style="font-size:48px;opacity:0.08;margin-bottom:1rem;">⧡</div>
            <div style="font-size:14px;color:#3a3d52;font-family:'DM Mono',monospace;">
                Click "Run Multi-Model Comparison" to evaluate all models.<br>
                Uses your currently uploaded dataset.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Pareto scatter chart ──────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">⧡ Pareto: Accuracy vs. Fairness</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-chip">◌ The optimal model is in the top-right quadrant (high accuracy AND high fairness ratio).
    The vertical line at 0.80 is the EEOC 4/5ths compliance threshold.</div>
    """, unsafe_allow_html=True)

    # Determine recommended model: highest fairness_ratio that also passes compliance;
    # if none pass, pick the one with the highest fairness_ratio
    passing = [r for r in results if r.get("compliance_pass")]
    if passing:
        recommended = max(passing, key=lambda r: r["accuracy"])
    else:
        recommended = max(results, key=lambda r: r["fairness_ratio"])

    _model_names  = [r["model_name"] for r in results]
    _accuracies   = [r["accuracy"] for r in results]
    _fairness     = [r["fairness_ratio"] for r in results]
    _passing      = [r["compliance_pass"] for r in results]
    _colors       = ["#4ade80" if p else "#f87171" for p in _passing]
    _sizes        = [18 if r["model_name"] == recommended["model_name"] else 12 for r in results]

    fig = go.Figure()

    # EEOC threshold line
    fig.add_shape(
        type="line", x0=0, x1=1.05, y0=0.8, y1=0.8,
        line=dict(color="rgba(99,102,241,0.4)", width=1, dash="dot"),
    )
    fig.add_annotation(
        x=1.02, y=0.82, text="EEOC threshold 0.80",
        showarrow=False, font=dict(size=10, color="#6366f1", family="DM Mono"),
    )

    # Points
    fig.add_trace(go.Scatter(
        x=_accuracies,
        y=_fairness,
        mode="markers+text",
        text=_model_names,
        textposition="top center",
        textfont=dict(size=11, color="#c8cad4", family="DM Mono"),
        marker=dict(
            size=_sizes,
            color=_colors,
            line=dict(color="rgba(255,255,255,0.15)", width=1),
        ),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Accuracy: %{x:.4f}<br>"
            "Fairness Ratio: %{y:.4f}<extra></extra>"
        ),
    ))

    # Star marker for recommended model
    fig.add_trace(go.Scatter(
        x=[recommended["accuracy"]],
        y=[recommended["fairness_ratio"]],
        mode="markers",
        marker=dict(symbol="star", size=22, color="#fbbf24"),
        name="★ Recommended",
        hovertemplate=f"<b>Recommended: {recommended['model_name']}</b><extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#6b7280", family="DM Sans"),
        margin=dict(l=10, r=10, t=20, b=10),
        height=380,
        xaxis=dict(
            title="Accuracy",
            range=[0, 1.08],
            tickfont=dict(color="#6b7280", size=11, family="DM Mono"),
            gridcolor="#1a1c28",
            zerolinecolor="#1a1c28",
        ),
        yaxis=dict(
            title="Fairness Ratio (EEOC)",
            range=[0, 1.2],
            tickfont=dict(color="#6b7280", size=11, family="DM Mono"),
            gridcolor="#1a1c28",
            zerolinecolor="#1a1c28",
        ),
        showlegend=True,
        legend=dict(
            font=dict(color="#6b7280", size=11, family="DM Mono"),
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    st.plotly_chart(fig, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Recommended model banner ─────────────────────────────────────────────
    _rec_pass  = recommended.get("compliance_pass", False)
    _rec_color = "#4ade80" if _rec_pass else "#f87171"
    _rec_badge = '<span class="badge-pass">PASS</span>' if _rec_pass else '<span class="badge-fail">FAIL</span>'
    st.markdown(f"""
    <div style="background:rgba(251,191,36,0.06);border:1px solid rgba(251,191,36,0.2);border-radius:12px;padding:14px 18px;margin-bottom:1.5rem;display:flex;align-items:center;gap:16px;">
        <div style="font-size:24px;">★</div>
        <div>
            <div style="font-size:10px;color:#fbbf24;font-family:'DM Mono',monospace;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:4px;">Recommended Model</div>
            <div style="font-size:16px;font-weight:600;font-family:'Syne',sans-serif;color:#f0f1f5;">{recommended['model_name']}</div>
            <div style="font-size:12px;color:#6b7280;font-family:'DM Mono',monospace;margin-top:4px;">
                Accuracy: <span style="color:#818cf8;">{recommended['accuracy']:.4f}</span> ·
                Fairness Ratio: <span style="color:{_rec_color};">{recommended['fairness_ratio']:.4f}</span> ·
                EEOC: {_rec_badge}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Comparison table ─────────────────────────────────────────────────────
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">◈ All Models</div>', unsafe_allow_html=True)

    _header = """
    <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr;gap:8px;padding:8px 12px;
    border-bottom:1px solid #1a1c28;font-size:10px;color:#3a3d52;font-family:'DM Mono',monospace;
    letter-spacing:1px;text-transform:uppercase;">
        <div>Model</div><div>Accuracy</div><div>Fairness Ratio</div><div>EEOC</div><div>Top Bias Driver</div>
    </div>"""
    st.markdown(_header, unsafe_allow_html=True)

    for r in results:
        _is_rec = r["model_name"] == recommended["model_name"]
        _pass   = r.get("compliance_pass", False)
        _badge  = '<span class="badge-pass" style="font-size:10px;padding:2px 8px;">PASS</span>' if _pass else '<span class="badge-fail" style="font-size:10px;padding:2px 8px;">FAIL</span>'
        _fr_col = "#4ade80" if r["fairness_ratio"] >= 0.8 else "#f87171"
        _border = "border-left:3px solid #fbbf24;" if _is_rec else "border-left:3px solid transparent;"
        _star   = " ★" if _is_rec else ""
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr;gap:8px;
        padding:10px 12px;border-bottom:1px solid #1a1c28;{_border}align-items:center;">
            <div style="font-size:13px;color:#c8cad4;font-weight:500;">{r['model_name']}<span style="color:#fbbf24;font-size:11px;">{_star}</span></div>
            <div style="font-size:13px;color:#818cf8;font-family:'DM Mono',monospace;">{r['accuracy']:.4f}</div>
            <div style="font-size:13px;color:{_fr_col};font-family:'DM Mono',monospace;">{r['fairness_ratio']:.4f}</div>
            <div>{_badge}</div>
            <div style="font-size:11px;color:#4b5280;font-family:'DM Mono',monospace;">{r.get('top_biased_feature','—')[:20]}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
