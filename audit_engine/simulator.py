"""
audit_engine/simulator.py
=========================
What-If Mitigation Simulator.

For each numeric feature in the dataset, simulates the effect of dropping
that single feature and retraining — projecting the resulting EEOC fairness
ratio and accuracy cost versus the baseline model.
"""
import pandas as pd
import numpy as np

from audit_engine.model_runner import run_model
from audit_engine.mitigation import mitigate_and_retrain
from audit_engine.compliance import run_audit


def simulate_mitigation(data_path: str, target_col: str, protected_col: str) -> list:
    """
    Returns list sorted by projected_ratio descending:
    [
        {
            "feature": str,
            "projected_ratio": float,
            "accuracy_after": float,
            "accuracy_delta": float,   # accuracy_after - baseline_accuracy
            "recommendation": "drop" | "keep"
        },
        ...
    ]
    Handles per-feature exceptions gracefully (skips that feature).
    """
    # ── Baseline run ──────────────────────────────────────────────────────────
    try:
        baseline = run_model(data_path, target_col, protected_col)
        baseline_audit = run_audit(
            model=baseline["model"],
            X_test=baseline["X_test"],
            predictions=baseline["predictions"],
            protected_attributes=baseline["protected_attributes"],
        )
        baseline_accuracy = baseline["accuracy"]
        baseline_ratio = baseline_audit["fairness_ratio"]
    except Exception:
        return []

    # ── Feature list ──────────────────────────────────────────────────────────
    try:
        df = pd.read_csv(data_path)
        df = df.dropna(subset=[target_col, protected_col])
        cols_to_drop = [c for c in [target_col, protected_col] if c in df.columns]
        numeric_features = (
            df.drop(columns=cols_to_drop)
            .select_dtypes(include=[np.number])
            .columns.tolist()
        )
    except Exception:
        return []

    results = []
    for feature in numeric_features:
        try:
            mit = mitigate_and_retrain([feature], data_path, target_col, protected_col)
            mit_audit = run_audit(
                model=mit["model"],
                X_test=mit["X_test"],
                predictions=mit["predictions"],
                protected_attributes=mit["protected_attributes"],
            )
            projected_ratio = mit_audit["fairness_ratio"]
            accuracy_after = mit["accuracy"]
            accuracy_delta = round(accuracy_after - baseline_accuracy, 4)
            ratio_improvement = projected_ratio - baseline_ratio
            recommendation = "drop" if ratio_improvement >= 0.05 else "keep"
            results.append({
                "feature": feature,
                "projected_ratio": round(projected_ratio, 4),
                "accuracy_after": round(accuracy_after, 4),
                "accuracy_delta": accuracy_delta,
                "recommendation": recommendation,
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["projected_ratio"], reverse=True)
    return results
