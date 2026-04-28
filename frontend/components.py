import plotly.graph_objects as go
import pandas as pd

# ── Gauge Chart ────────────────────────────────────────────────────────────────
def render_fairness_gauge(score):
    color = "#4ade80" if score >= 0.8 else ("#fbbf24" if score >= 0.6 else "#f87171")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Fairness Ratio", 'font': {'color': '#6b7280', 'size': 13, 'family': 'DM Mono'}},
        number={'font': {'color': color, 'size': 42, 'family': 'Syne'}, 'valueformat': '.2f'},
        gauge={
            'axis': {'range': [0.0, 1.0], 'tickcolor': "#2a2d40", 'tickfont': {'color': '#3a3d52', 'size': 10}},
            'bar': {'color': color, 'thickness': 0.25},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [
                {'range': [0.0, 0.6],  'color': "rgba(239,68,68,0.08)"},
                {'range': [0.6, 0.8],  'color': "rgba(251,191,36,0.08)"},
                {'range': [0.8, 1.0],  'color': "rgba(74,222,128,0.08)"}
            ],
            'threshold': {
                'line': {'color': "#6366f1", 'width': 2},
                'thickness': 0.75,
                'value': 0.8
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={'color': "white", 'family': 'DM Sans'},
        margin=dict(l=20, r=20, t=40, b=10),
        height=240
    )
    return fig


# ── SHAP Waterfall Chart ───────────────────────────────────────────────────────
def render_shap_waterfall(shap_summary: dict):
    """
    Renders a horizontal waterfall bar chart from shap_summary dict
    {feature: mean_abs_shap_value} — top 5 features, sorted by impact.
    """
    if not shap_summary:
        return None

    items = sorted(shap_summary.items(), key=lambda x: x[1])  # ascending for bottom-up display
    features = [i[0] for i in items]
    values   = [i[1] for i in items]

    # Color: highest bar gets red accent, rest get indigo gradient
    colors = ["#6366f1"] * len(values)
    colors[-1] = "#f87171"   # top driver = red warning
    colors[-2] = "#fb923c" if len(values) > 1 else colors[-2]  # second = amber

    fig = go.Figure()

    # Invisible base bars (waterfall effect)
    cumulative = [0] + list(values[:-1])
    for i in range(len(features)):
        c = cumulative[i] if i == 0 else sum(values[:i])
        _ = c  # kept for clarity

    # Simple horizontal bar (mean abs SHAP — the standard presentation)
    fig.add_trace(go.Bar(
        x=values,
        y=features,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(width=0),
        ),
        text=[f"{v:.4f}" for v in values],
        textposition='outside',
        textfont=dict(color='#6b7280', size=11, family='DM Mono'),
        hovertemplate='<b>%{y}</b><br>SHAP Impact: %{x:.4f}<extra></extra>',
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#6b7280", family="DM Sans", size=12),
        margin=dict(l=10, r=60, t=10, b=10),
        height=260,
        xaxis=dict(
            showgrid=True,
            gridcolor="#1a1c28",
            zeroline=True,
            zerolinecolor="#2a2d40",
            zerolinewidth=1,
            showline=False,
            tickfont=dict(color="#3a3d52", size=10, family="DM Mono"),
            title=dict(text="Mean |SHAP| Value", font=dict(color="#3a3d52", size=11)),
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            tickfont=dict(color="#c8cad4", size=12, family="DM Sans"),
        ),
        bargap=0.35,
        showlegend=False,
    )

    # Vertical reference line at x=0
    fig.add_vline(x=0, line_color="#2a2d40", line_width=1)

    return fig


# ── Bias Drift Chart ───────────────────────────────────────────────────────────
def render_bias_drift(history_data: list):
    """
    Renders a Plotly area+line chart of fairness_ratio over time.
    Marks PASS/FAIL points with colored markers.
    """
    if not history_data:
        return None

    df = pd.DataFrame(history_data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    pass_df = df[df["fairness_ratio"] >= 0.8]
    fail_df = df[df["fairness_ratio"] < 0.8]

    fig = go.Figure()

    # Shaded area under the line
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["fairness_ratio"],
        mode="lines",
        line=dict(color="rgba(99,102,241,0)", width=0),
        fill='tozeroy',
        fillcolor="rgba(99,102,241,0.06)",
        showlegend=False,
        hoverinfo='skip',
    ))

    # Main line
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["fairness_ratio"],
        mode="lines",
        line=dict(color="#6366f1", width=2.5, shape='spline', smoothing=0.8),
        showlegend=False,
        hovertemplate='<b>%{x|%Y-%m-%d %H:%M}</b><br>Fairness Ratio: <b>%{y:.3f}</b><extra></extra>',
    ))

    # PASS markers (green dots)
    if not pass_df.empty:
        fig.add_trace(go.Scatter(
            x=pass_df["timestamp"],
            y=pass_df["fairness_ratio"],
            mode="markers",
            name="PASS",
            marker=dict(color="#4ade80", size=9, line=dict(color="#080910", width=2)),
            hovertemplate='<b>PASS</b><br>%{x|%Y-%m-%d %H:%M}<br>Ratio: %{y:.3f}<extra></extra>',
        ))

    # FAIL markers (red dots)
    if not fail_df.empty:
        fig.add_trace(go.Scatter(
            x=fail_df["timestamp"],
            y=fail_df["fairness_ratio"],
            mode="markers",
            name="FAIL",
            marker=dict(color="#f87171", size=9, symbol="x", line=dict(color="#080910", width=2)),
            hovertemplate='<b>FAIL</b><br>%{x|%Y-%m-%d %H:%M}<br>Ratio: %{y:.3f}<extra></extra>',
        ))

    # EEOC threshold line
    fig.add_hline(
        y=0.8,
        line_dash="dot",
        line_color="rgba(239,68,68,0.45)",
        line_width=1.5,
        annotation_text="EEOC Minimum (0.80)",
        annotation_font_color="#f87171",
        annotation_font_size=10,
        annotation_font_family="DM Mono",
        annotation_position="top right",
    )

    # Compliance zone shading
    fig.add_hrect(
        y0=0.8, y1=1.05,
        fillcolor="rgba(34,197,94,0.03)",
        line_width=0,
    )
    fig.add_hrect(
        y0=0, y1=0.8,
        fillcolor="rgba(239,68,68,0.03)",
        line_width=0,
    )

    max_y = min(1.05, df["fairness_ratio"].max() * 1.03)

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#6b7280", family="DM Sans", size=12),
        margin=dict(l=10, r=10, t=10, b=10),
        height=260,
        xaxis=dict(
            gridcolor="#1a1c28",
            showline=False,
            zeroline=False,
            tickfont=dict(color="#3a3d52", size=10, family="DM Mono"),
        ),
        yaxis=dict(
            range=[0, max_y],
            gridcolor="#1a1c28",
            showline=False,
            zeroline=False,
            tickfont=dict(color="#3a3d52", size=10, family="DM Mono"),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(color="#6b7280", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
    )

    return fig

    return fig

# ── Uiverse Download Button ──────────────────────────────────────────────────
def render_uiverse_download(file_bytes, file_name, mime_type, label="Download", completed_label="Open"):
    """
    Renders the Uiverse animated download button with a transparent st.download_button
    overlaid on top via CSS :has() — so the animation shows AND the download works.
    """
    import streamlit as st
    import uuid

    uid = str(uuid.uuid4())[:8]

    # Single markdown block: Uiverse HTML + scoped CSS that overlays the NEXT download button
    st.markdown(f"""
    <style>
    /* Move the stElementContainer that immediately follows our wrap UP over the Uiverse visual */
    .stElementContainer:has(#uv-dl-wrap-{uid}) + .stElementContainer [data-testid="stDownloadButton"],
    .stElementContainer:has(#uv-dl-wrap-{uid}) + div [data-testid="stDownloadButton"] {{
        margin-top: -72px !important;
        position: relative !important;
        z-index: 10 !important;
    }}
    /* Make only the button itself transparent so Uiverse shows through */
    .stElementContainer:has(#uv-dl-wrap-{uid}) + .stElementContainer [data-testid="stDownloadButton"] > button,
    .stElementContainer:has(#uv-dl-wrap-{uid}) + div [data-testid="stDownloadButton"] > button {{
        opacity: 0 !important;
        height: 57px !important;
        width: 100% !important;
        cursor: pointer !important;
        background: transparent !important;
        border: none !important;
    }}
    </style>

    <div id="uv-dl-wrap-{uid}" style="display:flex; justify-content:center; margin-bottom:8px; width:100%;">
        <div class="uv-dl-container">
          <label class="uv-dl-label" for="uv-dl-{uid}">
            <input type="checkbox" id="uv-dl-{uid}" class="uv-dl-input" />
            <span class="uv-dl-circle">
              <svg class="uv-dl-icon" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 19V5m0 14-4-4m4 4 4-4"></path>
              </svg>
              <div class="uv-dl-square"></div>
            </span>
            <span class="uv-dl-title">{label}</span>
            <span class="uv-dl-title">{completed_label}</span>
          </label>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Download button rendered IMMEDIATELY after — CSS above moves it on top of the Uiverse HTML
    st.download_button(
        label=label,
        data=file_bytes,
        file_name=file_name,
        mime=mime_type,
        use_container_width=True,
        key=f"dl-btn-{uid}",
    )

    # Trigger checkbox animation when the (invisible) download button is clicked
    st.iframe(f"""
    <script>
    (function() {{
        try {{
            var doc = window.parent.document;
            function init() {{
                var checkbox = doc.getElementById('uv-dl-{uid}');
                var wrap = doc.getElementById('uv-dl-wrap-{uid}');
                if (!checkbox || !wrap) {{ setTimeout(init, 100); return; }}
                // The download button is the next stElementContainer after wrap's parent
                var wrapEl = wrap.closest('.stElementContainer') || wrap.parentElement;
                var next = wrapEl ? wrapEl.nextElementSibling : null;
                if (!next) {{ setTimeout(init, 100); return; }}
                var btn = next.querySelector('[data-testid="stDownloadButton"] button');
                if (!btn) {{ setTimeout(init, 100); return; }}
                if (!btn.dataset.uvAnim) {{
                    btn.addEventListener('click', function() {{
                        if (!checkbox.checked) checkbox.click();
                    }});
                    btn.dataset.uvAnim = '1';
                }}
            }}
            init();
        }} catch(e) {{}}
    }})();
    </script>
    """, height=1)


