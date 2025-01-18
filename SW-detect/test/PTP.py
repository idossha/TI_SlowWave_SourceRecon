
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description="Analyze PTP statistics from a CSV file.")
    parser.add_argument('csv_path', type=str, help='Path to the input CSV file.')
    parser.add_argument('--output', type=str, default='ptp_statistics.png', help='Path to save the output bar plot.')
    parser.add_argument('--use_quartiles', action='store_true', help='Use quartiles instead of standard deviation for error bars.')
    return parser.parse_args()

def load_data(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"The file {csv_path} does not exist.")
    df = pd.read_csv(csv_path)
    if 'PTP' not in df.columns:
        raise ValueError("The CSV file does not contain a 'PTP' column.")
    return df

def compute_statistics(df, use_quartiles=False):
    stats = {}
    if use_quartiles:
        stats['mean'] = df['PTP'].mean()
        stats['25th_percentile'] = df['PTP'].quantile(0.25)
        stats['75th_percentile'] = df['PTP'].quantile(0.75)
    else:
        stats['mean'] = df['PTP'].mean()
        stats['std'] = df['PTP'].std()
    return stats

def visualize_statistics(df, stats, use_quartiles=False, output_path='ptp_statistics.png'):
    sns.set(style="whitegrid")
    
    # Bar Plot with Error Bars
    plt.figure(figsize=(8,6))
    if use_quartiles:
        # Calculate asymmetric error bars based on quartiles
        lower_error = stats['mean'] - stats['25th_percentile']
        upper_error = stats['75th_percentile'] - stats['mean']
        plt.bar(['PTP'], [stats['mean']], yerr=[[lower_error], [upper_error]], capsize=10, color='skyblue')
        plt.ylabel('PTP')
        plt.title('Mean PTP with Interquartile Range')
    else:
        plt.bar(['PTP'], [stats['mean']], yerr=[stats['std']], capsize=10, color='skyblue')
        plt.ylabel('PTP')
        plt.title('Mean PTP with Standard Deviation')
    
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Bar plot saved to {output_path}")

    # Violin Plot for Distribution
    plt.figure(figsize=(6,4))
    sns.violinplot(y=df['PTP'], color='lightgreen', inner='quartile')
    plt.ylabel('PTP')
    plt.title('Violin Plot of PTP')
    plt.tight_layout()
    violinplot_path = os.path.splitext(output_path)[0] + '_violinplot.png'
    plt.savefig(violinplot_path)
    plt.close()
    print(f"Violin plot saved to {violinplot_path}")

if __name__ == "__main__":
    args = parse_arguments()
    try:
        df = load_data(args.csv_path)
        stats = compute_statistics(df, use_quartiles=args.use_quartiles)
        visualize_statistics(df, stats, use_quartiles=args.use_quartiles, output_path=args.output)
    except Exception as e:
        print(f"Error: {e}")

