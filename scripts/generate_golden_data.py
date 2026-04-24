import pandas as pd

def generate():
    url = "https://raw.githubusercontent.com/propublica/compas-analysis/master/compas-scores-two-years.csv"
    print("Fetching raw COMPAS data...")
    df = pd.read_csv(url)
    
    # Filter to requested columns
    cols = ['race', 'age', 'priors_count', 'juv_fel_count', 'c_charge_degree', 'two_year_recid']
    df = df[cols]
    
    # Filter race
    df = df[df['race'].isin(['African-American', 'Caucasian'])]
    
    # Map target variable (flip 0 and 1)
    df['loan_approved'] = 1 - df['two_year_recid']
    df = df.drop(columns=['two_year_recid'])
    
    # Map categorical variable to numeric so scikit-learn LogisticRegression doesn't crash
    df['c_charge_degree'] = df['c_charge_degree'].map({'F': 1, 'M': 0})
    
    # Drop missing values
    df = df.dropna()
    
    # Save to data directory
    df.to_csv("data/golden_demo_dataset.csv", index=False)
    print("Successfully generated data/golden_demo_dataset.csv")

if __name__ == "__main__":
    generate()
