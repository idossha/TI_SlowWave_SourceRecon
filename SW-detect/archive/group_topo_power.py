
#!/usr/bin/env python
"""
Group-level script for averaging subject topomap CSV files.
There are two file types:
  (a) Regular topomap data with columns:
       Channel, Q1 Power, Q4 Power, Difference (Q4 - Q1)
  (b) FFT topomap data with columns:
       Channel, Q1 FFT Power, Q4 FFT Power, Difference FFT (Q4 - Q1)
A file named subject_condition.csv (located in the main directory) maps 
subject IDs to conditions.
The script:
  - Recursively finds all subject power_analysis folders in a main directory.
  - Reads subject_condition.csv to map subject ID → condition.
  - For each subject, extracts the subject ID from the folder path (by matching a numeric token that appears in subject_condition.csv).
  - Reads the subject CSV file (for each file type) and computes z-scores (across channels) for each metric.
  - Within each condition group, concatenates the subject data for documentation (saving a combined CSV) and
    then averages the subject z-scored data (using only channels that appear) for group topoplots.
  - Uses a standard montage to create topoplots for the group average (for Q1, Q4, and the difference).
  
Note: If not all group channels are present in the standard montage, only the common channels are used for plotting.
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
MAIN_OUTPUT_DIR = "/Volumes/Ido/strength/"  # <<< CHANGE THIS to your project directory

# Filenames for the two file types (choose one at a time or process both)
CSV_FILENAME_REGULAR = "topomap_data_stim_0.99-1.01_welch.csv"
CSV_FILENAME_FFT     = "topomap_data_stim_0.99-1.01_fft.csv"

# File that maps subject IDs to conditions (in the main project directory)
SUBJECT_CONDITION_FILE = os.path.join(MAIN_OUTPUT_DIR, "subject_condition.csv")

# Montage to use for plotting – adjust if necessary.
MONTAGE_NAME = "GSN-HydroCel-256"

# Fixed color scale limits for topoplots (adjust as desired)
VMIN = -2
VMAX = 2

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
# 6) CREATE GROUP TOPOPLOTS
##############################################################################
def plot_group_topoplots(group_df, group_name, output_dir, logger=None):
    """
    Given a group-level DataFrame (with columns: Channel, Q1, Q4, Diff) and
    an output directory, create three topoplots (for Q1, Q4, and Diff).
    
    This function finds the intersection between the group channels and the standard montage,
    builds a new montage from the common channels, and then plots using that Info object.
    A fixed color scale (vmin, vmax) is applied.
    """
    ch_names = group_df["Channel"].tolist()
    
    # Load the standard montage.
    try:
        montage_std = mne.channels.make_standard_montage(MONTAGE_NAME)
    except Exception as e:
        if logger:
            logger.error(f"Error loading montage {MONTAGE_NAME}: {e}")
        raise
    
    # Determine the common channels between group data and standard montage.
    common_ch = list(set(ch_names).intersection(set(montage_std.ch_names)))
    if not common_ch:
        if logger:
            logger.error("None of the group channels are present in the montage. Exiting plotting.")
        return
    
    # Order channels according to the standard montage.
    ordered_ch = [ch for ch in montage_std.ch_names if ch in common_ch]
    
    # Filter and order group_df accordingly.
    group_df_subset = group_df[group_df["Channel"].isin(ordered_ch)].copy()
    group_df_subset = group_df_subset.set_index("Channel").loc[ordered_ch].reset_index()
    
    # Build a channel-position dictionary from the standard montage.
    montage_positions = montage_std.get_positions()['ch_pos']
    ch_pos = {ch: montage_positions[ch] for ch in ordered_ch}
    
    # Create a new montage using the common channel positions.
    montage_subset = mne.channels.make_dig_montage(ch_pos=ch_pos, coord_frame='head')
    
    # Create an Info object.
    info = mne.create_info(ch_names=ordered_ch, sfreq=100, ch_types="eeg")
    info.set_montage(montage_subset)
    
    metrics = [("Q1", "Q1 Power (z-scored)"),
               ("Q4", "Q4 Power (z-scored)"),
               ("Diff", "Difference (Q4 - Q1) (z-scored)")]
    
    for metric_key, title in metrics:
        data = group_df_subset[metric_key].values
        fig, ax = plt.subplots(figsize=(6, 5))
        im, _ = mne.viz.plot_topomap(data, info, axes=ax, show=False, vlim=(VMIN,VMAX))
        ax.set_title(f"{group_name} Group - {title}")
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_ticks(np.linspace(VMIN, VMAX, 5))
        out_fname = os.path.join(output_dir, f"{group_name}_{metric_key}_topomap.png")
        fig.tight_layout()
        fig.savefig(out_fname)
        plt.close(fig)
        if logger:
            logger.info(f"Saved {out_fname}")

##############################################################################
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
      - Plotting group-level topoplots.
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

