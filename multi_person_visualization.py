# if you make this different plots, it's way faster

import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from scipy.stats import pearsonr, spearmanr

# Load data
data = pd.read_csv('/Users/scott/Downloads/NASDAQ-main/insider_data/MSFT_encoded_data_expanded.csv', parse_dates=['Effective Date'])
data.set_index('Effective Date', inplace=True)
data.sort_index(inplace=True)

# Filter data for the years 2013 to 2017
data = data[(data.index >= '2013-01-01') & (data.index <= '2017-12-31')]

# Ensure unique daily data per person by aggregating transactions
data['Day'] = data.index.date
grouped = data.groupby(['person_ID', 'Day']).agg({'transactionShares': 'sum', 'transaction_1_Disposed_2_Acquired': 'first'}).reset_index()
grouped['Day'] = pd.to_datetime(grouped['Day'])
grouped.set_index('Day', inplace=True)

# Function to calculate alignment scores for individual transactions
def calculate_alignment_score(data_daily, period, offset):
    period_starts = pd.date_range(start=data_daily.index.min(), end=data_daily.index.max(), freq=period) + pd.DateOffset(days=offset)
    aligned_data = data_daily.reindex(period_starts, fill_value=0)
    if aligned_data.std() == 0 or len(aligned_data) < 2:
        return np.nan, np.nan, [], np.nan, np.nan  # Avoid constant input warning
    score, p_value = pearsonr(aligned_data, aligned_data.shift(fill_value=aligned_data.mean()))
    spearman_corr, spearman_p = spearmanr(aligned_data, aligned_data.shift(fill_value=aligned_data.mean()))
    return score, p_value, period_starts, spearman_corr, spearman_p

# Function to evaluate and visualize data for an individual
def evaluate_and_visualize(data_daily, title, row, fig):
    if data_daily.empty or data_daily.index.min() is pd.NaT or data_daily.index.max() is pd.NaT:
        print(f"No data available for {title}. Skipping...")
        return

    periods = {'MS': 31, 'QS': 92, 'YS': 365}
    best_results = {}

    for period, max_offset in periods.items():
        best_score = -np.inf
        best_offset = None
        best_p_value = None
        best_spearman_corr = None
        best_spearman_p = None

        for offset in range(max_offset):
            score, p_value, period_starts, spearman_corr, spearman_p = calculate_alignment_score(data_daily, period, offset)
            if score > best_score:
                best_score = score
                best_offset = offset
                best_p_value = p_value
                best_spearman_corr = spearman_corr
                best_spearman_p = spearman_p

        if best_offset is not None:
            best_results[period] = (best_offset, best_score, best_p_value, best_spearman_corr, best_spearman_p)

    # Determine best period and offset
    if best_results:
        period, (offset, score, p_value, spearman_corr, spearman_p) = max(best_results.items(), key=lambda item: item[1][1])
        period_starts = pd.date_range(start=data_daily.index.min(), end=data_daily.index.max(), freq=period) + pd.DateOffset(days=offset)

        # Calculate true positive rate
        true_signals = data_daily.index
        tp_count = sum([1 for date in period_starts if any(abs((date - ts).days) <= 2 for ts in true_signals)])
        tpr = tp_count / len(period_starts) if not period_starts.empty else 0

        # Print results for the best found period
        period_desc = {
            'MS': 'month',
            'QS': 'quarter',
            'YS': 'year'
        }
        print(f"{title} - Best Period: {period_desc[period]}, Offset: {offset}, Score: {score:.2f}, P-Value: {p_value:.2e}, Spearman Corr: {spearman_corr:.2f}, Spearman P: {spearman_p:.2e}, True Positive Rate: {tpr:.2%}")

        # Add trace for transaction volume
        fig.add_trace(go.Scatter(x=data_daily.index, y=data_daily, mode='lines', name=f'{title} Volume'), row=row, col=1)

        # Add green lines for the detected periodic predictions
        for date in period_starts:
            fig.add_vline(x=date, line=dict(color='green', width=2), row=row, col=1)

        # Add annotations
        fig.add_annotation(
            x=0.5, y=-0.2, xref='paper', yref='paper', showarrow=False, align='center', 
            text=f"Period: Every {offset+1} day of each {period_desc[period]}, Score: {score:.2f}, P-Value: {p_value:.2e}, True Positive Rate: {tpr:.2%}",
            row=row, col=1
        )

    # Add thin black lines for each month
    months = pd.date_range(start='2013-01-01', end='2017-12-31', freq='MS')
    for month in months:
        fig.add_vline(x=month, line=dict(color='black', width=1), row=row, col=1)

# Get unique person IDs
unique_person_ids = grouped['person_ID'].unique()

# Create a figure with multiple subplots
fig = make_subplots(rows=len(unique_person_ids) * 2, cols=1)

# Iterate over each individual in the dataset
for idx, person_id in enumerate(unique_person_ids):
    individual_data = grouped[grouped['person_ID'] == person_id]
    
    # Separate data into buys and sells
    buys = individual_data[individual_data['transaction_1_Disposed_2_Acquired'] == 2]
    sells = individual_data[individual_data['transaction_1_Disposed_2_Acquired'] == 1]
    
    # Resample to daily sums
    buys_daily = buys.resample('D').sum()['transactionShares'].fillna(0)
    sells_daily = sells.resample('D').sum()['transactionShares'].fillna(0)
    
    # Process buys and sells
    evaluate_and_visualize(buys_daily, f"Buys (Person {person_id})", idx * 2 + 1, fig)
    evaluate_and_visualize(sells_daily, f"Sells (Person {person_id})", idx * 2 + 2, fig)

# Update layout and axes
fig.update_layout(title='Transaction Volume Analysis for All Individuals', height=900 * len(unique_person_ids), showlegend=True)
fig.update_xaxes(range=['2013-01-01', '2017-12-31'])
fig.update_yaxes(type="log")

# Show the figure
fig.show()
