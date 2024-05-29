import pandas as pd
import numpy as np
from scipy.signal import spectrogram
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# Load the data
file_path = '/for/path/to/csv/for/example/insider_data/MSFT_encoded_data_expanded.csv'
data = pd.read_csv(file_path)

# Define the list of possible date columns
possible_date_columns = ['transactionDate', 'Effective Date', 'periodOfReport']

# Determine the best date for each row
def find_first_valid_date(row):
    for date_col in possible_date_columns:
        if date_col in row and pd.notna(row[date_col]):
            return pd.to_datetime(row[date_col])
    return pd.NaT

# Apply the function row-wise
data['best_date'] = data.apply(find_first_valid_date, axis=1)
if data['best_date'].isna().any():
    raise ValueError("Some rows lack a valid date even after trying all specified fallbacks.")

# Prepare other data fields
data['sign'] = data['transaction_1_Disposed_2_Acquired'].apply(lambda x: 1 if x == 1 else -1)
data['adjusted_magnitude'] = data['transactionShares'].replace(-1, np.nan) * data['sign']
data['is_placeholder'] = data['transactionShares'] == -1

# Ensure `is_placeholder` is boolean
data['is_placeholder'] = data['is_placeholder'].astype(bool)

# Method for filling NaN values
data['adjusted_magnitude'] = data['adjusted_magnitude'].ffill()

# Aggregate data to handle duplicate dates
data = data.groupby('best_date').sum().reset_index()

# Sort data by the best available date
data = data.sort_values(by='best_date')

# Resample data to include all days
full_date_range = pd.date_range(start=data['best_date'].min(), end=data['best_date'].max(), freq='D')
full_data = data.set_index('best_date').reindex(full_date_range).fillna({'adjusted_magnitude': 0, 'is_placeholder': False}).reset_index().rename(columns={'index': 'best_date'})

# Ensure `is_placeholder` is boolean after resampling...
full_data['is_placeholder'] = full_data['is_placeholder'].astype(bool)

# Overall visualization setup
fig = make_subplots(rows=2, cols=1, subplot_titles=('Transaction Magnitudes Over Time', 'Spectrogram of Non-Placeholder Transactions'), vertical_spacing=0.15)

# Subplot 1: Transaction Magnitudes Over Time
fig.add_trace(go.Scatter(x=full_data['best_date'], y=full_data['adjusted_magnitude'], mode='lines', name='Transaction Magnitudes'), row=1, col=1)

# Spectrogram computation parameters
nperseg = 256  # Adjusted window size for better frequency resolution
noverlap = nperseg // 2
nfft = 512  # Larger FFT length for finer frequency resolution

# Subplot 2: Spectrogram for non-placeholder transactions
non_placeholder_data = full_data.loc[~full_data['is_placeholder'], 'adjusted_magnitude']
frequencies, times, Sxx = spectrogram(non_placeholder_data.values, fs=1, nperseg=nperseg, noverlap=noverlap, nfft=nfft, window='hann')
valid_indices = frequencies > 0
frequencies = frequencies[valid_indices]
Sxx = Sxx[valid_indices, :]
if Sxx.size > 0:
    periods = 1 / frequencies  # Convert frequencies to periods
    times_mapped = pd.to_datetime(full_data['best_date'].min() + pd.to_timedelta(times, unit='D'))
    intensity = 10 * np.log10(Sxx + 1e-10)
    if np.any(intensity != intensity[0, 0]):  # Check for significant data
        fig.add_trace(go.Heatmap(x=times_mapped, y=periods, z=intensity, colorscale='Viridis', showscale=False, name='Spectrogram'), row=2, col=1)

# Add vertical lines for year boundaries, quarter boundaries, and month boundaries
def add_vertical_lines(fig, start_date, end_date, row):
    for year in pd.date_range(start=start_date, end=end_date, freq='YE'):
        fig.add_vline(x=year, line=dict(color='black', width=2), row=row, col=1)
    for quarter in pd.date_range(start=start_date, end=end_date, freq='QE'):
        fig.add_vline(x=quarter, line=dict(color='blue', width=1.5, dash='dot'), row=row, col=1)
    for month in pd.date_range(start=start_date, end=end_date, freq='MS'):
        fig.add_vline(x=month, line=dict(color='gray', width=1, dash='dash'), row=row, col=1)

