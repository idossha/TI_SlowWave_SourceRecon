
# group_PSD.py
"""
Group-level script for PSD comparison (SHAM vs. ACTIVE) with:
1) Cluster-based permutation test for significance analysis.
2) Bonferroni correction for multiple comparisons in the standard t-test.
3) Highlighting of significant frequency bins in the plot.
"""

import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind, zscore
from statsmodels.stats.multitest import multipletests
from mne.stats import permutation_cluster_test
import logging
import sys
import ast  # optional, for safer literal_eval

# Constants
FREQ_BAND = [0.5, 2]  # Full band of interest
ENTRAINMENT_BAND = [0.9, 1.1]  # Narrow band for separate analysis

# Logger setup
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s', 
                              datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(console_handler)


##############################################################################
# 1) LOAD & CONCATENATE DATA
##############################################################################
def load_and_concatenate_subject_data(power_analysis_dirs, logger=None):
    """Loads PSD data from each subject and concatenates into a single DataFrame."""
    all_dfs = []
    for padir in power_analysis_dirs:
        csv_path = os.path.join(padir, "psd_data_stim.csv")
        if not os.path.exists(csv_path):
            if logger:
                logger.warning(f"No PSD CSV found in {padir}. Skipping.")
            continue
        try:
            df_sub = pd.read_csv(csv_path)
            # Ensure freq_bins and psd_diff are stored as proper numpy arrays.
            # Using ast.literal_eval for safety.
            df_sub["freq_bins"] = df_sub["freq_bins"].apply(
                lambda x: np.array(ast.literal_eval(x)) if isinstance(x, str) else np.array(x))
            df_sub["psd_diff"] = df_sub["psd_diff"].apply(
                lambda x: np.array(ast.literal_eval(x)) if isinstance(x, str) else np.array(x))
            all_dfs.append(df_sub)
        except Exception as e:
            if logger:
                logger.error(f"Error reading {csv_path}: {e}", exc_info=True)
            continue

    if not all_dfs:
        if logger:
            logger.warning("No subject data loaded. Returning empty DataFrame.")
        return pd.DataFrame()

    df_all = pd.concat(all_dfs, ignore_index=True)
    return df_all


##############################################################################
# 2) CHECK IF INTERPOLATION IS NECESSARY
##############################################################################
def check_and_unify_freq_bins(df_all, logger=None):
    """Checks if freq_bins are already identical; if not, interpolates."""
    if df_all.empty:
        return df_all

    # Check if all subjects have the same number of frequency bins
    unique_bin_counts = df_all["freq_bins"].apply(len).nunique()
    if unique_bin_counts == 1:
        if logger:
            logger.info("All subjects already have matching freq_bins. Skipping interpolation.")
        return df_all

    # Otherwise, interpolate to match the first subject's bins
    ref_freq = df_all.iloc[0]["freq_bins"]
    if logger:
        logger.info(f"Using subject {df_all.iloc[0]['Subject']} freq_bins as reference.")

    for idx, row in df_all.iterrows():
        current_freq = row["freq_bins"]
        current_psd  = row["psd_diff"]

        if len(current_freq) != len(ref_freq):
            sort_idx = np.argsort(current_freq)
            current_freq = current_freq[sort_idx]
            current_psd  = current_psd[sort_idx]
            new_psd = np.interp(ref_freq, current_freq, current_psd)

            df_all.at[idx, "freq_bins"] = ref_freq
            df_all.at[idx, "psd_diff"]  = new_psd

    if logger:
        logger.info("Interpolation complete.")
    return df_all


