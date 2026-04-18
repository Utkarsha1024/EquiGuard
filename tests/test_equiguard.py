"""
EquiGuard Test Suite
====================
Tests for:
  - audit_engine/compliance.py  — EEOC fairness ratio + SHAP
  - audit_engine/proxy_hunter.py — proxy variable detection
  - audit_engine/model_runner.py — model training pipeline
  - audit_engine/mitigation.py  — bias mitigation + retraining
  - backend/main.py             — FastAPI endpoints (via TestClient)

Run with:
    pytest tests/ -v
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

# ── Make sure project root is on path ─────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Set a dummy API key before importing the app ──────────────────────────────
os.environ["EQUIGUARD_API_KEY"] = "test-secret-key-for-ci"
os.environ["ENV"] = "testing"

# ═════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def simple_pipeline():
    """
    A minimal trained sklearn pipeline (imputer → scaler → logistic regression)
    that mirrors the real EquiGuard pipeline structure exactly.
    """
    np.random.seed(42)
    X = pd.DataFrame({
        "income":      np.random.normal(50000, 15000, 200),
        "credit_score": np.random.normal(650, 80, 200),
        "age":         np.random.randint(22, 65, 200).astype(float),
    })
    y = (X["income"] > 50000).astype(int)

    pipeline = Pipeline([
        ("imputer",    SimpleImputer(strategy="median")),
        ("scaler",     StandardScaler()),
        ("classifier", LogisticRegression(random_state=42)),
    ])
    pipeline.fit(X, y)
    return pipeline, X, y


@pytest.fixture
def fair_audit_inputs():
    """
    Predictions + protected attributes engineered so fairness_ratio >= 0.8
    (group 0 rate = 0.8, group 1 rate = 1.0  →  ratio = 0.80).
    """
    protected = [0] * 10 + [1] * 10
    # group 0: 8 positive / 10  →  rate = 0.8
    # group 1: 10 positive / 10 →  rate = 1.0
    predictions = [1] * 8 + [0] * 2 + [1] * 10
    return predictions, protected


@pytest.fixture
def biased_audit_inputs():
    """
    Predictions + protected attributes engineered so fairness_ratio < 0.8
    (group 0 rate = 0.3, group 1 rate = 1.0  →  ratio = 0.30).
    """
    protected = [0] * 10 + [1] * 10
    predictions = [1] * 3 + [0] * 7 + [1] * 10
    return predictions, protected


@pytest.fixture
def demo_dataframe():
    """
    Synthetic dataset matching the golden_demo_dataset.csv schema
    (loan_approved + race + numeric features).
    """
    np.random.seed(0)
    n = 300
    race   = np.random.choice(["White", "Black", "Asian"], n)
    income = np.random.normal(55000, 12000, n)
    credit = np.random.normal(660, 70, n)
    age    = np.random.randint(25, 60, n).astype(float)
    approved = ((income > 50000) & (credit > 640)).astype(int)

    return pd.DataFrame({
        "race":         race,
        "income":       income,
        "credit_score": credit,
        "age":          age,
        "loan_approved": approved,
    })


@pytest.fixture
def tmp_csv(demo_dataframe, tmp_path):
    """Write demo_dataframe to a temp CSV and return its path."""
    path = str(tmp_path / "test_dataset.csv")
    demo_dataframe.to_csv(path, index=False)
    return path


# ═════════════════════════════════════════════════════════════════════════════
# 1. COMPLIANCE — EEOC FAIRNESS RATIO
# ═════════════════════════════════════════════════════════════════════════════

class TestComplianceFairnessRatio:

    def test_fair_predictions_pass(self, simple_pipeline, fair_audit_inputs):
        """fairness_ratio >= 0.8 should set compliance_pass = True."""
        from audit_engine.compliance import run_audit
        pipeline, X, _ = simple_pipeline
        predictions, protected = fair_audit_inputs

        result = run_audit(
            model=pipeline,
            X_test=X.iloc[:20],
            predictions=predictions,
            protected_attributes=protected,
        )
        assert result["compliance_pass"] is True

    def test_biased_predictions_fail(self, simple_pipeline, biased_audit_inputs):
        """fairness_ratio < 0.8 should set compliance_pass = False."""
        from audit_engine.compliance import run_audit
        pipeline, X, _ = simple_pipeline
        predictions, protected = biased_audit_inputs

        result = run_audit(
            model=pipeline,
            X_test=X.iloc[:20],
            predictions=predictions,
            protected_attributes=protected,
        )
        assert result["compliance_pass"] is False

    def test_fairness_ratio_is_float_between_0_and_1(self, simple_pipeline, biased_audit_inputs):
        """fairness_ratio must be a float in [0.0, 1.0]."""
        from audit_engine.compliance import run_audit
        pipeline, X, _ = simple_pipeline
        predictions, protected = biased_audit_inputs

        result = run_audit(
            model=pipeline,
            X_test=X.iloc[:20],
            predictions=predictions,
            protected_attributes=protected,
        )
        ratio = result["fairness_ratio"]
        assert isinstance(ratio, float)
        assert 0.0 <= ratio <= 1.0

    def test_eeoc_threshold_is_exactly_0_8(self, simple_pipeline):
        """
        Ratio exactly at 0.80 must PASS (≥ 0.8 rule).
        group 0: 4/5 = 0.8, group 1: 5/5 = 1.0 → ratio = 0.8
        """
        from audit_engine.compliance import run_audit
        pipeline, X, _ = simple_pipeline

        predictions = [1, 1, 1, 1, 0, 1, 1, 1, 1, 1]
        protected   = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]

        result = run_audit(
            model=pipeline,
            X_test=X.iloc[:10],
            predictions=predictions,
            protected_attributes=protected,
        )
        assert result["compliance_pass"] is True
        assert abs(result["fairness_ratio"] - 0.8) < 1e-6

    def test_single_group_returns_ratio_1(self, simple_pipeline):
        """If only one demographic group exists, ratio should default to 1.0."""
        from audit_engine.compliance import run_audit
        pipeline, X, _ = simple_pipeline

        predictions = [1, 0, 1, 0, 1]
        protected   = [0, 0, 0, 0, 0]   # only group 0

        result = run_audit(
            model=pipeline,
            X_test=X.iloc[:5],
            predictions=predictions,
            protected_attributes=protected,
        )
        assert result["fairness_ratio"] == 1.0

    def test_result_contains_required_keys(self, simple_pipeline, fair_audit_inputs):
        """Response dict must contain all expected keys."""
        from audit_engine.compliance import run_audit
        pipeline, X, _ = simple_pipeline
        predictions, protected = fair_audit_inputs

        result = run_audit(
            model=pipeline,
            X_test=X.iloc[:20],
            predictions=predictions,
            protected_attributes=protected,
        )
        for key in ["compliance_pass", "fairness_ratio", "top_biased_feature",
                    "group_a_rate", "group_b_rate", "shap_summary"]:
            assert key in result, f"Missing key: {key}"


# ═════════════════════════════════════════════════════════════════════════════
# 2. COMPLIANCE — SHAP EXPLAINABILITY
# ═════════════════════════════════════════════════════════════════════════════

class TestSHAPExplainability:

    def test_shap_summary_is_dict(self, simple_pipeline, fair_audit_inputs):
        """shap_summary must be a dict."""
        from audit_engine.compliance import run_audit
        pipeline, X, _ = simple_pipeline
        predictions, protected = fair_audit_inputs

        result = run_audit(
            model=pipeline,
            X_test=X.iloc[:20],
            predictions=predictions,
            protected_attributes=protected,
        )
        assert isinstance(result["shap_summary"], dict)

    def test_shap_summary_max_5_features(self, simple_pipeline, fair_audit_inputs):
        """shap_summary must contain at most 5 features (top-5 logic)."""
        from audit_engine.compliance import run_audit
        pipeline, X, _ = simple_pipeline
        predictions, protected = fair_audit_inputs

        result = run_audit(
            model=pipeline,
            X_test=X.iloc[:20],
            predictions=predictions,
            protected_attributes=protected,
        )
        assert len(result["shap_summary"]) <= 5

    def test_shap_values_are_non_negative(self, simple_pipeline, fair_audit_inputs):
        """All SHAP values are mean absolute — must be >= 0."""
        from audit_engine.compliance import run_audit
        pipeline, X, _ = simple_pipeline
        predictions, protected = fair_audit_inputs

        result = run_audit(
            model=pipeline,
            X_test=X.iloc[:20],
            predictions=predictions,
            protected_attributes=protected,
        )
        for feature, val in result["shap_summary"].items():
            assert val >= 0.0, f"Negative SHAP value for {feature}: {val}"

    def test_top_biased_feature_is_in_shap_summary(self, simple_pipeline, fair_audit_inputs):
        """top_biased_feature must be present in shap_summary."""
        from audit_engine.compliance import run_audit
        pipeline, X, _ = simple_pipeline
        predictions, protected = fair_audit_inputs

        result = run_audit(
            model=pipeline,
            X_test=X.iloc[:20],
            predictions=predictions,
            protected_attributes=protected,
        )
        if result["shap_summary"]:   # only if SHAP succeeded
            assert result["top_biased_feature"] in result["shap_summary"]


# ═════════════════════════════════════════════════════════════════════════════
# 3. PROXY HUNTER
# ═════════════════════════════════════════════════════════════════════════════

class TestProxyHunter:

    def test_returns_list(self, demo_dataframe):
        """find_proxies must always return a list."""
        from audit_engine.proxy_hunter import find_proxies
        result = find_proxies(demo_dataframe, "race", "loan_approved")
        assert isinstance(result, list)

    def test_no_false_positives_on_independent_data(self):
        """
        Completely independent features should not be flagged as proxies.
        """
        from audit_engine.proxy_hunter import find_proxies
        np.random.seed(99)
        n = 200
        df = pd.DataFrame({
            "protected":  np.random.randint(0, 2, n),
            "feature_a":  np.random.normal(0, 1, n),   # independent
            "feature_b":  np.random.normal(0, 1, n),   # independent
            "target":     np.random.randint(0, 2, n),
        })
        flagged = find_proxies(df, "protected", "target", correlation_threshold=0.9)
        assert len(flagged) == 0

    def test_detects_obvious_proxy(self):
        """
        A feature that is a near-copy of the protected attribute
        should be flagged.
        """
        from audit_engine.proxy_hunter import find_proxies
        np.random.seed(7)
        n = 300
        protected = np.random.randint(0, 2, n)
        df = pd.DataFrame({
            "protected":   protected,
            "proxy_col":   protected + np.random.normal(0, 0.05, n),  # near-copy
            "unrelated":   np.random.normal(0, 1, n),
            "target":      np.random.randint(0, 2, n),
        })
        flagged = find_proxies(df, "protected", "target", correlation_threshold=0.15)
        assert "proxy_col" in flagged

    def test_missing_protected_col_returns_empty(self, demo_dataframe):
        """If the protected column doesn't exist, return empty list gracefully."""
        from audit_engine.proxy_hunter import find_proxies
        result = find_proxies(demo_dataframe, "nonexistent_col", "loan_approved")
        assert result == []

    def test_too_few_features_returns_empty(self):
        """With fewer than 2 numeric features, return empty list."""
        from audit_engine.proxy_hunter import find_proxies
        df = pd.DataFrame({
            "protected": [0, 1, 0, 1],
            "target":    [1, 0, 1, 0],
        })
        result = find_proxies(df, "protected", "target")
        assert result == []


