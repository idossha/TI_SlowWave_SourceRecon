
#!/usr/bin/env python
"""
wavelet_power_analysis.py

This module computes time-domain power using wavelets for each protocol.
For each protocol, it:
  - Extracts the segment from pre-stim to post-stim,
  - Computes a time-frequency representation (0.5–4 Hz) with a color map,
  - Overlays vertical lines for stim start and stim end,
  - Computes moving-average (1-s window) trends for broadband (0.5–4 Hz) and narrowband (0.95–1.05 Hz) power,
  - Fits linear trend lines separately for pre-stim, stim, and post-stim phases,
  - Exports a CSV file with the time series data,
  - Returns a dictionary with the computed trend slopes.

A separate function then averages the slopes across protocols, plots them, and exports a CSV summary.

All outputs are saved under output_dir/time_domain_power/.
"""

import os
import numpy as np
import mne
import matplotlib.pyplot as plt
import argparse
import logging
import pandas as pd
from scipy.ndimage import uniform_filter1d

###############################################################################
# Global parameters
###############################################################################
FMIN = 0.5
FMAX = 4.0
WIN_SEC = 4  # window length (seconds) for the wavelet transform
TARGET_CHANNELS = ['E37', 'E33', 'E32', 'E31', 'E25', 'E18', 'E28', 'E11']

