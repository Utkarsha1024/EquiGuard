import os
import json
import zipfile
import tempfile
import pandas as pd
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse

from backend.dependencies import require_api_key
from backend.config import get_settings
from backend.utils import remove_file
from backend.alerting import fire_audit_alert
from audit_engine.model_runner import run_model
from audit_engine.compliance import run_audit
from audit_engine.proxy_hunter import find_proxies
from audit_engine.mitigation import mitigate_and_retrain
from audit_engine.report_gen import generate_executive_summary
from audit_engine.certificate import generate_certificate
from audit_engine.simulator import simulate_mitigation
from audit_engine.intersectional import run_intersectional_audit
from audit_engine.model_registry import run_comparison
from database.db import log_audit_run, get_audit_history

router = APIRouter(tags=["Audit"])

@router.post("/audit/model", dependencies=[Depends(require_api_key)])
def audit_model(payload: dict = None):
    payload = payload or {}
    data_path     = payload.get("data_path",     "data/golden_demo_dataset.csv")
    target_col    = payload.get("target_col",    "loan_approved")
    protected_col = payload.get("protected_col", "race")

    result = run_model(data_path, target_col, protected_col)
    return {
        "status":      "success",
        "accuracy":    result["accuracy"],
        "predictions": result["predictions"],
    }

@router.post("/audit/compliance", dependencies=[Depends(require_api_key)])
def audit_compliance(payload: dict = None, background_tasks: BackgroundTasks = None):
    payload = payload or {}
    data_path     = payload.get("data_path",     "data/golden_demo_dataset.csv")
    file_name     = payload.get("file_name",     "golden_demo_dataset.csv")
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
        file_name=file_name,
    )

    # Fire webhook alert on FAIL
    if not audit_result["compliance_pass"] and background_tasks is not None:
        settings = get_settings()
        background_tasks.add_task(fire_audit_alert, audit_result, settings)

    response = {
        "compliance_pass":        audit_result["compliance_pass"],
        "fairness_ratio":         audit_result["fairness_ratio"],
        "top_biased_feature":     audit_result["top_biased_feature"],
        "group_a_rate":           audit_result.get("group_a_rate", 0.0),
        "group_b_rate":           audit_result.get("group_b_rate", 0.0),
        "shap_summary":           audit_result.get("shap_summary", {}),
    }
    if "equal_opportunity_diff" in audit_result:
        response["equal_opportunity_diff"] = audit_result["equal_opportunity_diff"]
    if "avg_odds_diff" in audit_result:
        response["avg_odds_diff"] = audit_result["avg_odds_diff"]
    return response

@router.post("/audit/preprocess", dependencies=[Depends(require_api_key)])
def audit_preprocess(payload: dict):
    data_path     = payload.get("data_path",     "data/golden_demo_dataset.csv")
    target_col    = payload.get("target_col",    "loan_approved")
    protected_col = payload.get("protected_col", "race")

    df      = pd.read_csv(data_path)
    flagged = find_proxies(df, protected_col, target_col)

    return {
        "proxies_detected": len(flagged) > 0,
        "flagged_columns":  flagged,
    }

@router.post("/audit/mitigate", dependencies=[Depends(require_api_key)])
def audit_mitigate(payload: dict):
    flagged_columns = payload.get("flagged_columns", [])
    data_path       = payload.get("data_path",       "data/golden_demo_dataset.csv")
    file_name       = payload.get("file_name",       "golden_demo_dataset.csv")
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
        file_name=file_name,
    )

    response = {
        "status":                 "success",
        "compliance_pass":        audit_result["compliance_pass"],
        "fairness_ratio":         audit_result["fairness_ratio"],
        "top_biased_feature":     audit_result["top_biased_feature"],
        "group_a_rate":           audit_result.get("group_a_rate", 0.0),
        "group_b_rate":           audit_result.get("group_b_rate", 0.0),
        "shap_summary":           audit_result.get("shap_summary", {}),
        "accuracy":               result["accuracy"],
    }
    if "equal_opportunity_diff" in audit_result:
        response["equal_opportunity_diff"] = audit_result["equal_opportunity_diff"]
    if "avg_odds_diff" in audit_result:
        response["avg_odds_diff"] = audit_result["avg_odds_diff"]
    return response

@router.post("/audit/export", dependencies=[Depends(require_api_key)])
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

@router.get("/audit/history", dependencies=[Depends(require_api_key)])
def audit_history():
    history = get_audit_history()
    return {"status": "success", "history": history}

@router.post("/audit/certificate", dependencies=[Depends(require_api_key)])
def audit_certificate(payload: dict):
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

@router.post("/audit/simulate", dependencies=[Depends(require_api_key)])
def audit_simulate(payload: dict):
    data_path     = payload.get("data_path",     "data/golden_demo_dataset.csv")
    target_col    = payload.get("target_col",    "loan_approved")
    protected_col = payload.get("protected_col", "race")

    try:
        results = simulate_mitigation(data_path, target_col, protected_col)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")

    return {"status": "success", "simulations": results}

@router.post("/audit/intersectional", dependencies=[Depends(require_api_key)])
def audit_intersectional(payload: dict):
    data_path  = payload.get("data_path",  "data/golden_demo_dataset.csv")
    target_col = payload.get("target_col", "loan_approved")

    try:
        result = run_intersectional_audit(data_path, target_col)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intersectional audit failed: {e}")

    return {"status": "success", **result}

