
# statistical_analysis.py

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

def add_value_labels(ax, spacing=5):
    """Add labels to the end of each bar in a bar chart."""
    for rect in ax.patches:
        y_value = rect.get_height()
        x_value = rect.get_x() + rect.get_width() / 2
        label = f"{y_value:.2f}" if y_value != 0 else "0"
        ax.annotate(
            label,
            (x_value, y_value),
            xytext=(0, spacing),
            textcoords="offset points",
            ha='center',
            va='bottom'
        )

def perform_statistical_analysis(df_filtered, output_dir, suffix=''):
    """
    Perform statistical analysis and generate plots using the filtered DataFrame.

    Parameters:
    - df_filtered: pd.DataFrame, DataFrame containing filtered and classified slow waves.
    - output_dir: str, path to the output directory where plots will be saved.
    - suffix: str, additional suffix to differentiate output files.
    """
    columns_to_plot = ['Duration', 'ValNegPeak', 'ValPosPeak', 'PTP', 'Frequency']
    all_classifications = ['pre-stim', 'stim', 'post-stim']

    # Ensure Classification column is properly formatted
    df_filtered['Classification'] = df_filtered['Classification'].str.lower().str.replace(' ', '-')

    # Compute mean values
    comparison_means = df_filtered.groupby('Classification')[columns_to_plot].mean().reindex(all_classifications, fill_value=0)
    # Compute counts
    comparison_counts = df_filtered['Classification'].value_counts().reindex(all_classifications, fill_value=0)

    # Plotting overall mean values
    plt.figure(figsize=(15, 6))
    ax = comparison_means.plot(kind='bar', color=['#6baed6', '#9ecae1', '#c6dbef', '#fd8d3c', '#fdae6b'])
    plt.title(f'Overall Mean Values of Wave Properties ({suffix})')
    plt.ylabel('Mean Values')
    plt.xlabel('Classification', labelpad=10)
    plt.xticks(rotation=0)
    plt.legend(title='Properties', loc='upper right', bbox_to_anchor=(1.15, 1))
    add_value_labels(ax)
    plt.tight_layout()
    output_path = os.path.join(output_dir, f'overall_mean_values_{suffix}.png')
    plt.savefig(output_path)
    plt.close()

    # Plotting overall counts
    plt.figure(figsize=(8, 6))
    ax2 = comparison_counts.plot(kind='bar', color='#6baed6')
    plt.title(f'Overall Count of Instances by Classification ({suffix})')
    plt.ylabel('Count')
    plt.xlabel('Classification', labelpad=10)
    plt.xticks(rotation=0)
    add_value_labels(ax2)
    plt.tight_layout()
    output_path_counts = os.path.join(output_dir, f'overall_counts_{suffix}.png')
    plt.savefig(output_path_counts)
    plt.close()

    # Plotting per protocol
    protocol_numbers = df_filtered['Protocol Number'].dropna().unique()
    for protocol in protocol_numbers:
        protocol_data = df_filtered[df_filtered['Protocol Number'] == protocol]
        protocol_means = protocol_data.groupby('Classification')[columns_to_plot].mean().reindex(all_classifications, fill_value=0)
        protocol_counts = protocol_data['Classification'].value_counts().reindex(all_classifications, fill_value=0)

        # Plot mean values per protocol
        plt.figure(figsize=(15, 6))
        ax = protocol_means.plot(kind='bar', color=['#6baed6', '#9ecae1', '#c6dbef', '#fd8d3c', '#fdae6b'])
        plt.title(f'Mean Values of Wave Properties (Protocol {int(protocol)}, {suffix})')
        plt.ylabel('Mean Values')
        plt.xlabel('Classification', labelpad=10)
        plt.xticks(rotation=0)
        plt.legend(title='Properties', loc='upper right', bbox_to_anchor=(1.15, 1))
        add_value_labels(ax)
        plt.tight_layout()
        output_protocol_means = os.path.join(output_dir, f'protocol_{int(protocol)}_mean_values_{suffix}.png')
        plt.savefig(output_protocol_means)
        plt.close()

        # Plot counts per protocol
        plt.figure(figsize=(8, 6))
        ax2 = protocol_counts.plot(kind='bar', color='#6baed6')
        plt.title(f'Count of Instances by Classification (Protocol {int(protocol)}, {suffix})')
        plt.ylabel('Count')
        plt.xlabel('Classification', labelpad=10)
        plt.xticks(rotation=0)
        add_value_labels(ax2)
        plt.tight_layout()
        output_protocol_counts = os.path.join(output_dir, f'protocol_{int(protocol)}_counts_{suffix}.png')
        plt.savefig(output_protocol_counts)
        plt.close()

