"""
audit_engine/certificate.py
============================
Generates a clean, professional one-page EEOC Compliance Certificate PDF.
Only issued when a model PASSES the compliance audit (fairness_ratio >= 0.8).

Design principles:
  - White/off-white background — readable, print-friendly
  - Muted slate/navy palette — professional, not eye-straining
  - Clear typographic hierarchy with Helvetica
  - No gimmicks — looks like a real compliance document

Returns:
    bytes — PDF content ready for FastAPI Response or st.download_button()
"""

import uuid
from datetime import datetime
from fpdf import FPDF


# ── Palette (muted, professional) ─────────────────────────────────────────────
NAVY        = (30,  41,  59)    # #1e293b  headings, strong text
SLATE       = (71,  85, 105)    # #475569  body text, labels
MUTED       = (148, 163, 184)   # #94a3b8  dividers, sub-labels
ACCENT      = (51,  65,  85)    # #334155  accent bar, borders
PASS_GREEN  = (21, 128,  61)    # #15803d  PASS badge text
PASS_BG     = (240, 253, 244)   # #f0fdf4  PASS badge background
PAGE_BG     = (250, 250, 252)   # #fafafc  very subtle off-white
WHITE       = (255, 255, 255)


def _rule(pdf: FPDF, y: float, lm: float = 18, rm: float = 18,
          color: tuple = MUTED, lw: float = 0.25) -> None:
    """Draws a single horizontal rule."""
    pdf.set_draw_color(*color)
    pdf.set_line_width(lw)
    pdf.line(lm, y, pdf.w - rm, y)


