
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

                    # Parse region from the filename
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
    
    # Condition variable:
    condition = "SHAM"  # or "SHAM", etc.

    # Gather data
    df_all = gather_data(project_directory, subjects, nights, csv_files)
    if df_all.empty:
        # No data => stop here
        return

    # Create output directory if it doesn't exist:
    output_dir = os.path.join(project_directory, "Group_Analysis")
    os.makedirs(output_dir, exist_ok=True)

    # Save aggregated data with condition in the filename
    aggregated_csv_path = os.path.join(output_dir, f"aggregated_wave_data_{condition}.csv")
    df_all.to_csv(aggregated_csv_path, index=False)
    print(f"Aggregated CSV saved to: {aggregated_csv_path}")

    # 1. Bar graph of total waves by Stage (across all Regions)
    stage_sums = (
        df_all.groupby('Stage')['Number_of_Waves']
             .sum()
             .reset_index()
             .sort_values('Stage')
    )

    plt.figure(figsize=(8, 6))
    bars = plt.bar(stage_sums['Stage'], stage_sums['Number_of_Waves'], color=['blue', 'orange', 'green'])
    plt.title(f"Total Number of Waves by Stage (All Regions) - {condition}")
    plt.xlabel('Stage')
    plt.ylabel('Total Number of Waves')

    # Annotate each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2,
            height,
            str(int(height)),
            ha='center', va='bottom'
        )

    plt.tight_layout()
    stage_fig_path = os.path.join(output_dir, f"total_waves_by_stage_{condition}.png")
    plt.savefig(stage_fig_path, dpi=300)
    print(f"Saved bar graph (by Stage, all Regions) to: {stage_fig_path}")
    plt.close()

    # 2. Bar graph of total waves by Region (across all Stages)
    region_sums = (
        df_all.groupby('Region')['Number_of_Waves']
             .sum()
             .reset_index()
    )

    plt.figure(figsize=(8, 6))
    bars = plt.bar(region_sums['Region'], region_sums['Number_of_Waves'], color=['purple', 'gray', 'cyan'])
    plt.title(f"Total Number of Waves by Region (All Stages) - {condition}")
    plt.xlabel('Region')
    plt.ylabel('Total Number of Waves')

    # Annotate each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2,
            height,
            str(int(height)),
            ha='center', va='bottom'
        )

    plt.tight_layout()
    region_fig_path = os.path.join(output_dir, f"total_waves_by_region_{condition}.png")
    plt.savefig(region_fig_path, dpi=300)
    print(f"Saved bar graph (by Region, all Stages) to: {region_fig_path}")
    plt.close()

    # 3. Bar graphs of total waves by Stage, separated by Region
    region_stage_sums = (
        df_all.groupby(['Region', 'Stage'])['Number_of_Waves']
             .sum()
             .reset_index()
    )

    # Loop over unique regions
    for region in region_stage_sums['Region'].unique():
        subset = region_stage_sums[region_stage_sums['Region'] == region].copy()
        subset = subset.sort_values('Stage')

        plt.figure(figsize=(8, 6))
        bars = plt.bar(subset['Stage'], subset['Number_of_Waves'], color=['blue', 'orange', 'green'])
        plt.title(f"Total Waves by Stage for {region} - {condition}")
        plt.xlabel('Stage')
        plt.ylabel('Total Number of Waves')

        # Annotate each bar
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2,
                height,
                str(int(height)),
                ha='center', va='bottom'
            )

        plt.tight_layout()
        region_stage_fig_path = os.path.join(output_dir, f"total_waves_by_stage_for_{region}_{condition}.png")
        plt.savefig(region_stage_fig_path, dpi=300)
        print(f"Saved bar graph (Stage for {region}) to: {region_stage_fig_path}")
        plt.close()


if __name__ == "__main__":
    main()