@router.post("/audit/package", dependencies=[Depends(require_api_key)])
def audit_package(payload: dict, background_tasks: BackgroundTasks):
    if not payload.get("compliance_pass", False):
        raise HTTPException(
            status_code=400,
            detail="Regulatory package can only be issued for compliant models.",
        )

    temp_files = []
    try:
        report_path = generate_executive_summary(payload)
        temp_files.append(report_path)

        cert_bytes = generate_certificate(payload)
        cert_fd, cert_path = tempfile.mkstemp(suffix=".pdf")
        os.close(cert_fd)
        with open(cert_path, "wb") as f:
            f.write(cert_bytes)
        temp_files.append(cert_path)

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

        json_fd, json_path = tempfile.mkstemp(suffix=".json")
        os.close(json_fd)
        with open(json_path, "w") as f:
            json.dump(payload, f, indent=2, default=str)
        temp_files.append(json_path)

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

    for p in temp_files[:-1]:
        background_tasks.add_task(remove_file, p)
    background_tasks.add_task(remove_file, zip_path)

    return FileResponse(
        path=zip_path,
        filename="EquiGuard_Regulatory_Package.zip",
        media_type="application/zip",
    )


# ── Multi-model Pareto Comparison ────────────────────────────────────────────────
@router.post("/audit/compare", dependencies=[Depends(require_api_key)])
def audit_compare(payload: dict = None):
    """
    Trains 4 classifier families on the dataset and returns per-model
    accuracy and EEOC audit results for a Pareto comparison chart.
    """
    payload       = payload or {}
    data_path     = payload.get("data_path",     "data/golden_demo_dataset.csv")
    target_col    = payload.get("target_col",    "loan_approved")
    protected_col = payload.get("protected_col", "race")

    try:
        results = run_comparison(data_path, target_col, protected_col)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {e}")


# ── Gemini Pre-flight Dataset Check ──────────────────────────────────────────────

# Heuristic proxy flag words (used when Gemini is unavailable)
_PROXY_WORDS = {
    "zip", "zipcode", "zip_code", "postal", "postcode",
    "age", "dob", "birth", "born", "year",
    "race", "ethnic", "gender", "sex", "religion",
    "income", "salary", "wage", "credit", "score",
}

@router.post("/audit/preflight", dependencies=[Depends(require_api_key)])
def audit_preflight(payload: dict = None):
    """
    Runs a pre-flight dataset check before the main audit.
    Uses Gemini to analyse column statistics and flag risks.
    Falls back to keyword heuristics when Gemini is not configured.
    """
    payload   = payload or {}
    data_path = payload.get("data_path", "data/golden_demo_dataset.csv")

    try:
        df = pd.read_csv(data_path, sep=None, engine="python", nrows=500)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read dataset: {e}")

    # Build column statistics for the prompt
    col_stats = []
    for col in df.columns:
        dtype  = str(df[col].dtype)
        n_unique = int(df[col].nunique())
        top_vals = df[col].value_counts().head(5).to_dict()
        col_stats.append({
            "column":   col,
            "dtype":    dtype,
            "n_unique": n_unique,
            "top_values": {str(k): int(v) for k, v in top_vals.items()},
        })

    settings   = get_settings()
    gemini_key = settings.get("gemini_api_key", "")

    if gemini_key:
        from google import genai as _genai_sdk
        _client = _genai_sdk.Client(api_key=gemini_key)
        _fallback_models = ["gemini-3.0-flash", "gemini-2.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]
        for _model in _fallback_models:
            try:
                resp = _client.models.generate_content(
                    model=_model,
                    contents=prompt,
                )
                raw = resp.text.strip()
                if raw.startswith("```"):
                    raw = "\n".join(raw.split("\n")[1:])
                if raw.endswith("```"):
                    raw = raw.rsplit("```", 1)[0]
                data = json.loads(raw)
                data["engine"] = _model
                data["columns_checked"] = len(df.columns)
                data["rows_sampled"]    = len(df)
                return data
            except Exception as _e:
                _err = str(_e)
                if any(c in _err for c in ("429", "RESOURCE_EXHAUSTED", "404", "NOT_FOUND", "503", "UNAVAILABLE")):
                    continue  # try next model
                break  # non-quota error, give up

    # Heuristic fallback
    high_risk   = [c for c in df.columns if any(w in c.lower() for w in _PROXY_WORDS)]
    proxy_cands = [c for c in df.columns if df[c].nunique() < 10 and df[c].dtype == object]
    risk_level  = "HIGH" if len(high_risk) >= 3 else ("MEDIUM" if high_risk else "LOW")
    return {
        "overall_risk":     risk_level,
        "high_risk_columns": high_risk,
        "proxy_candidates": proxy_cands,
        "summary": (
            f"Heuristic scan detected {len(high_risk)} potentially sensitive column(s): "
            f"{', '.join(high_risk) if high_risk else 'none'}. "
            "Set GEMINI_API_KEY for an AI-powered analysis."
        ),
        "engine":          "heuristic",
        "columns_checked": len(df.columns),
        "rows_sampled":    len(df),
    }
