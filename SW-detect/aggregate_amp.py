
import os
import pandas as pd
import matplotlib.pyplot as plt

def gather_data(
    project_dir,
    subjects,
    nights,
    csv_files
):
    """
    1. Loops over each subject and night,
    2. Looks for CSV files (csv_files) in the folder:
       project_dir/subject/night/output/Strength_{subject}_{night}_forSW/file.csv
    3. Concatenates the data into one DataFrame,
    4. Adds columns: Subject, Night, and Region.
    """

    all_data = []

    # Loop through the specified subjects and nights
    for subject in subjects:
        for night in nights:
            # For each CSV file of interest
            for csv_file in csv_files:
                # Build the path:
                file_path = os.path.join(
                    project_dir,
                    str(subject),
                    str(night),
                    "output",
                    f"Strength_{subject}_{night}_forSW",
                    csv_file
                )

                # Only proceed if the file actually exists
                if os.path.isfile(file_path):
                    df_temp = pd.read_csv(file_path)

                    # Parse region from filename
                    base_name = os.path.basename(csv_file)
                    region = base_name.replace("wave_quantification_", "").replace(".csv", "")

                    # Add Subject, Night, and Region columns
                    df_temp["Subject"] = subject
                    df_temp["Night"] = night
                    df_temp["Region"] = region

                    all_data.append(df_temp)
                else:
                    print(f"File not found: {file_path}")

    # If no data is found, return an empty DataFrame
    if not all_data:
        print("No valid CSV files were found matching the given criteria.")
        return pd.DataFrame()

    # Concatenate everything into one DataFrame
    df_all = pd.concat(all_data, ignore_index=True)
    return df_all


def main():
    # --- User-specified parameters ---
    project_directory = "/Volumes/CSC-Ido/Analyze/"
    # subjects = [101, 102, 108, 109, 112, 114, 115, 116, 117, 120, 121, 122, 132]
    subjects = [107,110,111,119,127]
    nights = ["N1"]
    csv_files = [
        "wave_quantification_L_frontal.csv",
        "wave_quantification_R_frontal.csv",
        "wave_quantification_Posterior.csv"
    ]
    
    # Condition variable (e.g., "Active" or "SHAM")
    condition = "SHAM"
    
    # 1. Gather Data
    df_all = gather_data(project_directory, subjects, nights, csv_files)
    if df_all.empty:
        return

    # Create output directory for group-level analysis
    output_dir = os.path.join(project_directory, "Group_Analysis")
    os.makedirs(output_dir, exist_ok=True)

    # 2. Save the aggregated data (if you want to keep a record)
    aggregated_csv_path = os.path.join(output_dir, f"aggregated_wave_data_{condition}.csv")
    df_all.to_csv(aggregated_csv_path, index=False)
    print(f"Aggregated CSV saved to: {aggregated_csv_path}")

    ########################################################################
    #                 A. MEAN AMPLITUDE BY STAGE (ALL REGIONS)             #
    ########################################################################
    # Group by Stage => compute mean and std of Average_Amplitude
    stage_amp = (
        df_all.groupby('Stage')['Average_Amplitude']
             .agg(['mean', 'std'])
             .reset_index()
             .sort_values('Stage')
    )

    # Plot with error bars
    plt.figure(figsize=(5, 4))
    bars = plt.bar(
        stage_amp['Stage'],
        stage_amp['mean'],
        yerr=stage_amp['std'],
        capsize=4,  # adds little lines at the end of error bars
        color=['blue', 'orange', 'green']
    )
    plt.title(f"Mean Wave Amplitude by Stage (All Regions) - {condition}")
    plt.xlabel('Stage')
    plt.ylabel('Mean Average_Amplitude')

    # Annotate each bar (show the mean with 1 decimal or so)
    for i, bar in enumerate(bars):
        mean_val = stage_amp['mean'].iloc[i]
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{mean_val:.1f}",
            ha='center', va='bottom'
        )

    plt.tight_layout()
    stage_fig_path = os.path.join(output_dir, f"mean_amplitude_by_stage_{condition}.png")
    plt.savefig(stage_fig_path, dpi=300)
    print(f"Saved mean amplitude bar chart (by Stage) to: {stage_fig_path}")
    plt.close()

    ########################################################################
    #                 B. MEAN AMPLITUDE BY REGION (ALL STAGES)             #
    ########################################################################
    region_amp = (
        df_all.groupby('Region')['Average_Amplitude']
             .agg(['mean', 'std'])
             .reset_index()
    )

    plt.figure(figsize=(5, 4))
    bars = plt.bar(
        region_amp['Region'],
        region_amp['mean'],
        yerr=region_amp['std'],
        capsize=4,
        color=['purple', 'gray', 'cyan']
    )
    plt.title(f"Mean Wave Amplitude by Region (All Stages) - {condition}")
    plt.xlabel('Region')
    plt.ylabel('Mean Average_Amplitude')

    for i, bar in enumerate(bars):
        mean_val = region_amp['mean'].iloc[i]
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{mean_val:.1f}",
            ha='center', va='bottom'
        )

    plt.tight_layout()
    region_fig_path = os.path.join(output_dir, f"mean_amplitude_by_region_{condition}.png")
    plt.savefig(region_fig_path, dpi=300)
    print(f"Saved mean amplitude bar chart (by Region) to: {region_fig_path}")
    plt.close()

    ########################################################################
    #                 C. MEAN AMPLITUDE BY STAGE *FOR EACH REGION*         #
    ########################################################################
    region_stage_amp = (
        df_all.groupby(['Region', 'Stage'])['Average_Amplitude']
             .agg(['mean', 'std'])
             .reset_index()
    )

    # For each region, plot Stage vs. Mean(Amplitude) with error bars
    for region in region_stage_amp['Region'].unique():
        subset = region_stage_amp[region_stage_amp['Region'] == region].copy()
        subset.sort_values('Stage', inplace=True)

        plt.figure(figsize=(5, 4))
        bars = plt.bar(
            subset['Stage'],
            subset['mean'],
            yerr=subset['std'],
            capsize=4,
            color=['blue', 'orange', 'green']
        )
        plt.title(f"Mean Wave Amplitude by Stage for {region} - {condition}")
        plt.xlabel('Stage')
        plt.ylabel('Mean Average_Amplitude')

        # Annotate each bar
        for i, bar in enumerate(bars):
            mean_val = subset['mean'].iloc[i]
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{mean_val:.1f}",
                ha='center', va='bottom'
            )

        plt.tight_layout()
        region_stage_fig_path = os.path.join(output_dir, f"mean_amplitude_by_stage_for_{region}_{condition}.png")
        plt.savefig(region_stage_fig_path, dpi=300)
        print(f"Saved mean amplitude bar chart (Stage for {region}) to: {region_stage_fig_path}")
        plt.close()


if __name__ == "__main__":
    main()