# ═════════════════════════════════════════════════════════════════════════════
# 4. MODEL RUNNER
# ═════════════════════════════════════════════════════════════════════════════

class TestModelRunner:

    def test_returns_required_keys(self, tmp_csv):
        """run_model must return all expected keys."""
        from audit_engine.model_runner import run_model
        result = run_model(tmp_csv, "loan_approved", "race")
        for key in ["predictions", "accuracy", "model", "X_test", "protected_attributes"]:
            assert key in result

    def test_accuracy_is_float_between_0_and_1(self, tmp_csv):
        """Accuracy must be a float in [0.0, 1.0]."""
        from audit_engine.model_runner import run_model
        result = run_model(tmp_csv, "loan_approved", "race")
        assert isinstance(result["accuracy"], float)
        assert 0.0 <= result["accuracy"] <= 1.0

    def test_predictions_are_binary(self, tmp_csv):
        """All predictions must be 0 or 1."""
        from audit_engine.model_runner import run_model
        result = run_model(tmp_csv, "loan_approved", "race")
        assert set(result["predictions"]).issubset({0, 1})

    def test_model_is_sklearn_pipeline(self, tmp_csv):
        """Returned model must be a sklearn Pipeline."""
        from audit_engine.model_runner import run_model
        result = run_model(tmp_csv, "loan_approved", "race")
        assert isinstance(result["model"], Pipeline)

    def test_predictions_length_matches_test_set(self, tmp_csv):
        """len(predictions) must equal len(X_test)."""
        from audit_engine.model_runner import run_model
        result = run_model(tmp_csv, "loan_approved", "race")
        assert len(result["predictions"]) == len(result["X_test"])


