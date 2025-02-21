
# statistical_analysis.py

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
import logging

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
    Perform statistical analysis, generate plots, quantify waves, 
    and optionally do region-based breakdown.

    Parameters:
    - df_filtered: pd.DataFrame, DataFrame containing filtered and classified slow waves.
      Must include 'Classification' (time-based) and 'Region_Classification' columns.
    - output_dir: str, path to the output directory where plots and quantification CSV will be saved.
    - project_dir: str, path to the root project directory.
    - subject: str, subject identifier.
    - night: str, night identifier.
    - suffix: str, additional suffix to differentiate output files.
    """
 
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    wave_description_dir = os.path.join(output_dir, 'wave_description')
    os.makedirs(wave_description_dir, exist_ok=True)

    # Columns of interest for mean-value plots
    columns_to_plot = ['Duration', 'ValNegPeak', 'ValPosPeak', 'PTP', 'Frequency']
    all_classifications = ['pre-stim', 'stim', 'post-stim']

    # Ensure Classification column is properly formatted (lowercase, hyphenated)
    df_filtered['Classification'] = df_filtered['Classification'].str.lower().str.replace(' ', '-')

    # === 1) OVERALL (ENTIRE NET) STATISTICS ===
    # Compute mean values by Classification
    comparison_means = (
        df_filtered
        .groupby('Classification')[columns_to_plot]
        .mean()
        .reindex(all_classifications, fill_value=0)
    )
    # Compute counts by Classification
    comparison_counts = (
        df_filtered['Classification']
        .value_counts()
        .reindex(all_classifications, fill_value=0)
    )

    # --- Plotting overall mean values ---
    plt.figure(figsize=(15, 6))
    ax = comparison_means.plot(kind='bar', 
                               color=['#6baed6', '#9ecae1', '#c6dbef', '#fd8d3c', '#fdae6b'])
    plt.title(f'Overall Mean Values of Wave Properties ({suffix})')
    plt.ylabel('Mean Values')
    plt.xlabel('Classification', labelpad=10)
    plt.xticks(rotation=0)
    plt.legend(title='Properties', loc='upper right', bbox_to_anchor=(1.15, 1))
    add_value_labels(ax)
    plt.tight_layout()
    overall_mean_png = os.path.join(wave_description_dir, f'overall_mean_values_{suffix}.png')
    plt.savefig(overall_mean_png)
    plt.close()

    # --- Plotting overall counts ---
    plt.figure(figsize=(8, 6))
    ax2 = comparison_counts.plot(kind='bar', color='#6baed6')
    plt.title(f'Overall Count of Instances by Classification ({suffix})')
    plt.ylabel('Count')
    plt.xlabel('Classification', labelpad=10)
    plt.xticks(rotation=0)
    add_value_labels(ax2)
    plt.tight_layout()
    overall_counts_png = os.path.join(wave_description_dir, f'overall_counts_{suffix}.png')
    plt.savefig(overall_counts_png)
    plt.close()

    # === 2) PER-PROTOCOL STATISTICS (ENTIRE NET) ===
    protocol_numbers = df_filtered['Protocol Number'].dropna().unique()

    for protocol in protocol_numbers:
        protocol_data = df_filtered[df_filtered['Protocol Number'] == protocol]
        protocol_means = (
            protocol_data
            .groupby('Classification')[columns_to_plot]
            .mean()
            .reindex(all_classifications, fill_value=0)
        )
        protocol_counts = (
            protocol_data['Classification']
            .value_counts()
            .reindex(all_classifications, fill_value=0)
        )

        # --- Plot mean values per protocol ---
        plt.figure(figsize=(15, 6))
        ax = protocol_means.plot(kind='bar', 
                                 color=['#6baed6', '#9ecae1', '#c6dbef', '#fd8d3c', '#fdae6b'])
        plt.title(f'Mean Values of Wave Properties (Protocol {int(protocol)}, {suffix})')
        plt.ylabel('Mean Values')
        plt.xlabel('Classification', labelpad=10)
        plt.xticks(rotation=0)
        plt.legend(title='Properties', loc='upper right', bbox_to_anchor=(1.15, 1))
        add_value_labels(ax)
        plt.tight_layout()
        protocol_mean_png = os.path.join(wave_description_dir, f'protocol_{int(protocol)}_mean_values_{suffix}.png')
        plt.savefig(protocol_mean_png)
        plt.close()

        # --- Plot counts per protocol ---
        plt.figure(figsize=(8, 6))
        ax2 = protocol_counts.plot(kind='bar', color='#6baed6')
        plt.title(f'Count of Instances by Classification (Protocol {int(protocol)}, {suffix})')
        plt.ylabel('Count')
        plt.xlabel('Classification', labelpad=10)
        plt.xticks(rotation=0)
        add_value_labels(ax2)
        plt.tight_layout()
        protocol_counts_png = os.path.join(wave_description_dir, f'protocol_{int(protocol)}_counts_{suffix}.png')
        plt.savefig(protocol_counts_png)
        plt.close()

    # === 3) WAVE QUANTIFICATION (ENTIRE NET) ===
    logging.info("Quantifying waves per protocol per stage (entire net)...")
    try:
        required_columns = ['Protocol Number', 'Classification', 'PTP']
        missing_columns = [col for col in required_columns if col not in df_filtered.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns in df_filtered: {', '.join(missing_columns)}")

        # Rename for consistency
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

        # Handle NaN in std (e.g., if only one wave in a group)
        quantification['Std_Amplitude'] = quantification['Std_Amplitude'].fillna(0)

        # Round to two decimal places
        for col in ['Average_Amplitude', 'Max_Amplitude', 'Min_Amplitude', 'Std_Amplitude']:
            quantification[col] = quantification[col].round(2)

        # Output CSV path for entire net
        quant_csv_path = os.path.join(output_dir, 'wave_quantification.csv')
        quantification.to_csv(quant_csv_path, index=False)
        logging.info(f"Wave quantification (entire net) saved to {quant_csv_path}")

    except Exception as e:
        logging.error(f"Error in quantifying waves (entire net): {e}")
        return  # Exit the function if errors occur

    # === 4) APPEND ENTIRE-NET RESULTS TO group_summary.csv ===
    logging.info("Appending entire-net results to group_summary.csv...")
    try:
        group_analysis_dir = os.path.join(project_dir, 'Group_Analysis')
        os.makedirs(group_analysis_dir, exist_ok=True)

        group_summary_csv = os.path.join(group_analysis_dir, 'group_summary.csv')
        # Create or load existing group_summary.csv
        if not os.path.exists(group_summary_csv):
            columns = [
                'Subject', 'Night', 'Protocol_Number', 'Stage', 'Number_of_Waves',
                'Average_Amplitude', 'Max_Amplitude', 'Min_Amplitude', 'Std_Amplitude'
            ]
            group_summary_df = pd.DataFrame(columns=columns)
        else:
            group_summary_df = pd.read_csv(group_summary_csv)

        # Read the new quantification CSV
        if not os.path.exists(quant_csv_path):
            logging.warning(f"Quantification CSV not found at {quant_csv_path}. "
                            f"Skipping append for Subject: {subject}, Night: {night}.")
        else:
            quant_df = pd.read_csv(quant_csv_path)
            # Add Subject and Night columns
            quant_df['Subject'] = subject
            quant_df['Night'] = night
            # Reorder columns
            cols = ['Subject', 'Night'] + [c for c in quant_df.columns if c not in ['Subject', 'Night']]
            quant_df = quant_df[cols]

            # Merge with existing group_summary
            if not group_summary_df.empty and not quant_df.empty:
                group_summary_df = pd.concat([group_summary_df, quant_df], ignore_index=True, sort=False)
            elif group_summary_df.empty and not quant_df.empty:
                group_summary_df = quant_df.copy()

            group_summary_df.to_csv(group_summary_csv, index=False)
            logging.info(f"Appended entire-net data to group_summary.csv in {group_analysis_dir}")

    except Exception as e:
        logging.error(f"Error appending entire-net data to group_summary.csv: {e}")
        # Continue, but skip region-based if desired.

    # === 5) REGION-BASED ANALYSIS ===
    logging.info("Performing region-based analysis...")

    # Identify unique regions in the data
    all_regions = df_filtered['Region_Classification'].unique()

    for region in all_regions:
        # Filter data for this region
        region_data = df_filtered[df_filtered['Region_Classification'] == region].copy()
        if region_data.empty:
            # If no data for this region, skip
            logging.warning(f"No data found for region: {region}. Skipping region-level analysis.")
            continue

        # --- (A) Region-Level Means and Counts ---
        region_means = (
            region_data
            .groupby('Classification')[columns_to_plot]
            .mean()
            .reindex(all_classifications, fill_value=0)
        )
        region_counts = (
            region_data['Classification']
            .value_counts()
            .reindex(all_classifications, fill_value=0)
        )

        # Plot region-level means
        plt.figure(figsize=(15, 6))
        ax_region_means = region_means.plot(
            kind='bar',
            color=['#6baed6', '#9ecae1', '#c6dbef', '#fd8d3c', '#fdae6b']
        )
        plt.title(f'{region}: Mean Values of Wave Properties ({suffix})')
        plt.ylabel('Mean Values')
        plt.xlabel('Classification', labelpad=10)
        plt.xticks(rotation=0)
        plt.legend(title='Properties', loc='upper right', bbox_to_anchor=(1.15, 1))
        add_value_labels(ax_region_means)
        plt.tight_layout()
        region_mean_png = os.path.join(wave_description_dir, f'region_{region}_mean_values_{suffix}.png')
        plt.savefig(region_mean_png)
        plt.close()

        # Plot region-level counts
        plt.figure(figsize=(8, 6))
        ax_region_counts = region_counts.plot(kind='bar', color='#6baed6')
        plt.title(f'{region}: Count of Instances by Classification ({suffix})')
        plt.ylabel('Count')
        plt.xlabel('Classification', labelpad=10)
        plt.xticks(rotation=0)
        add_value_labels(ax_region_counts)
        plt.tight_layout()
        region_counts_png = os.path.join(wave_description_dir, f'region_{region}_counts_{suffix}.png')
        plt.savefig(region_counts_png)
        plt.close()

        # --- (B) Region-Level Per-Protocol Statistics ---
        region_protocols = region_data['Protocol Number'].dropna().unique()
        for protocol in region_protocols:
            rp_data = region_data[region_data['Protocol Number'] == protocol]
            rp_means = (
                rp_data
                .groupby('Classification')[columns_to_plot]
                .mean()
                .reindex(all_classifications, fill_value=0)
            )
            rp_counts = (
                rp_data['Classification']
                .value_counts()
                .reindex(all_classifications, fill_value=0)
            )

            # Plot region+protocol mean values
            plt.figure(figsize=(15, 6))
            ax_rp_means = rp_means.plot(
                kind='bar',
                color=['#6baed6', '#9ecae1', '#c6dbef', '#fd8d3c', '#fdae6b']
            )
            plt.title(f'{region}: Mean Values (Protocol {int(protocol)}, {suffix})')
            plt.ylabel('Mean Values')
            plt.xlabel('Classification', labelpad=10)
            plt.xticks(rotation=0)
            plt.legend(title='Properties', loc='upper right', bbox_to_anchor=(1.15, 1))
            add_value_labels(ax_rp_means)
            plt.tight_layout()
            rp_means_png = os.path.join(
                wave_description_dir, 
                f'region_{region}_protocol_{int(protocol)}_mean_values_{suffix}.png'
            )
            plt.savefig(rp_means_png)
            plt.close()

            # Plot region+protocol counts
            plt.figure(figsize=(8, 6))
            ax_rp_counts = rp_counts.plot(kind='bar', color='#6baed6')
            plt.title(f'{region}: Count of Instances (Protocol {int(protocol)}, {suffix})')
            plt.ylabel('Count')
            plt.xlabel('Classification', labelpad=10)
            plt.xticks(rotation=0)
            add_value_labels(ax_rp_counts)
            plt.tight_layout()
            rp_counts_png = os.path.join(
                wave_description_dir, 
                f'region_{region}_protocol_{int(protocol)}_counts_{suffix}.png'
            )
            plt.savefig(rp_counts_png)
            plt.close()

        # --- (C) Region-Level Wave Quantification ---
        logging.info(f"Quantifying waves for region: {region}")
        try:
            req_cols = ['Protocol Number', 'Classification', 'PTP']
            missing_cols = [col for col in req_cols if col not in region_data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns in region_data: {', '.join(missing_cols)}")

            # Rename for consistency
            df_region_quant = region_data.rename(columns={
                'Protocol Number': 'Protocol_Number',
                'Classification': 'Stage',
                'PTP': 'Amplitude'
            })

            # Group by Protocol_Number and Stage
            grouped_region = df_region_quant.groupby(['Protocol_Number', 'Stage'])

            # Quantify number of waves and compute amplitude statistics
            region_quantification = grouped_region['Amplitude'].agg(
                Number_of_Waves='count',
                Average_Amplitude='mean',
                Max_Amplitude='max',
                Min_Amplitude='min',
                Std_Amplitude='std'
            ).reset_index()

            # Handle NaN in std
            region_quantification['Std_Amplitude'] = region_quantification['Std_Amplitude'].fillna(0)

            # Round to two decimal places
            for col in ['Average_Amplitude', 'Max_Amplitude', 'Min_Amplitude', 'Std_Amplitude']:
                region_quantification[col] = region_quantification[col].round(2)

            # Output CSV path for this region
            region_quant_csv = os.path.join(output_dir, f'wave_quantification_{region}.csv')
            region_quantification.to_csv(region_quant_csv, index=False)
            logging.info(f"Region-based quantification saved to {region_quant_csv}")

        except Exception as e:
            logging.error(f"Error in region-based quantification for {region}: {e}")
            # Continue to next region

    logging.info("Region-based analysis completed.")

