import pandas as pd
import numpy as np
import shap

def run_audit(model, X_test, predictions, protected_attributes):
    # 1. EEOC 4/5ths Rule
    # Combine protected attributes and predictions
    df_eval = pd.DataFrame({'protected': protected_attributes, 'prediction': predictions})
    
    # Calculate selection rate for each demographic group
    # A prediction of 1 means they are predicted to recidivate.
    selection_rates = df_eval.groupby('protected')['prediction'].mean()
    
    if len(selection_rates) > 1:
        rates = selection_rates.sort_index().values
        group_b_rate = float(rates[0])
        group_a_rate = float(rates[1])
        if rates[1] > 0:
            fairness_ratio = rates[0] / rates[1]
        else:
            fairness_ratio = 1.0
    else:
        group_b_rate = float(selection_rates.get(0, 0.0))
        group_a_rate = float(selection_rates.get(1, 0.0))
        fairness_ratio = 1.0
        
    compliance_pass = bool(fairness_ratio >= 0.8)
    
    # 2. Explainability Layer with SHAP
    try:
        # Extract the classifier and transformer from the pipeline
        classifier = model.named_steps['classifier']
        transformer = model[:-1]
        
        # Transform X_test to get the data as the classifier sees it
        X_test_transformed = transformer.transform(X_test)
        
        try:
            # LinearExplainer expects the model and the background data (we use the test set as background)
            explainer = shap.LinearExplainer(classifier, X_test_transformed)
            shap_values = explainer.shap_values(X_test_transformed)
        except Exception:
            # Fallback if LinearExplainer fails
            explainer = shap.Explainer(classifier, X_test_transformed)
            shap_values = explainer(X_test_transformed).values
        
        # Calculate mean absolute SHAP value for each feature
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        
        # Get feature names from X_test
        feature_names = X_test.columns.tolist()
        
        # Calculate Top 5 SHAP values
        shap_dict = dict(zip(feature_names, mean_abs_shap))
        top_5_shap = dict(sorted(shap_dict.items(), key=lambda item: item[1], reverse=True)[:5])
        
        top_feature_index = int(np.argmax(mean_abs_shap))
        top_biased_feature = feature_names[top_feature_index]
    except Exception:
        top_biased_feature = "Unable to extract feature"
        top_5_shap = {}
    
    return {
        "compliance_pass": compliance_pass,
        "fairness_ratio": float(fairness_ratio),
        "top_biased_feature": top_biased_feature,
        "group_a_rate": group_a_rate,
        "group_b_rate": group_b_rate,
        "shap_summary": top_5_shap
    }
