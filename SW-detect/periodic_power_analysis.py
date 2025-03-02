
#!/usr/bin/env python
"""
periodic_power_analysis.py

This script performs an IRASA analysis on quarter segments of stimulation and post-stimulation epochs.
For each protocol, it computes the periodic and aperiodic components (using IRASA)
from Q1 and Q4 segments and then:
  1. For stimulation epochs: compares (Q4 - Q1)
  2. For post-stimulation epochs (after splitting via get_quarters): compares (Q1 - Q4)
It then computes average differences across protocols and produces topoplots
for a set of frequency bands for both the periodic and aperiodic components.
"""

import os
import numpy as np
import pandas as pd
import mne
import matplotlib
import matplotlib.pyplot as plt
import yasa
import logging
import argparse
from scipy.signal import welch

matplotlib.use('Agg')

###############################################################################
# Global Constants
###############################################################################
FMIN = 0.5
FMAX = 30
WIN_SEC = 4
TARGET_CHANNELS = ['E37', 'E33', 'E32', 'E31', 'E25', 'E18', 'E28', 'E11']

ENTRAINMENT_BANDS = [
    [0.99, 1.01],
    [0.95, 1.05],
    [0.9, 1.1],
    [0.85, 1.15],
    [0.8, 1.2],
    [0.5, 2],
    [0.5, 4]
]

###############################################################################
# Helper Functions
###############################################################################
def get_quarters(epoch_tuple):
    """
    Given an epoch (start, end, protocol_number), return:
      Q1 = (start, start+quarter, protocol_number)
      Q4 = (end - quarter, end, protocol_number)
    """
    start, end, prot_num = epoch_tuple
    duration = end - start
    quarter = duration // 4
    return ((start, start + quarter, prot_num),
            (end - quarter, end, prot_num))

