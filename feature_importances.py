import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.feature_selection import RFECV
from sklearn.inspection import permutation_importance
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

# Load the dataset
df = pd.read_csv('/Users/scott/Downloads/stock/NASDAQ_fundamentals.csv')

# Drop rows with missing target values
df = df.dropna(subset=[df.columns[1]])
features = df.select_dtypes(include=['int64', 'float64']).columns.drop(df.columns[1])

# Preprocessing
num_pipeline = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='constant', fill_value=-9999)),
    ('scaler', StandardScaler())
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', num_pipeline, features)
    ]
)

# Split the dataset
X = df[features]
y = df[df.columns[1]]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Models to evaluate
models = {
    "RandomForestRegressor": RandomForestRegressor(random_state=42),
    "LinearRegression": LinearRegression(),
    "GradientBoostingRegressor": GradientBoostingRegressor(random_state=42),
    # "LogisticRegression": LogisticRegression(max_iter=1000) # Uncomment if your target is suitable for classification
}

for name, model in models.items():
    # Define the modeling pipeline
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', model)
    ])
    
    # Fit the pipeline
    pipeline.fit(X_train, y_train)
    
    # Feature importance extraction for tree-based models
    if hasattr(model, 'feature_importances_'):
        feature_importances = model.feature_importances_
        
        plt.figure(figsize=(10, 8))
        plt.barh(features, feature_importances, color='skyblue')
        plt.title(f'{name} Feature Importance', fontsize=16)
        plt.xlabel('Importance', fontsize=14)
        plt.ylabel('Features', fontsize=14)
        plt.tight_layout()
        plt.show()
    
    # Permutation Importance for all models
    perm_importance_result = permutation_importance(pipeline, X_test, y_test, n_repeats=10, random_state=42)
    sorted_idx = perm_importance_result.importances_mean.argsort()
    
    plt.figure(figsize=(10, 8))
    plt.barh(features[sorted_idx], perm_importance_result.importances_mean[sorted_idx], color='lightgreen')
    plt.title(f'{name} Permutation Importance', fontsize=16)
    plt.xlabel('Mean Decrease in Accuracy', fontsize=14)
    plt.ylabel('Features', fontsize=14)
    plt.tight_layout()
    plt.show()
