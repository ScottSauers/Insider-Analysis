import pandas as pd
from yahooquery import Ticker
from datetime import datetime
import send2trash
import os



def hist_prices(ticker, start_year, end_year):

    # Dynamic output file path based on the ticker
    output_file_path = f"historical/{ticker}_historical_close.csv"

    try:
        send2trash.send2trash(output_file_path)
    except:
        None

    if not os.path.exists('historical'):
        os.makedirs('historical')

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
        if isinstance(start_date, int) or len(str(start_date)) == 4:
            start_date = str(start_date) + '-01-01'
        if isinstance(end_date, int) or len(str(end_date)) == 4:
            end_date = str(end_date) + '-12-31'

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

            # Current date doesn't have close yet
            current_date = datetime.today().strftime('%Y-%m-%d')
            historical_data = historical_data[historical_data['Date'].astype(str).str[:10] != current_date]


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
    #fetch_and_save_historical_close("MSFT", "2014", "2024")
    fetch_and_save_historical_close(ticker, start_year, end_year)

#hist_prices("AAPL", "2014", "2024")