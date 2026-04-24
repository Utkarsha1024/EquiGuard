import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline

def run_model(data_path: str = "data/golden_demo_dataset.csv", target_col: str = "loan_approved", protected_col: str = "race"):
    # Load dataset
    df = pd.read_csv(data_path)
    
    # Drop rows where target or protected is missing
    df = df.dropna(subset=[target_col, protected_col])
    
    # Target Encoding: Force string labels into binary integers
    df[target_col] = LabelEncoder().fit_transform(df[target_col])
    
    # Protected Binarization: Ensure discrete groups for EEOC math
    if pd.api.types.is_numeric_dtype(df[protected_col]):
        if len(df[protected_col].unique()) > 2:
            median_val = df[protected_col].median()
            df[protected_col] = (df[protected_col] >= median_val).astype(int)
    else:
        df[protected_col] = LabelEncoder().fit_transform(df[protected_col])
    
    # Dynamically select numeric features excluding target and protected
    cols_to_drop = [c for c in [target_col, protected_col] if c in df.columns]
    X = df.drop(columns=cols_to_drop).select_dtypes(include=[np.number])
    
    y = df[target_col]
    
    # Split the data
    X_train, X_test, y_train, y_test, race_train, race_test = train_test_split(
        X, y, df[protected_col], test_size=0.2, random_state=42
    )
    
    # Basic pipeline with imputation and scaling
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(random_state=42))
    ])
    
    # Train the model
    pipeline.fit(X_train, y_train)
    
    # Predict
    predictions = pipeline.predict(X_test)
    
    # Calculate accuracy
    accuracy = accuracy_score(y_test, predictions)
    
    return {
        "predictions": predictions.tolist(),
        "accuracy": float(accuracy),
        "model": pipeline,
        "X_test": X_test,
        "protected_attributes": race_test.tolist()
    }
