
# power_analysis.py

import os
import numpy as np
import pandas as pd
import mne
import matplotlib
import matplotlib.pyplot as plt
import antropy as ant

from mne.time_frequency import psd_array_welch

matplotlib.use('Agg')

###############################################################################
# Define constants
###############################################################################
FIXED_NFFT = 4096
FMIN, FMAX = 0.5, 2
# Define a list of entrainment bands of interest.
ENTRAINMENT_BANDS = [
    [0.99, 1.01],
    [0.95, 1.05],
    [0.9, 1.1],
    [0.85, 1.15],
    [0.8, 1.2],
    [0.5, 2],
    [0.5, 4]
]
TARGET_CHANNELS = ['E37', 'E33', 'E32', 'E31', 'E25', 'E18', 'E28', 'E11']

###############################################################################
# Helper: Split an epoch into Q1 and Q4
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

###############################################################################
# 1) SPLIT STIMULATION EPOCHS
###############################################################################
def split_stim_epochs(raw, min_stim_duration_sec=100, logger=None):
    """
    Extract pre-stim, Q1 stim, Q4 stim, and post-stim epochs from raw.
    """
    sf = raw.info['sfreq']
    column_dict = {'stim end': 1, 'stim start': 2}
    stim_end_index = column_dict['stim end']
    stim_start_index = column_dict['stim start']
    events, event_id = mne.events_from_annotations(raw)
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
            # For stim, we want Q4 - Q1 (later used for difference)
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