add_vertical_lines(fig, full_data['best_date'].min(), full_data['best_date'].max(), row=1)
add_vertical_lines(fig, full_data['best_date'].min(), full_data['best_date'].max(), row=2)

# Render the overall figure
fig.update_layout(title_text="Overall Transaction Analysis", height=800)
fig.show()

# Person-specific spectrograms
person_ids = data['person_ID'].unique()
person_spectrograms = []

for person_id in person_ids:
    person_data = data[data['person_ID'] == person_id]
    if len(person_data) < 5:
        continue
    person_data = person_data.groupby('best_date').sum().reset_index()
    person_data = person_data.sort_values(by='best_date')
    person_date_range = pd.date_range(start=person_data['best_date'].min(), end=person_data['best_date'].max(), freq='D')
    person_full_data = person_data.set_index('best_date').reindex(person_date_range).fillna({'adjusted_magnitude': 0, 'is_placeholder': False}).reset_index().rename(columns={'index': 'best_date'})
    person_full_data['is_placeholder'] = person_full_data['is_placeholder'].astype(bool)

    person_non_placeholder_data = person_full_data.loc[~person_full_data['is_placeholder'], 'adjusted_magnitude']
    if person_non_placeholder_data.empty:
        continue

    person_frequencies, person_times, person_Sxx = spectrogram(person_non_placeholder_data.values, fs=1, nperseg=nperseg, noverlap=noverlap, nfft=nfft, window='hann')
    valid_indices = person_frequencies > 0
    person_frequencies = person_frequencies[valid_indices]
    person_Sxx = person_Sxx[valid_indices, :]

    if person_Sxx.size == 0 or np.ptp(person_Sxx) < 1e-10:
        continue  # Skip if person_Sxx is empty or has no intensity differential

    person_spectrograms.append((person_id, person_frequencies, person_times, person_Sxx, person_full_data['best_date'].min()))

# Sort person spectrograms by range
person_spectrograms.sort(key=lambda x: np.ptp(x[3]), reverse=True)

# Plot person-specific spectrograms
if person_spectrograms:
    total_rows = 2 + len(person_spectrograms)  # Total rows: 2 overall + individual person spectrograms
    fig = make_subplots(rows=total_rows, cols=1, shared_xaxes=True, subplot_titles=['Transaction Magnitudes Over Time', 'Spectrogram of Non-Placeholder Transactions'] + [f'Spectrogram for Person ID {pid}' for pid, _, _, _, _ in person_spectrograms], vertical_spacing=0.02)

    # Add the existing overall subplots to the new figure
    fig.add_trace(go.Scatter(x=full_data['best_date'], y=full_data['adjusted_magnitude'], mode='lines', name='Transaction Magnitudes'), row=1, col=1)
    fig.add_trace(go.Heatmap(x=times_mapped, y=periods, z=intensity, colorscale='Viridis', showscale=False, name='Spectrogram'), row=2, col=1)

    add_vertical_lines(fig, full_data['best_date'].min(), full_data['best_date'].max(), row=1)
    add_vertical_lines(fig, full_data['best_date'].min(), full_data['best_date'].max(), row=2)

    for i, (pid, pf, pt, psxx, pdate) in enumerate(person_spectrograms):
        person_periods = 1 / pf
        person_times_mapped = pd.to_datetime(pdate + pd.to_timedelta(pt, unit='D'))
        fig.add_trace(go.Heatmap(z=10 * np.log10(psxx + 1e-10), x=person_times_mapped, y=person_periods, colorscale='Jet', showscale=False), row=i + 3, col=1)
        fig.update_yaxes(title_text='Period (days)', type='log', row=i + 3, col=1)
        fig.update_xaxes(title_text='Date', row=i + 3, col=1)  # Add "Date" subtitle

        # Add vertical lines for year, quarter, and month boundaries
        add_vertical_lines(fig, pdate, person_times_mapped.max(), row=i + 3)

    fig.update_layout(height=300 * total_rows, title_text="Transaction Analysis with Person-Specific Spectrograms")
    fig.show()
else:
    print("No valid person-specific spectrograms to display.")