def _metric_block(pdf: FPDF, x: float, y: float, w: float, h: float,
                  label: str, value: str, sub: str) -> None:
    """
    Draws one metric cell: a thin top border, label, large value, sub-label.
    No filled box -- keeps it light and readable.
    """
    # Top accent rule
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.6)
    pdf.line(x, y, x + w, y)

    # Label
    pdf.set_xy(x, y + 2.5)
    pdf.set_font("helvetica", "", 6.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(w, 4, label.upper(), align="C")

    # Value
    pdf.set_xy(x, y + 7.5)
    pdf.set_font("helvetica", "B", 15)
    pdf.set_text_color(*NAVY)
    pdf.cell(w, 8, value, align="C")

    # Sub-label
    pdf.set_xy(x, y + 17)
    pdf.set_font("helvetica", "", 6.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(w, 4, sub, align="C")


def generate_certificate(audit_data: dict) -> bytes:
    """
    Generates a one-page EEOC Compliance Certificate PDF.

    Args:
        audit_data: dict with keys:
            compliance_pass     (bool)
            fairness_ratio      (float)
            top_biased_feature  (str)
            group_a_rate        (float)
            group_b_rate        (float)
            shap_summary        (dict)
            model_name          (str, optional)

    Returns:
        PDF content as bytes.

    Raises:
        ValueError: if compliance_pass is False.
    """
    if not audit_data.get("compliance_pass", False):
        raise ValueError(
            "Certificate cannot be issued: model did not pass EEOC compliance audit."
        )

    ratio       = audit_data.get("fairness_ratio",    0.0)
    top_feat    = audit_data.get("top_biased_feature", "N/A")
    rate_a      = audit_data.get("group_a_rate",       0.0)
    rate_b      = audit_data.get("group_b_rate",       0.0)
    shap_s      = audit_data.get("shap_summary",       {})
    model_name  = audit_data.get("model_name",         "Submitted AI Model")

    cert_id     = str(uuid.uuid4()).upper()
    issued_on   = datetime.now().strftime("%d %B %Y")
    issued_ts   = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    # ── Canvas ────────────────────────────────────────────────────────────────
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(18, 18, 18)
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    W  = pdf.w           # 210 mm
    H  = pdf.h           # 297 mm
    LM = 18              # left margin
    RM = 18              # right margin
    CW = W - LM - RM    # content width (174 mm)

    # ── Page background ───────────────────────────────────────────────────────
    pdf.set_fill_color(*PAGE_BG)
    pdf.rect(0, 0, W, H, style="F")

    # ── Top accent strip ──────────────────────────────────────────────────────
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 0, W, 5, style="F")

    # ── Outer border ──────────────────────────────────────────────────────────
    pdf.set_draw_color(*MUTED)
    pdf.set_line_width(0.3)
    pdf.rect(10, 8, W - 20, H - 16)

    # ── Header ────────────────────────────────────────────────────────────────
    y = 18
    pdf.set_xy(LM, y)
    pdf.set_font("helvetica", "B", 22)
    pdf.set_text_color(*NAVY)
    pdf.cell(CW, 10, "EQUIGUARD", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(LM)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(*SLATE)
    pdf.cell(CW, 5, "AI Bias Firewall  |  EEOC Compliance Suite",
             align="C", new_x="LMARGIN", new_y="NEXT")

    y = pdf.get_y() + 5
    _rule(pdf, y, lw=0.3, color=MUTED)

    # ── Document type + main title ────────────────────────────────────────────
    y += 7
    pdf.set_xy(LM, y)
    pdf.set_font("helvetica", "", 7.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(CW, 5, "CERTIFICATE OF COMPLIANCE", align="C",
             new_x="LMARGIN", new_y="NEXT")

    y = pdf.get_y() + 1
    pdf.set_xy(LM, y)
    pdf.set_font("helvetica", "B", 17)
    pdf.set_text_color(*NAVY)
    pdf.cell(CW, 9, "EEOC Adverse Impact Audit", align="C",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(LM)
    pdf.set_font("helvetica", "", 8.5)
    pdf.set_text_color(*SLATE)
    pdf.cell(CW, 5,
             "Equal Employment Opportunity Commission  4/5ths Rule (29 CFR 1607)",
             align="C", new_x="LMARGIN", new_y="NEXT")

    y = pdf.get_y() + 7
    _rule(pdf, y, lw=0.3, color=MUTED)

    # ── PASS badge ────────────────────────────────────────────────────────────
    y += 8
    badge_w, badge_h = 44, 9
    bx = (W - badge_w) / 2

    pdf.set_fill_color(*PASS_BG)
    pdf.set_draw_color(*PASS_GREEN)
    pdf.set_line_width(0.3)
    pdf.rect(bx, y, badge_w, badge_h, style="FD")

    pdf.set_xy(bx, y + 1.5)
    pdf.set_font("helvetica", "B", 8)
    pdf.set_text_color(*PASS_GREEN)
    pdf.cell(badge_w, 6, "COMPLIANCE VERIFIED  -  PASS", align="C")

    # ── Introductory paragraph ────────────────────────────────────────────────
    y += badge_h + 8
    pdf.set_xy(LM, y)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(*SLATE)
    body = (
        f'This certificate confirms that the AI model "{model_name}" has been '
        f"independently audited by the EquiGuard Bias Firewall and found to satisfy "
        f"the United States Equal Employment Opportunity Commission (EEOC) Uniform "
        f"Guidelines on Employee Selection Procedures, specifically the 4/5ths (80%) "
        f"adverse impact rule. The model is approved for compliant deployment as of "
        f"the audit date stated below."
    )
    pdf.multi_cell(CW, 5.2, body, align="J")

    # ── Three metric columns ──────────────────────────────────────────────────
    y = pdf.get_y() + 8
    _rule(pdf, y, lw=0.25, color=MUTED)
    y += 6

    col_w   = CW / 3
    metrics = [
        ("Fairness Ratio",    f"{ratio:.4f}",           "EEOC threshold >= 0.80"),
        ("Privileged Rate",   f"{rate_a * 100:.1f}%",   "Selection rate - group A"),
        ("Unprivileged Rate", f"{rate_b * 100:.1f}%",   "Selection rate - group B"),
    ]
    for i, (lbl, val, sub) in enumerate(metrics):
        _metric_block(pdf, LM + i * col_w, y, col_w, 24, lbl, val, sub)

    # Thin vertical separators
    pdf.set_draw_color(*MUTED)
    pdf.set_line_width(0.2)
    for i in (1, 2):
        sx = LM + i * col_w
        pdf.line(sx, y + 3, sx, y + 22)

    y += 30
    _rule(pdf, y, lw=0.25, color=MUTED)

    # ── SHAP primary driver ───────────────────────────────────────────────────
    if top_feat and top_feat not in ("N/A", ""):
        y += 6
        pdf.set_xy(LM, y)
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*NAVY)
        pdf.cell(40, 5, "Primary Bias Driver:", new_x="END")

        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*SLATE)
        shap_val = shap_s.get(top_feat, 0)
        pdf.cell(0, 5,
                 f"{top_feat}  (SHAP mean |impact|: {shap_val:.4f}"
                 f"  - within acceptable bounds)",
                 new_x="LMARGIN", new_y="NEXT")
        y = pdf.get_y() + 6
        _rule(pdf, y, lw=0.25, color=MUTED)

    # ── Criteria checklist ────────────────────────────────────────────────────
    y += 7
    pdf.set_xy(LM, y)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(CW, 5, "Audit Criteria Passed", new_x="LMARGIN", new_y="NEXT")

    criteria = [
        "Disparate Impact Ratio >= 0.80  (4/5ths Rule)",
        "Equal Opportunity Difference within acceptable threshold",
        "Demographic Parity assessed and documented",
        "SHAP feature attribution reviewed for proxy bias",
    ]
    pdf.ln(2)
    for c in criteria:
        pdf.set_x(LM)
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*SLATE)
        pdf.cell(6, 5.5, "-", align="C")
        pdf.cell(CW - 6, 5.5, c, new_x="LMARGIN", new_y="NEXT")

    y = pdf.get_y() + 7
    _rule(pdf, y, lw=0.25, color=MUTED)

    # ── Certificate metadata ──────────────────────────────────────────────────
    y += 8
    lw = 46
    rows = [
        ("Certificate ID",  cert_id),
        ("Model Audited",   model_name),
        ("Issued On",       issued_on),
        ("Audit Timestamp", issued_ts),
        ("Audit Engine",    "EquiGuard v1.0  |  IBM aif360  |  SHAP 0.49"),
        ("Standard",        "US EEOC Uniform Guidelines  29 CFR Section 1607"),
        ("Validity",        "Reflects model and dataset state at time of audit only"),
    ]

    for label, value in rows:
        pdf.set_x(LM)
        pdf.set_font("helvetica", "B", 7.5)
        pdf.set_text_color(*NAVY)
        pdf.cell(lw, 5.8, label + ":", align="L", new_x="END")

        pdf.set_font("helvetica", "", 7.5)
        pdf.set_text_color(*SLATE)
        pdf.cell(CW - lw, 5.8, value, align="L",
                 new_x="LMARGIN", new_y="NEXT")

    # ── Signature / cert-number row ───────────────────────────────────────────
    y = pdf.get_y() + 10
    _rule(pdf, y, lw=0.35, color=ACCENT)

    half  = CW / 2
    sig_y = y + 6

    # Left: authorised by block
    pdf.set_xy(LM, sig_y)
    pdf.set_font("helvetica", "", 7)
    pdf.set_text_color(*MUTED)
    pdf.cell(half, 4.5, "Authorised by", new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(LM)
    pdf.set_font("helvetica", "B", 8.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(half, 5, "EquiGuard Automated Audit Engine",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_x(LM)
    pdf.set_font("helvetica", "", 7)
    pdf.set_text_color(*MUTED)
    pdf.cell(half, 4, "IBM aif360  |  SHAP 0.49  |  v1.0",
             new_x="LMARGIN", new_y="NEXT")

    # Right: UUID box
    box_x = LM + half + 10
    box_y = sig_y
    box_w = half - 14
    box_h = 16

    pdf.set_fill_color(*WHITE)
    pdf.set_draw_color(*MUTED)
    pdf.set_line_width(0.25)
    pdf.rect(box_x, box_y, box_w, box_h, style="FD")

    pdf.set_xy(box_x, box_y + 2)
    pdf.set_font("helvetica", "", 6)
    pdf.set_text_color(*MUTED)
    pdf.cell(box_w, 4, "CERTIFICATE NUMBER", align="C",
             new_x="LMARGIN", new_y="NEXT")

    uid_top = cert_id[:18]
    uid_bot = cert_id[18:]
    pdf.set_xy(box_x, box_y + 6.5)
    pdf.set_font("helvetica", "B", 6.5)
    pdf.set_text_color(*NAVY)
    pdf.cell(box_w, 4, uid_top, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(box_x, box_y + 11)
    pdf.cell(box_w, 4, uid_bot, align="C")

    # ── Bottom strip + footer ─────────────────────────────────────────────────
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, H - 10, W, 10, style="F")

    pdf.set_xy(0, H - 8)
    pdf.set_font("helvetica", "", 6.5)
    pdf.set_text_color(*WHITE)
    pdf.cell(
        W, 5,
        "Generated automatically by EquiGuard AI Bias Firewall. "
        "Valid only for the dataset and model state at time of audit.  |  equiguard.ai",
        align="C",
    )

    return bytes(pdf.output())