###############################################################################
# 2) PROTOCOL-BY-PROTOCOL ANALYSIS (PSD & Permutation Entropy)
###############################################################################
def analyze_protocols(raw,
                      pre_stim_epochs,
                      q1_stim_epochs,
                      q4_stim_epochs,
                      post_stim_epochs,
                      output_dir,
                      subject_id=None,
                      condition=None,
                      logger=None):
    """
    For each protocol:
      - For STIM epochs, compute PSD using Welch and FFT (averaging across TARGET_CHANNELS)
        and calculate the difference as (Q4 - Q1).
      - For POST-STIM epochs, first split each post-stim epoch using get_quarters and compute
        PSD with the difference as (Q1 - Q4).
      - For each protocol, plot the PSD comparisons (both Welch and FFT) and save protocol-level
        statistics to CSV files.
      - Finally, create bar plots summarizing the average differences across STIM protocols.
    """
    sf = raw.info['sfreq']
    data = raw.get_data(units='uV')
    available_indices = [i for i, ch in enumerate(raw.info['ch_names']) if ch in TARGET_CHANNELS]
    if not available_indices:
        if logger:
            logger.warning("No target channels found. Using first channel as fallback.")
        available_indices = [0]

    pa_dir = os.path.join(output_dir, "power_analysis")
    os.makedirs(pa_dir, exist_ok=True)
    fmin, fmax = FMIN, FMAX
    # Use the first entrainment band for protocol-level stats.
    band = ENTRAINMENT_BANDS[0]

    # --- STIM Analysis (difference = Q4 - Q1) ---
    protocol_stats_stim = []
    for prot_idx, (q1_ep, q4_ep) in enumerate(zip(q1_stim_epochs, q4_stim_epochs)):
        prot_num = prot_idx + 1
        q1_start, q1_end, _ = q1_ep
        q4_start, q4_end, _ = q4_ep
        q1_data = np.mean(data[available_indices, q1_start:q1_end], axis=0)
        q4_data = np.mean(data[available_indices, q4_start:q4_end], axis=0)
        try:
            psd_q1, freqs = psd_array_welch(q1_data[np.newaxis, :], sfreq=sf,
                                            fmin=fmin, fmax=fmax, n_fft=FIXED_NFFT, verbose=False)
            psd_q4, _ = psd_array_welch(q4_data[np.newaxis, :], sfreq=sf,
                                        fmin=fmin, fmax=fmax, n_fft=FIXED_NFFT, verbose=False)
        except Exception as e:
            if logger:
                logger.warning(f"Stim Protocol {prot_num}: Error computing Welch PSD: {e}. Skipping protocol.")
            continue
        psd_q1 = psd_q1[0]
        psd_q4 = psd_q4[0]
        band_idx = np.where((freqs >= band[0]) & (freqs <= band[1]))[0]
        power_q1 = np.mean(psd_q1[band_idx]) if len(band_idx) else np.nan
        power_q4 = np.mean(psd_q4[band_idx]) if len(band_idx) else np.nan
        diff_power = power_q4 - power_q1
        ent_q1 = ant.perm_entropy(q1_data, order=3, delay=1, normalize=True)
        ent_q4 = ant.perm_entropy(q4_data, order=3, delay=1, normalize=True)
        diff_ent = ent_q4 - ent_q1
        N_q1 = len(q1_data)
        N_q4 = len(q4_data)
        fft_q1 = np.fft.rfft(q1_data)
        fft_freqs = np.fft.rfftfreq(N_q1, d=1/sf)
        fft_psd_q1 = (np.abs(fft_q1)**2) / (sf * N_q1)
        if N_q1 > 1:
            fft_psd_q1[1:-1] *= 2
        fft_q4 = np.fft.rfft(q4_data)
        fft_psd_q4 = (np.abs(fft_q4)**2) / (sf * N_q4)
        if N_q4 > 1:
            fft_psd_q4[1:-1] *= 2
        band_idx_fft = np.where((fft_freqs >= band[0]) & (fft_freqs <= band[1]))[0]
        power_fft_q1 = np.mean(fft_psd_q1[band_idx_fft]) if len(band_idx_fft) else np.nan
        power_fft_q4 = np.mean(fft_psd_q4[band_idx_fft]) if len(band_idx_fft) else np.nan
        diff_power_fft = power_fft_q4 - power_fft_q1
        protocol_stats_stim.append({
            "protocol": prot_num,
            "power_q1": power_q1,
            "power_q4": power_q4,
            "diff_power": diff_power,
            "ent_q1": ent_q1,
            "ent_q4": ent_q4,
            "diff_ent": diff_ent,
            "freqs": freqs,
            "psd_q1": psd_q1,
            "psd_q4": psd_q4,
            "fft_freqs": fft_freqs,
            "fft_psd_q1": fft_psd_q1,
            "fft_psd_q4": fft_psd_q4,
            "diff_power_fft": diff_power_fft
        })
        # Plot PSD comparisons for this stim protocol.
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(freqs, psd_q1, label="Q1 PSD (Welch)", color="orange")
        ax.plot(freqs, psd_q4, label="Q4 PSD (Welch)", color="red")
        ax.axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
        ax.axvspan(band[0], band[1], color="gray", alpha=0.3, label=f"{band[0]}–{band[1]} Hz")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Power (uV²/Hz)")
        ax.set_title(f"Stim Protocol {prot_num}: Welch PSD (Q4-Q1)")
        ax.legend()
        ax.set_xlim(fmin, fmax)
        fig.tight_layout()
        fig.savefig(os.path.join(pa_dir, f"stim_protocol_{prot_num}_psd_comparison.png"))
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(fft_freqs, fft_psd_q1, label="Q1 FFT PSD", color="blue")
        ax.plot(fft_freqs, fft_psd_q4, label="Q4 FFT PSD", color="purple")
        ax.axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
        ax.axvspan(band[0], band[1], color="gray", alpha=0.3, label=f"{band[0]}–{band[1]} Hz")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Power (uV²/Hz)")
        ax.set_title(f"Stim Protocol {prot_num}: FFT PSD (Q4-Q1)")
        ax.legend()
        ax.set_xlim(fmin, fmax)
        fig.tight_layout()
        fig.savefig(os.path.join(pa_dir, f"stim_protocol_{prot_num}_fft_psd_comparison.png"))
        plt.close(fig)
        if logger:
            logger.info(f"Stim Protocol {prot_num}: Welch diff={diff_power:.4f}, FFT diff={diff_power_fft:.4f}, Entropy diff={diff_ent:.4f}")

    # Create bar plots summarizing average differences across STIM protocols.
    if protocol_stats_stim:
        prot_nums = np.arange(1, len(protocol_stats_stim)+1)
        welch_diffs = np.array([ps["diff_power"] for ps in protocol_stats_stim])
        fft_diffs = np.array([ps["diff_power_fft"] for ps in protocol_stats_stim])
        avg_welch = np.nanmean(welch_diffs)
        avg_fft = np.nanmean(fft_diffs)
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(prot_nums, welch_diffs, color="blue", alpha=0.7)
        ax.axhline(avg_welch, color="red", linestyle="--", label=f"Avg = {avg_welch:.4f}")
        ax.set_xlabel("Protocol #")
        ax.set_ylabel("Welch Power Diff (Q4-Q1)")
        ax.set_title("Average Welch PSD Difference Across STIM Protocols")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(pa_dir, "welch_band_power_diff_across_protocols.png"))
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(prot_nums, fft_diffs, color="purple", alpha=0.7)
        ax.axhline(avg_fft, color="red", linestyle="--", label=f"Avg = {avg_fft:.4f}")
        ax.set_xlabel("Protocol #")
        ax.set_ylabel("FFT Power Diff (Q4-Q1)")
        ax.set_title("Average FFT PSD Difference Across STIM Protocols")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(pa_dir, "fft_band_power_diff_across_protocols.png"))
        plt.close(fig)
        if logger:
            logger.info("Saved bar plots for average differences across STIM protocols.")

    # --- POST-STIM Analysis (difference = Q1 - Q4) ---
    q1_post_epochs = []
    q4_post_epochs = []
    for post_ep in post_stim_epochs:
        q1, q4 = get_quarters(post_ep)
        q1_post_epochs.append(q1)
        q4_post_epochs.append(q4)
    protocol_stats_post = []
    for prot_idx, (q1_ep, q4_ep) in enumerate(zip(q1_post_epochs, q4_post_epochs)):
        prot_num = prot_idx + 1
        q1_start, q1_end, _ = q1_ep
        q4_start, q4_end, _ = q4_ep
        q1_data = np.mean(data[available_indices, q1_start:q1_end], axis=0)
        q4_data = np.mean(data[available_indices, q4_start:q4_end], axis=0)
        try:
            psd_q1, freqs = psd_array_welch(q1_data[np.newaxis, :], sfreq=sf,
                                            fmin=fmin, fmax=fmax, n_fft=FIXED_NFFT, verbose=False)
            psd_q4, _ = psd_array_welch(q4_data[np.newaxis, :], sfreq=sf,
                                        fmin=fmin, fmax=fmax, n_fft=FIXED_NFFT, verbose=False)
        except Exception as e:
            if logger:
                logger.warning(f"Post-Stim Protocol {prot_num}: Error computing Welch PSD: {e}. Skipping protocol.")
            continue
        psd_q1 = psd_q1[0]
        psd_q4 = psd_q4[0]
        band_idx = np.where((freqs >= band[0]) & (freqs <= band[1]))[0]
        power_q1 = np.mean(psd_q1[band_idx]) if len(band_idx) else np.nan
        power_q4 = np.mean(psd_q4[band_idx]) if len(band_idx) else np.nan
        diff_power = power_q1 - power_q4   # For post-stim, difference = Q1 - Q4.
        ent_q1 = ant.perm_entropy(q1_data, order=3, delay=1, normalize=True)
        ent_q4 = ant.perm_entropy(q4_data, order=3, delay=1, normalize=True)
        diff_ent = ent_q1 - ent_q4
        N_q1 = len(q1_data)
        N_q4 = len(q4_data)
        fft_q1 = np.fft.rfft(q1_data)
        fft_freqs = np.fft.rfftfreq(N_q1, d=1/sf)
        fft_psd_q1 = (np.abs(fft_q1)**2) / (sf * N_q1)
        if N_q1 > 1:
            fft_psd_q1[1:-1] *= 2
        fft_q4 = np.fft.rfft(q4_data)
        fft_psd_q4 = (np.abs(fft_q4)**2) / (sf * N_q4)
        if N_q4 > 1:
            fft_psd_q4[1:-1] *= 2
        band_idx_fft = np.where((fft_freqs >= band[0]) & (fft_freqs <= band[1]))[0]
        power_fft_q1 = np.mean(fft_psd_q1[band_idx_fft]) if len(band_idx_fft) else np.nan
        power_fft_q4 = np.mean(fft_psd_q4[band_idx_fft]) if len(band_idx_fft) else np.nan
        diff_power_fft = power_fft_q1 - power_fft_q4
        protocol_stats_post.append({
            "protocol": prot_num,
            "power_q1": power_q1,
            "power_q4": power_q4,
            "diff_power": diff_power,
            "ent_q1": ent_q1,
            "ent_q4": ent_q4,
            "diff_ent": diff_ent,
            "freqs": freqs,
            "psd_q1": psd_q1,
            "psd_q4": psd_q4,
            "fft_freqs": fft_freqs,
            "fft_psd_q1": fft_psd_q1,
            "fft_psd_q4": fft_psd_q4,
            "diff_power_fft": diff_power_fft
        })
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(freqs, psd_q1, label="Q1 PSD (Welch)", color="orange")
        ax.plot(freqs, psd_q4, label="Q4 PSD (Welch)", color="red")
        ax.axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
        ax.axvspan(band[0], band[1], color="gray", alpha=0.3, label=f"{band[0]}–{band[1]} Hz")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Power (uV²/Hz)")
        ax.set_title(f"Post-Stim Protocol {prot_num}: Welch PSD (Q1-Q4)")
        ax.legend()
        ax.set_xlim(fmin, fmax)
        fig.tight_layout()
        fig.savefig(os.path.join(pa_dir, f"poststim_protocol_{prot_num}_psd_comparison.png"))
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(fft_freqs, fft_psd_q1, label="Q1 FFT PSD", color="blue")
        ax.plot(fft_freqs, fft_psd_q4, label="Q4 FFT PSD", color="purple")
        ax.axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
        ax.axvspan(band[0], band[1], color="gray", alpha=0.3, label=f"{band[0]}–{band[1]} Hz")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Power (uV²/Hz)")
        ax.set_title(f"Post-Stim Protocol {prot_num}: FFT PSD (Q1-Q4)")
        ax.legend()
        ax.set_xlim(fmin, fmax)
        fig.tight_layout()
        fig.savefig(os.path.join(pa_dir, f"poststim_protocol_{prot_num}_fft_psd_comparison.png"))
        plt.close(fig)
        if logger:
            logger.info(f"Post-Stim Protocol {prot_num}: Welch diff={diff_power:.4f}, FFT diff={diff_power_fft:.4f}, Entropy diff={diff_ent:.4f}")

    # Save protocol-level statistics.
    pd.DataFrame(protocol_stats_stim).to_csv(os.path.join(pa_dir, "protocol_stats_stim.csv"), index=False)
    pd.DataFrame(protocol_stats_post).to_csv(os.path.join(pa_dir, "protocol_stats_poststim.csv"), index=False)
    if logger:
        logger.info("Saved protocol-by-protocol statistics for STIM and POST-STIM protocols.")

