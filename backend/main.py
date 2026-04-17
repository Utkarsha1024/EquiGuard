from fastapi import FastAPI, HTTPException

# Initialize the API
app = FastAPI(title="EquiGuard API", version="1.0")

@app.get("/")
def read_root():
    return {"status": "Active", "message": "EquiGuard Firewall is running and ready for data."}

@app.post("/audit/model")
def audit_model():
    from audit_engine.model_runner import run_model
    result = run_model()
    return {"status": "success", "accuracy": result["accuracy"], "predictions": result["predictions"]}

@app.post("/audit/compliance")
def audit_compliance():
    from audit_engine.model_runner import run_model
    from audit_engine.compliance import run_audit
    
    # Fetch trained model and artifacts
    result = run_model()
    
    # Run the compliance and explainability audit
    audit_result = run_audit(
        model=result["model"],
        X_test=result["X_test"],
        predictions=result["predictions"],
        protected_attributes=result["protected_attributes"]
    )
    
    # Log the audit run to the database
    from database.db import log_audit_run
    log_audit_run(
        fairness_ratio=audit_result["fairness_ratio"],
        compliance_pass=audit_result["compliance_pass"],
        top_feature=audit_result["top_biased_feature"]
    )
    
    return {
        "compliance_pass": audit_result["compliance_pass"],
        "fairness_ratio": audit_result["fairness_ratio"],
        "top_biased_feature": audit_result["top_biased_feature"]
    }

@app.post("/audit/preprocess")
def audit_preprocess(payload: dict):
    import pandas as pd
    from audit_engine.proxy_hunter import find_proxies
    
    dataset_id = payload.get("dataset_id", "compas")
    
    # Load golden dataset
    url = "golden_demo_dataset.csv"
    df = pd.read_csv(url)
    
    # Evaluate 'race' for hidden proxy clusters
    flagged = find_proxies(df, "race")
    
    return {
        "proxies_detected": len(flagged) > 0,
        "flagged_columns": flagged
    }

@app.post("/audit/mitigate")
def audit_mitigate(payload: dict):
    from audit_engine.mitigation import mitigate_and_retrain
    from audit_engine.compliance import run_audit
    from database.db import log_audit_run
    
    flagged_columns = payload.get("flagged_columns", [])
    
    if not flagged_columns:
        raise HTTPException(status_code=400, detail="No proxy columns provided for mitigation.")
    
    # Retrain model without proxy columns
    result = mitigate_and_retrain(flagged_columns)
    
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
        "accuracy": result["accuracy"]
    }

@app.post("/audit/export")
def audit_export(payload: dict):
    from audit_engine.report_gen import generate_executive_summary
    from fastapi.responses import FileResponse
    
    try:
        filepath = generate_executive_summary(payload)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate the PDF report. Ensure an audit has been run.")
    
    return FileResponse(
        path=filepath,
        filename="EquiGuard_Executive_Report.pdf",
        media_type="application/pdf"
    )

@app.get("/audit/history")
def audit_history():
    from database.db import get_audit_history
    history = get_audit_history()
    return {"status": "success", "history": history}
