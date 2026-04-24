"""
audit_engine/model_registry.py
Defines multiple sklearn classifiers for multi-model Pareto comparison.
"""
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score

from audit_engine.compliance import run_audit

MODELS = {
    "Logistic Regression": LogisticRegression(random_state=42, max_iter=1000),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
    "Gradient Boosting": GradientBoostingClassifier(random_state=42),
    "Decision Tree": DecisionTreeClassifier(max_depth=5, random_state=42),
}


def run_comparison(data_path: str, target_col: str, protected_col: str) -> list:
    """
    Trains each model in MODELS on the dataset, runs an EEOC audit for each,
    and returns a list of result dicts for the Pareto chart.

    Preprocessing mirrors model_runner.py exactly:
    - LabelEncoder on target column   (handles string labels like yes/no/0/1)
    - LabelEncoder or median-binarize on protected column
    - select_dtypes(numeric) for feature matrix
    """
    df = pd.read_csv(data_path, sep=None, engine="python")

    # Drop rows where target or protected attribute is missing
    df = df.dropna(subset=[target_col, protected_col])

    # ── Encode target column ──────────────────────────────────────────────────
    df[target_col] = LabelEncoder().fit_transform(df[target_col])

    # ── Binarise / encode protected column ───────────────────────────────────
    if pd.api.types.is_numeric_dtype(df[protected_col]):
        if df[protected_col].nunique() > 2:
            median_val = df[protected_col].median()
            df[protected_col] = (df[protected_col] >= median_val).astype(int)
    else:
        df[protected_col] = LabelEncoder().fit_transform(df[protected_col])

    # ── Build feature matrix (numeric only, excluding target & protected) ─────
    cols_to_drop = [c for c in [target_col, protected_col] if c in df.columns]
    X = df.drop(columns=cols_to_drop).select_dtypes(include=[np.number])
    y = df[target_col]
    protected = df[protected_col]

    X_train, X_test, y_train, y_test, p_train, p_test = train_test_split(
        X, y, protected, test_size=0.2, random_state=42
    )

    results = []
    for model_name, classifier in MODELS.items():
        try:
            pipeline = Pipeline([
                ("imputer",    SimpleImputer(strategy="median")),
                ("scaler",     StandardScaler()),
                ("classifier", classifier),
            ])
            pipeline.fit(X_train, y_train)
            predictions = pipeline.predict(X_test)
            accuracy    = float(accuracy_score(y_test, predictions))

            audit = run_audit(
                model=pipeline,
                X_test=X_test,
                predictions=predictions,
                protected_attributes=p_test.values,
            )

            results.append({
                "model_name":         model_name,
                "accuracy":           round(accuracy, 4),
                "fairness_ratio":     round(audit["fairness_ratio"], 4),
                "compliance_pass":    audit["compliance_pass"],
                "top_biased_feature": audit["top_biased_feature"],
                "group_a_rate":       round(audit.get("group_a_rate", 0.0), 4),
                "group_b_rate":       round(audit.get("group_b_rate", 0.0), 4),
            })
        except Exception as e:
            results.append({
                "model_name":         model_name,
                "accuracy":           0.0,
                "fairness_ratio":     0.0,
                "compliance_pass":    False,
                "top_biased_feature": f"Error: {e}",
                "group_a_rate":       0.0,
                "group_b_rate":       0.0,
            })

    # Sort by fairness_ratio descending so the most compliant model is first
    results.sort(key=lambda r: r["fairness_ratio"], reverse=True)
    return results
