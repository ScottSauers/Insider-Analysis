import os
import pandas as pd
from scipy.stats import ttest_1samp
from scipy.stats import pearsonr, spearmanr

def test_association(ticker):
    def load_and_preprocess(csv_path):
        df = pd.read_csv(csv_path)
        # Ensure 'total_dollar_amount' is numeric to avoid issues with non-numeric types
        df['total_dollar_amount'] = pd.to_numeric(df['total_dollar_amount'], errors='coerce')
        # Drop rows where 'Price Change' or 'total_dollar_amount' is NaN to ensure accurate calculations
        return df.dropna(subset=['Price Change', 'total_dollar_amount'])

    def perform_test(df, condition_desc):
        # Ensure we are working with non-empty DataFrame for meaningful t-test
        if not df.empty:
            mean_price_change = df['Price Change'].mean()
            print(f"Average Price Change ({condition_desc}): {mean_price_change}")
            t_stat, p_value = ttest_1samp(df['Price Change'], 0, alternative='greater')
            print(f"P-value ({condition_desc}): {p_value}\n")
        else:
            print(f"No data available for t-test ({condition_desc}).")

    csv_path = os.path.join(os.getcwd(), 'insider_data', f"{ticker}_encoded_data.csv")

    # Original Test
    df_original = load_and_preprocess(csv_path)
    original_condition = (df_original['0_gift_comp_vesting_1_other'] == 1) & (df_original['transaction_1_Disposed_2_Acquired'] == 2)
    df_original_filtered = df_original[original_condition]
    perform_test(df_original_filtered, "Original")
    df_original_filtered[['Effective Date', 'Price Change']].to_csv(os.path.join(os.getcwd(), 'insider_data', f"{ticker}_price_change_analysis.csv"), index=False)
    print(f"Filtered data saved to {os.path.join(os.getcwd(), 'insider_data', f'{ticker}_price_change_analysis.csv')}\n")

    # Test for Top 50% Total Dollar Amount
    df_top50 = load_and_preprocess(csv_path)
    median_value = df_top50['total_dollar_amount'][df_top50['total_dollar_amount'] > 0].median()
    top_50_condition = (df_top50['total_dollar_amount'] > median_value) & (df_top50['0_gift_comp_vesting_1_other'] == 1) & (df_top50['transaction_1_Disposed_2_Acquired'] == 2)
    df_top50_filtered = df_top50[top_50_condition]
    perform_test(df_top50_filtered, "Top 50% Total Dollar Amount")

    # Test for Non-Zero Total Dollar Amount
    df_non_zero = load_and_preprocess(csv_path)
    non_zero_condition = (df_non_zero['total_dollar_amount'] > 0) & (df_non_zero['0_gift_comp_vesting_1_other'] == 1) & (df_non_zero['transaction_1_Disposed_2_Acquired'] == 2)
    df_non_zero_filtered = df_non_zero[non_zero_condition]
    perform_test(df_non_zero_filtered, "Non-Zero Total Dollar Amount")



    def correlation_test(ticker):
        # Dynamically generate the CSV filename from the ticker
        csv_path = os.path.join(os.getcwd(), 'insider_data', f"{ticker}_encoded_data.csv")

        # Load the CSV into a DataFrame
        df = pd.read_csv(csv_path)

        # Preprocess: Ensure 'total_dollar_amount' is numeric and drop NaNs
        df['total_dollar_amount'] = pd.to_numeric(df['total_dollar_amount'], errors='coerce')
        df.dropna(subset=['Price Change', 'total_dollar_amount'], inplace=True)

        # Ensure there is sufficient data for correlation tests
        if df.shape[0] > 2:
            # Pearson Correlation Test
            pearson_corr, pearson_p_value = pearsonr(df['total_dollar_amount'], df['Price Change'])
            print(f"Pearson Correlation (Total Dollar Amount vs. Price Change): {pearson_corr:.4f}, P-value: {pearson_p_value:.8f}")

            # Spearman's Rank Correlation Test
            spearman_corr, spearman_p_value = spearmanr(df['total_dollar_amount'], df['Price Change'])
            print(f"Spearman Correlation (Total Dollar Amount vs. Price Change): {spearman_corr:.4f}, P-value: {spearman_p_value:.8f}")
        else:
            print("Insufficient data for correlation tests.")

    correlation_test(ticker)

# Example usage
test_association("CRSP")