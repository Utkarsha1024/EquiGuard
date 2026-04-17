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
    
    if len(selection_rates) > 0 and selection_rates.max() > 0:
        fairness_ratio = selection_rates.min() / selection_rates.max()
    else:
        fairness_ratio = 1.0
        
    compliance_pass = bool(fairness_ratio >= 0.8)
    
    # 2. Explainability Layer with SHAP
    # Extract the classifier and transformer from the pipeline
    classifier = model.named_steps['classifier']
    transformer = model[:-1]
    
    # Transform X_test to get the data as the classifier sees it
    X_test_transformed = transformer.transform(X_test)
    
    # LinearExplainer expects the model and the background data (we use the test set as background)
    explainer = shap.LinearExplainer(classifier, X_test_transformed)
    shap_values = explainer.shap_values(X_test_transformed)
    
    # Calculate mean absolute SHAP value for each feature
    mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
    
    # Get feature names from X_test
    feature_names = X_test.columns.tolist()
    
    top_feature_index = int(np.argmax(mean_abs_shap))
    top_biased_feature = feature_names[top_feature_index]
    
    return {
        "compliance_pass": compliance_pass,
        "fairness_ratio": float(fairness_ratio),
        "top_biased_feature": top_biased_feature
    }
