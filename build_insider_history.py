import pandas as pd
import random
from get_fundamentals import NASDAQ_fundamentals
from filter_fundamentals import filter
from get_historical_closing_prices import hist_prices
from ticker_to_encoded_csv import encode
from make_training_csv import make_data_file
from simple_correlation import test_association
from collapse_dates import collapse_ticker_data
from get_optimal_trade_length import analyze_trades

start_year = 2014
end_year = 2024
dates = f"{start_year}-{end_year}"
days_to_add = 2

NASDAQ_fundamentals()
filter()

filtered_df = pd.read_csv('filtered_NASDAQ_fundamentals.csv')
tickers = filtered_df.iloc[:, 0].tolist()

#random.shuffle(tickers)
tickers = ["UNFI"]

with open('finished.csv', 'r') as file:
    finished_tickers = set(file.read().splitlines())

for ticker in tickers:
    if ticker in finished_tickers:
        print(f"Skipping {ticker}, already processed.")
        continue

    try:
        print(f"\nStarting {ticker}...")
        hist_prices(ticker, start_year, end_year)
        encode(ticker, dates)
        make_data_file(ticker, days_to_add)
        #test_association(ticker)
        collapse_ticker_data(ticker)
        analyze_trades(ticker)
        with open('finished.csv', 'a') as file:
            file.write(f"{ticker}\n")

    except Exception as e:
        with open('fails.csv', 'a') as file:
            file.write(f"{ticker}\n")