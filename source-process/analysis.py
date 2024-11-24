import sys
import pandas as pd
import numpy as np
from scipy.stats import f_oneway, ttest_rel
from statsmodels.stats.multitest import multipletests
import matplotlib.pyplot as plt
import seaborn as sns
import pingouin as pg

"""
Script Name: analyze_data.py

Description:
This script reads the DataFrame compiled by 'extract_data.py' and performs both involvement and origin analyses.
It conducts statistical tests and creates visualizations to compare involvement percentages and regional origins between conditions.

Usage:
python analyze_data.py /path/to/compiled_data.csv
"""

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_data.py /path/to/compiled_data.csv")
        sys.exit(1)

    data_file = sys.argv[1]

    # Load DataFrame
    df = pd.read_csv(data_file)

    # Ensure 'condition' is treated as a categorical variable
    df['condition'] = df['condition'].astype('category')

    # Analyze involvement
    analyze_involvement(df)

    # Analyze regions
    analyze_regions(df)

def analyze_involvement(df):
    print("\nAnalyzing involvement percentages between conditions...\n")
    # Descriptive statistics
    involvement_stats = df.groupby('condition')['percentage_involved'].agg(['mean', 'std'])
    print("Mean and Standard Deviation of Involvement Percentages by Condition:")
    print(involvement_stats)

    # Visualization
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='condition', y='percentage_involved', data=df)
    plt.title('Involvement Percentage by Condition')
    plt.xlabel('Condition')
    plt.ylabel('Percentage Involved')
    plt.show()

    # Repeated Measures ANOVA
    anova_df = df.pivot(index='subject', columns='condition', values='percentage_involved').dropna()
    conditions = df['condition'].unique()
    if len(anova_df) >= 2:
        # Melt the data for ANOVA
        rm_data = anova_df.reset_index().melt(id_vars=['subject'], var_name='condition', value_name='percentage_involved')
        # Perform repeated measures ANOVA using pingouin
        aov = pg.rm_anova(data=rm_data, dv='percentage_involved', within='condition', subject='subject')
        print("\nRepeated Measures ANOVA Results:")
        print(aov)
        p_value = aov['p-unc'][0]

        # If significant, perform post-hoc tests
        if p_value < 0.05:
            posthoc = pg.pairwise_ttests(data=rm_data, dv='percentage_involved', within='condition', subject='subject', padjust='bonf')
            print("\nPost-hoc Pairwise Comparisons with Bonferroni Correction:")
            print(posthoc[['A', 'B', 'T', 'p-unc', 'p-corr', 'significant']])
        else:
            print("No significant differences found between conditions.")
    else:
        print("Not enough subjects with data across all conditions for repeated measures ANOVA.")

def analyze_regions(df):
    print("\nAnalyzing regional origins between conditions...\n")
    # Select region columns (exclude 'subject', 'condition', 'percentage_involved')
    region_cols = df.columns.difference(['subject', 'condition', 'percentage_involved'])

    # Melt the DataFrame to long format for regions
    df_melted = df.melt(id_vars=['subject', 'condition'], value_vars=region_cols, var_name='region', value_name='percentage')
    # Drop NaN values
    df_melted = df_melted.dropna(subset=['percentage'])

    # Identify top regions across all data
    top_regions = df_melted['region'].value_counts().head(10).index.tolist()
    print("Top 10 regions for analysis:")
    print(top_regions)

    # Filter data to top regions
    df_top = df_melted[df_melted['region'].isin(top_regions)]

    # Visualization
    plt.figure(figsize=(12, 6))
    sns.barplot(x='region', y='percentage', hue='condition', data=df_top, ci='sd')
    plt.title('Region Percentages by Condition')
    plt.xlabel('Brain Region')
    plt.ylabel('Average Percentage')
    plt.xticks(rotation=90)
    plt.legend(title='Condition')
    plt.tight_layout()
    plt.show()

    # Repeated Measures ANOVA per region
    anova_results = []

    for region in top_regions:
        region_data = df_top[df_top['region'] == region]
        anova_region_df = region_data.pivot(index='subject', columns='condition', values='percentage').dropna()
        if len(anova_region_df) >= 2:
            # Melt the data for ANOVA
            rm_data = anova_region_df.reset_index().melt(id_vars=['subject'], var_name='condition', value_name='percentage')
            # Perform repeated measures ANOVA
            aov = pg.rm_anova(data=rm_data, dv='percentage', within='condition', subject='subject')
            p_value = aov['p-unc'][0]
            anova_results.append({'region': region, 'p_value': p_value})
        else:
            print(f"Not enough data for region {region} across all conditions.")

    # Correct for multiple comparisons
    if anova_results:
        anova_df = pd.DataFrame(anova_results)
        p_values = anova_df['p_value']
        reject, pvals_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
        anova_df['p_value_corrected'] = pvals_corrected
        anova_df['significant'] = reject

        print("\nANOVA results per region after FDR correction:")
        print(anova_df[['region', 'p_value', 'p_value_corrected', 'significant']])
    else:
        print("No regions with enough data for ANOVA.")

if __name__ == "__main__":
    main()

