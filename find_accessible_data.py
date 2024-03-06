import yfinance as yf

# Create a Ticker instance
ticker = yf.Ticker("AAPL")

# Get all attributes of the Ticker object
ticker_attrs = dir(ticker)

print("Accessible Fundamentals:")

# Iterate over all attributes
for attr in ticker_attrs:
    try:
        # Check if the attribute is a method
        attr_value = getattr(ticker, attr)
        if callable(attr_value):
            try:
                # Call the method and get its keys
                method_result = attr_value()
                if isinstance(method_result, dict):
                    print(f"\n{attr}:")
                    for key in method_result.keys():
                        print(f"- {key}")
            except Exception as e:
                # Print the exception message for debugging
                print(f"Error calling '{attr}': {e}")
    except Exception as e:
        # Print the exception message for debugging
        print(f"Error getting attribute '{attr}': {e}")
