import pandas as pd
import numpy as np
from sklearn.cluster import FeatureAgglomeration
from sklearn.preprocessing import StandardScaler

def find_proxies(dataset_df: pd.DataFrame, protected_col: str, correlation_threshold: float = 0.15) -> list:
    """
    Performs hierarchical clustering on features to group similar variables,
    then correlates the cluster representations with the protected column
    to find proxy variables.
    """
    # Create a working copy and drop entirely empty columns
    df = dataset_df.copy().dropna(axis=1, how='all')
    
    # Isolate the protected column and convert to numeric codes if categorical
    if protected_col not in df.columns:
        return []
        
    y = df[protected_col]
    if y.dtype == 'object' or y.dtype.name == 'category':
        y = y.astype('category').cat.codes
        
    # Drop target and protected column from features, select numeric features only
    target_col = 'loan_approved'
    cols_to_drop = [c for c in [protected_col, target_col] if c in df.columns]
    X = df.drop(columns=cols_to_drop).select_dtypes(include=[np.number])
    
    # Handle NaNs
    X = X.fillna(X.median(numeric_only=True))
    
    features = X.columns.tolist()
    if len(features) < 2:
        return []
        
    # Scale features for clustering
    X_scaled = StandardScaler().fit_transform(X)
    
    # Perform FeatureAgglomeration (hierarchical clustering for features)
    n_clusters = min(5, len(features))
    agglo = FeatureAgglomeration(n_clusters=n_clusters)
    X_clustered = agglo.fit_transform(X_scaled)
    
    flagged_columns = set()
    
    # Check correlation of each cluster representation with the protected column
    for i in range(n_clusters):
        cluster_repr = X_clustered[:, i]
        
        # Calculate Pearson correlation (safely handle constant clusters)
        if np.std(cluster_repr) > 0 and np.std(y) > 0:
            corr = np.corrcoef(cluster_repr, y)[0, 1]
            if abs(corr) >= correlation_threshold:
                # Find all original features that belong to this highly-correlated cluster
                cluster_features = [features[j] for j, label in enumerate(agglo.labels_) if label == i]
                flagged_columns.update(cluster_features)
                
    return list(flagged_columns)
