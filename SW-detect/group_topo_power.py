
#!/usr/bin/env python
"""
Group-level script for averaging subject topomap CSV files.

Modifications:
1) Adds a global list of channels (EXCLUDE_CHANNELS) that you do NOT want to plot.
2) Uses an EEGLAB-like layout for topoplots by computing the head sphere
   origin and radius from four reference channels (Oz=E126, Fpz=E26, T7=E69, T8=E202).
"""

import os
import re
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import zscore
import mne
import logging

# --- SETTINGS --- #
# Main directory that contains subject-level output directories.
MAIN_OUTPUT_DIR = "/Volumes/Ido/analyze/"  # <<< CHANGE THIS to your project directory

# Filenames for the two file types (choose one at a time or process both)
CSV_FILENAME_REGULAR = "topomap_data_poststim_0.85-1.15_welch.csv"
CSV_FILENAME_FFT     = "topomap_data_poststim_0.85-1.15_fft.csv"

# File that maps subject IDs to conditions (in the main project directory)
SUBJECT_CONDITION_FILE = os.path.join(MAIN_OUTPUT_DIR, "subject_condition.csv")

# Montage to use for plotting
MONTAGE_NAME = "GSN-HydroCel-256"

# Fixed color scale limits for topoplots (adjust as desired)
VMIN = -2
VMAX = 2

# ------------------------------
# NEW: Channels to exclude
# (Will be dropped before plotting)
# Example: EXCLUDE_CHANNELS = ["E1", "E2", "E3"]
# ------------------------------

EXCLUDE_CHANNELS = [
    "E67", "E73", "E82", "E91", "E92", "E93", "E102", "E103", "E104", "E111", "E112", "E113",
    "E120", "E121", "E122", "E133", "E134", "E135", "E145", "E146", "E147", "E156", "E157",
    "E165", "E166", "E167", "E174", "E175", "E176", "E187", "E188", "E189", "E190", "E199",
    "E200", "E201", "E208", "E209", "E216", "E217", "E218", "E219", "E225", "E226", "E227", "E228",
    "E229", "E230", "E231","E232", "E233", "E234", "E235", "E236", "E237", "E238", "E239", "E240",
    "E241", "E242", "E243", "E244", "E245","E246", "E247", "E248", "E249", "E250", "E251", "E252",
    "E253", "E254", "E255", "E256"
]


##############################################################################
# Expected column mappings for each file type.
# For the regular file:
COL_MAP_REGULAR = {
    "Q1": "Q1 Power",
    "Q4": "Q4 Power",
    "Diff": "Difference"
}
# For the FFT file:
COL_MAP_FFT = {
    "Q1": "Q1 Power",
    "Q4": "Q4 Power",
    "Diff": "Difference"
}

##############################################################################
# 1) READ SUBJECT CONDITION MAPPING
##############################################################################
def read_subject_condition(mapping_file, logger=None):
    """
    Reads the subject_condition.csv file and returns a dictionary mapping
    subject ID (as a string) to condition (upper-case, stripped).
    
    Expected CSV format:
         subject, condition
    """
    try:
        df = pd.read_csv(mapping_file, sep=None, engine='python')
    except Exception as e:
        if logger:
            logger.error(f"Error reading {mapping_file}: {e}")
        raise

    cols = [col.lower() for col in df.columns]
    if "subject" not in cols or "condition" not in cols:
        msg = f"Expected columns 'subject' and 'condition' in {mapping_file}."
        if logger:
            logger.error(msg)
        raise ValueError(msg)

    mapping = {}
    for _, row in df.iterrows():
        subj = str(row["subject"]).strip()
        cond = str(row["condition"]).strip().upper()
        mapping[subj] = cond
    return mapping

