import pandas as pd
import numpy as np
from datetime import timedelta
import statistics
from scipy.stats import ttest_ind, mannwhitneyu, ks_2samp, ttest_ind_from_stats, bootstrap
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import random
import os

from get_prices import find_next_available_price, get_buy_date, get_sell_price



def evaluate_strategy(ticker, predictions_df, sell_timedelta):
    prices_file_path = os.path.join(os.getcwd(), 'historical', f"{ticker}_historical_close.csv")
    prices_df = pd.read_csv(prices_file_path)
    pd.set_option('display.max_rows', 20, 'display.max_columns', 16)

    # Convert date columns to datetime format across all dataframes
    predictions_df['Date'] = pd.to_datetime(predictions_df['Date'])
    prices_df['Date'] = prices_df['Date'].astype(str).str[:10]
    prices_df['Date'] = pd.to_datetime(prices_df['Date'])

    # Ensure the 'Date' column is set as the index for prices_df if not already set
    if 'Date' in prices_df.columns:
        prices_df.set_index('Date', inplace=True)
    elif prices_df.index.name != 'Date' and 'Date' not in prices_df.columns:
        raise ValueError("DataFrame index is not 'Date', and 'Date' column is not present.")

    # Merge the predictions_df and prices_df on 'Date'
    merged_df = pd.merge(predictions_df, prices_df, left_on='Date', right_index=True, how='left')

    print(f"Number of rows in merged_df: {len(merged_df)}")

    positive_change_sum = sum(merged_df['Predicted Price Change'] > 0)

    if positive_change_sum == 0:
        insider_strategy_initial_investment = 2
        print("insider_strategy_initial_investment", insider_strategy_initial_investment)
    else:
        insider_strategy_initial_investment = sum(merged_df['Predicted Price Change'] > 0)
        print("insider_strategy_initial_investment", insider_strategy_initial_investment)

    print(f"Number of rows with positive predicted price change: {insider_strategy_initial_investment}")


    # Initialize variables for Insider Buy Strategy calculations
    insider_strategy_profits = []
    total_investment = 100  # Total investment amount

    top_two_predicted_changes = merged_df['Predicted Price Change'].nlargest(2).values

    number_of_unique_dates = merged_df['Date'].nunique()

    print(f'Number of unique dates: {number_of_unique_dates}')

    for _, row in merged_df.iterrows():
        if row['Predicted Price Change'] > 0 or row['Predicted Price Change'] in top_two_predicted_changes:
            #print(row['Predicted Price Change'])
            buy_date = row['Date']
            actual_buy_date, buy_price = get_buy_date(buy_date, prices_df)

            try:
                sell_date, sell_price = find_next_available_price(actual_buy_date, prices_df, sell_timedelta)
            except (KeyError, TypeError, ValueError) as e:
                print(f"Error occurred while finding next available price: {str(e)}")
                continue

            if isinstance(sell_price, (float, int)) and isinstance(buy_price, (float, int)):
                if pd.notnull(sell_price) and pd.notnull(buy_price):
                    profit = (sell_price - buy_price) / buy_price
                    insider_strategy_profits.append(profit)
                else:
                    print(f"[Insider] Invalid sell_price or buy_price: sell_price={sell_price}, buy_price={buy_price}")
                    print("buy_date", buy_date)

            #insider_strategy_initial_investment += 1

    # After iterating through all rows, calculate the total profit and ROI for Insider Buy Strategy
    insider_strategy_total_profit = sum(insider_strategy_profits)
    if insider_strategy_initial_investment > 0:
        investment_per_trade = total_investment / insider_strategy_initial_investment
        insider_strategy_roi_percent = (insider_strategy_total_profit / insider_strategy_initial_investment) * 100
        insider_strategy_roi_dollars = total_investment * (insider_strategy_roi_percent / 100)
    else:
        investment_per_trade = 0
        insider_strategy_roi_dollars = 0
        insider_strategy_roi_percent = 0




    #print(range(insider_strategy_initial_investment))
    #print(range(len(insider_strategy_profits)))

    #iterations = (range(len(insider_strategy_profits)))
    iterations = 100
    #print(iterations)

    # Initialize variables for Random Buy Strategy calculations
    total_investments_per_iteration = []
    total_profits_per_iteration = []
    roi_dollars_per_iteration = []
    roi_percent_per_iteration = []
    number_of_profitable_trades_per_iteration = []
    all_random_strategy_profits = []
    random_walks = []

    total_investment = 100

    # Get the first and last dates from the insider strategy
    first_date = merged_df['Date'].min()
    last_date = merged_df['Date'].max()

    for _ in range(iterations):
        random_strategy_profits = []

        positive_change_sum = sum(merged_df['Predicted Price Change'] > 0)

        if positive_change_sum == 0:
            random_strategy_initial_investment = 2
        else:
            random_strategy_initial_investment = sum(merged_df['Predicted Price Change'] > 0)
        #print("random_strategy_initial_investment", random_strategy_initial_investment)
        random_trade_counter = 0
        #print("range: ", insider_strategy_initial_investment)
        #print(range(insider_strategy_initial_investment))
        for _ in range(insider_strategy_initial_investment):
            #print("Loop.")
            buy_date = pd.to_datetime(np.random.uniform(first_date.timestamp(), last_date.timestamp()), unit='s').normalize()
            try:
                actual_buy_date, buy_price = get_buy_date(buy_date, prices_df)

                if actual_buy_date is not None and buy_price is not None:
                    sell_date, sell_price = find_next_available_price(actual_buy_date, prices_df, sell_timedelta)

                    if pd.notnull(sell_price) and pd.notnull(buy_price):
                        profit = (sell_price - buy_price) / buy_price
                        random_strategy_profits.append(profit)
                        all_random_strategy_profits.append(profit)
                        random_trade_counter += 1
                        #print("2", random_strategy_initial_investment)
                    else:
                        print(f"Invalid sell_price or buy_price: sell_price={sell_price}, buy_price={buy_price}")
                        print("buy_date", buy_date)
                        print("actual_buy_date", actual_buy_date)

                else:
                    print(f"No valid buy date found for {buy_date}")
            except (KeyError, TypeError, ValueError) as e:
                print("actual_buy_date", actual_buy_date)
                print("buy_price", buy_price)
                print("buy_date", buy_date)
                print("prices_df", prices_df)
                print(f"[Random strat] Error occurred while finding next available price: {str(e)}")
                continue

            #random_strategy_initial_investment += 1

        #print("random_strategy_profits, ", random_strategy_profits)
        # After iterating, collect the values
        random_walks.append(random_strategy_profits)
        #print("random walks: ", random_walks)
        #len(random_walks)
        #print(random_walks)
        total_investment = random_strategy_initial_investment * investment_per_trade
        random_strategy_total_profit = sum(random_strategy_profits)
        random_investment_per_trade = total_investment / random_strategy_initial_investment
        random_strategy_roi_percent = (random_strategy_total_profit / random_strategy_initial_investment) * 100
        random_strategy_roi_dollars = total_investment * (random_strategy_roi_percent / 100)

        # Append the iteration's results to the respective lists
        total_investments_per_iteration.append(total_investment)
        total_profits_per_iteration.append(random_strategy_total_profit)
        roi_dollars_per_iteration.append(random_strategy_roi_dollars)
        roi_percent_per_iteration.append(random_strategy_roi_percent)
        number_of_profitable_trades_per_iteration.append(sum(profit > 0 for profit in random_strategy_profits))

    # Calculate the averages after all iterations
    average_total_investment = sum(total_investments_per_iteration) / len(total_investments_per_iteration)
    average_total_profit = sum(total_profits_per_iteration) / len(total_profits_per_iteration)
    average_roi_dollars = sum(roi_dollars_per_iteration) / len(roi_dollars_per_iteration)
    average_roi_percent = sum(roi_percent_per_iteration) / len(roi_percent_per_iteration)
    average_number_of_profitable_trades = sum(number_of_profitable_trades_per_iteration) / len(number_of_profitable_trades_per_iteration)

    sd_total_investment = statistics.stdev(total_investments_per_iteration)
    sd_total_profit = statistics.stdev(total_profits_per_iteration)
    sd_roi_dollars = statistics.stdev(roi_dollars_per_iteration)
    sd_roi_percent = statistics.stdev(roi_percent_per_iteration)
    sd_number_of_profitable_trades = statistics.stdev(int(x) for x in number_of_profitable_trades_per_iteration)


    # Print the averaged results
    print(f"\nRandom Number of Trades: {random_trade_counter}")
    print(f"Random Strategy Investment per Trade: ${random_investment_per_trade:.4f}")
    print(f"Random ROI in Dollars: ${average_roi_dollars:.3f} (SD: ${sd_roi_dollars:.1f})")
    print(f"Random ROI Percent: {average_roi_percent:.6f}% (SD: {sd_roi_percent:.1f}%)")
    print(f"Random Number of Profitable Trades: {average_number_of_profitable_trades:.2f} (SD: {sd_number_of_profitable_trades:.1f})")
    print(f"Random Total Profit: ${average_total_profit:.4f} (SD: ${sd_total_profit:.1f})")


    # Print the summarized results for Insider Buy Strategy
    #print(insider_strategy_profits)
    print(f"\nInsider Number of Trades: {len(insider_strategy_profits)}")
    print(f"Insider Investment per Trade: ${investment_per_trade:.4f}")
    print(f"Insider ROI in Dollars: ${insider_strategy_roi_dollars:.3f}")
    print(f"Insider ROI Percent: {insider_strategy_roi_percent:.6f}%")
    print(f"Insider Number of Profitable Trades: {sum(profit > 0 for profit in insider_strategy_profits)}")
    print(f"Insider Total Profit: ${sum(insider_strategy_profits)}")



    # Conduct significance tests to compare the two strategies

    print("\nDISTRIBUTION vs. DISTRIBUTION TESTS")


    # Mann-Whitney U test for ROI percent
    # Testing if the distribution of insider strategy profits is higher
    u_stat_roi_percent, p_value_mannwhitney = mannwhitneyu(insider_strategy_profits, all_random_strategy_profits, alternative='greater')
    print(f"\nMann-Whitney U test for ROI percent:")
    print(f"p-value: {p_value_mannwhitney:.8f}")

    # Welch's t-test for ROI percent
    # Compares means with unequal variances, testing if insider strategy profits are higher
    welch_t_stat_roi_percent, welch_p_value_roi_percent = ttest_ind_from_stats(
        np.mean(insider_strategy_profits), np.std(insider_strategy_profits, ddof=1), len(insider_strategy_profits),
        np.mean(all_random_strategy_profits), np.std(all_random_strategy_profits, ddof=1), len(all_random_strategy_profits),
        alternative='greater'
    )
    print(f"\nWelch's t-test for ROI percent:")
    print(f"p-value: {welch_p_value_roi_percent:.8f}")

    # Kolmogorov-Smirnov test for ROI percent
    # Testing if the distribution of insider strategy profits is stochastically greater
    #ks_stat_roi_percent, p_value_ks = ks_2samp(insider_strategy_profits, all_random_strategy_profits, alternative='greater')
    #print(f"\nKolmogorov-Smirnov test for ROI percent:")
    #print(f"p-value: {p_value_ks:.8f}")






    insider_roi_percent_array = np.array(insider_strategy_profits)
    all_random_strategy_profits_array = np.array(all_random_strategy_profits)

    # Create a figure with 1 row and 2 columns
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Random Walks vs. Insider Strategy", "Normalized Histogram of ROI Percent"))

    #print(insider_strategy_profits)
    # Plot the main walk (insider_strategy_profits)
    cumulative_profits = [0] + [sum(insider_strategy_profits[:i+1]) for i in range(len(insider_strategy_profits))]
    #print("cumulative_profits", cumulative_profits)
    fig.add_trace(go.Scatter(x=list(range(len(cumulative_profits))), y=cumulative_profits,
                            mode='lines', name='Insider Strategy', line=dict(width=3, color='#FF5733')), row=1, col=1)

    for walk in random_walks:
        #print(walk)
        #print(range(len(walk)))
        #print(len(walk))
        cumulative_walk = [0] + [sum(walk[:i+1]) for i in range(len(walk))]
        final_value = cumulative_walk[-1]

        # Use matplotlib to get a colormap value, then scale RGB values to 0-255
        color = plt.cm.rainbow(final_value / max(all_random_strategy_profits_array))
        color_scaled = [int(c * 255) for c in color[:3]]  # Scale RGB to 0-255
        alpha = 0.1  # Set a fixed translucent level for visibility
        color_str = 'rgba({}, {}, {}, {})'.format(*color_scaled, alpha)  # Format with fixed alpha

        # Adding the trace with the corrected color format and fixed translucency
        fig.add_trace(go.Scatter(x=list(range(len(cumulative_walk))), y=cumulative_walk,
                                mode='lines', name='Random Walk',
                                line=dict(width=0.8, color=color_str),
                                showlegend=False))



    # Set the layout for the first subplot
    fig.update_xaxes(
        title_text='Step', 
        gridcolor='rgba(240, 240, 240, 0.5)',  # Translucent gridlines
        zerolinecolor='#F0F0F0', 
        dtick=1,  # Place a gridline at every integer value
        ticklen=0,  # Remove ticks
        gridwidth=2,  # Thinner gridlines
        showticklabels=False,  # Do not show tick labels
        row=1, col=1
    )

    fig.update_yaxes(
        title_text='Cumulative Value', 
        gridcolor='#F0F0F0', 
        zerolinecolor='#F0F0F0', 
        row=1, col=1
    )



    # Plot the normalized histogram for Insider Strategy
    fig.add_trace(go.Histogram(x=insider_roi_percent_array, nbinsx=20, name='Insider Strategy', marker_color='#FF5733',
                            opacity=0.6, histnorm='probability density'), row=1, col=2)

    # Plot the normalized histogram for All Random Strategy Profits
    fig.add_trace(go.Histogram(x=all_random_strategy_profits_array, nbinsx=20, name='All Random Strategy Profits',
                            marker_color='#4682B4', opacity=0.6, histnorm='probability density'), row=1, col=2)

    # Set the layout for the second subplot
    fig.update_xaxes(title_text='ROI Percent', gridcolor='#F0F0F0', zerolinecolor='#F0F0F0', row=1, col=2)
    fig.update_yaxes(title_text='Density', gridcolor='#F0F0F0', zerolinecolor='#F0F0F0', row=1, col=2)

    # Update the overall layout
    fig.update_layout(
        title=(f"Random Buying vs. Insider Buying Strategy (same hold period) for ${ticker}"),
        plot_bgcolor='#FFFFFF',
        paper_bgcolor='#FFFFFF',
        font=dict(family='Arial', size=14),
        legend=dict(x=0, y=1, orientation='h', bgcolor='rgba(255, 255, 255, 0.8)'),
        width=1200,
        height=600,
        margin=dict(l=80, r=80, t=100, b=80)
    )

    # Display the plot in a new window
    fig.show(renderer='browser')