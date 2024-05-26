import pandas as pd
from yahooquery import Ticker
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Common function to check processed tickers
def check_processed_tickers(output_file_path):
    if os.path.exists(output_file_path):
        processed_df = pd.read_csv(output_file_path)
        return set(processed_df['Ticker'])
    else:
        return set()

# Common function to process a ticker
def process_ticker(ticker, processed_tickers, output_file_path, silent):
    if ticker in processed_tickers:
        if not silent:
            print(f'{ticker} has already been processed. Skipping.')
        return

    if not silent:
        print(f'Processing {ticker}...')
    t = Ticker(ticker)

    # Initialize a dictionary to hold data for the current ticker
    ticker_data = {'Ticker': ticker}

    # Fetch and add data explicitly from each module
    try:
        financial_data = t.financial_data[ticker]
        key_stats = t.key_stats[ticker]
        share_purchase_activity = t.share_purchase_activity[ticker]

        # Add specific financial data attributes
        financial_attributes = [
            'currentPrice', 'totalCash', 'totalCashPerShare', 'ebitda',
            'totalDebt', 'quickRatio', 'currentRatio', 'totalRevenue', 'debtToEquity',
            'revenuePerShare', 'returnOnAssets', 'returnOnEquity',
            'freeCashflow', 'ebitdaMargins', 'profitMargins'
        ]
        for attr in financial_attributes:
            ticker_data[f'Financial_{attr}'] = financial_data.get(attr)

        # Add specific key stats attributes
        key_stats_attributes = [
            'enterpriseValue', 'sharesOutstanding', 'heldPercentInsiders',
            'priceToBook', 'enterpriseToEbitda'
        ]
        for attr in key_stats_attributes:
            ticker_data[f'KeyStats_{attr}'] = key_stats.get(attr)

        # Add specific share purchase activity attributes
        share_purchase_attributes = [
            'period', 'buyInfoCount', 'buyInfoShares', 'buyPercentInsiderShares',
            'sellInfoCount', 'sellInfoShares', 'sellPercentInsiderShares', 'netInfoCount',
            'netInfoShares', 'netPercentInsiderShares', 'totalInsiderShares'
        ]
        for attr in share_purchase_attributes:
            ticker_data[f'SharePurchase_{attr}'] = share_purchase_activity.get(attr)

    except Exception as e:
        print(f"Error processing {ticker}: {e}")

    # Write/Append the current ticker's data to the CSV
    df = pd.DataFrame([ticker_data])
    if not os.path.exists(output_file_path):
        df.to_csv(output_file_path, mode='w', header=True, index=False)
    else:
        df.to_csv(output_file_path, mode='a', header=False, index=False)

    if not silent:
        print(f'Finished processing {ticker}. Data saved.')

# Common function to fetch and process data
def fetch_and_process_data(input_file_path, output_file_path, silent, ticker_column_index=0, sep=',', encoding='utf-8'):
    # Read the input file to get the list of tickers
    tickers_df = pd.read_csv(input_file_path, sep=sep, encoding=encoding)
    tickers = tickers_df.iloc[:, ticker_column_index].tolist()

    # Determine which tickers have already been processed
    processed_tickers = check_processed_tickers(output_file_path)

    # Process tickers in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_ticker, ticker, processed_tickers, output_file_path, silent): ticker for ticker in tickers}
        for future in as_completed(futures):
            ticker = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error processing {ticker}: {e}")

    print(f'Completed processing all tickers. Data saved to {output_file_path}.')

# Function to process NASDAQ data
def NASDAQ_fundamentals(silent):
    fetch_and_process_data('NASDAQ.csv', 'NASDAQ_fundamentals.csv', silent)

# Function to process NYSE data
def NYSE_fundamentals(silent):
    fetch_and_process_data('NYSE_tickers.txt', 'NYSE_fundamentals.csv', silent, ticker_column_index=1, sep='\t', encoding='ISO-8859-1')

# Function to combine NASDAQ and NYSE data
def combine_fundamentals():
    nasdaq_file_path = 'NASDAQ_fundamentals.csv'
    nyse_file_path = 'NYSE_fundamentals.csv'
    combined_file_path = 'combined_fundamentals.csv'

    # Read the NASDAQ and NYSE data files
    nasdaq_df = pd.read_csv(nasdaq_file_path)
    nyse_df = pd.read_csv(nyse_file_path)

    # Combine the two dataframes
    combined_df = pd.concat([nasdaq_df, nyse_df])

    # Save the combined dataframe to a new CSV file
    combined_df.to_csv(combined_file_path, index=False)

    print('Combined data saved to combined_fundamentals.csv.')

# Main function to process and combine all data
def get_fundamentals(silent):
    NASDAQ_fundamentals(silent)
    NYSE_fundamentals(silent)
    combine_fundamentals()

if __name__ == '__main__':
    get_fundamentals(silent=0)