###############################################################################
# Helper: Split stimulation epochs (as before)
###############################################################################
def split_stim_epochs(raw, min_stim_duration_sec=100, logger=None):
    """
    Extract pre-stim, Q1 stim, Q4 stim, and post-stim epochs from raw.
    Each epoch is a tuple: (start_sample, end_sample, protocol_number)
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
            pre_stim_epoch = (stim_start - stim_duration, stim_start, protocol_number)
            q1_stim_epoch = (stim_start, stim_start + stim_duration//4, protocol_number)
            q4_stim_epoch = (stim_end - stim_duration//4, stim_end, protocol_number)
            post_stim_epoch = (stim_end, stim_end + stim_duration, protocol_number)
            if pre_stim_epoch[0] < previous_end:
                continue
            previous_end = post_stim_epoch[1]
            pre_stim_epochs.append(pre_stim_epoch)
            q1_stim_epochs.append(q1_stim_epoch)
            q4_stim_epochs.append(q4_stim_epoch)
            post_stim_epochs.append(post_stim_epoch)
            protocol_number += 1
    if logger:
        logger.info(f"Found {len(pre_stim_epochs)} valid stimulation blocks.")
    return pre_stim_epochs, q1_stim_epochs, q4_stim_epochs, post_stim_epochs

###############################################################################
# Helper: Extract protocol segment and stim markers
###############################################################################
def extract_protocol_segment(raw, pre_epoch, post_epoch):
    """
    For a given protocol, extract data from the beginning of pre-stim to the end of post-stim.
    Returns the data, time vector (in s), and stim markers (relative to segment start).
    pre_epoch: (start_pre, end_pre, protocol)
    post_epoch: (start_post, end_post, protocol)
    Stim start is pre_epoch[1], stim end is post_epoch[0].
    """
    sf = raw.info['sfreq']
    protocol_start = pre_epoch[0]
    protocol_end = post_epoch[1]
    stim_start = pre_epoch[1]
    stim_end = post_epoch[0]
    
    data = raw.copy().crop(tmin=protocol_start/sf, tmax=protocol_end/sf).get_data()
    times = np.arange(data.shape[1]) / sf
    stim_start_rel = (stim_start - protocol_start) / sf
    stim_end_rel = (stim_end - protocol_start) / sf
    return data, times, stim_start_rel, stim_end_rel

###############################################################################
# Helper: Moving average
###############################################################################
def moving_average(x, window_size):
    return uniform_filter1d(x, size=window_size)

###############################################################################
# Protocol-level Wavelet Power Plotting & CSV Export, with Trend Slopes
###############################################################################
def plot_protocol_wavelet_power(raw, pre_epoch, post_epoch, q1_epoch, q4_epoch, output_dir, protocol_num, logger=None):
    """
    For a given protocol, extract the segment from pre-stim to post-stim,
    compute the wavelet transform in the 0.5–4 Hz range (using Morlet wavelets),
    and produce a two-panel figure:
    
      Top panel:
        - Time-frequency representation (x: time, y: frequency; color shows power)
          with an improved color scale.
        - Vertical lines for stim start and stim end.
        
      Bottom panel:
        - Moving-average trend lines (1-s window) for broadband (0.5–4 Hz)
          and narrowband (0.95–1.05 Hz) power.
        - Fitted linear trend lines (via np.polyfit) for each stage:
            pre-stim, stim, post-stim.
    
    In addition, exports a CSV file with the time series data (time, broadband MA, narrowband MA)
    and returns that data along with a dictionary of the computed trend slopes.
    """
    sfreq = raw.info['sfreq']
    # Extract segment and markers.
    data, times, stim_start_rel, stim_end_rel = extract_protocol_segment(raw, pre_epoch, post_epoch)
    data_avg = np.mean(data, axis=0)
    
    # Compute time-frequency representation.
    freqs = np.linspace(FMIN, FMAX, 30)
    n_cycles = 3
    data_for_tfr = data_avg[np.newaxis, np.newaxis, :]
    import mne.time_frequency as tfr
    power = tfr.tfr_array_morlet(data_for_tfr, sfreq=sfreq, freqs=freqs, n_cycles=n_cycles,
                                 decim=1, output='power')[0, 0]
    
    # Set color scale limits.
    vmin = np.percentile(power, 5)
    vmax = np.percentile(power, 95)
    
    # Compute broadband and narrowband power.
    broadband_power = np.mean(power, axis=0)
    narrow_mask = (freqs >= 0.95) & (freqs <= 1.05)
    if np.sum(narrow_mask) > 0:
        narrow_power = np.mean(power[narrow_mask, :], axis=0)
    else:
        narrow_power = broadband_power.copy()
    
    window_size = int(sfreq)
    broadband_ma = moving_average(broadband_power, window_size)
    narrow_ma = moving_average(narrow_power, window_size)
    
    # Compute trend slopes for each stage.
    # Define stages based on times relative to stim markers.
    mask_pre = times <= stim_start_rel
    mask_stim = (times >= stim_start_rel) & (times <= stim_end_rel)
    mask_post = times >= stim_end_rel
    
    def compute_slope(x, y):
        if np.sum(x) > 1:
            return np.polyfit(x, y, 1)[0]
        else:
            return np.nan
    
    slopes = {
        "protocol": protocol_num,
        "broadband": {
            "pre": compute_slope(times[mask_pre], broadband_ma[mask_pre]),
            "stim": compute_slope(times[mask_stim], broadband_ma[mask_stim]),
            "post": compute_slope(times[mask_post], broadband_ma[mask_post]),
        },
        "narrowband": {
            "pre": compute_slope(times[mask_pre], narrow_ma[mask_pre]),
            "stim": compute_slope(times[mask_stim], narrow_ma[mask_stim]),
            "post": compute_slope(times[mask_post], narrow_ma[mask_post]),
        }
    }
    
    # Create two-panel figure.
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    im = ax1.pcolormesh(times, freqs, power, shading='auto', cmap='inferno', vmin=vmin, vmax=vmax)
    ax1.set_ylabel("Frequency (Hz)")
    ax1.set_title(f"Protocol {protocol_num}: Time-Frequency Power")
    ax1.axvline(x=stim_start_rel, color="green", linestyle="--", label="Stim Start")
    ax1.axvline(x=stim_end_rel, color="purple", linestyle="--", label="Stim End")
    fig.colorbar(im, ax=ax1, label="Power (a.u.)")
    ax1.legend()
    
    ax2.plot(times, broadband_ma, label="Broadband MA (0.5–4 Hz)", color="blue")
    ax2.plot(times, narrow_ma, label="Narrowband MA (0.95–1.05 Hz)", color="red")
    ax2.axvline(x=stim_start_rel, color="green", linestyle="--")
    ax2.axvline(x=stim_end_rel, color="purple", linestyle="--")
    # Fit and plot linear trend lines for each stage.
    for label, data_series, trend_color in zip(["Broadband", "Narrowband"],
                                                 [broadband_ma, narrow_ma],
                                                 ["cyan", "magenta"]):
        # Pre-stim
        if np.sum(mask_pre) > 1:
            coef = np.polyfit(times[mask_pre], data_series[mask_pre], 1)
            fit_line = np.polyval(coef, times[mask_pre])
            ax2.plot(times[mask_pre], fit_line, color=trend_color, linestyle="--",
                     label=f"Pre-stim trend ({label})")
        # Stim
        if np.sum(mask_stim) > 1:
            coef = np.polyfit(times[mask_stim], data_series[mask_stim], 1)
            fit_line = np.polyval(coef, times[mask_stim])
            ax2.plot(times[mask_stim], fit_line, color=trend_color, linestyle=":",
                     label=f"Stim trend ({label})")
        # Post-stim
        if np.sum(mask_post) > 1:
            coef = np.polyfit(times[mask_post], data_series[mask_post], 1)
            fit_line = np.polyval(coef, times[mask_post])
            ax2.plot(times[mask_post], fit_line, color=trend_color, linestyle="-.",
                     label=f"Post-stim trend ({label})")
    
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Average Power (a.u.)")
    ax2.set_title("Moving-Average Power and Trend Fits")
    ax2.legend(ncol=2, fontsize='small')
    
    fig.tight_layout()
    fig_path = os.path.join(output_dir, f"protocol_{protocol_num}_wavelet_power.png")
    fig.savefig(fig_path)
    plt.close(fig)
    
    if logger:
        logger.info(f"Saved wavelet power plot for protocol {protocol_num} at {fig_path}")
    
    # Export CSV with time series data.
    df = pd.DataFrame({
        "time": times,
        "broadband_ma": broadband_ma,
        "narrowband_ma": narrow_ma
    })
    csv_path = os.path.join(output_dir, f"protocol_{protocol_num}_wavelet_data.csv")
    df.to_csv(csv_path, index=False)
    if logger:
        logger.info(f"Exported CSV data for protocol {protocol_num} at {csv_path}")
    
    return times, broadband_ma, narrow_ma, slopes

###############################################################################
# Function to Average Trend Slopes Across Protocols and Export/Plot
###############################################################################

def compute_average_trend_slopes(protocol_slopes, output_dir, logger=None):
    """
    Given a list of trend slopes dictionaries (one per protocol), compute the average slope
    for each stage (pre, stim, post) and for both broadband and narrowband.
    Create a bar plot and export the summary to CSV.
    """
    # Ensure output directory exists.
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare lists for each stage and band.
    broadband_pre = []
    broadband_stim = []
    broadband_post = []
    narrow_pre = []
    narrow_stim = []
    narrow_post = []
    
    for slopes in protocol_slopes:
        broadband_pre.append(slopes["broadband"]["pre"])
        broadband_stim.append(slopes["broadband"]["stim"])
        broadband_post.append(slopes["broadband"]["post"])
        narrow_pre.append(slopes["narrowband"]["pre"])
        narrow_stim.append(slopes["narrowband"]["stim"])
        narrow_post.append(slopes["narrowband"]["post"])
    
    # Compute averages.
    avg_slopes = {
        "Broadband": {
            "pre": np.nanmean(broadband_pre),
            "stim": np.nanmean(broadband_stim),
            "post": np.nanmean(broadband_post)
        },
        "Narrowband": {
            "pre": np.nanmean(narrow_pre),
            "stim": np.nanmean(narrow_stim),
            "post": np.nanmean(narrow_post)
        }
    }
    
    # Export CSV with individual slopes and averages.
    df_individual = pd.DataFrame(protocol_slopes)
    csv_indiv = os.path.join(output_dir, "individual_trend_slopes.csv")
    df_individual.to_csv(csv_indiv, index=False)
    
    df_avg = pd.DataFrame({
        "Stage": ["pre", "stim", "post"],
        "Broadband": [avg_slopes["Broadband"]["pre"], avg_slopes["Broadband"]["stim"], avg_slopes["Broadband"]["post"]],
        "Narrowband": [avg_slopes["Narrowband"]["pre"], avg_slopes["Narrowband"]["stim"], avg_slopes["Narrowband"]["post"]]
    })
    csv_avg = os.path.join(output_dir, "average_trend_slopes.csv")
    df_avg.to_csv(csv_avg, index=False)
    
    # Create a bar plot.
    stages = ["pre", "stim", "post"]
    x = np.arange(len(stages))
    width = 0.35
    fig, ax = plt.subplots(figsize=(8,6))
    ax.bar(x - width/2, [avg_slopes["Broadband"][s] for s in stages], width, label="Broadband")
    ax.bar(x + width/2, [avg_slopes["Narrowband"][s] for s in stages], width, label="Narrowband")
    ax.set_xticks(x)
    ax.set_xticklabels(stages)
    ax.set_ylabel("Average Trend Slope")
    ax.set_title("Average Trend Slopes Across Protocols")
    ax.legend()
    fig.tight_layout()
    bar_plot_path = os.path.join(output_dir, "average_trend_slopes.png")
    fig.savefig(bar_plot_path)
    plt.close(fig)
    
    if logger:
        logger.info(f"Exported individual slopes to {csv_indiv}, average slopes to {csv_avg}, and saved bar plot at {bar_plot_path}")
    
    return avg_slopes
###############################################################################
# Main Function
###############################################################################
def main():
    parser = argparse.ArgumentParser(description="Wavelet-based Time-Domain Power Analysis")
    parser.add_argument("raw_file", help="Path to raw data file (e.g. .fif)")
    parser.add_argument("output_dir", help="Directory to save outputs")
    args = parser.parse_args()
    
    # Create a dedicated subdirectory for time-domain power outputs.
    time_power_dir = os.path.join(args.output_dir, "time_domain_power")
    os.makedirs(time_power_dir, exist_ok=True)
    
    logger = logging.getLogger("wavelet_power_analysis")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    ch.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(ch)
    
    raw = mne.io.read_raw_fif(args.raw_file, preload=True)
    logger.info(f"Loaded raw data from {args.raw_file}")
    
    # Split epochs into protocols.
    pre_stim_epochs, q1_stim_epochs, q4_stim_epochs, post_stim_epochs = split_stim_epochs(raw, logger=logger)
    
    # Process each protocol.
    all_times = []
    all_broadband = []
    all_narrow = []
    protocol_slopes = []
    
    for pre_ep, q1_ep, q4_ep, post_ep in zip(pre_stim_epochs, q1_stim_epochs, q4_stim_epochs, post_stim_epochs):
        times, broadband_ma, narrow_ma, slopes = plot_protocol_wavelet_power(
            raw, pre_ep, post_ep, q1_ep, q4_ep, time_power_dir, pre_ep[2], logger=logger)
        all_times.append(times)
        all_broadband.append(broadband_ma)
        all_narrow.append(narrow_ma)
        protocol_slopes.append(slopes)
    
    # Optionally, you can average the moving-average time series across protocols.
    # (Truncate to common length if necessary.)
    # Here we just call a function if needed.
    # For now, we focus on trend slopes.
    
    avg_slopes = compute_average_trend_slopes(protocol_slopes, time_power_dir, logger=logger)
    
if __name__ == "__main__":
    main()

