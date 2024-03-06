import yfinance as yf

# Create a Ticker object for "AAPL"
ticker = yf.Ticker("AAPL")

# List of method names to call with parentheses
methods_to_call = [
    "get_info",
    "get_balance_sheet",
    "get_capital_gains",
    "get_cash_flow",
    "get_dividends",
    "get_earnings_dates",
    "get_fast_info",
    "get_financials",
    "get_history_metadata",
    "get_income_stmt",
    "get_incomestmt",
    "get_insider_purchases",
    "get_insider_roster_holders",
    "get_insider_transactions",
    "get_institutional_holders",
    "get_isin",
    "get_major_holders",
    "get_mutualfund_holders",
    "get_news",
    "get_recommendations",
    "get_recommendations_summary",
    "get_shares_full",
    "get_splits",
    "history"
]

# Properties to access without parentheses
properties_to_access = [
    "quarterly_balance_sheet",
    "quarterly_cashflow",
    "quarterly_financials",
    "quarterly_income_stmt"
]

# Call methods and access properties, handle exceptions
for method in methods_to_call:
    try:
        print(f"\n{method}:")
        data = getattr(ticker, method)()
        print(data)
    except Exception as e:
        print(f"Could not retrieve data for {method}. Error: {e}")

for prop in properties_to_access:
    try:
        print(f"\n{prop}:")
        data = getattr(ticker, prop)
        print(data)
    except Exception as e:
        print(f"Could not access property {prop}. Error: {e}")
