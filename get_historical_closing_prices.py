import pandas as pd
from yahooquery import Ticker
import os

def fetch_and_save_historical_close(ticker, start_date, end_date):
    """
    Fetches historical closing prices for a given ticker within a specified date range and saves to CSV.
    The output file is named dynamically based on the ticker symbol.
    
    Parameters:
    - ticker: The stock ticker symbol as a string.
    - start_date: The start date in 'YYYY-MM-DD' format or 'YYYY' for just the year.
    - end_date: The end date in 'YYYY-MM-DD' format or 'YYYY' for just the year.
    """
    # Adjust the start and end dates if only years are provided
    if len(start_date) == 4: start_date += '-01-01'
    if len(end_date) == 4: end_date += '-12-31'
    
    # Dynamic output file path based on the ticker
    output_file_path = f"{ticker}_historical_close.csv"

    t = Ticker(ticker)
    try:
        historical_data = t.history(start=start_date, end=end_date)
        
        # Check if the DataFrame is empty or if the request failed
        if historical_data.empty:
            print(f"No data found for {ticker}.")
            return
        
        # Prepare the DataFrame: select 'close' and reset index to include the date
        historical_data = historical_data.reset_index()
        historical_data = historical_data[['date', 'close']]
        historical_data.rename(columns={'date': 'Date', 'close': 'Close'}, inplace=True)

        # Insert the ticker column at the beginning
        historical_data.insert(0, 'Ticker', ticker)

        # Save or append the data to the dynamically named CSV file
        if not os.path.exists(output_file_path):
            historical_data.to_csv(output_file_path, index=False)
        else:
            # Append without writing the header again
            historical_data.to_csv(output_file_path, mode='a', header=False, index=False)

        print(f'Successfully saved historical closing prices for {ticker} to {output_file_path}.')

    except Exception as e:
        print(f"Error fetching historical data for {ticker}: {e}")

# Example usage
fetch_and_save_historical_close("MSFT", "2014", "2024")
