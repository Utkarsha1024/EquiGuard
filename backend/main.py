import os
import sys
from functools import lru_cache

# Add the project root to sys.path to resolve 'audit_engine' and 'database' imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import FileResponse
from starlette.status import HTTP_403_FORBIDDEN

from audit_engine.model_runner import run_model
from audit_engine.compliance import run_audit
from audit_engine.proxy_hunter import find_proxies
from audit_engine.mitigation import mitigate_and_retrain
from audit_engine.report_gen import generate_executive_summary
from database.db import log_audit_run, get_audit_history

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