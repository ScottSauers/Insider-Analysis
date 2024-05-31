import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind, sem

# Load the dataset
path_to_csv = '/KOSS_encoded_data_expanded.csv'
data = pd.read_csv(path_to_csv)

# Convert dates to datetime format
data['transactionDate'] = pd.to_datetime(data['transactionDate'])
data['month'] = data['transactionDate'].dt.month
data['day'] = data['transactionDate'].dt.day
data['year'] = data['transactionDate'].dt.year

# Filter data for buying and selling activities
buying_data = data[data['transaction_1_Disposed_2_Acquired'] == 2]
selling_data = data[data['transaction_1_Disposed_2_Acquired'] == 1]

def plot_stacked_histogram_by_person_id(data, overall_data, title, x_label, bins, ax, bin_labels):
    counts, bin_edges = np.histogram(overall_data, bins=bins)
    bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])
    conf_intervals = [1.96 * np.sqrt(count) for count in counts]
    
    person_id_counts = {pid: [] for pid in data['person_ID'].unique()}
    
    for pid in person_id_counts.keys():
        pid_data = data[data['person_ID'] == pid]
        pid_counts, _ = np.histogram(pid_data[x_label.lower()], bins=bin_edges)
        person_id_counts[pid] = pid_counts
    
    bottom_counts = np.zeros_like(counts)
    colors = plt.cm.tab20(np.linspace(0, 1, len(person_id_counts)))
    
    for i, (pid, pid_counts) in enumerate(person_id_counts.items()):
        ax.bar(bin_centers, pid_counts, width=(bin_edges[1] - bin_edges[0]), alpha=0.6, edgecolor='black', bottom=bottom_counts, color=colors[i])
        bottom_counts += pid_counts
    
    ax.errorbar(bin_centers, counts, yerr=conf_intervals, fmt='none', ecolor='black', capsize=5)
    
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel('Frequency')
    ax.set_xticks(bin_centers)
    ax.set_xticklabels(bin_labels)

month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

plt.rcParams['figure.dpi'] = 300

fig, axs = plt.subplots(2, 1, figsize=(12, 10))

plot_stacked_histogram_by_person_id(buying_data, buying_data['month'], 'Buying Activity by Month', 'Month', bins=12, ax=axs[0], bin_labels=month_labels)
plot_stacked_histogram_by_person_id(buying_data, buying_data.groupby('month')['transactionShares'].sum(), 'Buying Activity Magnitude by Month', 'Month', bins=12, ax=axs[1], bin_labels=month_labels)

plt.tight_layout()
plt.show()

fig, axs = plt.subplots(2, 1, figsize=(12, 10))

plot_stacked_histogram_by_person_id(selling_data, selling_data['month'], 'Selling Activity by Month', 'Month', bins=12, ax=axs[0], bin_labels=month_labels)
plot_stacked_histogram_by_person_id(selling_data, selling_data.groupby('month')['transactionShares'].sum(), 'Selling Activity Magnitude by Month', 'Month', bins=12, ax=axs[1], bin_labels=month_labels)

plt.tight_layout()
plt.show()

fig, ax = plt.subplots(1, 1, figsize=(12, 5))

plot_stacked_histogram_by_person_id(buying_data, buying_data['day'], 'Buying Activity by Day of the Month', 'Day', bins=31, ax=ax, bin_labels=list(range(1, 32)))

plt.tight_layout()
plt.show()

fig, ax = plt.subplots(1, 1, figsize=(12, 5))

plot_stacked_histogram_by_person_id(selling_data, selling_data['day'], 'Selling Activity by Day of the Month', 'Day', bins=31, ax=ax, bin_labels=list(range(1, 32)))

plt.tight_layout()
plt.show()

def l1o_analysis(data, activity_column, group_column, high_group):
    unique_ids = data['person_ID'].unique()
    p_values = []
    percent_differences = []

    for person_id in unique_ids:
        l1o_data = data[data['person_ID'] != person_id]
        high_group_data = l1o_data[l1o_data[group_column] == high_group][activity_column]
        other_group_data = l1o_data[l1o_data[group_column] != high_group][activity_column]
        
        if len(high_group_data) == 0 or len(other_group_data) == 0:
            continue
        
        t_stat, p_value = ttest_ind(high_group_data, other_group_data)
        p_values.append(p_value)
        
        mean_high = high_group_data.mean()
        mean_other = other_group_data.mean()
        percent_difference = ((mean_high - mean_other) / mean_other) * 100
        percent_differences.append(percent_difference)
    
    return p_values, percent_differences

