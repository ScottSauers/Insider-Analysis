import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.impute import KNNImputer
from sklearn.linear_model import RidgeCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import SelectFromModel, mutual_info_regression
from sklearn.pipeline import Pipeline
from sklearn.inspection import permutation_importance

# Load the dataset
df = pd.read_csv('NASDAQ_fundamentals.csv')

# Preprocessing: Removing rows with missing target values and selecting numerical features
df.dropna(subset=[df.columns[1]], inplace=True)
features = df.select_dtypes(include=['int64', 'float64']).columns.drop(df.columns[1])

# Sophisticated imputation with KNNImputer
imputer = KNNImputer(n_neighbors=5)
df[features] = imputer.fit_transform(df[features])

# Splitting the dataset
X = df[features]
y = df[df.columns[1]]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Setup for RandomForestRegressor
rf = RandomForestRegressor(random_state=42)

# Select features based on mutual information
mi = mutual_info_regression(X_train, y_train)
mi_threshold = np.median(mi)  # or any other threshold according to your dataset characteristics
features_to_keep = features[mi > mi_threshold]

X_train_mi = X_train[features_to_keep]
X_test_mi = X_test[features_to_keep]

if X_train_mi.shape[1] > 0:
    # Fit the model on features selected based on mutual information
    rf.fit(X_train_mi, y_train)

    # Displaying Feature Importance
    plt.figure(figsize=(10, 8))
    plt.barh(features_to_keep, rf.feature_importances_, color='skyblue')
    plt.title('Feature Importance with Mutual Information Selection', fontsize=16)
    plt.xlabel('Importance', fontsize=14)
    plt.ylabel('Features', fontsize=14)
    plt.tight_layout()
    plt.show()

    # Permutation Importance
    perm_importance = permutation_importance(rf, X_test_mi, y_test, n_repeats=10, random_state=42)
    sorted_idx = perm_importance.importances_mean.argsort()
    plt.figure(figsize=(10, 8))
    plt.barh(features_to_keep[sorted_idx], perm_importance.importances_mean[sorted_idx], color='lightgreen')
    plt.title('Permutation Importance with Mutual Information Selection', fontsize=16)
    plt.xlabel('Importance', fontsize=14)
    plt.ylabel('Features', fontsize=14)
    plt.tight_layout()
    plt.show()
else:
    print("No features were selected. Consider adjusting the selection threshold.")
