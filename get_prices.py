from datetime import datetime, timedelta
import pandas as pd


# finds date AT date, and goes earlier if not found
def get_buy_date(date, historical_prices_df):
    #("Starting get_buy_date...")
    if date in historical_prices_df.index:
        try:
            return date, historical_prices_df.loc[date, 'Close']
        except (KeyError, TypeError, ValueError):
            return date, historical_prices_df.loc[date, 'Close'].iloc[0]
    else:
        current_date = date
        while current_date not in historical_prices_df.index:
            current_date -= timedelta(days=1)
            if current_date < historical_prices_df.index.min():
                print("Cannot get price: date before min price df")
                return None, None
        try:
            return current_date, historical_prices_df.loc[current_date, 'Close']
        except (KeyError, TypeError, ValueError):
            return current_date, historical_prices_df.loc[current_date, 'Close'].iloc[0]

# finds date AT ideal sell date, fall back to BEFORE, final fall back to AFTER
def get_sell_price(prices_df, sell_date):
    # Extract rows from prices_df where the date matches sell_date
    matching_rows = prices_df.loc[prices_df['Date'] == sell_date]

    if len(matching_rows) > 0:
        sell_price = matching_rows['Close'].iloc[0]
        return sell_price
    else:
        # If no rows match sell_date, look for the last available price before sell_date
        last_available_before = prices_df[prices_df['Date'] < sell_date].tail(1)
        if len(last_available_before) > 0:
            sell_price = last_available_before['Close'].iloc[0]
            return sell_price
        else:
            # As a final fallback, find the next available trading day after sell_date
            next_available_after = prices_df[prices_df['Date'] > sell_date].head(1)
            if len(next_available_after) > 0:
                sell_price = next_available_after['Close'].iloc[0]
                return sell_price
            else:
                # If this branch is reached, prices_df is unexpectedly empty or sell_date is outside the range of dates in prices_df
                raise ValueError("sell_date is outside the available date range in prices_df.")

# finds date AT or BEFORE date
def find_price_for_date(date, historical_prices_df):
    current_date = date
    #print("Starting find_price_for_date...")
    if date in historical_prices_df.index:
        return date, historical_prices_df.loc[date, 'Close']
    else:
        while current_date not in historical_prices_df.index:
            current_date -= timedelta(days=1)
            if current_date < historical_prices_df.index.min():
                return None, None
        return current_date, historical_prices_df.loc[current_date, 'Close']

# finds date available for sale and price
def find_next_available_price(effective_date, historical_prices_df, days_to_add):
    try:
        # Convert the index of historical_prices_df to datetime if it's not already
        if not isinstance(historical_prices_df.index, pd.DatetimeIndex):
            historical_prices_df.index = pd.to_datetime(historical_prices_df.index)

        # Convert effective_date to datetime if it's not already
        if not isinstance(effective_date, pd.Timestamp):
            effective_date = pd.to_datetime(effective_date)

        current_date = effective_date + pd.Timedelta(days=days_to_add)

        if current_date > historical_prices_df.index.max():
            # If the current_date is beyond the available dates, find the last available price
            last_available_date = historical_prices_df.index.max()
            sell_price = historical_prices_df.loc[last_available_date, 'Close']
            if isinstance(sell_price, pd.Series):
                sell_price = sell_price.sample().iloc[0]
            return last_available_date, sell_price

        while current_date not in historical_prices_df.index:
            current_date += pd.Timedelta(days=1)

        sell_price = historical_prices_df.loc[current_date, 'Close']
        
        # If sell_price is a Series (multiple dates on one day), randomly select a value
        if isinstance(sell_price, pd.Series):
            sell_price = sell_price.sample().iloc[0]
        
        return current_date, sell_price

    except (KeyError, TypeError, ValueError) as e:
        print(f"Error occurred while finding next available price: {str(e)}")
        # Return the last available date and price if an error occurs
        last_available_date = historical_prices_df.index.max()
        sell_price = historical_prices_df.loc[last_available_date, 'Close']
        
        # If sell_price is a Series (multiple dates on one day), randomly select a value
        if isinstance(sell_price, pd.Series):
            sell_price = sell_price.sample().iloc[0]
        
        return last_available_date, sell_price