
# group_topo_power.py
"""
Group-level script for topographic power comparison (Late - Early).
Uses a default montage "GSN-HydroCel-257" for topomap plotting.
"""

import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind
import mne
import logging

##############################################################################
# 1) PARSING / SAFETY CHECK FOR topomap_diff
##############################################################################
def parse_topomap_diff(val, logger=None):
    """
    Safely parse a 'topomap_diff' entry into a numeric NumPy array.
    Returns an empty array if parsing fails or data is non-numeric.
    """
    # If it's already a list/array, convert to np.array
    if not isinstance(val, str):
        arr = np.array(val)
        # Check numeric
        if arr.dtype.kind in ["i", "f"]:
            return arr
        else:
            if logger:
                logger.warning(f"Non-numeric topomap array: {val}. Dropping.")
            return np.array([])
    else:
        # It's a string like "[0.1, 0.2, ...]"
        try:
            arr = np.array(eval(val))
            # Check numeric
            if arr.dtype.kind in ["i", "f"]:
                return arr
            else:
                if logger:
                    logger.warning(f"Non-numeric topomap string: {val[:60]}... Dropping.")
                return np.array([])
        except Exception as e:
            if logger:
                logger.warning(f"Error parsing topomap string: {val[:60]}... => {e}")
            return np.array([])

##############################################################################
# 2) LOAD & CONCAT
##############################################################################
def load_topo_data(power_analysis_dirs, logger=None):
    """
    Loads 'topomap_data.csv' from each subject's power_analysis folder,
    concatenates, and returns a single DataFrame. 
    Expects columns: ["Subject", "Condition", "topomap_diff"], possibly "channel_names".
    """
    all_dfs = []
    for padir in power_analysis_dirs:
        csv_path = os.path.join(padir, "topomap_data.csv")
        if not os.path.exists(csv_path):
            if logger:
                logger.warning(f"No topomap_data.csv found in {padir}. Skipping.")
            continue
        try:
            df_sub = pd.read_csv(csv_path)
            all_dfs.append(df_sub)
        except Exception as e:
            if logger:
                logger.error(f"Error reading {csv_path}: {e}", exc_info=True)
            continue
    
    if not all_dfs:
        if logger:
            logger.warning("No subject topo data loaded. Returning empty DataFrame.")
        return pd.DataFrame()
    
    df_all = pd.concat(all_dfs, ignore_index=True)

    # --- Parse 'topomap_diff' into numeric arrays & drop invalid rows ---
    df_all["topomap_diff"] = df_all["topomap_diff"].apply(lambda x: parse_topomap_diff(x, logger=logger))
    # Drop rows if we got an empty array or length 0
    original_len = len(df_all)
    df_all = df_all[df_all["topomap_diff"].apply(len) > 0].copy()
    if logger and len(df_all) < original_len:
        logger.info(f"Dropped {original_len - len(df_all)} rows with invalid topomap_diff data.")
    
    return df_all

##############################################################################
# 3) PLOT GROUP TOPO
##############################################################################
def plot_group_topomap(df_all, raw_info, output_dir, logger=None):
    """
    Splits df_all by Condition (SHAM vs. ACTIVE), stacks 'topomap_diff',
    computes t-tests at each channel, and plots group topomap difference.
    """
    # Clean up condition strings
    df_all["Condition"] = df_all["Condition"].astype(str).str.strip()

    df_sham   = df_all[df_all["Condition"] == "SHAM"]
    df_active = df_all[df_all["Condition"] == "ACTIVE"]

    if df_sham.empty or df_active.empty:
        if logger:
            logger.warning("One or both groups are empty. Cannot do topomap comparison.")
        return

    # Now topomap_diff are guaranteed numeric arrays
    sham_topos   = np.vstack(df_sham["topomap_diff"].values)   # shape (n_sham, n_channels)
    active_topos = np.vstack(df_active["topomap_diff"].values) # shape (n_active, n_channels)

    mean_sham   = sham_topos.mean(axis=0)
    mean_active = active_topos.mean(axis=0)
    diff_groups = mean_active - mean_sham

    tvals, pvals = ttest_ind(active_topos, sham_topos, axis=0, equal_var=False)
    alpha = 0.05
    n_ch = len(diff_groups)
    pvals_corrected = pvals * n_ch
    sig_channels = pvals_corrected < alpha

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))

    # 1) SHAM
    im0, _ = mne.viz.plot_topomap(
        mean_sham, raw_info, axes=axes[0], show=False, contours=0
    )
    axes[0].set_title("SHAM (mean Late-Early)")
    cbar0 = plt.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)
    cbar0.set_label("Power (uV²/Hz)")

    # 2) ACTIVE
    im1, _ = mne.viz.plot_topomap(
        mean_active, raw_info, axes=axes[1], show=False, contours=0
    )
    axes[1].set_title("ACTIVE (mean Late-Early)")
    cbar1 = plt.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)
    cbar1.set_label("Power (uV²/Hz)")

    # 3) DIFF (ACTIVE - SHAM) with significant channels
    im2, _ = mne.viz.plot_topomap(
        diff_groups, raw_info, axes=axes[2], show=False, contours=0,
        mask=sig_channels,
        mask_params=dict(marker='o', markerfacecolor='white', markeredgecolor='black', linewidth=2)
    )
    axes[2].set_title("ACTIVE - SHAM\n(sig chans highlighted)")
    cbar2 = plt.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)
    cbar2.set_label("Power (uV²/Hz)")

    fig.suptitle("Group Topomap Comparison (Late-Early PSD)")
    fig.tight_layout()

    fname = os.path.join(output_dir, "group_topomap_comparison.png")
    fig.savefig(fname)
    plt.close(fig)
    if logger:
        logger.info(f"Saved group topomap comparison to {fname}")

##############################################################################
# 4) MAIN GROUP TOPO FUNCTION
##############################################################################
def group_topo_power(main_output_dir):
    """
    1) Finds all subject-level power_analysis directories
    2) Loads 'topomap_data.csv' from each subject
    3) Uses a default montage 'GSN-HydroCel-257' for topomap
    4) Plots group-level difference with significant channels marked
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    if not os.path.exists(main_output_dir):
        os.makedirs(main_output_dir, exist_ok=True)

    pattern = os.path.join(main_output_dir, "**", "power_analysis")
    power_analysis_dirs = glob.glob(pattern, recursive=True)

    if not power_analysis_dirs:
        logger.warning("No power_analysis directories found. Exiting.")
        return

    # 1) Load all subject topomap data (and parse 'topomap_diff')
    df_all = load_topo_data(power_analysis_dirs, logger=logger)
    if df_all.empty:
        logger.warning("No topomap data loaded after parsing. Exiting.")
        return

    # 2) Create a dummy Info with the GSN-HydroCel-257 montage
    montage_name = "GSN-HydroCel-256"
    montage = mne.channels.make_standard_montage(montage_name)
    
    n_channels = len(montage.ch_names)
    info = mne.create_info(ch_names=montage.ch_names, sfreq=250, ch_types="eeg")
    info.set_montage(montage)

    # 3) Plot group-level topomap
    plot_group_topomap(df_all, info, main_output_dir, logger=logger)

    logger.info("Group-level topomap comparison complete.")


# Optional CLI usage:
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main_output_dir = sys.argv[1]
    else:
        main_output_dir = "/path/to/project"
    group_topo_power(main_output_dir)

