import pandas as pd
import numpy as np
import shap
import logging
import warnings

logger = logging.getLogger(__name__)


def run_audit(model, X_test, predictions, protected_attributes):
    """
    Runs the EEOC 4/5ths compliance check and SHAP explainability analysis.

    Uses IBM aif360 for disparate impact, equal opportunity difference, and
    average odds difference when available. Falls back to manual pandas
    calculation if aif360 fails for any reason.
    """
    # ── 1. Compute selection rates manually (always available as fallback) ──────
    df_eval = pd.DataFrame({'protected': protected_attributes, 'prediction': predictions})
    selection_rates = df_eval.groupby('protected')['prediction'].mean()

    group_b_rate = float(selection_rates.get(0, 0.0))
    group_a_rate = float(selection_rates.get(1, 0.0))

    if group_a_rate > 0:
        manual_fairness_ratio = group_b_rate / group_a_rate
    else:
        manual_fairness_ratio = 1.0

    fairness_ratio = manual_fairness_ratio
    equal_opportunity_diff = None
    avg_odds_diff = None

    # ── 2. aif360 — try to use it; fall back gracefully ──────────────────────────
    try:
        import logging
        root_logger = logging.getLogger()
        old_level = root_logger.level
        root_logger.setLevel(logging.ERROR)
        try:
            from aif360.datasets import BinaryLabelDataset
            from aif360.metrics import ClassificationMetric
        finally:
            root_logger.setLevel(old_level)

        # Cast predictions to float — aif360 stores labels as float64 internally;
        # passing int labels causes the 'labels do not match' validation error.
        preds_float = [float(p) for p in predictions]
        df_aif = pd.DataFrame({
            'protected': protected_attributes,
            'prediction': preds_float,
            'label': preds_float,
        })
        # Ensure the label column is explicitly float64 (avoids int/float type mismatch)
        df_aif['label'] = df_aif['label'].astype(float)

        dataset_pred = BinaryLabelDataset(
            df=df_aif,
            label_names=['label'],
            protected_attribute_names=['protected'],
            favorable_label=1.0,
            unfavorable_label=0.0,
        )

        # Reference dataset: assume all positive outcomes (ideal baseline)
        df_ref = df_aif.copy()
        df_ref['label'] = 1.0
        dataset_ref = BinaryLabelDataset(
            df=df_ref,
            label_names=['label'],
            protected_attribute_names=['protected'],
            favorable_label=1.0,
            unfavorable_label=0.0,
        )

        privileged_groups   = [{'protected': 1}]
        unprivileged_groups = [{'protected': 0}]

        # Suppress the expected divide-by-zero warnings that aif360 emits when
        # a group has no positive or negative samples (NaN result is handled below).
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning, message="invalid value encountered")

            metric = ClassificationMetric(
                dataset_ref,
                dataset_pred,
                unprivileged_groups=unprivileged_groups,
                privileged_groups=privileged_groups,
            )

            di = metric.disparate_impact()
            if di is not None and not np.isnan(di) and not np.isinf(di):
                fairness_ratio = float(di)

            try:
                eod = metric.equal_opportunity_difference()
                if eod is not None and not np.isnan(eod):
                    equal_opportunity_diff = float(eod)
            except Exception:
                pass

            try:
                aod = metric.average_odds_difference()
                if aod is not None and not np.isnan(aod):
                    avg_odds_diff = float(aod)
            except Exception:
                pass

    except Exception as e:
        warnings.warn(
            f"aif360 unavailable or failed ({e}). Falling back to manual disparate impact calculation.",
            RuntimeWarning,
        )
        fairness_ratio = manual_fairness_ratio

    compliance_pass = bool(fairness_ratio >= 0.8)

    # ── 3. SHAP Explainability ────────────────────────────────────────────────────
    try:
        classifier = model.named_steps['classifier']
        transformer = model[:-1]
        X_test_transformed = transformer.transform(X_test)
        X_test_arr = np.asarray(X_test_transformed, dtype=float)
        # Replace NaN/inf that StandardScaler produces when a feature has
        # near-zero variance (common after proxy removal during mitigation)
        X_test_arr = np.nan_to_num(X_test_arr, nan=0.0, posinf=0.0, neginf=0.0)

        shap_values = None
        try:
            # Use maskers.Independent (replaces deprecated feature_perturbation arg)
            _n_bg = min(100, len(X_test_arr))
            _masker = shap.maskers.Independent(X_test_arr, max_samples=_n_bg)
            explainer = shap.LinearExplainer(classifier, _masker)
            shap_values = explainer.shap_values(X_test_arr)
        except Exception:
            pass

        if shap_values is None:
            try:
                explainer2 = shap.Explainer(classifier, X_test_arr)
                shap_values = explainer2(X_test_arr).values
            except Exception:
                pass

        if shap_values is None:
            # Manual fallback: SHAP ≈ (x − mean_x) × coef for linear models
            if hasattr(classifier, 'coef_'):
                coef = classifier.coef_[0]          # (n_features,) for binary LR
                mean_x = X_test_arr.mean(axis=0)
                shap_values = (X_test_arr - mean_x) * coef
            else:
                raise ValueError("No linear coefficients available for SHAP fallback")

        # LinearExplainer may return a list [class_0_vals, class_1_vals] for binary
        if isinstance(shap_values, list):
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]

        shap_values = np.asarray(shap_values, dtype=float)

        # 3-D: shap.Explainer returns (n_samples, n_features, n_outputs) for multi-output.
        # Take [:, :, -1] (positive class) — NOT [-1] which slices the last SAMPLE (wrong).
        if shap_values.ndim == 3:
            shap_values = shap_values[:, :, -1]

        # 1-D: single-feature models may return (n_samples,) — reshape to (n_samples, 1)
        if shap_values.ndim == 1:
            shap_values = shap_values.reshape(-1, 1)

        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        # atleast_1d: single-feature mean produces a 0-D scalar; .tolist() would return
        # a plain float, making zip(feature_names, float) fail with TypeError.
        mean_abs_shap = np.atleast_1d(mean_abs_shap)
        # Sanitise: NaN/inf cause JSON serialisation errors
        mean_abs_shap = np.nan_to_num(mean_abs_shap, nan=0.0, posinf=0.0, neginf=0.0)
        feature_names = X_test.columns.tolist()
        shap_dict = dict(zip(feature_names, mean_abs_shap.tolist()))
        top_5_shap = dict(sorted(shap_dict.items(), key=lambda item: item[1], reverse=True)[:5])
        top_feature_index = int(np.argmax(mean_abs_shap)) if mean_abs_shap.any() else 0
        top_biased_feature = feature_names[top_feature_index]
    except Exception as _shap_err:
        logger.warning("SHAP computation failed: %s", _shap_err)
        top_biased_feature = "Unable to extract feature"
        top_5_shap = {}


    result = {
        "compliance_pass":       compliance_pass,
        "fairness_ratio":        float(fairness_ratio),
        "top_biased_feature":    top_biased_feature,
        "group_a_rate":          group_a_rate,
        "group_b_rate":          group_b_rate,
        "shap_summary":          top_5_shap,
    }
    if equal_opportunity_diff is not None:
        result["equal_opportunity_diff"] = equal_opportunity_diff
    if avg_odds_diff is not None:
        result["avg_odds_diff"] = avg_odds_diff

    return result
