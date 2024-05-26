import pandas as pd

def filter():
    # Load the dataset
    #df = pd.read_csv('NASDAQ_fundamentals.csv')
    df = pd.read_csv('combined_fundamentals.csv')

    # Initial number of stocks
    total_stocks_before = len(df)

    # Filter out rows where 'Financial_currentPrice' is zero, NA, or where 'KeyStats_enterpriseValue' does not meet the conditions
    filtered_df = df[(df['Financial_currentPrice'].notna()) & (df['Financial_currentPrice'] != 0) &
                    (df['KeyStats_enterpriseValue'].notna()) & (df['KeyStats_enterpriseValue'] < 25_000_000) &
                    (df['KeyStats_enterpriseValue'] != 0)]

    # Number of stocks after filtering
    total_stocks_after = len(filtered_df)

    # Calculate the percentage of stocks filtered out
    percentage_filtered_out = ((total_stocks_before - total_stocks_after) / total_stocks_before) * 100

    # Save the filtered dataframe to a new CSV file
    filtered_df.to_csv('filtered_combined_fundamentals.csv', index=False)

    # Print the results
    print("Filtered data saved to filtered_combined_fundamentals.csv.")
    print(f"Total stocks before filter: {total_stocks_before}")
    print(f"Percentage of total stocks filtered out: {percentage_filtered_out:.2f}%")
    print(f"Total stocks after filter: {total_stocks_after}")