# ═════════════════════════════════════════════════════════════════════════════
# 5. MITIGATION — BIAS REDUCTION
# ═════════════════════════════════════════════════════════════════════════════

class TestMitigation:

    def test_mitigation_removes_flagged_columns(self, tmp_csv):
        """After mitigation, flagged columns must not appear in X_test."""
        from audit_engine.mitigation import mitigate_and_retrain
        # income is a real feature in our demo CSV
        result = mitigate_and_retrain(
            flagged_columns=["income"],
            data_path=tmp_csv,
            target_col="loan_approved",
            protected_col="race",
        )
        assert "income" not in result["X_test"].columns

    def test_mitigation_returns_required_keys(self, tmp_csv):
        """mitigate_and_retrain must return all expected keys."""
        from audit_engine.mitigation import mitigate_and_retrain
        result = mitigate_and_retrain(
            flagged_columns=["income"],
            data_path=tmp_csv,
            target_col="loan_approved",
            protected_col="race",
        )
        for key in ["model", "predictions", "X_test", "protected_attributes", "accuracy"]:
            assert key in result

    def test_mitigation_accuracy_is_valid(self, tmp_csv):
        """Accuracy after mitigation must be a float in [0.0, 1.0]."""
        from audit_engine.mitigation import mitigate_and_retrain
        result = mitigate_and_retrain(
            flagged_columns=["income"],
            data_path=tmp_csv,
            target_col="loan_approved",
            protected_col="race",
        )
        assert 0.0 <= result["accuracy"] <= 1.0


