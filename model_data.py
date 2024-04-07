import os
import pandas as pd

def save_model_results(model, importance_df, ticker, csv_file='model_data.csv'):
    # Create a new DataFrame with ticker as the first column
    result_df = pd.DataFrame({'ticker': [ticker]})

    # Add feature importances as columns
    for feature, importance in zip(importance_df['feature'], importance_df['importance']):
        result_df[feature] = importance

    # Get hyperparameters dynamically
    hyperparams = {}
    if hasattr(model, 'best_params_'):
        # Handle models with best_params_ attribute (e.g., GridSearchCV)
        best_params = model.best_params_
        for param, value in best_params.items():
            hyperparams[param] = value
    else:
        # Handle models without best_params_ attribute
        for param, value in model.get_params().items():
            hyperparams[param] = value

    # Add hyperparameters as columns
    for param, value in hyperparams.items():
        result_df[param] = str(value)

    # Save to CSV, appending if the file already exists
    if os.path.exists(csv_file):
        existing_df = pd.read_csv(csv_file)
        combined_df = pd.concat([existing_df, result_df], ignore_index=True)
        combined_df.to_csv(csv_file, index=False)
    else:
        result_df.to_csv(csv_file, index=False)