def split_stim_epochs(raw, min_stim_duration_sec=100, logger=None):
    """
    Extract pre-stim, Q1 stim, Q4 stim, and post-stim epochs from raw.
    """
    sf = raw.info['sfreq']
    column_dict = {'stim end': 1, 'stim start': 2}
    stim_end_index = column_dict['stim end']
    stim_start_index = column_dict['stim start']
    events, _ = mne.events_from_annotations(raw)
    filtered_data = [evt for evt in events if evt[2] in (stim_end_index, stim_start_index)]
    min_stim_samples = int(min_stim_duration_sec * sf)
    
    pre_stim_epochs = []
    q1_stim_epochs = []
    q4_stim_epochs = []
    post_stim_epochs = []
    
    previous_end = 0
    protocol_number = 1
    for i in range(0, len(filtered_data), 2):
        if i + 1 < len(filtered_data):
            stim_start = filtered_data[i][0]
            stim_end = filtered_data[i+1][0]
            stim_duration = stim_end - stim_start
            if stim_duration < min_stim_samples:
                if logger:
                    logger.info(f"Skipping stim block #{protocol_number}: duration < {min_stim_duration_sec}s.")
                continue
            # For stim, define Q1 and Q4 as the first and last quarters of the stimulation period.
            q1_epoch = (stim_start, stim_start + (stim_duration // 4), protocol_number)
            q4_epoch = (stim_end - (stim_duration // 4), stim_end, protocol_number)
            pre_stim_epoch = (stim_start - stim_duration, stim_start, protocol_number)
            post_stim_epoch = (stim_end, stim_end + stim_duration, protocol_number)
            if pre_stim_epoch[0] < previous_end:
                continue
            previous_end = post_stim_epoch[1]
            pre_stim_epochs.append(pre_stim_epoch)
            q1_stim_epochs.append(q1_epoch)
            q4_stim_epochs.append(q4_epoch)
            post_stim_epochs.append(post_stim_epoch)
            protocol_number += 1
    if logger:
        logger.info(f"Found {len(q1_stim_epochs)} valid stimulation blocks.")
    return pre_stim_epochs, q1_stim_epochs, q4_stim_epochs, post_stim_epochs

def compute_irasa_for_segment_quarter(raw, epoch, chan_name, chan_list, fmin=FMIN, fmax=FMAX, win_sec=WIN_SEC):
    """
    Compute IRASA on the data in the segment defined by epoch (start, end, protocol).
    Returns:
      freqs, psd_aperiodic, psd_osc (periodic component)
    for the specified channel.
    """
    sf = raw.info['sfreq']
    if chan_name not in chan_list:
        raise ValueError(f"Channel {chan_name} not found in channel list.")
    chan_idx = chan_list.index(chan_name)
    
    # Extract data for the segment
    segment_data = raw.get_data(start=epoch[0], stop=epoch[1])
    freqs, psd_aperiodic_all, psd_osc_all = yasa.irasa(segment_data, sf, ch_names=chan_list,
                                                       band=(fmin, fmax), win_sec=win_sec,
                                                       return_fit=False)
    psd_aperiodic = psd_aperiodic_all[chan_idx, :]
    psd_osc = psd_osc_all[chan_idx, :]
    return freqs, psd_aperiodic, psd_osc

###############################################################################
# Protocol-Level IRASA Analysis
###############################################################################
def analyze_protocols_irasa(raw, q1_stim_epochs, q4_stim_epochs, post_stim_epochs, output_dir,
                            subject_id=None, condition=None, logger=None, target_chan=None):
    """
    For each protocol:
      - For stimulation epochs:
          * Compute IRASA on Q1 and Q4 segments.
          * Compare periodic difference = (Q4_periodic - Q1_periodic)
            and aperiodic difference = (Q4_aperiodic - Q1_aperiodic).
      - For post-stimulation epochs:
          * Split each post-stim epoch into quarters via get_quarters.
          * Compute IRASA on Q1 and Q4 and compare differences as (Q1 - Q4).
    Generates comparison plots and saves CSV statistics.
    """
    sf = raw.info['sfreq']
    chan_list = raw.info['ch_names']
    if target_chan is None:
        for ch in TARGET_CHANNELS:
            if ch in chan_list:
                target_chan = ch
                break
        if target_chan is None:
            target_chan = chan_list[0]
    
    irasa_dir = os.path.join(output_dir, "irasa_analysis")
    os.makedirs(irasa_dir, exist_ok=True)
    
    protocol_stats = []
    
    # Process stimulation protocols
    for prot_idx, (q1_ep, q4_ep) in enumerate(zip(q1_stim_epochs, q4_stim_epochs)):
        prot_num = prot_idx + 1
        try:
            freqs_q1, aperiodic_q1, periodic_q1 = compute_irasa_for_segment_quarter(raw, q1_ep, target_chan, chan_list)
            freqs_q4, aperiodic_q4, periodic_q4 = compute_irasa_for_segment_quarter(raw, q4_ep, target_chan, chan_list)
        except Exception as e:
            if logger:
                logger.warning(f"Stim Protocol {prot_num}: Error computing IRASA: {e}. Skipping.")
            continue
        
        if not np.array_equal(freqs_q1, freqs_q4):
            if logger:
                logger.warning(f"Stim Protocol {prot_num}: Frequency arrays differ. Skipping.")
            continue
        
        # For stimulation, differences are (Q4 - Q1)
        diff_periodic = periodic_q4 - periodic_q1
        diff_aperiodic = aperiodic_q4 - aperiodic_q1
        
        protocol_stats.append({
            "protocol": prot_num,
            "stage": "stim",
            "freqs": freqs_q1,
            "q1_periodic": periodic_q1,
            "q4_periodic": periodic_q4,
            "diff_periodic": diff_periodic,
            "q1_aperiodic": aperiodic_q1,
            "q4_aperiodic": aperiodic_q4,
            "diff_aperiodic": diff_aperiodic
        })
        
        # Plot periodic and aperiodic comparisons for this stim protocol
        fig, axs = plt.subplots(2, 1, figsize=(10, 10))
        axs[0].plot(freqs_q1, periodic_q1, label="Q1 Periodic", color="orange")
        axs[0].plot(freqs_q1, periodic_q4, label="Q4 Periodic", color="red")
        axs[0].plot(freqs_q1, diff_periodic, label="Diff (Q4-Q1)", color="blue")
        axs[0].axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
        axs[0].set_xlabel("Frequency (Hz)")
        axs[0].set_ylabel("Periodic Power")
        axs[0].set_title(f"Stim Protocol {prot_num}: Periodic Component")
        axs[0].legend()
        
        axs[1].plot(freqs_q1, aperiodic_q1, label="Q1 Aperiodic", color="orange")
        axs[1].plot(freqs_q1, aperiodic_q4, label="Q4 Aperiodic", color="red")
        axs[1].plot(freqs_q1, diff_aperiodic, label="Diff (Q4-Q1)", color="blue")
        axs[1].axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
        axs[1].set_xlabel("Frequency (Hz)")
        axs[1].set_ylabel("Aperiodic Power")
        axs[1].set_title(f"Stim Protocol {prot_num}: Aperiodic Component")
        axs[1].legend()
        
        fig.tight_layout()
        fig.savefig(os.path.join(irasa_dir, f"stim_protocol_{prot_num}_irasa_comparison.png"))
        plt.close(fig)
        if logger:
            logger.info(f"Stim Protocol {prot_num}: IRASA comparisons plotted.")
    
    # Process post-stimulation protocols
    post_protocol_stats = []
    for prot_idx, post_ep in enumerate(post_stim_epochs):
        prot_num = prot_idx + 1
        # Split post-stim epoch into quarters using get_quarters
        q1_post, q4_post = get_quarters(post_ep)
        try:
            freqs_post_q1, aperiodic_post_q1, periodic_post_q1 = compute_irasa_for_segment_quarter(raw, q1_post, target_chan, chan_list)
            freqs_post_q4, aperiodic_post_q4, periodic_post_q4 = compute_irasa_for_segment_quarter(raw, q4_post, target_chan, chan_list)
        except Exception as e:
            if logger:
                logger.warning(f"Post-Stim Protocol {prot_num}: Error computing IRASA: {e}. Skipping.")
            continue
        
        if not np.array_equal(freqs_post_q1, freqs_post_q4):
            if logger:
                logger.warning(f"Post-Stim Protocol {prot_num}: Frequency arrays differ. Skipping.")
            continue
        
        # For post-stim, differences are (Q1 - Q4)
        diff_periodic_post = periodic_post_q1 - periodic_post_q4
        diff_aperiodic_post = aperiodic_post_q1 - aperiodic_post_q4
        
        post_protocol_stats.append({
            "protocol": prot_num,
            "stage": "poststim",
            "freqs": freqs_post_q1,
            "q1_periodic": periodic_post_q1,
            "q4_periodic": periodic_post_q4,
            "diff_periodic": diff_periodic_post,
            "q1_aperiodic": aperiodic_post_q1,
            "q4_aperiodic": aperiodic_post_q4,
            "diff_aperiodic": diff_aperiodic_post
        })
        
        # Plot comparisons for post-stim protocol
        fig, axs = plt.subplots(2, 1, figsize=(10, 10))
        axs[0].plot(freqs_post_q1, periodic_post_q1, label="Q1 Periodic", color="orange")
        axs[0].plot(freqs_post_q1, periodic_post_q4, label="Q4 Periodic", color="red")
        axs[0].plot(freqs_post_q1, diff_periodic_post, label="Diff (Q1-Q4)", color="blue")
        axs[0].axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
        axs[0].set_xlabel("Frequency (Hz)")
        axs[0].set_ylabel("Periodic Power")
        axs[0].set_title(f"Post-Stim Protocol {prot_num}: Periodic Component")
        axs[0].legend()
        
        axs[1].plot(freqs_post_q1, aperiodic_post_q1, label="Q1 Aperiodic", color="orange")
        axs[1].plot(freqs_post_q1, aperiodic_post_q4, label="Q4 Aperiodic", color="red")
        axs[1].plot(freqs_post_q1, diff_aperiodic_post, label="Diff (Q1-Q4)", color="blue")
        axs[1].axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
        axs[1].set_xlabel("Frequency (Hz)")
        axs[1].set_ylabel("Aperiodic Power")
        axs[1].set_title(f"Post-Stim Protocol {prot_num}: Aperiodic Component")
        axs[1].legend()
        
        fig.tight_layout()
        fig.savefig(os.path.join(irasa_dir, f"poststim_protocol_{prot_num}_irasa_comparison.png"))
        plt.close(fig)
        if logger:
            logger.info(f"Post-Stim Protocol {prot_num}: IRASA comparisons plotted.")
    
    # Combine and save protocol statistics as CSV
    all_stats = protocol_stats + post_protocol_stats
    if all_stats:
        df_stats = pd.DataFrame(all_stats)
        df_stats.to_csv(os.path.join(irasa_dir, "protocol_irasa_stats.csv"), index=False)
        if logger:
            logger.info("Saved protocol IRASA statistics CSV.")

###############################################################################
# Average IRASA Components Across Protocols
###############################################################################
def plot_average_irasa_components(raw, q1_epochs, q4_epochs, output_dir, epoch_type="stim",
                                  logger=None, target_chan=None):
    """
    Computes the average IRASA periodic and aperiodic components across protocols.
    For stimulation epochs: difference = (avg Q4 - avg Q1)
    For post-stimulation epochs: difference = (avg Q1 - avg Q4)
    Plots the average curves and saves CSV data.
    """
    sf = raw.info['sfreq']
    chan_list = raw.info['ch_names']
    if target_chan is None:
        for ch in TARGET_CHANNELS:
            if ch in chan_list:
                target_chan = ch
                break
        if target_chan is None:
            target_chan = chan_list[0]
    fmin, fmax, win_sec = FMIN, FMAX, WIN_SEC
    avg_dir = os.path.join(output_dir, "irasa_analysis")
    os.makedirs(avg_dir, exist_ok=True)
    
    psd_q1_periodic_list = []
    psd_q1_aperiodic_list = []
    psd_q4_periodic_list = []
    psd_q4_aperiodic_list = []
    freqs = None
    
    for ep in q1_epochs:
        try:
            f_tmp, aperiodic, periodic = compute_irasa_for_segment_quarter(raw, ep, target_chan, chan_list, fmin, fmax, win_sec)
            psd_q1_periodic_list.append(periodic)
            psd_q1_aperiodic_list.append(aperiodic)
            if freqs is None:
                freqs = f_tmp
        except Exception as e:
            if logger:
                logger.warning(f"Error computing IRASA for Q1 epoch: {e}")
    
    for ep in q4_epochs:
        try:
            f_tmp, aperiodic, periodic = compute_irasa_for_segment_quarter(raw, ep, target_chan, chan_list, fmin, fmax, win_sec)
            psd_q4_periodic_list.append(periodic)
            psd_q4_aperiodic_list.append(aperiodic)
            if freqs is None:
                freqs = f_tmp
        except Exception as e:
            if logger:
                logger.warning(f"Error computing IRASA for Q4 epoch: {e}")
    
    if not psd_q1_periodic_list or not psd_q4_periodic_list:
        if logger:
            logger.warning("No valid IRASA computations for average plot. Skipping.")
        return
    
    avg_q1_periodic = np.mean(psd_q1_periodic_list, axis=0)
    avg_q1_aperiodic = np.mean(psd_q1_aperiodic_list, axis=0)
    avg_q4_periodic = np.mean(psd_q4_periodic_list, axis=0)
    avg_q4_aperiodic = np.mean(psd_q4_aperiodic_list, axis=0)
    
    if epoch_type.lower() == "stim":
        diff_periodic = avg_q4_periodic - avg_q1_periodic
        diff_aperiodic = avg_q4_aperiodic - avg_q1_aperiodic
    else:  # poststim
        diff_periodic = avg_q1_periodic - avg_q4_periodic
        diff_aperiodic = avg_q1_aperiodic - avg_q4_aperiodic
    
    # Plot average periodic components
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(freqs, avg_q1_periodic, label="Avg Q1 Periodic", color="orange")
    ax.plot(freqs, avg_q4_periodic, label="Avg Q4 Periodic", color="red")
    diff_label = "Q4-Q1" if epoch_type.lower() == "stim" else "Q1-Q4"
    ax.plot(freqs, diff_periodic, label=f"Diff ({diff_label})", color="blue")
    ax.axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Periodic Power")
    ax.set_title(f"Average IRASA Periodic Component ({diff_label})")
    ax.legend()
    fig.tight_layout()
    fname_periodic = f"average_irasa_periodic_{epoch_type}.png"
    fig.savefig(os.path.join(avg_dir, fname_periodic))
    plt.close(fig)
    
    # Plot average aperiodic components
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(freqs, avg_q1_aperiodic, label="Avg Q1 Aperiodic", color="orange")
    ax.plot(freqs, avg_q4_aperiodic, label="Avg Q4 Aperiodic", color="red")
    ax.plot(freqs, diff_aperiodic, label=f"Diff ({diff_label})", color="blue")
    ax.axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Aperiodic Power")
    ax.set_title(f"Average IRASA Aperiodic Component ({diff_label})")
    ax.legend()
    fig.tight_layout()
    fname_aperiodic = f"average_irasa_aperiodic_{epoch_type}.png"
    fig.savefig(os.path.join(avg_dir, fname_aperiodic))
    plt.close(fig)
    
    # Save CSV data (example: saving frequency bins and differences)
    df_periodic = pd.DataFrame({
        "freq_bins": freqs,
        "diff_periodic": diff_periodic
    })
    df_periodic.to_csv(os.path.join(avg_dir, f"average_irasa_periodic_{epoch_type}.csv"), index=False)
    
    df_aperiodic = pd.DataFrame({
        "freq_bins": freqs,
        "diff_aperiodic": diff_aperiodic
    })
    df_aperiodic.to_csv(os.path.join(avg_dir, f"average_irasa_aperiodic_{epoch_type}.csv"), index=False)
    
    if logger:
        logger.info(f"Saved average IRASA plots and CSV data for {epoch_type} epochs.")

###############################################################################
# Topoplot for IRASA Components Across Frequency Bands
###############################################################################
def plot_irasa_topomaps(raw, q1_epochs, q4_epochs, output_dir, epoch_type="stim", logger=None, win_sec=WIN_SEC):
    """
    Computes channel-wise average IRASA (periodic and aperiodic) power for Q1 and Q4 epochs,
    then for each topomap band (only 0.95–1.05 Hz and 0.5–4 Hz), computes the average power per channel
    and plots topoplots of the differences.
    
    For stimulation epochs: difference = (Q4 - Q1)
    For post-stimulation epochs: difference = (Q1 - Q4)
    
    This function excludes channels in EXCLUDE_CHANNELS and uses mne.pick_info to process only the remaining channels.
    """
    # Define channels to exclude and the bands for topomap plots.
    EXCLUDE_CHANNELS = [
        "E67", "E73", "E82", "E91", "E92", "E93", "E102", "E103", "E104", "E111", "E112", "E113",
        "E120", "E121", "E122", "E133", "E134", "E135", "E145", "E146", "E147", "E156", "E157",
        "E165", "E166", "E167", "E174", "E175", "E176", "E187", "E188", "E189", "E190", "E199",
        "E200", "E201", "E208", "E209", "E216", "E217", "E218", "E219", "E225", "E226", "E227", "E228",
        "E229", "E230", "E231","E232", "E233", "E234", "E235", "E236", "E237", "E238", "E239", "E240",
        "E241", "E242", "E243", "E244", "E245","E246", "E247", "E248", "E249", "E250", "E251", "E252",
        "E253", "E254", "E255", "E256"
    ]
    TOPOMAP_BANDS = [[0.95, 1.05], [0.5, 4]]
    
    # Pick only channels not in EXCLUDE_CHANNELS.
    all_chan = raw.info["ch_names"]
    keep_idx = mne.pick_channels(all_chan, include=[ch for ch in all_chan if ch not in EXCLUDE_CHANNELS])
    if len(keep_idx) == 0:
        if logger:
            logger.warning("No channels remain after exclusion.")
        return
    filtered_info = mne.pick_info(raw.info, keep_idx)
    filtered_chan_list = filtered_info["ch_names"]
    
    # Loop over the two bands.
    for band in TOPOMAP_BANDS:
        new_fmin, new_fmax = band[0], band[1]
        band_label = f"{new_fmin}-{new_fmax}"
        q1_power = []
        q4_power = []
        # For each channel in the filtered list, compute the average periodic power over Q1 and Q4 epochs in this band.
        for ch_name in filtered_chan_list:
            pp_q1 = []
            pp_q4 = []
            for ep in q1_epochs:
                try:
                    # Compute IRASA for the given channel and epoch using the specified band.
                    _, _, periodic = compute_irasa_for_segment_quarter(raw, ep, ch_name, all_chan, new_fmin, new_fmax, win_sec)
                    pp_q1.append(periodic)
                except Exception:
                    continue
            for ep in q4_epochs:
                try:
                    _, _, periodic = compute_irasa_for_segment_quarter(raw, ep, ch_name, all_chan, new_fmin, new_fmax, win_sec)
                    pp_q4.append(periodic)
                except Exception:
                    continue
            if pp_q1:
                q1_power.append(np.mean(pp_q1))
            else:
                q1_power.append(np.nan)
            if pp_q4:
                q4_power.append(np.mean(pp_q4))
            else:
                q4_power.append(np.nan)
        q1_power = np.array(q1_power)
        q4_power = np.array(q4_power)
        # Compute difference based on epoch type.
        if epoch_type.lower() == "stim":
            diff_power = q4_power - q1_power
        else:
            diff_power = q1_power - q4_power
        
        # Create topoplots using the filtered info.
        topo_output_dir = os.path.join(output_dir, "irasa_analysis")
        os.makedirs(topo_output_dir, exist_ok=True)
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        im0, _ = mne.viz.plot_topomap(q1_power, filtered_info, axes=axes[0], show=False, contours=0)
        axes[0].set_title("Q1")
        im1, _ = mne.viz.plot_topomap(q4_power, filtered_info, axes=axes[1], show=False, contours=0)
        axes[1].set_title("Q4")
        im2, _ = mne.viz.plot_topomap(diff_power, filtered_info, axes=axes[2], show=False, contours=0)
        axes[2].set_title("Difference")
        fig.suptitle(f"IRASA Topomap for Band {band_label} ({epoch_type})")
        fig.tight_layout()
        fname = f"topomap_irasa_periodic_{band_label}_{epoch_type}.png"
        fig.savefig(os.path.join(topo_output_dir, fname))
        plt.close(fig)
        if logger:
            logger.info(f"Saved IRASA topomap for band {band_label} ({epoch_type}).")
###############################################################################
# Main Function
###############################################################################
def main():
    parser = argparse.ArgumentParser(description="IRASA Analysis on Quarter Segments for Periodic/Aperiodic Comparison")
    parser.add_argument("raw_file", help="Path to raw data file (e.g. .fif)")
    parser.add_argument("output_dir", help="Directory to save outputs")
    args = parser.parse_args()
    
    # Set up logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    ch.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(ch)
    
    # Load raw data (assuming a .fif file)
    raw = mne.io.read_raw_fif(args.raw_file, preload=True)
    logger.info(f"Loaded raw data from {args.raw_file}")
    
    # Split stimulation epochs into pre-stim, Q1, Q4, and post-stim segments
    pre_stim_epochs, q1_stim_epochs, q4_stim_epochs, post_stim_epochs = split_stim_epochs(raw, logger=logger)
    
    # Run protocol-level IRASA analysis (both stim and post-stim)
    analyze_protocols_irasa(raw, q1_stim_epochs, q4_stim_epochs, post_stim_epochs,
                            args.output_dir, logger=logger)
    
    # Compute and plot average IRASA components across protocols (for stim epochs)
    plot_average_irasa_components(raw, q1_stim_epochs, q4_stim_epochs, args.output_dir,
                                  epoch_type="stim", logger=logger)
    
    # Generate topoplots for the IRASA components across predefined bands (for stim epochs)
    plot_irasa_topomaps(raw, q1_stim_epochs, q4_stim_epochs, args.output_dir,
                        epoch_type="stim", logger=logger)
    
if __name__ == "__main__":
    main()

