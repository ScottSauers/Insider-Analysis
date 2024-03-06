import pandas as pd
from yahooquery import Ticker
import os

# Define file paths
input_file_path = 'NASDAQ.csv'
output_file_path = 'NASDAQ_fundamentals.csv'

# Check and return the set of processed tickers
def check_processed_tickers(output_file_path):
    if os.path.exists(output_file_path):
        processed_df = pd.read_csv(output_file_path)
        return set(processed_df['Ticker'])
    else:
        return set()

# Read the NASDAQ.csv file to get the list of tickers
tickers_df = pd.read_csv(input_file_path)
tickers = tickers_df.iloc[:, 0].tolist()

# Determine which tickers have already been processed
processed_tickers = check_processed_tickers(output_file_path)

# Iterate over each ticker to fetch and process data
for ticker in tickers:
    if ticker in processed_tickers:
        print(f'{ticker} has already been processed. Skipping.')
        continue

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
            'freeCashflow',
            'ebitdaMargins', 'profitMargins'
        ]
        for attr in financial_attributes:
            ticker_data[f'Financial_{attr}'] = financial_data.get(attr)

        # Add specific key stats attributes
        key_stats_attributes = [
            'enterpriseValue',
            'sharesOutstanding','heldPercentInsiders',
            'priceToBook',
            'enterpriseToEbitda'
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

    print(f'Finished processing {ticker}. Data saved.')

print('Completed processing all tickers. Data saved to NASDAQ_fundamentals.csv.')