###############################################################################
# 3) AVERAGE PSD ACROSS PROTOCOLS
###############################################################################
def plot_average_psd(raw,
                     q1_epochs,
                     q4_epochs,
                     output_dir,
                     subject_id=None,
                     condition=None,
                     epoch_type="stim",  # "stim" or "poststim"
                     logger=None):
    """
    Computes the average PSD across protocols using Welch.
    For stim: difference = (avg PSD of Q4) - (avg PSD of Q1).
    For poststim: difference = (avg PSD of Q1) - (avg PSD of Q4).
    """
    sf = raw.info['sfreq']
    data = raw.get_data(units='uV')
    available_indices = [i for i, ch in enumerate(raw.info['ch_names']) if ch in TARGET_CHANNELS]
    if not available_indices:
        available_indices = [0]
    fmin, fmax = FMIN, FMAX
    # Use the first band from the list for the average PSD analysis.
    band = ENTRAINMENT_BANDS[0]
    pa_dir = os.path.join(output_dir, "power_analysis")
    os.makedirs(pa_dir, exist_ok=True)
    all_q1 = [np.mean(data[available_indices, q1_ep[0]:q1_ep[1]], axis=0) for q1_ep in q1_epochs]
    all_q4 = [np.mean(data[available_indices, q4_ep[0]:q4_ep[1]], axis=0) for q4_ep in q4_epochs]
    if not all_q1 or not all_q4:
        if logger:
            logger.warning("No valid Q1/Q4 epochs found. Skipping average PSD plot.")
        return
    common_len = min(min(len(x) for x in all_q1), min(len(x) for x in all_q4))
    cropped_q1 = [x[:common_len] for x in all_q1]
    cropped_q4 = [x[:common_len] for x in all_q4]
    psds_q1 = []
    psds_q4 = []
    valid_freqs = None
    for cq1 in cropped_q1:
        try:
            n_per_seg = len(cq1) if len(cq1) < FIXED_NFFT else None
            psd, freqs = psd_array_welch(cq1[np.newaxis, :], sfreq=sf, fmin=fmin, fmax=fmax,
                                         n_fft=FIXED_NFFT, n_per_seg=n_per_seg, verbose=False)
            psds_q1.append(psd[0])
            valid_freqs = freqs
        except Exception as e:
            if logger:
                logger.warning(f"Error computing Welch PSD for a Q1 epoch: {e}.")
    for cq4 in cropped_q4:
        try:
            n_per_seg = len(cq4) if len(cq4) < FIXED_NFFT else None
            psd, _ = psd_array_welch(cq4[np.newaxis, :], sfreq=sf, fmin=fmin, fmax=fmax,
                                     n_fft=FIXED_NFFT, n_per_seg=n_per_seg, verbose=False)
            psds_q4.append(psd[0])
        except Exception as e:
            if logger:
                logger.warning(f"Error computing Welch PSD for a Q4 epoch: {e}.")
    if not psds_q1 or not psds_q4:
        if logger:
            logger.warning("No valid Welch PSDs computed. Skipping average PSD plot.")
        return
    avg_psd_q1 = np.mean(psds_q1, axis=0)
    avg_psd_q4 = np.mean(psds_q4, axis=0)
    diff_psd = (avg_psd_q4 - avg_psd_q1) if epoch_type.lower() == "stim" else (avg_psd_q1 - avg_psd_q4)
    if logger and valid_freqs is not None and len(valid_freqs) > 1:
        freq_res = valid_freqs[1] - valid_freqs[0]
        logger.info(f"Average Welch PSD freq resolution = {freq_res:.6f} Hz (n_fft={FIXED_NFFT})")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(valid_freqs, avg_psd_q1, label="Avg Q1 PSD (Welch)", color="orange")
    ax.plot(valid_freqs, avg_psd_q4, label="Avg Q4 PSD (Welch)", color="red")
    diff_label = "Q4-Q1" if epoch_type.lower() == "stim" else "Q1-Q4"
    ax.plot(valid_freqs, diff_psd, label=f"Diff ({diff_label}, Welch)", color="blue")
    ax.axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
    ax.axvspan(band[0], band[1], color="gray", alpha=0.3, label=f"{band[0]}–{band[1]} Hz")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power (uV²/Hz)")
    ax.set_title(f"Average Welch PSD Across Protocols ({diff_label}, n_fft={FIXED_NFFT})")
    ax.legend()
    ax.set_xlim(fmin, fmax)
    fig.tight_layout()
    fname = f"average_psd_q1_vs_q4_{epoch_type}.png"
    fig.savefig(os.path.join(pa_dir, fname))
    plt.close(fig)
    if logger:
        logger.info(f"Saved average Welch PSD plot for {epoch_type} epochs as {fname}.")
    df_psd = pd.DataFrame([{
        "Subject": subject_id,
        "Condition": condition,
        "freq_bins": list(valid_freqs),
        "psd_diff": list(diff_psd)
    }])
    csv_path = os.path.join(pa_dir, f"psd_data_{epoch_type}.csv")
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path)
        df_psd = pd.concat([df_existing, df_psd], ignore_index=True)
    df_psd.to_csv(csv_path, index=False)
    if logger:
        logger.info(f"Saved average Welch PSD CSV data to {csv_path}.")

