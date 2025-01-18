import os
import pandas as pd

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
    subjects = [101, 102, 108, 109, 112, 114, 115, 116, 117, 120, 121, 122, 132]
    # subjects = [107,110,111,119,127]
    nights = ["N1"]
    csv_files = [
        "wave_quantification_L_frontal.csv",
        "wave_quantification_R_frontal.csv",
        "wave_quantification_Posterior.csv"
    ]
    
    # Condition variable (e.g., "Active" or "SHAM")
    condition = "Active"
    
    # 1. Gather Data
    df_all = gather_data(project_directory, subjects, nights, csv_files)
    if df_all.empty:
        return

    # Create output directory for group-level analysis
    output_dir = os.path.join(project_directory, "Group_Analysis")
    os.makedirs(output_dir, exist_ok=True)

    # 2. Save the aggregated data
    aggregated_csv_path = os.path.join(output_dir, f"aggregated_wave_data_{condition}.csv")
    df_all.to_csv(aggregated_csv_path, index=False)
    print(f"Aggregated CSV saved to: {aggregated_csv_path}")


if __name__ == "__main__":
    main()
