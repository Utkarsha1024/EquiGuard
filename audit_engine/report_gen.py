import os
import tempfile
from datetime import datetime
from fpdf import FPDF

def generate_executive_summary(audit_data: dict) -> str:
    """
    Generates a PDF executive summary of the model audit using fpdf2.
    Returns the path to the temporary PDF file.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("helvetica", "B", 20)
    pdf.cell(0, 15, "EquiGuard Executive Audit Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Timestamp
    pdf.set_font("helvetica", "I", 12)
    pdf.set_text_color(100, 100, 100)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(0, 10, f"Generated on: {current_time}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.set_text_color(0, 0, 0)
    
    # 1. Executive Summary
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "1. Executive Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    
    fairness_ratio = audit_data.get("fairness_ratio", 0.0)
    compliance_pass = audit_data.get("compliance_pass", False)
    
    status_text = "PASS" if compliance_pass else "FAIL"
    pdf.cell(60, 10, "US EEOC Compliance Status:", ln=0)
    if compliance_pass:
        pdf.set_text_color(0, 128, 0) # Green
    else:
        pdf.set_text_color(200, 0, 0) # Red
    pdf.cell(0, 10, status_text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Disparate Impact Ratio: {fairness_ratio:.2f}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # 2. Data Integrity
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "2. Data Integrity (Pre-Processing)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    
    flagged_proxies = audit_data.get("flagged_proxies", [])
    if flagged_proxies:
        pdf.multi_cell(0, 10, "The following variables were flagged as highly correlated proxies for protected attributes:", new_x="LMARGIN", new_y="NEXT")
        for p in flagged_proxies:
            pdf.cell(10) # indent
            pdf.cell(0, 8, f"- {p}", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 10, "No hidden proxy variables detected.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # 3. Bias Analysis
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "3. Bias Analysis (Post-Processing)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    
    group_a_rate = audit_data.get("group_a_rate", 0.0)
    group_b_rate = audit_data.get("group_b_rate", 0.0)
    pdf.cell(0, 10, f"- Privileged Group Selection Rate: {group_a_rate * 100:.1f}%", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"- Unprivileged Group Selection Rate: {group_b_rate * 100:.1f}%", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # 4. Feature Impact
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "4. Feature Impact (Explainability)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    
    shap_summary = audit_data.get("shap_summary", {})
    if shap_summary:
        pdf.cell(0, 10, "Top 5 features influencing the model's decisions:", new_x="LMARGIN", new_y="NEXT")
        for feature, score in shap_summary.items():
            pdf.cell(10)
            pdf.cell(0, 8, f"- {feature}: {score:.4f}", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 10, "Feature impact data unavailable.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # Summary Sentence
    pdf.set_font("helvetica", "I", 12)
    if compliance_pass:
        summary = "The model has been audited and cleared of proxy-variable bias. It operates within acceptable EEOC bounds."
    else:
        summary = "The model exhibits statistically significant bias. Immediate mitigation is required before deployment."
        
    pdf.multi_cell(0, 10, f"Summary: {summary}", new_x="LMARGIN", new_y="NEXT")
    
    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    filepath = temp_file.name
    temp_file.close()
    
    pdf.output(filepath)
    
    return filepath