def l1o_analysis_year(data, activity_column, group_column, high_group):
    unique_years = data['year'].unique()
    p_values = []

    for year in unique_years:
        l1o_data = data[data['year'] != year]
        high_group_data = l1o_data[l1o_data[group_column] == high_group][activity_column]
        other_group_data = l1o_data[l1o_data[group_column] != high_group][activity_column]
        
        if len(high_group_data) == 0 or len(other_group_data) == 0:
            continue
        
        t_stat, p_value = ttest_ind(high_group_data, other_group_data)
        p_values.append(p_value)
    
    return p_values

def get_high_activity_months(data, activity_column, group_column):
    grouped = data.groupby(group_column)[activity_column].count()
    max_month = grouped.idxmax()
    max_value = grouped[max_month]
    ci = 1.96 * np.sqrt(max_value)
    
    high_activity_months = grouped[(grouped >= (max_value - ci)) & (grouped <= (max_value + ci))].index.tolist()
    
    return high_activity_months

buying_high_months = get_high_activity_months(buying_data, 'transactionShares', 'month')
selling_high_months = get_high_activity_months(selling_data, 'transactionShares', 'month')
buying_high_days = get_high_activity_months(buying_data, 'transactionShares', 'day')
selling_high_days = get_high_activity_months(selling_data, 'transactionShares', 'day')

buying_l1o_results_months = l1o_analysis(buying_data, 'transactionShares', 'month', buying_high_months[0])
selling_l1o_results_months = l1o_analysis(selling_data, 'transactionShares', 'month', selling_high_months[0])
buying_l1o_results_days = l1o_analysis(buying_data, 'transactionShares', 'day', buying_high_days[0])
selling_l1o_results_days = l1o_analysis(selling_data, 'transactionShares', 'day', selling_high_days[0])

buying_l1o_year_results_months = l1o_analysis_year(buying_data, 'transactionShares', 'month', buying_high_months[0])
selling_l1o_year_results_months = l1o_analysis_year(selling_data, 'transactionShares', 'month', selling_high_months[0])
buying_l1o_year_results_days = l1o_analysis_year(buying_data, 'transactionShares', 'day', buying_high_days[0])
selling_l1o_year_results_days = l1o_analysis_year(selling_data, 'transactionShares', 'day', selling_high_days[0])

def interpret_results(group, group_label, p_values, percent_differences):
    mean_p_value = np.mean(p_values)
    largest_p_value = np.max(p_values)
    if mean_p_value < 0.05:
        mean_percent_difference = np.mean(percent_differences)
        return f"The {group_label} ({group}) is statistically significant and robust to L1O analysis. The activity is {mean_percent_difference:.2f}% higher than the overall mean. Mean p-value: {mean_p_value:.4f}, Largest p-value: {largest_p_value:.4f}"
    else:
        return f"The {group_label} ({group}) is not statistically significant or not robust to L1O analysis. Mean p-value: {mean_p_value:.4f}, Largest p-value: {largest_p_value:.4f}"

def interpret_year_results(group, group_label, p_values):
    mean_p_value = np.mean(p_values)
    largest_p_value = np.max(p_values)
    interpretation = f"Mean p-value for {group_label} ({group}) L1O by year: {mean_p_value:.4f}, Largest p-value: {largest_p_value:.4f}"
    if mean_p_value < 0.05:
        interpretation += f". P-values for each year: {p_values}"
    return interpretation

buying_months_interpretation = interpret_results(buying_high_months[0], 'month', *buying_l1o_results_months)
selling_months_interpretation = interpret_results(selling_high_months[0], 'month', *selling_l1o_results_months)
buying_days_interpretation = interpret_results(buying_high_days[0], 'day', *buying_l1o_results_days)
selling_days_interpretation = interpret_results(selling_high_days[0], 'day', *selling_l1o_results_days)

buying_months_year_interpretation = interpret_year_results(buying_high_months[0], 'month', buying_l1o_year_results_months)
selling_months_year_interpretation = interpret_year_results(selling_high_months[0], 'month', selling_l1o_year_results_months)
buying_days_year_interpretation = interpret_year_results(buying_high_days[0], 'day', buying_l1o_year_results_days)
selling_days_year_interpretation = interpret_year_results(selling_high_days[0], 'day', selling_l1o_year_results_days)

print(f"High buying activity months: {buying_high_months}")
print(f"High selling activity months: {selling_high_months}")
print(f"High buying activity days: {buying_high_days}")
print(f"High selling activity days: {selling_high_days}")

print("\nInterpretation of Results for Buying Activity by Month:")
print(buying_months_interpretation)
print(buying_months_year_interpretation)

print("\nInterpretation of Results for Selling Activity by Month:")
print(selling_months_interpretation)
print(selling_months_year_interpretation)

print("\nInterpretation of Results for Buying Activity by Day:")
print(buying_days_interpretation)
print(buying_days_year_interpretation)

print("\nInterpretation of Results for Selling Activity by Day:")
print(selling_days_interpretation)
print(selling_days_year_interpretation)