##############################################################################
# 2) READ AND Z-SCORE SUBJECT DATA (Generic)
##############################################################################
def read_and_zscore_subject(csv_path, col_map, logger=None):
    """
    Reads a subject's CSV file (with expected columns) into a DataFrame and computes
    z-scores (across channels) for each metric.
    
    col_map is a dict mapping keys ("Q1", "Q4", "Diff") to the expected CSV column names.
    
    Returns a DataFrame with columns:
      Channel, Q1, Q4, Diff
    where the metric columns are the z-scored values.
    """
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        if logger:
            logger.error(f"Error reading {csv_path}: {e}")
        raise

    expected_cols = ["Channel"] + list(col_map.values())
    for col in expected_cols:
        if col not in df.columns:
            msg = f"Column '{col}' not found in {csv_path}."
            if logger:
                logger.error(msg)
            raise ValueError(msg)
    
    # Compute z-scores for each metric (across the subject's available channels)
    df["Q1 Z"] = zscore(df[col_map["Q1"]])
    df["Q4 Z"] = zscore(df[col_map["Q4"]])
    df["Diff Z"] = zscore(df[col_map["Diff"]])
    # Rename the z-scored columns to "Q1", "Q4", and "Diff" (for subsequent processing)
    df = df.rename(columns={"Q1 Z": "Q1", "Q4 Z": "Q4", "Diff Z": "Diff"})
    return df[["Channel", "Q1", "Q4", "Diff"]]

##############################################################################
# 3) EXTRACT SUBJECT ID FROM PATH
##############################################################################
def extract_subject_id(path, valid_subjects, logger=None):
    """
    Searches the given path for a numeric token that is in the valid_subjects set.
    Returns the subject ID as a string if found; otherwise, returns None.
    """
    nums = re.findall(r'\d+', path)
    for num in nums:
        if num in valid_subjects:
            return num
    if logger:
        logger.warning(f"Could not extract a valid subject ID from {path}")
    return None

##############################################################################
# 4) LOAD ALL SUBJECTS AND GROUP BY CONDITION (for a given file type)
##############################################################################
def load_group_subject_data(main_dir, subj_cond_map, csv_filename, col_map, logger=None):
    """
    Recursively finds all power_analysis folders under main_dir,
    reads the CSV file (specified by csv_filename) from each,
    extracts the subject ID from the folder path,
    looks up the subject condition in subj_cond_map,
    and returns a dictionary: { condition: [subject_df, ...], ... }.
    
    The CSV is read using the provided col_map.
    """
    group_data = {}
    pattern = os.path.join(main_dir, "**", "power_analysis")
    power_dirs = glob.glob(pattern, recursive=True)
    if logger:
        logger.info(f"Found {len(power_dirs)} power_analysis directories in {main_dir}.")
    valid_subjects = set(subj_cond_map.keys())
    for padir in power_dirs:
        csv_path = os.path.join(padir, csv_filename)
        if not os.path.exists(csv_path):
            if logger:
                logger.warning(f"CSV file {csv_path} not found; skipping.")
            continue
        subj_id = extract_subject_id(padir, valid_subjects, logger=logger)
        if subj_id is None:
            continue
        condition = subj_cond_map.get(subj_id)
        if condition is None:
            if logger:
                logger.warning(f"Subject ID {subj_id} not found in mapping; skipping {csv_path}.")
            continue
        try:
            subj_df = read_and_zscore_subject(csv_path, col_map, logger=logger)
            subj_df["Subject"] = subj_id
            subj_df["Condition"] = condition
        except Exception as e:
            if logger:
                logger.error(f"Error processing {csv_path}: {e}")
            continue
        group_data.setdefault(condition, []).append(subj_df)
    return group_data

