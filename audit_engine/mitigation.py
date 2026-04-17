import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score

def mitigate_and_retrain(flagged_columns: list):
    # Fetch golden demo dataset
    url = "golden_demo_dataset.csv"
    df = pd.read_csv(url)
    
    target_col = 'loan_approved'
    
    # Original features used in model_runner
    features = ['age', 'juv_fel_count', 'c_charge_degree', 'priors_count']
    
    # Drop flagged proxy variables from the feature set
    clean_features = [f for f in features if f not in flagged_columns]
    
    # If all features were flagged, at least keep one to prevent crashing (fallback)
    if not clean_features:
        clean_features = ['juv_misd_count']
        
    df = df.dropna(subset=[target_col])
    
    X = df[clean_features]
    y = df[target_col]
    
    # Split the data, preserving the protected attribute for auditing
    X_train, X_test, y_train, y_test, race_train, race_test = train_test_split(
        X, y, df['race'], test_size=0.2, random_state=42
    )
    
    # Retrain pipeline
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(random_state=42))
    ])
    
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    
    return {
        "model": pipeline,
        "predictions": predictions.tolist(),
        "X_test": X_test,
        "protected_attributes": race_test.tolist(),
        "accuracy": float(accuracy),
        "clean_features": clean_features
    }
