import os
import sys
from functools import lru_cache

# Add the project root to sys.path to resolve 'audit_engine' and 'database' imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import FileResponse, Response
from starlette.status import HTTP_403_FORBIDDEN

from audit_engine.model_runner import run_model
from audit_engine.compliance import run_audit
from audit_engine.proxy_hunter import find_proxies
from audit_engine.mitigation import mitigate_and_retrain
from audit_engine.report_gen import generate_executive_summary
from audit_engine.certificate import generate_certificate
from audit_engine.simulator import simulate_mitigation
from audit_engine.intersectional import run_intersectional_audit
from database.db import log_audit_run, get_audit_history
import json
import zipfile
import tempfile

# ── Load environment variables from .env ───────────────────────────────────────
load_dotenv()

# ── Config ─────────────────────────────────────────────────────────────────────
@lru_cache()
def get_settings():
    """
    Reads config from environment variables (populated by .env via dotenv).
    Using lru_cache so it's only read once — not on every request.
    """
    api_key = os.getenv("EQUIGUARD_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "EQUIGUARD_API_KEY is not set. "
            "Copy .env.example → .env and set a strong secret key."
        )
    return {
        "api_key":    api_key,
        "env":        os.getenv("ENV", "development"),
        "db_url":     os.getenv("DATABASE_URL", "sqlite:///equiguard.db"),
        "host":       os.getenv("HOST", "127.0.0.1"),
        "port":       int(os.getenv("PORT", 8000)),
    }

# ── API Key Auth ───────────────────────────────────────────────────────────────
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

async def require_api_key(
    api_key_header: str = Security(API_KEY_HEADER),
):
    """
    Dependency injected into every protected endpoint.
    Reads the expected key from settings — never hardcoded.
    Returns 403 if the header is missing or wrong.
    """
    settings = get_settings()
    if not api_key_header or api_key_header != settings["api_key"]:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key. Pass your key in the X-API-Key header.",
        )
    return api_key_header

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="EquiGuard API",
    version="1.0",
    description="AI Bias Firewall — EEOC Compliance Audit Engine",
    docs_url="/docs",       # Swagger UI (useful in dev)
    redoc_url="/redoc",
)

# ── Utility ────────────────────────────────────────────────────────────────────
def remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

# ── Public Endpoints (no auth required) ───────────────────────────────────────

