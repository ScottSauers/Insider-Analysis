import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
import xgboost as xgb
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error
from scipy.stats import pearsonr, spearmanr
from sklearn.inspection import permutation_importance
import numpy as np

from model_data import save_model_results
from predictions_info import get_prediction_info
from evaluate_strategy import evaluate_strategy
pd.set_option('display.max_rows', 20, 'display.max_columns', 12)

def prepare_data(ticker, validation_percentage):
    csv_path = os.path.join(os.getcwd(), 'insider_data', f"{ticker}_encoded_data.csv")
    df = pd.read_csv(csv_path)

    # Columns to be removed, excluding 'Effective Date' initially for sorting
    columns_to_remove = ['transactionDate', 'firmName', 'periodOfReport',
                         'dateOfOriginalSubmission', 'Next Available Date', 'transactionShares',
                         'Days Difference', 'Next Available Price', 'sharesOwnedPrecedingTransaction']

    # Remove the specified columns
    df.drop(columns=columns_to_remove, errors='ignore', inplace=True)

    const_columns_to_remove = []
    for column in df.columns:
        if df[column].nunique() == 1:
            const_columns_to_remove.append(column)

    # Print the columns that will be dropped
    if const_columns_to_remove:
        print("Columns to be dropped:")
        for column in const_columns_to_remove:
            print(column)

    # Drop the identified columns
    df.drop(columns=const_columns_to_remove, errors='ignore', inplace=True)

    # Drop rows where 'Price Change' is NaN
    df.dropna(subset=['Price Change'], inplace=True)

    # Fill all remaining NaN values in the dataframe with -1
    df.fillna(-1, inplace=True)

    # Sort by 'Effective Date' if it exists, then remove it after sorting
    if 'Effective Date' in df.columns:
        df['Effective Date'] = pd.to_datetime(df['Effective Date'])
        df.sort_values('Effective Date', inplace=True)
        full_df = df.copy(deep=True)
        df.drop(columns=['Effective Date'], inplace=True)  # Remove after sorting

    #print(full_df)
    # Calculate the split index. This approach doesn't require an additional date column post-removal.
    split_idx = int(len(df) * (1 - validation_percentage / 100))
    #print(full_df)
    # Split the data into training and validation sets
    training_data = df.iloc[:split_idx]
    validation_data = df.iloc[split_idx:]
    date_validation_data = full_df.iloc[split_idx:]
    #print(date_validation_data)

    return training_data, validation_data, date_validation_data

def train_and_evaluate(training_data, validation_data, sell_timedelta, date_validation_data):
    X_train = training_data.drop(['Price Change'], axis=1)
    y_train = training_data['Price Change']
    X_validation = validation_data.drop(['Price Change'], axis=1)
    y_validation = validation_data['Price Change']



    param_grid = {
        'colsample_bytree': [0.3],
        'learning_rate': [0.1],
        'max_depth': [3, 5, 7],
        'alpha': [0.01, 1],
        'reg_lambda': [0.01, 1],
        'n_estimators': [150],
        'subsample': [0.8]
    }

    model = XGBRegressor(objective='reg:absoluteerror', seed=42)


    model = GridSearchCV(estimator=model, param_grid=param_grid, scoring='neg_mean_squared_error', cv=5, verbose=1)

    model.fit(X_train, y_train)

    print("Best hyperparameters:", model.best_params_)

    # Predict on training and validation data
    predictions_train = model.predict(X_train)
    predictions_validation = model.predict(X_validation)

    importance_df = get_prediction_info(model, y_train, predictions_train, X_validation, y_validation, predictions_validation)

    # Save the model results
    save_model_results(model, importance_df, ticker)

    #print(date_validation_data.columns)
    #print(predictions_validation)
    #print(len(date_validation_data['Effective Date']))
    #print(len(predictions_validation))
    predictions_df = pd.DataFrame({
        'Date': date_validation_data['Effective Date'],
        'Predicted Price Change': predictions_validation
    })
    print(predictions_df)
    evaluate_strategy(ticker, predictions_df, sell_timedelta)


# Example usage
ticker = "ABBV"
validation_percentage = 20
sell_timedelta = 2
training_data, validation_data, date_validation_data = prepare_data(ticker, validation_percentage)
train_and_evaluate(training_data, validation_data, sell_timedelta, date_validation_data)