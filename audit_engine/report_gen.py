import os
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from fpdf import FPDF

def generate_executive_summary(audit_data: dict) -> str:
    """
    Generates a PDF executive summary of the model audit using fpdf2.
    Returns the path to the temporary PDF file.
    """
    pdf = FPDF()
    chart1_path = None
    chart2_path = None
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
    
    # Generate Chart 1: Bias Analysis
    plt.figure(figsize=(6, 4))
    plt.bar(["Privileged", "Unprivileged"], [group_a_rate, group_b_rate], color=['#1f77b4', '#ff7f0e'])
    plt.ylabel("Selection Rate")
    plt.title("Bias Analysis: Selection Rates")
    chart1_fd, chart1_path = tempfile.mkstemp(suffix=".png")
    os.close(chart1_fd)
    plt.tight_layout()
    plt.savefig(chart1_path)
    plt.close()

    pdf.cell(0, 10, f"- Privileged Group Selection Rate: {group_a_rate * 100:.1f}%", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"- Unprivileged Group Selection Rate: {group_b_rate * 100:.1f}%", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Insert Chart 1
    pdf.image(chart1_path, w=120)
    pdf.ln(5)
    
    # 4. Feature Impact
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "4. Feature Impact (Explainability)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    
    shap_summary = audit_data.get("shap_summary", {})
    if shap_summary:
        pdf.cell(0, 10, "Top 5 features influencing the model's decisions:", new_x="LMARGIN", new_y="NEXT")
        
        # Generate Chart 2: Feature Impact
        features = list(shap_summary.keys())[:5]
        scores = list(shap_summary.values())[:5]
        
        plt.figure(figsize=(7, 4))
        plt.barh(features, scores, color='#2ca02c')
        plt.xlabel("SHAP Value (Impact)")
        plt.title("Top Feature Impacts")
        plt.gca().invert_yaxis()
        chart2_fd, chart2_path = tempfile.mkstemp(suffix=".png")
        os.close(chart2_fd)
        plt.tight_layout()
        plt.savefig(chart2_path)
        plt.close()
        
        pdf.image(chart2_path, w=140)
        pdf.ln(5)
        
        # Data Table
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(90, 10, "Feature", border=1, align="C")
        pdf.cell(90, 10, "SHAP Value", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("helvetica", "", 12)
        for feature, score in shap_summary.items():
            pdf.cell(90, 10, str(feature), border=1)
            pdf.cell(90, 10, f"{score:.4f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
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
    
    # Securely delete temp PNG files
    if chart1_path and os.path.exists(chart1_path):
        os.remove(chart1_path)
    if chart2_path and os.path.exists(chart2_path):
        os.remove(chart2_path)
        
    return filepath
