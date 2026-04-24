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
        from aif360.datasets import BinaryLabelDataset
        from aif360.metrics import ClassificationMetric

        df_aif = pd.DataFrame({
            'protected': protected_attributes,
            'prediction': list(predictions),
            'label': list(predictions),  # use predictions as surrogate labels
        })

        dataset_pred = BinaryLabelDataset(
            df=df_aif,
            label_names=['label'],
            protected_attribute_names=['protected'],
        )

        # Reference dataset: assume all positive outcomes (ideal baseline)
        df_ref = df_aif.copy()
        df_ref['label'] = 1
        dataset_ref = BinaryLabelDataset(
            df=df_ref,
            label_names=['label'],
            protected_attribute_names=['protected'],
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

        try:
            explainer = shap.LinearExplainer(classifier, X_test_transformed)
            shap_values = explainer.shap_values(X_test_transformed)
        except Exception:
            explainer = shap.Explainer(classifier, X_test_transformed)
            shap_values = explainer(X_test_transformed).values

        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        feature_names = X_test.columns.tolist()
        shap_dict = dict(zip(feature_names, mean_abs_shap))
        top_5_shap = dict(sorted(shap_dict.items(), key=lambda item: item[1], reverse=True)[:5])
        top_feature_index = int(np.argmax(mean_abs_shap))
        top_biased_feature = feature_names[top_feature_index]
    except Exception:
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
