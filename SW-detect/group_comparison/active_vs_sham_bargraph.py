'''
python active_vs_sham.py \
  --project_dir /Volumes/CSC-Ido/Analyze \
  --nights N1 \
  --active_subjects 101 102 109 112 114 115 116 117 120 121 122 132 \
  --sham_subjects 107 110 111 119 127 \
  --output_dir /Users/idohaber/Desktop
'''
import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def load_data_for_subject_night(project_dir, subject, night):
    """
    Load the CSV for a given subject and night.
    Adjust path to match your data structure:
      {project_dir}/{subject}/{night}/output/Strength_{subject}_{night}_forSW/original_detection.csv
    """
    csv_path = os.path.join(
        project_dir,
        str(subject),
        str(night),
        "output",
        f"Strength_{subject}_{night}_forSW",
        "original_detection.csv"
    )
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    
    return pd.read_csv(csv_path)

def filter_df_by_ptp_category(df, category_label, ptp_col="PTP"):
    """
    Return a filtered version of df based on the category label:
      - "ptp_under_75": keep only rows where PTP < 75
      - "ptp_over_75":  keep only rows where PTP >= 75
      - "ptp_all":      keep all rows (no filter)

    df:        input DataFrame
    category_label: one of ["ptp_under_75", "ptp_over_75", "ptp_all"]
    ptp_col:   name of the column containing PTP values
    """
    if category_label == "ptp_under_75":
        return df[df[ptp_col] < 75].copy()
    elif category_label == "ptp_over_75":
        return df[df[ptp_col] >= 75].copy()
    else:  # ptp_all
        return df.copy()

def compute_first_last_hour_diff(df,
                                 time_col='Start', 
                                 slope_col='Slope', 
                                 freq_col='Frequency', 
                                 ptp_col='PTP'):
    """
    Given a DataFrame with columns for time, slope, freq, and PTP,
    compute the difference in average values between the *last hour* 
    and the *first hour*.

    By default:
      - First hour = time <= 3600
      - Last hour = time >= (max_time - 3600)

    Returns a dict: {'slope_diff', 'freq_diff', 'ptp_diff'}
    or None if we cannot compute (e.g., no data in first or last hour).
    """
    if df.empty:
        return None

    times = df[time_col].values
    slope = df[slope_col].values
    freq  = df[freq_col].values
    ptp   = df[ptp_col].values

    max_time = np.max(times)

    # Define masks
    first_mask = (times <= 3600)
    last_mask = (times >= (max_time - 3600))

    # If no data in first or last hour, return None
    if not np.any(first_mask) or not np.any(last_mask):
        return None

    # Means
    first_slope_mean = np.mean(slope[first_mask])
    first_freq_mean  = np.mean(freq[first_mask])
    first_ptp_mean   = np.mean(ptp[first_mask])

    last_slope_mean  = np.mean(slope[last_mask])
    last_freq_mean   = np.mean(freq[last_mask])
    last_ptp_mean    = np.mean(ptp[last_mask])

    return {
        'slope_diff': last_slope_mean - first_slope_mean,
        'freq_diff':  last_freq_mean  - first_freq_mean,
        'ptp_diff':   last_ptp_mean   - first_ptp_mean
    }

def plot_group_diffs(active_data, sham_data, title_str, ylabel, save_name, output_dir):
    """
    Makes a bar chart comparing Active vs. SHAM for a single metric (e.g., slope diff),
    with standard deviation error bars, and saves the figure.

    active_data, sham_data: numeric arrays/lists
    title_str: Plot title
    ylabel: Y-axis label
    save_name: file name for the saved plot
    output_dir: directory to which we save
    """
    active_data = np.array(active_data)
    sham_data = np.array(sham_data)

    mean_active = np.mean(active_data) if len(active_data) else np.nan
    mean_sham   = np.mean(sham_data) if len(sham_data) else np.nan
    std_active  = np.std(active_data) if len(active_data) else np.nan
    std_sham    = np.std(sham_data) if len(sham_data) else np.nan

    x_pos = [0, 1]
    means = [mean_active, mean_sham]
    stds  = [std_active,  std_sham]

    fig, ax = plt.subplots(figsize=(5, 5))
    bars = ax.bar(x_pos, means, yerr=stds, capsize=5, color=['blue', 'gray'], alpha=0.7)
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(["Active", "SHAM"])
    ax.set_ylabel(ylabel)
    ax.set_title(title_str)

    # Jitter for individual subject points
    jitter_factor = 0.05
    for val in active_data:
        ax.plot(0 + np.random.uniform(-jitter_factor, jitter_factor), 
                val, 'o', color='blue', alpha=0.5, markersize=4)
    for val in sham_data:
        ax.plot(1 + np.random.uniform(-jitter_factor, jitter_factor), 
                val, 'o', color='gray', alpha=0.5, markersize=4)

    plt.tight_layout()
    outpath = os.path.join(output_dir, save_name)
    plt.savefig(outpath, dpi=150)
    print(f"Saved figure to: {outpath}")
    plt.close(fig)  # close for memory cleanliness

