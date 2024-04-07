import pandas as pd
import os
from datetime import datetime
from get_prices import find_next_available_price
import matplotlib.pyplot as plt

def analyze_trades(ticker):
    current_dir = os.getcwd()
    data_file_path = os.path.join(current_dir, 'insider_data', f'{ticker}_encoded_data_expanded.csv')
    historical_data_path = os.path.join(current_dir, 'historical', f'{ticker}_historical_close.csv')

    if not os.path.exists(data_file_path):
        print(f"Data file not found for ticker {ticker}.")
        return

    if not os.path.exists(historical_data_path):
        print(f"Historical data file not found for ticker {ticker}.")
        return

    df = pd.read_csv(data_file_path)
    historical_df = pd.read_csv(historical_data_path)
    # Scan for date column with time included
    historical_df['Date'] = historical_df['Date'].astype(str)
    historical_df['Date'] = historical_df['Date'].apply(lambda x: x.split(' ')[0] if ' ' in x else x)
    # Parse date column
    historical_df['Date'] = pd.to_datetime(historical_df['Date'])
    historical_df.set_index('Date', inplace=True)

    criteria = (
        #(df['securityTitle_1_common_2_restricted_3_options'] < 3) &
        (pd.to_numeric(df['transactionShares']) > 0) &
        (pd.to_numeric(df['transactionPricePerShare']) > 0) &
        (df['transaction_1_Disposed_2_Acquired'] == 2) &
        (df['officerTitle_low_is_important'] < 5) &
        (df['0_gift_comp_vesting_1_other'] == 1)
    )

    filter = "Filtered for positive transaction shares and price per share, acquired, non-gift, non-compensation, non-vesting, officer title CFO, CEO, COB, president, VP, CMO, CSO"

    filtered_df = df.loc[criteria, ['Effective Date', 'Effective Date Price']].copy()

    print(f"Number of rows matching criteria: {len(filtered_df)}")

    if len(filtered_df) < 16:
        print(f"{len(filtered_df)} rows match the criteria for ticker {ticker}. Trying again...")
        criteria = (
            #(df['securityTitle_1_common_2_restricted_3_options'] < 2) &
            #(pd.to_numeric(df['transactionShares']) > 0) &
            #(pd.to_numeric(df['transactionPricePerShare']) > 0) &
            (df['transaction_1_Disposed_2_Acquired'] == 2) &
            #(df['officerTitle_low_is_important'] < 5) &
            (df['0_gift_comp_vesting_1_other'] == 1)
        )
        filtered_df = df.loc[criteria, ['Effective Date', 'Effective Date Price']].copy()
        print(f"Number of rows matching criteria: {len(filtered_df)}")
        filter = "Filtered for acquired, non-gift, non-compensation, non-vesting"


    if len(filtered_df) < 8:
        print(f"{len(filtered_df)} rows match the criteria for ticker {ticker}. Trying again...")
        criteria = (
            #(df['securityTitle_1_common_2_restricted_3_options'] < 2) &
            #(pd.to_numeric(df['transactionShares']) > 0) &
            #(pd.to_numeric(df['transactionPricePerShare']) > 0) &
            (df['transaction_1_Disposed_2_Acquired'] == 2)
            #(df['officerTitle_low_is_important'] < 5) &
            #(df['0_gift_comp_vesting_1_other'] == 1)
        )
        filtered_df = df.loc[criteria, ['Effective Date', 'Effective Date Price']].copy()
        print(f"Number of rows matching criteria: {len(filtered_df)}")
        filter = "Filtered for acquired"






    results = []

    for days_to_add in range(1, 365):  # Adjust the range as needed
        temp_df = filtered_df.copy()
        temp_df['Sale Date'] = pd.NaT
        temp_df['Sell Price'] = 0.0
        temp_df['Price Change'] = 0.0
        temp_df['Actual Days Difference'] = 0

        for index, row in temp_df.iterrows():
            effective_date = row['Effective Date']
            effective_date_price = row['Effective Date Price']
            #print(historical_df)
            sale_date, sell_price = find_next_available_price(effective_date, historical_df, days_to_add)

            #print(f"Effective Date: {effective_date}, Sale Date: {sale_date}, Sell Price: {sell_price}")

            if sale_date and sell_price:
                temp_df.at[index, 'Sale Date'] = sale_date
                temp_df.at[index, 'Sell Price'] = sell_price
                temp_df.at[index, 'Price Change'] = (sell_price - effective_date_price) / abs(effective_date_price)
                temp_df.at[index, 'Actual Days Difference'] = (pd.to_datetime(sale_date) - pd.to_datetime(effective_date)).days

        # Filter out rows with significant deviation in actual added days vs days to add
        temp_df = temp_df[abs(temp_df['Actual Days Difference'] - days_to_add) <= 3]

        #print(f"Number of rows after filtering: {len(temp_df)}")

        if not temp_df.empty:
            temp_df.loc[:, 'Price Change per Day'] = temp_df['Price Change'] / temp_df['Actual Days Difference']
            change_per_day_per_trade = temp_df['Price Change per Day'].sum() / len(temp_df)
            results.append({'Ticker': ticker, 'Days to Add': days_to_add, 'Change per Day per Trade': change_per_day_per_trade})
        else:
            print(f"No valid rows found for days_to_add: {days_to_add}")

    if not results:
        print(f"No results found for ticker {ticker}.")
        return

    # Save the results to a CSV file
    results_df = pd.DataFrame(results)

    # Create a line plot
    plt.figure(figsize=(12, 8))
    plt.plot(results_df['Days to Add'], results_df['Change per Day per Trade'], marker='o')

    # Set the title and labels
    plt.title('Change per Day per Trade vs. Days to Add')
    plt.xlabel('Days Until Sale')
    plt.ylabel('Average Change per Day After Buy')

    # Add a grid for better readability
    plt.grid(True)

    # Rotate the x-axis labels for better visibility
    plt.xticks(rotation=45)

    # Adjust the layout to prevent overlapping labels
    plt.tight_layout()


    dir_path = os.path.join(current_dir, 'insider_data/figures')
    os.makedirs(dir_path, exist_ok=True)
    plt.savefig(os.path.join(current_dir, 'insider_data/figures', f'{ticker}_trade_analysis_graph.png'))
    plt.close()
    plt.clf()

    results_file_path = os.path.join(current_dir, 'insider_data', f'{ticker}_trade_analysis_results.csv')
    results_df.to_csv(results_file_path, index=False)

    results_file_path = os.path.join(current_dir, 'insider_data', f'{ticker}_trade_analysis_results.csv')
    results_df.to_csv(results_file_path, index=False)

    #print(results_df)

    results_file_path = os.path.join(current_dir, 'insider_data', f'{ticker}_trade_analysis_results.csv')
    results_df.to_csv(results_file_path, index=False)

    # Get the top 5 rows with the highest change per day per trade
    top_5_rows = results_df.nlargest(5, 'Change per Day per Trade')

    # Create a new DataFrame to store the top 5 highest change per day per trade values and their corresponding days to add
    highest_change_df = pd.DataFrame(columns=['Ticker'] + [f'Number {i+1} Change per Day per Trade' for i in range(5)] + [f'Number {i+1} Highest Days to Add' for i in range(5)])

    # Populate the highest_change_df with the top 5 values and their corresponding days to add
    highest_change_df.at[0, 'Ticker'] = ticker
    for i, row in top_5_rows.iterrows():
        highest_change_df.at[0, f'Number {i+1} Change per Day per Trade'] = row['Change per Day per Trade']
        highest_change_df.at[0, f'Number {i+1} Highest Days to Add'] = row['Days to Add']

    # Append the highest change row to the existing CSV file
    csv_file_path = os.path.join(current_dir, 'insider_delay.csv')
    with open(csv_file_path, 'a') as f:
        highest_change_df.to_csv(f, header=f.tell()==0, index=False)

    print(f"Results saved to {csv_file_path} for ticker {ticker}.")

analyze_trades('AAPL')