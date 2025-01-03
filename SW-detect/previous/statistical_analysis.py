
# statistical_analysis.py

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
import logging  # Import logging if not already imported

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

def perform_statistical_analysis(df_filtered, output_dir, project_dir, subject, night, suffix=''):
    """
    Perform statistical analysis, generate plots, quantify waves, and aggregate data.

    Parameters:
    - df_filtered: pd.DataFrame, DataFrame containing filtered and classified slow waves.
    - output_dir: str, path to the output directory where plots and quantification CSV will be saved.
    - project_dir: str, path to the root project directory.
    - subject: str, subject identifier.
    - night: str, night identifier.
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

    # --- Wave Quantification ---
    logging.info("Quantifying waves per protocol per stage...")
    try:
        # Ensure necessary columns are present
        required_columns = ['Protocol Number', 'Classification', 'PTP']
        missing_columns = [col for col in required_columns if col not in df_filtered.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns in df_filtered: {', '.join(missing_columns)}")

        # Rename columns for consistency
        df_quant = df_filtered.rename(columns={
            'Protocol Number': 'Protocol_Number',
            'Classification': 'Stage',
            'PTP': 'Amplitude'
        })

        # Group by Protocol_Number and Stage
        grouped = df_quant.groupby(['Protocol_Number', 'Stage'])

        # Quantify number of waves and compute amplitude statistics
        quantification = grouped['Amplitude'].agg(
            Number_of_Waves='count',
            Average_Amplitude='mean',
            Max_Amplitude='max',
            Min_Amplitude='min',
            Std_Amplitude='std'
        ).reset_index()

        # Handle NaN in std (e.g., if only one wave)
        quantification['Std_Amplitude'] = quantification['Std_Amplitude'].fillna(0)

        # Format amplitudes to two decimal places
        quantification['Average_Amplitude'] = quantification['Average_Amplitude'].round(2)
        quantification['Max_Amplitude'] = quantification['Max_Amplitude'].round(2)
        quantification['Min_Amplitude'] = quantification['Min_Amplitude'].round(2)
        quantification['Std_Amplitude'] = quantification['Std_Amplitude'].round(2)

        # Define the output CSV path
        quant_csv_path = os.path.join(output_dir, 'wave_quantification.csv')

        # Save the quantification to CSV
        quantification.to_csv(quant_csv_path, index=False)

        logging.info(f"Wave quantification saved to {quant_csv_path}")

    except Exception as e:
        logging.error(f"Error in quantifying waves: {e}")
        return  # Exit the function gracefully

    # --- Group Analysis ---
    logging.info("Appending to group_summary.csv...")
    try:
        group_analysis_dir = os.path.join(project_dir, 'Group_Analysis')
        os.makedirs(group_analysis_dir, exist_ok=True)

        group_summary_csv = os.path.join(group_analysis_dir, 'group_summary.csv')

        # Initialize or read the existing group_summary.csv
        if not os.path.exists(group_summary_csv):
            # Define columns
            columns = ['Subject', 'Night', 'Protocol_Number', 'Stage', 'Number_of_Waves', 
                       'Average_Amplitude', 'Max_Amplitude', 'Min_Amplitude', 'Std_Amplitude']
            group_summary_df = pd.DataFrame(columns=columns)
        else:
            group_summary_df = pd.read_csv(group_summary_csv)

        # Read the quantification CSV
        if not os.path.exists(quant_csv_path):
            logging.warning(f"Quantification CSV not found at {quant_csv_path}. Skipping append for Subject: {subject}, Night: {night}.")
        else:
            quant_df = pd.read_csv(quant_csv_path)

            # Add Subject and Night columns
            quant_df['Subject'] = subject
            quant_df['Night'] = night

            # Reorder columns to have Subject and Night first
            cols = ['Subject', 'Night'] + [col for col in quant_df.columns if col not in ['Subject', 'Night']]
            quant_df = quant_df[cols]

            # Concatenate while handling potential empty DataFrames
            if not group_summary_df.empty and not quant_df.empty:
                group_summary_df = pd.concat([group_summary_df, quant_df], ignore_index=True, sort=False)
            elif group_summary_df.empty and not quant_df.empty:
                group_summary_df = quant_df.copy()
            # If quant_df is empty, do nothing

            # Save back to group_summary.csv
            group_summary_df.to_csv(group_summary_csv, index=False)

            logging.info(f"Appended data to group_summary.csv in {group_analysis_dir}")

    except Exception as e:
        logging.error(f"Error appending to group_summary.csv: {e}")

