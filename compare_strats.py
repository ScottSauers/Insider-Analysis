import pandas as pd
import numpy as np
from datetime import timedelta
from scipy.stats import ttest_ind

# Load the data
prices_df = pd.read_csv("prices.csv", parse_dates=['Date'], dayfirst=False)
buy_dates_df = pd.read_csv("buy_dates.csv", parse_dates=['Date'], dayfirst=False)

def find_closest_trading_date(target_date, prices_df, direction='forward'):
    if direction == 'forward':
        closest_dates = prices_df[prices_df['Date'] >= target_date]
        if not closest_dates.empty:
            return closest_dates.iloc[0]['Date']
    else:  # direction == 'backward'
        closest_dates = prices_df[prices_df['Date'] <= target_date]
        if not closest_dates.empty:
            return closest_dates.iloc[-1]['Date']
    return target_date

# Strategy 1: Fixed buy dates and sell 1 week later
strategy1_profits = []
for buy_date in buy_dates_df['Date']:
    buy_date = find_closest_trading_date(buy_date, prices_df, 'forward')
    sell_date = find_closest_trading_date(buy_date + timedelta(days=250), prices_df, 'backward')

    buy_price = prices_df.loc[prices_df['Date'] == buy_date, 'Close'].iloc[0]
    sell_price = prices_df.loc[prices_df['Date'] == sell_date, 'Close'].iloc[0]

    profit = ((sell_price - buy_price) / buy_price) * 1
    strategy1_profits.append(profit)
    #print(f"profit: {profit}")

strategy1_initial_investment = len(buy_dates_df)
strategy1_roi_dollars = sum(strategy1_profits)
strategy1_roi_percent = (strategy1_roi_dollars / strategy1_initial_investment) * 100

# Strategy 2: Random buys, run 100 times
iterations = 100
strategy2_roi_dollars_list = []
strategy2_roi_percent_list = []

for _ in range(iterations):
    random_dates = np.random.choice(prices_df[(prices_df['Date'] >= '2017-01-01') & (prices_df['Date'] <= '2022-12-31')]['Date'], size=len(buy_dates_df), replace=False)
    strategy2_profits = []
    for buy_date in random_dates:
        buy_date = pd.to_datetime(buy_date)
        sell_date = find_closest_trading_date(buy_date + timedelta(days=250), prices_df, 'backward')

        buy_price = prices_df.loc[prices_df['Date'] == buy_date, 'Close'].iloc[0]
        sell_price = prices_df.loc[prices_df['Date'] == sell_date, 'Close'].iloc[0]

        profit = ((sell_price - buy_price) / buy_price) * 1
        strategy2_profits.append(profit)

    strategy2_roi_dollars = sum(strategy2_profits)
    strategy2_roi_percent = (strategy2_roi_dollars / len(buy_dates_df)) * 100

    strategy2_roi_dollars_list.append(strategy2_roi_dollars)
    strategy2_roi_percent_list.append(strategy2_roi_percent)

# Average ROI for strategy 2 over 100 iterations
avg_strategy2_roi_dollars = np.mean(strategy2_roi_dollars_list)
avg_strategy2_roi_percent = np.mean(strategy2_roi_percent_list)

# Hypothesis test on the last iteration for example comparison
t_stat, p_value = ttest_ind(strategy1_profits, strategy2_profits)
significant_diff = p_value < 0.05

print(f"Strategy 1 Initial Investment: ${strategy1_initial_investment}")
print(f"Strategy 1 ROI in Dollars: ${strategy1_roi_dollars:.2f}")
print(f"Average Strategy 2 ROI in Dollars (100 iterations): ${avg_strategy2_roi_dollars:.2f}")
print(f"Strategy 1 ROI Percent: {strategy1_roi_percent:.2f}%")
print(f"Average Strategy 2 ROI Percent (100 iterations): {avg_strategy2_roi_percent:.2f}%")
print(f"Hypothesis test (last iteration) shows significant difference: {'Yes' if significant_diff else 'No'} (p-value: {p_value:.5f})")