##############################################################################
# 5) COMBINE SUBJECTS FOR A GROUP
##############################################################################
def combine_subjects(subject_dfs):
    """
    For a list of subject DataFrames (each with columns: Channel, Q1, Q4, Diff),
    combine them by channel.
    
    For each channel that appears in any subject, average the subject z-scored
    values (using only those subjects that contain that channel).
    
    Returns a DataFrame with columns:
         Channel, Q1, Q4, Diff
    """
    combined = {}
    for df in subject_dfs:
        for _, row in df.iterrows():
            ch = row["Channel"]
            if ch not in combined:
                combined[ch] = {"Q1": [], "Q4": [], "Diff": []}
            combined[ch]["Q1"].append(row["Q1"])
            combined[ch]["Q4"].append(row["Q4"])
            combined[ch]["Diff"].append(row["Diff"])
    avg_data = {"Channel": [], "Q1": [], "Q4": [], "Diff": []}
    for ch, metrics in combined.items():
        avg_data["Channel"].append(ch)
        avg_data["Q1"].append(np.mean(metrics["Q1"]))
        avg_data["Q4"].append(np.mean(metrics["Q4"]))
        avg_data["Diff"].append(np.mean(metrics["Diff"]))
    return pd.DataFrame(avg_data)

##############################################################################
# 6) CREATE GROUP TOPOPLOTS (EEGLAB STYLE)
##############################################################################


def plot_group_topoplots(group_df, group_name, output_dir, logger=None):
    """
    Plots group-level topomaps (Q1, Q4, Diff) using MNE's default layout.
    Excludes any channels in EXCLUDE_CHANNELS from the final plot.
    Attempts to display sensor names by passing 'names=...' to plot_topomap().

    Steps:
      1) Load the standard GSN-HydroCel-256 montage.
      2) Subset the DataFrame channels to exclude those in EXCLUDE_CHANNELS
         and ensure they exist in the montage.
      3) Order channels according to the montage order.
      4) Create a new Info object and set the subset montage.
      5) Plot topomaps for Q1, Q4, and Diff using MNE's defaults,
         passing 'names=...' and 'sensors=True' to label sensors.
    """
    # Color scale limits (adjust as needed)
    VMIN, VMAX = -2, 2

    # 1) Load the standard montage
    try:
        montage_std = mne.channels.make_standard_montage("GSN-HydroCel-256")
    except Exception as e:
        if logger:
            logger.error(f"Error loading montage GSN-HydroCel-256: {e}")
        return

    # 2) Filter out excluded channels and those not in the montage
    df_channels = group_df["Channel"].tolist()
    valid_ch = set(montage_std.ch_names)
    common_ch = list(set(df_channels).intersection(valid_ch) - set(EXCLUDE_CHANNELS))

    if not common_ch:
        if logger:
            logger.error("No valid channels left after exclusions and montage intersection.")
        return

    # 3) Preserve montage order
    ordered_ch = [ch for ch in montage_std.ch_names if ch in common_ch]

    # Subset the group DataFrame to those channels only, in that order
    group_df_subset = group_df[group_df["Channel"].isin(ordered_ch)].copy()
    group_df_subset = group_df_subset.set_index("Channel").loc[ordered_ch].reset_index()

    # 4) Create an Info object with subset montage
    montage_positions = montage_std.get_positions()['ch_pos']
    ch_pos = {ch: montage_positions[ch] for ch in ordered_ch}
    montage_subset = mne.channels.make_dig_montage(ch_pos=ch_pos, coord_frame='head')

    info = mne.create_info(ch_names=ordered_ch, sfreq=100, ch_types="eeg")
    info.set_montage(montage_subset)

    # 5) Plot topomaps for Q1, Q4, and Diff (try labeling channels)
    metrics = [
        ("Q1",   "Q1 Power (z-scored)"),
        ("Q4",   "Q4 Power (z-scored)"),
        ("Diff", "Difference (Q4 - Q1) (z-scored)")
    ]
    for metric_key, title in metrics:
        data = group_df_subset[metric_key].values

        fig, ax = plt.subplots(figsize=(6, 5))
        # Note: older MNE versions do NOT have "show_names". Instead,
        # we pass 'names=ordered_ch' and 'sensors=True' to label them.
        im, _ = mne.viz.plot_topomap(
            data, info,
            axes=ax,
            show=False,
            vlim=(VMIN, VMAX),
            sensors=True,        # Show sensor location markers
            names=ordered_ch     # Provide channel names in the same order
        )
        ax.set_title(f"{group_name} Group - {title}")

        cbar = fig.colorbar(im, ax=ax)
        cbar.set_ticks(np.linspace(VMIN, VMAX, 5))

        out_fname = os.path.join(output_dir, f"{group_name}_{metric_key}_topomap.png")
        fig.tight_layout()
        fig.savefig(out_fname)
        plt.close(fig)

        if logger:
            logger.info(f"Saved {out_fname}")
