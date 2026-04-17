import os
import sys

# Add the project root to sys.path to resolve 'audit_engine' and 'database' imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from audit_engine.model_runner import run_model
from audit_engine.compliance import run_audit
from audit_engine.proxy_hunter import find_proxies
from audit_engine.mitigation import mitigate_and_retrain
from audit_engine.report_gen import generate_executive_summary
from database.db import log_audit_run, get_audit_history

# Initialize the API
app = FastAPI(title="EquiGuard API", version="1.0")

def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

@app.get("/")
def read_root():
    return {"status": "Active", "message": "EquiGuard Firewall is running and ready for data."}

@app.post("/audit/model")
def audit_model(payload: dict = None):
    payload = payload or {}
    data_path = payload.get("data_path", "golden_demo_dataset.csv")
    target_col = payload.get("target_col", "loan_approved")
    protected_col = payload.get("protected_col", "race")
    
    result = run_model(data_path, target_col, protected_col)
    return {"status": "success", "accuracy": result["accuracy"], "predictions": result["predictions"]}

@app.post("/audit/compliance")
def audit_compliance(payload: dict = None):
    payload = payload or {}
    data_path = payload.get("data_path", "golden_demo_dataset.csv")
    target_col = payload.get("target_col", "loan_approved")
    protected_col = payload.get("protected_col", "race")
    
    # Fetch trained model and artifacts
    result = run_model(data_path, target_col, protected_col)
    
    # Run the compliance and explainability audit
    audit_result = run_audit(
        model=result["model"],
        X_test=result["X_test"],
        predictions=result["predictions"],
        protected_attributes=result["protected_attributes"]
    )
    
    # Log the audit run to the database
    log_audit_run(
        fairness_ratio=audit_result["fairness_ratio"],
        compliance_pass=audit_result["compliance_pass"],
        top_feature=audit_result["top_biased_feature"]
    )
    
    return {
        "compliance_pass": audit_result["compliance_pass"],
        "fairness_ratio": audit_result["fairness_ratio"],
        "top_biased_feature": audit_result["top_biased_feature"],
        "group_a_rate": audit_result.get("group_a_rate", 0.0),
        "group_b_rate": audit_result.get("group_b_rate", 0.0),
        "shap_summary": audit_result.get("shap_summary", {})
    }

@app.post("/audit/preprocess")
def audit_preprocess(payload: dict):
    data_path = payload.get("data_path", "golden_demo_dataset.csv")
    target_col = payload.get("target_col", "loan_approved")
    protected_col = payload.get("protected_col", "race")
    
    # Load dataset
    df = pd.read_csv(data_path)
    
    # Evaluate for hidden proxy clusters
    flagged = find_proxies(df, protected_col, target_col)
    
    return {
        "proxies_detected": len(flagged) > 0,
        "flagged_columns": flagged
    }

@app.post("/audit/mitigate")
def audit_mitigate(payload: dict):
    flagged_columns = payload.get("flagged_columns", [])
    data_path = payload.get("data_path", "golden_demo_dataset.csv")
    target_col = payload.get("target_col", "loan_approved")
    protected_col = payload.get("protected_col", "race")
    
    if not flagged_columns:
        raise HTTPException(status_code=400, detail="No proxy columns provided for mitigation.")
    
    # Retrain model without proxy columns
    result = mitigate_and_retrain(flagged_columns, data_path, target_col, protected_col)
    
    # Run compliance audit on mitigated model
    audit_result = run_audit(
        model=result["model"],
        X_test=result["X_test"],
        predictions=result["predictions"],
        protected_attributes=result["protected_attributes"]
    )
    
    # Log the mitigated audit run to the database
    log_audit_run(
        fairness_ratio=audit_result["fairness_ratio"],
        compliance_pass=audit_result["compliance_pass"],
        top_feature=audit_result["top_biased_feature"]
    )
    
    return {
        "status": "success",
        "compliance_pass": audit_result["compliance_pass"],
        "fairness_ratio": audit_result["fairness_ratio"],
        "top_biased_feature": audit_result["top_biased_feature"],
        "group_a_rate": audit_result.get("group_a_rate", 0.0),
        "group_b_rate": audit_result.get("group_b_rate", 0.0),
        "shap_summary": audit_result.get("shap_summary", {}),
        "accuracy": result["accuracy"]
    }

@app.post("/audit/export")
def audit_export(payload: dict, background_tasks: BackgroundTasks):
    try:
        filepath = generate_executive_summary(payload)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate the PDF report. Ensure an audit has been run.")
    
    background_tasks.add_task(remove_file, filepath)
    
    return FileResponse(
        path=filepath,
        filename="EquiGuard_Executive_Report.pdf",
        media_type="application/pdf"
    )

@app.get("/audit/history")
def audit_history():
    history = get_audit_history()
    return {"status": "success", "history": history}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