###############################################################################
# 4) TOPOMAP PLOTTING
###############################################################################
def plot_topomaps(raw,
                  q1_epochs,
                  q4_epochs,
                  output_dir,
                  epoch_type="stim",  # "stim" or "poststim"
                  method="welch",     # "welch" or "fft"
                  logger=None):
    """
    Computes channel-wise narrow-band power topomaps for each entrainment band.
    For stim: difference = Q4 - Q1; for poststim: difference = Q1 - Q4.
    'method' chooses Welch or FFT.
    A separate figure and CSV file is generated for each band.
    """
    sf = raw.info['sfreq']
    data = raw.get_data(units='uV')
    n_channels = data.shape[0]
    channel_names = raw.info["ch_names"]
    fmin, fmax = FMIN, FMAX
    pa_dir = os.path.join(output_dir, "power_analysis")
    os.makedirs(pa_dir, exist_ok=True)

    # Loop over each entrainment band in the list.
    for band in ENTRAINMENT_BANDS:
        band_label = f"{band[0]}-{band[1]}"
        q1_topo = np.zeros(n_channels)
        q4_topo = np.zeros(n_channels)
        for ch_idx in range(n_channels):
            vals_q1 = []
            vals_q4 = []
            for q1_ep, q4_ep in zip(q1_epochs, q4_epochs):
                q1_start, q1_end, _ = q1_ep
                q4_start, q4_end, _ = q4_ep
                q1_data = data[ch_idx, q1_start:q1_end]
                q4_data = data[ch_idx, q4_start:q4_end]
                try:
                    if method.lower() == "welch":
                        psd_q1, freqs = psd_array_welch(q1_data[np.newaxis, :],
                                                        sfreq=sf, fmin=fmin, fmax=fmax,
                                                        n_fft=len(q1_data), verbose=False)
                        psd_q4, _ = psd_array_welch(q4_data[np.newaxis, :],
                                                    sfreq=sf, fmin=fmin, fmax=fmax,
                                                    n_fft=len(q4_data), verbose=False)
                        psd_q1 = psd_q1[0]
                        psd_q4 = psd_q4[0]
                    else:
                        N1 = len(q1_data)
                        fft_vals1 = np.fft.rfft(q1_data)
                        freqs = np.fft.rfftfreq(N1, d=1/sf)
                        psd_q1 = (np.abs(fft_vals1)**2) / (sf * N1)
                        if N1 > 1:
                            psd_q1[1:-1] *= 2
                        N4 = len(q4_data)
                        fft_vals4 = np.fft.rfft(q4_data)
                        psd_q4 = (np.abs(fft_vals4)**2) / (sf * N4)
                        if N4 > 1:
                            psd_q4[1:-1] *= 2
                except Exception as e:
                    if logger:
                        logger.warning(f"Channel {channel_names[ch_idx]}: Error computing PSD: {e}")
                    continue
                band_idx = np.where((freqs >= band[0]) & (freqs <= band[1]))[0]
                if len(band_idx) == 0:
                    continue
                vals_q1.append(np.mean(psd_q1[band_idx]))
                vals_q4.append(np.mean(psd_q4[band_idx]))
            q1_topo[ch_idx] = np.mean(vals_q1) if vals_q1 else np.nan
            q4_topo[ch_idx] = np.mean(vals_q4) if vals_q4 else np.nan
        diff_topo = (q4_topo - q1_topo) if epoch_type.lower() == "stim" else (q1_topo - q4_topo)
        common_vmin = np.nanmin([np.nanmin(q1_topo), np.nanmin(q4_topo)])
        common_vmax = np.nanmax([np.nanmax(q1_topo), np.nanmax(q4_topo)])
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        im0, _ = mne.viz.plot_topomap(q1_topo, raw.info, axes=axes[0], show=False, contours=0,
                                      vlim=(common_vmin, common_vmax), names=channel_names)
        axes[0].set_title("Q1")
        cbar0 = plt.colorbar(im0, ax=axes[0], orientation='vertical', fraction=0.046, pad=0.04)
        cbar0.set_label('Power (uV²/Hz)')
        im1, _ = mne.viz.plot_topomap(q4_topo, raw.info, axes=axes[1], show=False, contours=0,
                                      vlim=(common_vmin, common_vmax), names=channel_names)
        axes[1].set_title("Q4")
        cbar1 = plt.colorbar(im1, ax=axes[1], orientation='vertical', fraction=0.046, pad=0.04)
        cbar1.set_label('Power (uV²/Hz)')
        im2, _ = mne.viz.plot_topomap(diff_topo, raw.info, axes=axes[2], show=False, contours=0)
        diff_label = "Q4-Q1" if epoch_type.lower()=="stim" else "Q1-Q4"
        axes[2].set_title(f"Difference ({diff_label})")
        cbar2 = plt.colorbar(im2, ax=axes[2], orientation='vertical', fraction=0.046, pad=0.04)
        cbar2.set_label('Power Diff (uV²/Hz)')
        fig.suptitle(f"{method.upper()} Topomaps ({epoch_type.capitalize()}) for Band {band_label} Hz")
        fig.tight_layout()
        fname = f"topomaps_q1_q4_difference_{epoch_type}_{band_label}_{method}.png"
        fig.savefig(os.path.join(pa_dir, fname))
        plt.close(fig)
        if logger:
            logger.info(f"Saved topomap figures ({method.upper()}) for {epoch_type} epochs for band {band_label} as {fname}.")
        df_topo = pd.DataFrame({
            "Channel": channel_names,
            "Q1 Power": q1_topo,
            "Q4 Power": q4_topo,
            "Difference": diff_topo
        })
        csv_path = os.path.join(pa_dir, f"topomap_data_{epoch_type}_{band_label}_{method}.csv")
        df_topo.to_csv(csv_path, index=False)
        if logger:
            logger.info(f"Saved topomap CSV data for band {band_label} to {csv_path}.")

