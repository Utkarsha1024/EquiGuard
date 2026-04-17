import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

def run_model():
    # Fetch COMPAS dataset
    url = "https://raw.githubusercontent.com/propublica/compas-analysis/master/compas-scores-two-years.csv"
    
    # Load dataset
    df = pd.read_csv(url)
    
    # Target variable
    target_col = 'two_year_recid'
    
    # For a basic model, let's select a few numeric/categorical columns
    # We will just use 'age', 'juv_fel_count', 'juv_misd_count', 'juv_other_count', 'priors_count'
    features = ['age', 'juv_fel_count', 'juv_misd_count', 'juv_other_count', 'priors_count']
    
    # Drop rows where target is missing just in case
    df = df.dropna(subset=[target_col])
    
    X = df[features]
    y = df[target_col]
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
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
        "accuracy": float(accuracy)
    }