# 7) SAVE CONCATENATED SUBJECT CSV FOR DOCUMENTATION
##############################################################################
def save_concatenated_csv(group_data, output_dir, file_suffix, logger=None):
    """
    For each condition (group) in group_data (a dict with lists of subject DataFrames),
    concatenate the subject DataFrames into one DataFrame (adding subject and condition columns)
    and save it as a CSV file in output_dir. The filename will include file_suffix.
    """
    for condition, subj_dfs in group_data.items():
        if not subj_dfs:
            continue
        concat_df = pd.concat(subj_dfs, ignore_index=True)
        out_fname = os.path.join(output_dir, f"{condition}_concatenated_{file_suffix}.csv")
        concat_df.to_csv(out_fname, index=False)
        if logger:
            logger.info(f"Saved concatenated CSV for {condition} to {out_fname}")

##############################################################################
# 8) MAIN PROCESSING FUNCTION FOR A GIVEN FILE TYPE
##############################################################################
def process_file_type(main_dir, csv_filename, col_map, file_suffix, logger=None):
    """
    Processes one type of CSV file (specified by csv_filename and col_map) by:
      - Loading subject data and grouping by condition.
      - Saving concatenated subject CSVs for documentation.
      - Combining subject data within each group.
      - Plotting group-level topoplots (EEGLAB-style).
    """
    subj_cond_map = read_subject_condition(SUBJECT_CONDITION_FILE, logger=logger)
    logger.info(f"Loaded subject condition mapping for {len(subj_cond_map)} subjects.")
    group_data = load_group_subject_data(main_dir, subj_cond_map, csv_filename, col_map, logger=logger)
    if not group_data:
        logger.error("No subject data loaded. Exiting processing for file type.")
        return

    # Create an output directory for group plots for this file type.
    group_out_dir = os.path.join(main_dir, f"group_topoplots_{file_suffix}")
    os.makedirs(group_out_dir, exist_ok=True)
    
    # Save concatenated CSVs for documentation.
    save_concatenated_csv(group_data, group_out_dir, file_suffix, logger=logger)
    
    # For each group, combine subject data and plot.
    for condition, subj_dfs in group_data.items():
        logger.info(f"Group {condition}: {len(subj_dfs)} subject files found.")
        combined_df = combine_subjects(subj_dfs)
        logger.info(f"Group {condition}: Combined data has {len(combined_df)} channels.")
        plot_group_topoplots(combined_df, condition, group_out_dir, logger=logger)

##############################################################################
# 9) MAIN
##############################################################################
def main(main_output_dir):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    if not os.path.exists(main_output_dir):
        logger.error(f"Main output directory {main_output_dir} does not exist. Exiting.")
        return

    # Process the regular topomap data
    logger.info("Processing regular topomap data...")
    process_file_type(main_output_dir, CSV_FILENAME_REGULAR, COL_MAP_REGULAR, "regular", logger=logger)
    
    # Process the FFT topomap data
    logger.info("Processing FFT topomap data...")
    process_file_type(main_output_dir, CSV_FILENAME_FFT, COL_MAP_FFT, "fft", logger=logger)
    
    logger.info("Group topoplot processing complete.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main_output_dir = sys.argv[1]
    else:
        main_output_dir = MAIN_OUTPUT_DIR
    main(main_output_dir)