# ═════════════════════════════════════════════════════════════════════════════
# 6. FASTAPI ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

class TestAPI:

    @pytest.fixture(autouse=True)
    def client(self):
        """Create a FastAPI TestClient with the API key pre-set."""
        from fastapi.testclient import TestClient
        from backend.main import app
        self.client = TestClient(app)
        self.headers = {"X-API-Key": "test-secret-key-for-ci"}

    def test_root_is_public(self):
        """GET / should return 200 with no auth header."""
        resp = self.client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "Active"

    def test_health_is_public(self):
        """GET /health should return 200 with no auth header."""
        resp = self.client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_compliance_requires_auth(self):
        """POST /audit/compliance without key must return 403."""
        resp = self.client.post("/audit/compliance", json={})
        assert resp.status_code == 403

    def test_preprocess_requires_auth(self):
        """POST /audit/preprocess without key must return 403."""
        resp = self.client.post("/audit/preprocess", json={
            "data_path": "golden_demo_dataset.csv",
            "target_col": "loan_approved",
            "protected_col": "race",
        })
        assert resp.status_code == 403

    def test_history_requires_auth(self):
        """GET /audit/history without key must return 403."""
        resp = self.client.get("/audit/history")
        assert resp.status_code == 403

    def test_wrong_api_key_returns_403(self):
        """A wrong API key must return 403, not 200."""
        resp = self.client.get("/audit/history", headers={"X-API-Key": "wrong-key"})
        assert resp.status_code == 403

    def test_history_with_valid_key(self):
        """GET /audit/history with correct key must return 200."""
        resp = self.client.get("/audit/history", headers=self.headers)
        assert resp.status_code == 200
        assert "history" in resp.json()

    def test_compliance_response_shape(self, tmp_csv):
        """
        POST /audit/compliance with valid payload + correct key
        must return all required fields.
        """
        resp = self.client.post(
            "/audit/compliance",
            json={
                "data_path":      tmp_csv,
                "target_col":     "loan_approved",
                "protected_col":  "race",
            },
            headers=self.headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        for key in ["compliance_pass", "fairness_ratio",
                    "top_biased_feature", "shap_summary"]:
            assert key in data

    def test_mitigate_requires_flagged_columns(self, tmp_csv):
        """POST /audit/mitigate with empty flagged_columns must return 400."""
        resp = self.client.post(
            "/audit/mitigate",
            json={
                "data_path":       tmp_csv,
                "target_col":      "loan_approved",
                "protected_col":   "race",
                "flagged_columns": [],
            },
            headers=self.headers,
        )
        assert resp.status_code == 400