def main():
    parser = argparse.ArgumentParser(
        description="Compute and plot changes from first hour to last hour for Active vs SHAM, split by PTP category."
    )
    parser.add_argument("--project_dir", "-p", type=str, required=True,
                        help="Path to the project directory.")
    parser.add_argument("--nights", "-n", nargs="+", default=["N1"],
                        help="Nights to process (default: N1).")
    parser.add_argument("--active_subjects", nargs="+", default=[],
                        help="List of subject IDs in the Active group.")
    parser.add_argument("--sham_subjects", nargs="+", default=[],
                        help="List of subject IDs in the SHAM group.")
    parser.add_argument("--output_dir", "-o", type=str, default=None,
                        help="Directory to save figures. Defaults to project_dir if not specified.")
    args = parser.parse_args()

    project_dir = args.project_dir
    output_dir = args.output_dir if args.output_dir else project_dir
    nights = args.nights

    active_subjects = args.active_subjects
    sham_subjects = args.sham_subjects

    # We will handle 3 categories of PTP:
    categories = [
        ("ptp_under_75", "waves with PTP < 75"),
        ("ptp_over_75",  "waves with PTP >= 75"),
        ("ptp_all",      "all waves")
    ]

    # For each category, we will create 3 bar plots: slope, freq, ptp => 9 total

    # Loop over each category
    for cat_label, cat_desc in categories:
        print(f"\n--- Processing category: {cat_label} ({cat_desc}) ---")
        
        # We collect diffs for Active group
        active_slope_diffs = []
        active_freq_diffs  = []
        active_ptp_diffs   = []

        # We collect diffs for SHAM group
        sham_slope_diffs = []
        sham_freq_diffs  = []
        sham_ptp_diffs   = []

        # Process Active group
        for subj in active_subjects:
            for night in nights:
                try:
                    df = load_data_for_subject_night(project_dir, subj, night)
                except FileNotFoundError:
                    print(f"Warning: no data for subject {subj}, night {night}. Skipping.")
                    continue
                
                # Filter by the PTP category (if needed)
                df_filtered = filter_df_by_ptp_category(df, cat_label, ptp_col="PTP")
                # Compute difference if possible
                diffs = compute_first_last_hour_diff(df_filtered)
                if diffs is not None:
                    active_slope_diffs.append(diffs['slope_diff'])
                    active_freq_diffs.append(diffs['freq_diff'])
                    active_ptp_diffs.append(diffs['ptp_diff'])
                else:
                    print(f"Warning: insufficient data for {subj}, night {night} in category {cat_label}.")

        # Process SHAM group
        for subj in sham_subjects:
            for night in nights:
                try:
                    df = load_data_for_subject_night(project_dir, subj, night)
                except FileNotFoundError:
                    print(f"Warning: no data for subject {subj}, night {night}. Skipping.")
                    continue
                
                # Filter by the PTP category
                df_filtered = filter_df_by_ptp_category(df, cat_label, ptp_col="PTP")
                # Compute difference if possible
                diffs = compute_first_last_hour_diff(df_filtered)
                if diffs is not None:
                    sham_slope_diffs.append(diffs['slope_diff'])
                    sham_freq_diffs.append(diffs['freq_diff'])
                    sham_ptp_diffs.append(diffs['ptp_diff'])
                else:
                    print(f"Warning: insufficient data for {subj}, night {night} in category {cat_label}.")

        # Now we produce 3 plots for each category: slope, freq, ptp

        # 1) Slope
        plot_group_diffs(
            active_slope_diffs,
            sham_slope_diffs,
            title_str=f"ΔSlope (Last Hr - First Hr)\n({cat_desc})",
            ylabel="ΔSlope",
            save_name=f"Diff_Slope_Active_vs_SHAM_{cat_label}.png",
            output_dir=output_dir
        )

        # 2) Frequency
        plot_group_diffs(
            active_freq_diffs,
            sham_freq_diffs,
            title_str=f"ΔFrequency (Last Hr - First Hr)\n({cat_desc})",
            ylabel="ΔFrequency (Hz)",
            save_name=f"Diff_Freq_Active_vs_SHAM_{cat_label}.png",
            output_dir=output_dir
        )

        # 3) PTP
        plot_group_diffs(
            active_ptp_diffs,
            sham_ptp_diffs,
            title_str=f"ΔPTP (Last Hr - First Hr)\n({cat_desc})",
            ylabel="ΔPTP",
            save_name=f"Diff_PTP_Active_vs_SHAM_{cat_label}.png",
            output_dir=output_dir
        )

if __name__ == "__main__":
    main()