##############################################################################
# 3) PLOT & STORE T-TEST RESULTS WITH PERMUTATION TEST
##############################################################################
def plot_group_psd_comparison(df_all, output_dir, logger=None):
    """
    1) Z-score the difference per subject.
    2) Compute mean Z-scored PSD for SHAM and ACTIVE.
    3) Perform independent T-tests with Bonferroni correction.
    4) Run a cluster-based permutation test.
    5) Save T-test results to CSV.
    6) Plot the PSD comparison and mark significant bins.
    """
    df_all["Condition"] = df_all["Condition"].astype(str).str.strip()

    df_sham = df_all[df_all["Condition"] == "SHAM"]
    df_active = df_all[df_all["Condition"] == "ACTIVE"]

    if df_sham.empty or df_active.empty:
        if logger:
            logger.warning("One or both groups are empty. Cannot compare SHAM vs ACTIVE.")
        return

    freq_bins = df_sham.iloc[0]["freq_bins"]
    n_freqs = len(freq_bins)

    sham_psd_matrix = np.vstack(df_sham["psd_diff"].values)
    active_psd_matrix = np.vstack(df_active["psd_diff"].values)

    # Step 1: Z-score each subject's PSD difference
    sham_psd_matrix_z = zscore(sham_psd_matrix, axis=1, nan_policy="omit")
    active_psd_matrix_z = zscore(active_psd_matrix, axis=1, nan_policy="omit")

    # Step 2: Compute mean of Z-scored values for each condition
    mean_sham_z = np.nanmean(sham_psd_matrix_z, axis=0)
    mean_active_z = np.nanmean(active_psd_matrix_z, axis=0)

    # Step 3: Independent T-test across all frequency bins
    tvals, pvals = ttest_ind(active_psd_matrix_z, sham_psd_matrix_z, axis=0, equal_var=False)

    # Step 4: Bonferroni correction for multiple comparisons
    _, pvals_corrected, _, _ = multipletests(pvals, method='bonferroni')

    # Step 5: Cluster-based permutation test
    # Note: The 'tail' argument is ignored and a 1-tailed F-test is performed.
    data = [sham_psd_matrix_z, active_psd_matrix_z]
    T_obs, clusters, cluster_p_values, H0 = permutation_cluster_test(
        data, n_permutations=1000, tail=0, n_jobs=-1)

    # Map the cluster p-values to a full-length array (one per frequency bin)
    cluster_p_values_full = np.full(len(freq_bins), np.nan)
    for i, cluster in enumerate(clusters):
        # 'cluster' is a boolean array of indices for the frequency bins in that cluster.
        cluster_p_values_full[cluster] = cluster_p_values[i]

    # Step 6: Save T-test and permutation test results to CSV
    df_ttest = pd.DataFrame({
        "Frequency (Hz)": freq_bins,
        "T-value": tvals,
        "P-value (uncorrected)": pvals,
        "P-value (Bonferroni corrected)": pvals_corrected,
        "Cluster p-value": cluster_p_values_full
    })
    df_ttest.to_csv(os.path.join(output_dir, "t_test_results.csv"), index=False)

    # Step 7: Plot results
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(freq_bins, mean_sham_z, label="SHAM (Z-scored)", color="blue")
    ax.plot(freq_bins, mean_active_z, label="ACTIVE (Z-scored)", color="red")

    # Mark significant frequency bins (Bonferroni corrected)
    significant_bins = np.where(pvals_corrected < 0.05)[0]
    if significant_bins.size > 0:
        ax.scatter(freq_bins[significant_bins], mean_active_z[significant_bins],
                   color="black", label="Bonferroni p<0.05", zorder=3)

    # Mark significant clusters from permutation test
    for i, cluster in enumerate(clusters):
        if cluster_p_values[i] < 0.05:
            cluster_freqs = freq_bins[cluster]
            # Draw an axvspan covering the cluster range
            ax.axvspan(cluster_freqs[0], cluster_freqs[-1], color='purple', alpha=0.3,
                       label="Cluster p<0.05" if i == 0 else None)

    ax.axvspan(ENTRAINMENT_BAND[0], ENTRAINMENT_BAND[1], color='green', alpha=0.2,
               label="0.9–1.1 Hz Band")
    ax.axhline(0, color='gray', linestyle=':')
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Z-scored PSD Difference")
    ax.set_title("SHAM vs. ACTIVE: Group Mean PSD Difference (Z-scored)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "group_psd_comparison_zscore.png"))
    plt.close(fig)

    if logger:
        logger.info("Saved group PSD comparison plot and T-test results.")


##############################################################################
# MAIN FUNCTION
##############################################################################
def group_power_psd(main_output_dir):
    logger = logging.getLogger(__name__)
    power_analysis_dirs = glob.glob(os.path.join(main_output_dir, "**", "power_analysis"), recursive=True)
    df_all = load_and_concatenate_subject_data(power_analysis_dirs, logger=logger)
    df_all = check_and_unify_freq_bins(df_all, logger=logger)
    plot_group_psd_comparison(df_all, main_output_dir, logger=logger)


if __name__ == "__main__":
    main_output_dir = sys.argv[1] if len(sys.argv) > 1 else "/path/to/project"
    group_power_psd(main_output_dir)

