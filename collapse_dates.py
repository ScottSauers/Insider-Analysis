import pandas as pd
import numpy as np
import shutil
import os

def collapse_ticker_data(ticker):
    # Define file paths
    current_dir = os.getcwd()
    original_file_path = os.path.join(current_dir, f'insider_data/{ticker}_encoded_data.csv')
    backup_file_path = os.path.join(current_dir, f'insider_data/{ticker}_encoded_data_expanded.csv')



    if os.path.exists(backup_file_path):
        data = pd.read_csv(backup_file_path)
        print("Using backup")
    else:
        data = pd.read_csv(original_file_path)
        shutil.copyfile(original_file_path, backup_file_path)
        print("Using current")


    # Check file existence and backup
    if not os.path.exists(original_file_path):
        print(f"File for ticker {ticker} not found.")
        return


    data['Effective Date'] = pd.to_datetime(data['Effective Date'])

    # Replace -1 with NaN for numeric columns
    numeric_cols = data.select_dtypes(include=['number']).columns
    data[numeric_cols] = data[numeric_cols].applymap(lambda x: np.nan if x == -1 else x)

    # Adjust specific columns as required
    exclusion_rules = {
        'securityTitle_1_common_2_restricted_3_options': [4],
        'transaction_1_Disposed_2_Acquired': [3]
    }

    for col, values_to_exclude in exclusion_rules.items():
        if col in data.columns:
            for value in values_to_exclude:
                data[col] = data[col].replace(value, np.nan)

    # Aggregate data
    # Define a custom aggregation dictionary
    aggregation_dict = {col: 'mean' for col in numeric_cols}
    aggregation_dict.update({
        'total_dollar_amount': 'sum',
        # Add any non-numeric column aggregations if needed
    })

    # For modal values including 'person_ID'
    non_numeric_cols = data.select_dtypes(exclude=['number', 'datetime64[ns]']).columns.tolist()
    for col in non_numeric_cols:
        aggregation_dict[col] = lambda x: pd.Series.mode(x)[0] if not pd.Series.mode(x).empty else np.nan

    aggregated_data = data.groupby('Effective Date').agg(aggregation_dict)

    # One-hot encode the 4 most frequent 'person_ID' values
    top_person_ids = data['person_ID'].value_counts().nlargest(4).index
    for person_id in top_person_ids:
        aggregated_data[f'person_ID_{person_id}'] = data['person_ID'].apply(lambda x: 1 if x == person_id else 0)

    # Drop the original 'person_ID' column after encoding if needed
    if 'person_ID' in aggregated_data.columns:
        aggregated_data.drop(['person_ID'], axis=1, inplace=True)

    # Save the processed data
    aggregated_data.to_csv(original_file_path, index=True)
    print(f"Processed data for {ticker} has been saved. Original data backed up.")

# Example usage
#collapse_ticker_data('NVDA')