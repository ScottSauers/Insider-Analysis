import pandas as pd
from datetime import datetime, timedelta
import os

from get_prices import find_price_for_date, find_next_available_price, get_buy_date

def make_data_file(ticker, days_to_add):
    #ticker = "UNFI"

    current_dir = os.getcwd()
    encoded_data_path = os.path.join(current_dir, 'insider_data', f'{ticker}_encoded_data.csv')
    historical_data_path = os.path.join(current_dir, 'historical', f'{ticker}_historical_close.csv')

    def process_ticker_data(ticker, days_to_add):
        try:
            encoded_df = pd.read_csv(encoded_data_path)
            # Scan for date columns with time included
            date_columns = ['transactionDate', 'periodOfReport']
            for column in date_columns:
                encoded_df[column] = encoded_df[column].astype(str)
                encoded_df[column] = encoded_df[column].apply(lambda x: x.split(' ')[0] if ' ' in x else x)
            # Parse date columns
            encoded_df['transactionDate'] = pd.to_datetime(encoded_df['transactionDate'])
            encoded_df['periodOfReport'] = pd.to_datetime(encoded_df['periodOfReport'])
            encoded_df['effectiveDate'] = encoded_df['transactionDate'].fillna(encoded_df['periodOfReport'])
        except Exception as e:
            print(f"Error loading or processing encoded data: {e}")
            return

        try:
            historical_df = pd.read_csv(historical_data_path)
            # Scan for date column with time included
            historical_df['Date'] = historical_df['Date'].astype(str)
            historical_df['Date'] = historical_df['Date'].apply(lambda x: x.split(' ')[0] if ' ' in x else x)
            # Parse date column
            historical_df['Date'] = pd.to_datetime(historical_df['Date'])
            historical_df.set_index('Date', inplace=True)
        except Exception as e:
            print(f"Error loading or processing historical data: {e}")
            return

        results_df = iterate_transactions(encoded_df, historical_df, days_to_add)

        # Specify the path where you want to save the results CSV
        results_path = os.path.join(current_dir, f'insider_data/{ticker}_price_analysis_results.csv')
        results_df.to_csv(results_path, index=False)
        print(f"Results saved to {results_path}")

    def iterate_transactions(encoded_df, historical_df, days_to_add):
        results = []
        for _, row in encoded_df.iterrows():
            effective_date = row['effectiveDate']
            if pd.notnull(effective_date):
                #print("CORRECT date format: ", effective_date)
                #print("CORRECT historical_df format: " historical_df)
                effective_date_price_info = get_buy_date(effective_date, historical_df)
                #print(effective_date_price_info)
                next_available_date, next_available_price_info = find_next_available_price(effective_date, historical_df, days_to_add)

                # Processing to match the handling of 'Next Available Price'
                if next_available_date is not None:
                    days_diff = (next_available_date - effective_date).days
                    #print(f"Effective date: {effective_date}, Next available date: {next_available_date}, Days difference: {days_diff}")
                    if days_diff != days_to_add:
                        print(f"Day number mismatch. Effective date: {effective_date}, Next available date: {next_available_date}, Days difference: {days_diff}")
                else:
                    print(f"Effective date: {effective_date}, No available price information for next available date.")

                # Add effective date price info to results
                results.append({
                    'Effective Date': effective_date,
                    'Effective Date Price': effective_date_price_info[1], # Extracting the price directly
                    'Next Available Date': next_available_date,
                    'Days Difference': days_diff if next_available_date is not None else None,
                    'Next Available Price': next_available_price_info
                })
            else:
                print("Effective date is missing for a row, skipping.")

        results_df = pd.DataFrame(results)

        # Format 'Next Available Price' and 'Effective Date Price' columns to ensure consistency
        for column in ['Next Available Price', 'Effective Date Price']:
            results_df[column] = results_df[column].apply(lambda x: x.iloc[0] if isinstance(x, pd.Series) else x)

        return results_df

    def add_price_change_column(csv_path):
        # Check if the file exists
        if not os.path.exists(csv_path):
            print(f"The file {csv_path} does not exist.")
            return

        # Read the CSV into a DataFrame
        df = pd.read_csv(csv_path)

        # Calculate the price change and add it as a new column
        df['Price Change'] = (df['Next Available Price'] - df['Effective Date Price'])/(abs(df['Effective Date Price']))

        # Save the DataFrame with the new column to the new file
        df.to_csv(csv_path, index=False)
        print(f"Updated file saved to {csv_path}")

    process_ticker_data(ticker, days_to_add)
    csv_path = os.path.join(current_dir, f'insider_data/{ticker}_price_analysis_results.csv')
    add_price_change_column(csv_path)

    # Load the CSV files into DataFrames
    df_encoded_data = pd.read_csv(encoded_data_path)
    df_csv_data = pd.read_csv(csv_path)

    # Reset the index of both DataFrames to ensure they are unique and aligned
    df_encoded_data.reset_index(drop=True, inplace=True)
    df_csv_data.reset_index(drop=True, inplace=True)

    # Check if both DataFrames have the same number of rows to ensure direct correspondence
    if len(df_encoded_data) == len(df_csv_data):
        # Concatenate the DataFrames horizontally
        combined_df = pd.concat([df_encoded_data, df_csv_data], axis=1)
        # Save the combined DataFrame back to the original path or a new file as needed
        combined_df.to_csv(encoded_data_path, index=False)
    else:
        print("The DataFrames have a different number of rows; cannot concatenate them directly without additional alignment.")

#make_data_file("UNFI", 2)