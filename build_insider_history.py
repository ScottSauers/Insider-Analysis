import pandas as pd
import random
from get_fundamentals import NASDAQ_fundamentals
from filter_fundamentals import filter
from get_historical_closing_prices import hist_prices
from ticker_to_encoded_csv import encode
from make_training_csv import make_data_file
from simple_correlation import test_association

start_year = 2014
end_year = 2024
dates = f"{start_year}-{end_year}"
days_to_add = 300

NASDAQ_fundamentals()
filter()

filtered_df = pd.read_csv('filtered_NASDAQ_fundamentals.csv')
tickers = filtered_df.iloc[:, 0].tolist()

random.shuffle(tickers)
tickers = ["FBIO"]

for ticker in tickers:
    print(f"\nStarting {ticker}...")
    hist_prices(ticker, start_year, end_year)
    encode(ticker, dates)
    make_data_file(ticker, days_to_add)
    test_association(ticker)