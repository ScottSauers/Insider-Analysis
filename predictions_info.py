from sklearn.metrics import mean_squared_error
from scipy.stats import pearsonr, spearmanr
from sklearn.inspection import permutation_importance
import pandas as pd
import numpy as np

def get_prediction_info(model, y_train, predictions_train, X_validation, y_validation, predictions_validation):
    # Mean Squared Error
    mse_train = mean_squared_error(y_train, predictions_train)
    mse_validation = mean_squared_error(y_validation, predictions_validation)
    print(f"Training Mean Squared Error: {mse_train}")
    print(f"Validation Mean Squared Error: {mse_validation}")

    # Pearson and Spearman correlations
    pearson_corr_train, _ = pearsonr(y_train, predictions_train)
    spearman_corr_train, _ = spearmanr(y_train, predictions_train)
    print(f"Training Pearson Correlation: {pearson_corr_train:.4f}")

    pearson_corr_validation, _ = pearsonr(y_validation, predictions_validation)
    spearman_corr_validation, _ = spearmanr(y_validation, predictions_validation)
    print(f"Validation Pearson Correlation: {pearson_corr_validation:.4f}")

    # Average Percent Error
    avg_percent_error_train = np.mean(np.abs((y_train - predictions_train) / y_train)) * 100
    avg_percent_error_validation = np.mean(np.abs((y_validation - predictions_validation) / y_validation)) * 100
    print(f"Training Average Percent Error: {avg_percent_error_train:.2f}%")
    print(f"Validation Average Percent Error: {avg_percent_error_validation:.2f}%")

    # Permutation Feature Importance
    perm_importance = permutation_importance(model, X_validation, y_validation, n_repeats=10, random_state=42, n_jobs=-1)
    feature_importances = perm_importance.importances_mean
    features = X_validation.columns
    importance_df = pd.DataFrame({'feature': features, 'importance': feature_importances}).sort_values(by='importance', ascending=False)

    print("\nFeature importances based on permutation importance:")
    print(importance_df.to_string(index=False))

    return importance_df