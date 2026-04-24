"""
audit_engine/intersectional.py
================================
Intersectional Audit Engine.

Detects all candidate protected attributes (categorical / low-cardinality
integer columns with 2–10 unique values), runs an EEOC 4/5ths audit for
each, and computes Pearson correlations between numeric features and every
detected protected column.
"""
import pandas as pd
import numpy as np

from audit_engine.model_runner import run_model
from audit_engine.compliance import run_audit


def run_intersectional_audit(data_path: str, target_col: str) -> dict:
    """
    Returns:
    {
        "protected_columns": ["race", "gender", ...],
        "ratios": {"race": 0.71, "gender": 0.85, ...},
        "correlations": {
            "income": {"race": 0.34, "gender": 0.12, ...},
            ...
        }
    }
    """
    try:
        df = pd.read_csv(data_path)
    except Exception:
        return {"protected_columns": [], "ratios": {}, "correlations": {}}

    # ── Detect candidate protected columns ────────────────────────────────────
    protected_candidates: list[str] = []
    for col in df.columns:
        if col == target_col:
            continue
        n_unique = df[col].nunique(dropna=True)
        if n_unique < 2 or n_unique > 10:
            continue
        if df[col].dtype == "object" or df[col].dtype.name == "category" or pd.api.types.is_string_dtype(df[col]):
            protected_candidates.append(col)
        elif pd.api.types.is_integer_dtype(df[col]):
            protected_candidates.append(col)

    if not protected_candidates:
        return {"protected_columns": [], "ratios": {}, "correlations": {}}

    # ── EEOC ratio per protected column ───────────────────────────────────────
    ratios: dict = {}
    for prot_col in protected_candidates:
        try:
            result = run_model(data_path, target_col, prot_col)
            audit = run_audit(
                model=result["model"],
                X_test=result["X_test"],
                predictions=result["predictions"],
                protected_attributes=result["protected_attributes"],
            )
            ratios[prot_col] = round(audit["fairness_ratio"], 4)
        except Exception:
            ratios[prot_col] = None

    # ── Pearson correlations: numeric features × protected columns ─────────────
    safe_drop = [c for c in [target_col] + protected_candidates if c in df.columns]
    numeric_feats = (
        df.drop(columns=safe_drop, errors="ignore")
        .select_dtypes(include=[np.number])
        .columns.tolist()
    )

    correlations: dict = {}
    for feat in numeric_feats:
        correlations[feat] = {}
        feat_vals = pd.to_numeric(df[feat], errors="coerce")
        feat_vals = feat_vals.fillna(feat_vals.median())
        for prot_col in protected_candidates:
            try:
                prot_series = df[prot_col]
                if prot_series.dtype == "object" or prot_series.dtype.name == "category" or pd.api.types.is_string_dtype(prot_series):
                    prot_numeric = prot_series.astype("category").cat.codes.astype(float)
                else:
                    prot_numeric = prot_series.astype(float)
                prot_numeric = prot_numeric.fillna(prot_numeric.median())
                if np.std(feat_vals) > 0 and np.std(prot_numeric) > 0:
                    corr = float(np.corrcoef(feat_vals, prot_numeric)[0, 1])
                    correlations[feat][prot_col] = round(abs(corr), 4)
                else:
                    correlations[feat][prot_col] = 0.0
            except Exception:
                correlations[feat][prot_col] = 0.0

    return {
        "protected_columns": protected_candidates,
        "ratios": ratios,
        "correlations": correlations,
    }
