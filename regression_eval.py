import os
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import Lasso, Ridge
from sklearn.metrics import mean_squared_error
from sklearn.metrics import make_scorer, mean_absolute_error
from scipy.stats import pearsonr, spearmanr
from sklearn.inspection import permutation_importance
import numpy as np
from sklearn.impute import KNNImputer

from model_data import save_model_results
from predictions_info import get_prediction_info
from evaluate_strategy import evaluate_strategy

def negative_mean_absolute_error(y_true, y_pred):
    return -mean_absolute_error(y_true, y_pred)

mae_scorer = make_scorer(negative_mean_absolute_error)

def prepare_data(ticker, validation_percentage):
    csv_path = os.path.join(os.getcwd(), 'insider_data', f"{ticker}_encoded_data.csv")
    df = pd.read_csv(csv_path)

    df.dropna(subset=['Price Change'], inplace=True)

    df = df.fillna(-1)

    columns_to_remove = ['transactionDate', 'firmName', 'periodOfReport',
                         'dateOfOriginalSubmission', 'Next Available Date',
                         'Days Difference', 'Next Available Price', 'transactionShares',
                         'Effective Date Price']

    df.drop(columns=columns_to_remove, inplace=True)


    if 'Effective Date' in df.columns:
        df['Effective Date'] = pd.to_datetime(df['Effective Date'])
        df.sort_values('Effective Date', inplace=True)

    full_df = df.copy()

    split_idx = int(len(df) * (1 - validation_percentage / 100))
    training_data = df.iloc[:split_idx].drop(['Effective Date'], axis=1, errors='ignore')
    validation_data = df.iloc[split_idx:].drop(['Effective Date'], axis=1, errors='ignore')
    date_validation_data = full_df.iloc[split_idx:]

    return training_data, validation_data, date_validation_data

def train_and_evaluate(training_data, validation_data, sell_timedelta, date_validation_data):

    if training_data.isnull().any().any():
        print("Training data contains NaN values after preprocessing.")
        nan_rows, nan_cols = training_data.isnull().any().nonzero()
        for i, row in enumerate(nan_rows):
            col = nan_cols[row]
            print(f"Row {i}, Column {col} contains NaN values in training data after preprocessing.")

    if validation_data.isnull().any().any():
        print("Validation data contains NaN values after preprocessing.")
        nan_rows, nan_cols = validation_data.isnull().any().nonzero()
        for i, row in enumerate(nan_rows):
            col = nan_cols[row]
            print(f"Row {i}, Column {col} contains NaN values in validation data after preprocessing.")

    X_train = training_data.drop(['Price Change'], axis=1)
    y_train = training_data['Price Change']
    X_validation = validation_data.drop(['Price Change'], axis=1)
    y_validation = validation_data['Price Change']

    # Train and evaluate Lasso
    lasso = Lasso(random_state=42, alpha=0.0001, max_iter=10000)
    lasso.fit(X_train, y_train)
    predictions_lasso = lasso.predict(X_validation)
    importance_df_lasso = get_prediction_info(lasso, y_train, lasso.predict(X_train), X_validation, y_validation, predictions_lasso)
    save_model_results(lasso, importance_df_lasso, f"{ticker}_lasso")

    # Train and evaluate Ridge
    ridge = Ridge(random_state=42, alpha=0.0001, solver='lsqr')
    ridge.fit(X_train, y_train)
    predictions_ridge = ridge.predict(X_validation)
    importance_df_ridge = get_prediction_info(ridge, y_train, ridge.predict(X_train), X_validation, y_validation, predictions_ridge)
    save_model_results(ridge, importance_df_ridge, f"{ticker}_ridge")

    # Compare the variance in predictions
    print("Variance in Lasso predictions:", np.var(predictions_lasso))
    print("Variance in Ridge predictions:", np.var(predictions_ridge))

    # Create predictions dataframes for Lasso and Ridge
    predictions_df_lasso = pd.DataFrame({
        'Date': date_validation_data['Effective Date'],
        'Predicted Price Change': predictions_lasso
    })
    predictions_df_ridge = pd.DataFrame({
        'Date': date_validation_data['Effective Date'],
        'Predicted Price Change': predictions_ridge
    })

    # Evaluate strategies for Lasso and Ridge
    print("Evaluating Lasso strategy:")
    evaluate_strategy(ticker, predictions_df_lasso, sell_timedelta)
    #print("Evaluating Ridge strategy:")
    #evaluate_strategy(ticker, predictions_df_ridge, sell_timedelta)

# Example usage
ticker = "UNFI"
validation_percentage = 20
sell_timedelta = 7
training_data, validation_data, date_validation_data = prepare_data(ticker, validation_percentage)
train_and_evaluate(training_data, validation_data, sell_timedelta, date_validation_data)