@app.get("/", tags=["Health"])
def read_root():
    """Public health check — no auth required."""
    settings = get_settings()
    return {
        "status":  "Active",
        "env":     settings["env"],
        "message": "EquiGuard Firewall is running and ready for data.",
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Lightweight liveness probe for Docker / load balancers."""
    return {"status": "ok"}

# ── Protected Endpoints (X-API-Key required) ───────────────────────────────────

@app.post("/audit/model", tags=["Audit"], dependencies=[Depends(require_api_key)])
def audit_model(payload: dict = None):
    payload = payload or {}
    data_path    = payload.get("data_path",    "golden_demo_dataset.csv")
    target_col   = payload.get("target_col",   "loan_approved")
    protected_col = payload.get("protected_col", "race")

    result = run_model(data_path, target_col, protected_col)
    return {
        "status":      "success",
        "accuracy":    result["accuracy"],
        "predictions": result["predictions"],
    }

@app.post("/audit/compliance", tags=["Audit"], dependencies=[Depends(require_api_key)])
def audit_compliance(payload: dict = None):
    payload = payload or {}
    data_path     = payload.get("data_path",     "golden_demo_dataset.csv")
    target_col    = payload.get("target_col",    "loan_approved")
    protected_col = payload.get("protected_col", "race")

    result = run_model(data_path, target_col, protected_col)

    audit_result = run_audit(
        model=result["model"],
        X_test=result["X_test"],
        predictions=result["predictions"],
        protected_attributes=result["protected_attributes"],
    )

    log_audit_run(
        fairness_ratio=audit_result["fairness_ratio"],
        compliance_pass=audit_result["compliance_pass"],
        top_feature=audit_result["top_biased_feature"],
    )

    return {
        "compliance_pass":    audit_result["compliance_pass"],
        "fairness_ratio":     audit_result["fairness_ratio"],
        "top_biased_feature": audit_result["top_biased_feature"],
        "group_a_rate":       audit_result.get("group_a_rate", 0.0),
        "group_b_rate":       audit_result.get("group_b_rate", 0.0),
        "shap_summary":       audit_result.get("shap_summary", {}),
    }

@app.post("/audit/preprocess", tags=["Audit"], dependencies=[Depends(require_api_key)])
def audit_preprocess(payload: dict):
    data_path     = payload.get("data_path",     "golden_demo_dataset.csv")
    target_col    = payload.get("target_col",    "loan_approved")
    protected_col = payload.get("protected_col", "race")

    df      = pd.read_csv(data_path)
    flagged = find_proxies(df, protected_col, target_col)

    return {
        "proxies_detected": len(flagged) > 0,
        "flagged_columns":  flagged,
    }

@app.post("/audit/mitigate", tags=["Audit"], dependencies=[Depends(require_api_key)])
def audit_mitigate(payload: dict):
    flagged_columns = payload.get("flagged_columns", [])
    data_path       = payload.get("data_path",       "golden_demo_dataset.csv")
    target_col      = payload.get("target_col",      "loan_approved")
    protected_col   = payload.get("protected_col",   "race")

    if not flagged_columns:
        raise HTTPException(
            status_code=400,
            detail="No proxy columns provided for mitigation.",
        )

    result = mitigate_and_retrain(flagged_columns, data_path, target_col, protected_col)

    audit_result = run_audit(
        model=result["model"],
        X_test=result["X_test"],
        predictions=result["predictions"],
        protected_attributes=result["protected_attributes"],
    )

    log_audit_run(
        fairness_ratio=audit_result["fairness_ratio"],
        compliance_pass=audit_result["compliance_pass"],
        top_feature=audit_result["top_biased_feature"],
    )

    return {
        "status":             "success",
        "compliance_pass":    audit_result["compliance_pass"],
        "fairness_ratio":     audit_result["fairness_ratio"],
        "top_biased_feature": audit_result["top_biased_feature"],
        "group_a_rate":       audit_result.get("group_a_rate", 0.0),
        "group_b_rate":       audit_result.get("group_b_rate", 0.0),
        "shap_summary":       audit_result.get("shap_summary", {}),
        "accuracy":           result["accuracy"],
    }

@app.post("/audit/export", tags=["Audit"], dependencies=[Depends(require_api_key)])
def audit_export(payload: dict, background_tasks: BackgroundTasks):
    try:
        filepath = generate_executive_summary(payload)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate the PDF report. Ensure an audit has been run.",
        )

    background_tasks.add_task(remove_file, filepath)

    return FileResponse(
        path=filepath,
        filename="EquiGuard_Executive_Report.pdf",
        media_type="application/pdf",
    )

@app.get("/audit/history", tags=["Audit"], dependencies=[Depends(require_api_key)])
def audit_history():
    history = get_audit_history()
    return {"status": "success", "history": history}

@app.post("/audit/certificate", tags=["Audit"], dependencies=[Depends(require_api_key)])
def audit_certificate(payload: dict):
    """
    Generates a one-page EEOC Compliance Certificate PDF and returns it directly
    as bytes. Only succeeds if compliance_pass is True in the payload.
    Returns 400 if the model did not pass.
    """
    if not payload.get("compliance_pass", False):
        raise HTTPException(
            status_code=400,
            detail="Certificate can only be issued for models that passed the EEOC compliance audit.",
        )
    try:
        pdf_bytes = generate_certificate(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate compliance certificate: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="EquiGuard_EEOC_Certificate.pdf"'},
    )

@app.post("/audit/simulate", tags=["Audit"], dependencies=[Depends(require_api_key)])
def audit_simulate(payload: dict):
    """
    For each numeric feature, simulates dropping it and retraining to project
    the resulting EEOC fairness ratio and accuracy cost.
    """
    data_path     = payload.get("data_path",     "golden_demo_dataset.csv")
    target_col    = payload.get("target_col",    "loan_approved")
    protected_col = payload.get("protected_col", "race")

    try:
        results = simulate_mitigation(data_path, target_col, protected_col)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")

    return {"status": "success", "simulations": results}


@app.post("/audit/intersectional", tags=["Audit"], dependencies=[Depends(require_api_key)])
def audit_intersectional(payload: dict):
    """
    Auto-detects protected attribute columns (categorical / low-cardinality),
    runs an EEOC audit for each, and returns Pearson correlation heatmap data.
    """
    data_path  = payload.get("data_path",  "golden_demo_dataset.csv")
    target_col = payload.get("target_col", "loan_approved")

    try:
        result = run_intersectional_audit(data_path, target_col)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intersectional audit failed: {e}")

    return {"status": "success", **result}


@app.post("/audit/package", tags=["Audit"], dependencies=[Depends(require_api_key)])
def audit_package(payload: dict, background_tasks: BackgroundTasks):
    """
    Generates a full regulatory export ZIP containing:
      - EquiGuard_Executive_Report.pdf
      - EquiGuard_EEOC_Certificate.pdf
      - methodology.txt
      - audit_log.json
    Only available when compliance_pass is True.
    """
    if not payload.get("compliance_pass", False):
        raise HTTPException(
            status_code=400,
            detail="Regulatory package can only be issued for compliant models.",
        )

    temp_files = []
    try:
        # 1. Executive PDF
        report_path = generate_executive_summary(payload)
        temp_files.append(report_path)

        # 2. Certificate PDF
        cert_bytes = generate_certificate(payload)
        cert_fd, cert_path = tempfile.mkstemp(suffix=".pdf")
        os.close(cert_fd)
        with open(cert_path, "wb") as f:
            f.write(cert_bytes)
        temp_files.append(cert_path)

        # 3. Methodology text
        methodology = (
            "EquiGuard Audit Methodology\n"
            "===========================\n\n"
            "1. EEOC 4/5ths Rule (Disparate Impact Ratio)\n"
            "   The Equal Employment Opportunity Commission Uniform Guidelines (29 CFR § 1607)\n"
            "   require that the selection rate for any protected group be at least 4/5ths (80%)\n"
            "   of the rate for the group with the highest selection rate. EquiGuard computes\n"
            "   this as: ratio = unprivileged_selection_rate / privileged_selection_rate.\n"
            "   A ratio >= 0.80 is considered compliant.\n\n"
            "2. SHAP Feature Attribution\n"
            "   SHAP (SHapley Additive exPlanations) values quantify each feature's average\n"
            "   contribution to the model's predictions. EquiGuard uses SHAP LinearExplainer\n"
            "   on the trained LogisticRegression pipeline. Higher mean |SHAP| indicates\n"
            "   greater influence on outcomes — and greater risk of proxy bias.\n\n"
            "3. Proxy Variable Detection\n"
            "   EquiGuard applies hierarchical feature agglomeration (sklearn FeatureAgglomeration)\n"
            "   to cluster numeric features, then computes Pearson correlation between each\n"
            "   cluster representative and the protected attribute. Clusters with |r| >= 0.15\n"
            "   are flagged as potential proxy variables.\n\n"
            "4. Bias Mitigation\n"
            "   Flagged proxy variables are removed from the feature set. The model is\n"
            "   retrained on the remaining features and re-audited. Accuracy delta is\n"
            "   reported to document the fairness-accuracy trade-off.\n\n"
            "5. Legal Standard\n"
            "   US EEOC Uniform Guidelines on Employee Selection Procedures\n"
            "   29 CFR Part 1607 — https://www.ecfr.gov/current/title-29/part-1607\n"
        )
        meth_fd, meth_path = tempfile.mkstemp(suffix=".txt")
        os.close(meth_fd)
        with open(meth_path, "w") as f:
            f.write(methodology)
        temp_files.append(meth_path)

        # 4. Raw audit JSON
        json_fd, json_path = tempfile.mkstemp(suffix=".json")
        os.close(json_fd)
        with open(json_path, "w") as f:
            json.dump(payload, f, indent=2, default=str)
        temp_files.append(json_path)

        # 5. ZIP everything
        zip_fd, zip_path = tempfile.mkstemp(suffix=".zip")
        os.close(zip_fd)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(report_path,  "EquiGuard_Executive_Report.pdf")
            zf.write(cert_path,    "EquiGuard_EEOC_Certificate.pdf")
            zf.write(meth_path,    "methodology.txt")
            zf.write(json_path,    "audit_log.json")
        temp_files.append(zip_path)

    except Exception as e:
        for p in temp_files:
            remove_file(p)
        raise HTTPException(status_code=500, detail=f"Package generation failed: {e}")

    for p in temp_files[:-1]:  # clean everything except the zip (cleaned after response)
        background_tasks.add_task(remove_file, p)
    background_tasks.add_task(remove_file, zip_path)

    return FileResponse(
        path=zip_path,
        filename="EquiGuard_Regulatory_Package.zip",
        media_type="application/zip",
    )


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings["host"],
        port=settings["port"],
        reload=(settings["env"] == "development"),
    )