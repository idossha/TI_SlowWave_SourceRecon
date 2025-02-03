# power_analysis.py

import os
import numpy as np
import pandas as pd
import mne
import matplotlib
import matplotlib.pyplot as plt
import antropy as ant  # pip install antropy if not installed

from mne.time_frequency import psd_array_welch

matplotlib.use('Agg')  # Non-interactive backend for automated scripts

###############################################################################
# Define constants for analysis
###############################################################################
FIXED_NFFT = 4096          # Example: pick 4096 for high freq resolution
FMIN, FMAX = 0.5, 2        # Narrow band of interest (we highlight 0.9–1.1 Hz)
ENTRAINMENT_BAND = [0.9, 1.1]  # Band used for computing average power, etc.
TARGET_CHANNELS = ['E37', 'E33', 'E32', 'E31', 'E25', 'E18', 'E28', 'E11']

###############################################################################
# 1) SPLIT STIMULATION EPOCHS into Q1 and Q4
###############################################################################
def split_stim_epochs(raw, min_stim_duration_sec=100, logger=None):
    """
    Extracts pre-stim, Q1 (first quarter of stim), Q4 (last quarter of stim), 
    and post-stim epochs from `raw` based on annotations "stim start" and "stim end". 
    Q1 and Q4 are defined as the first and last quarters of the stimulation epoch.
    """
    sf = raw.info['sfreq']

    # Dictionary mapping event descriptions to numerical codes
    column_dict = {'stim end': 1, 'stim start': 2}
    stim_end_index = column_dict['stim end']
    stim_start_index = column_dict['stim start']

    # Extract events and event IDs from annotations
    events, event_id = mne.events_from_annotations(raw)
    
    # Filter for stim start/end only
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
            stim_end   = filtered_data[i+1][0]
            stim_duration = stim_end - stim_start

            if stim_duration < min_stim_samples:
                if logger:
                    logger.info(f"Skipping stim block #{protocol_number}: duration < {min_stim_duration_sec}s.")
                continue
            
            quarter = stim_duration // 4
            # Q1: first quarter of the stimulation period
            q1_epoch = (stim_start, stim_start + quarter, protocol_number)
            # Q4: last quarter of the stimulation period
            q4_epoch = (stim_end - quarter, stim_end, protocol_number)

            pre_stim_epoch  = (stim_start - stim_duration, stim_start, protocol_number)
            post_stim_epoch  = (stim_end, stim_end + stim_duration, protocol_number)

            if pre_stim_epoch[0] < previous_end:
                # Overlap found, skip this block
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
# 2) PROTOCOL-BY-PROTOCOL ANALYSIS (PSD, PERM ENTROPY) + PLOTTING for Q1 vs Q4
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
    For each protocol block:
      - Compute Welch PSD in [FMIN, FMAX] Hz for Q1 vs Q4 
        (first vs last quarter of the stimulation epoch)
      - Compute average power in [0.9, 1.1] Hz and the difference (Q4 - Q1)
      - Compute permutation entropy for each quarter and the difference
      - Compute FFT-based PSD (full window) for Q1 vs Q4 and similarly compute
        the average power in [0.9,1.1] Hz and the difference.
      - Plot the PSD comparison for each protocol (both Welch and FFT).
      
    The calculations use the average signal from available channels in TARGET_CHANNELS.
    
    NOTE: For Welch's method with fixed n_fft, if the epoch is too short for the 
    chosen n_fft, the protocol is excluded (with a logged warning) but analysis continues.
    """
    sf = raw.info['sfreq']
    data = raw.get_data(units='uV')  # shape: (n_channels, n_times)

    # Determine indices for target channels
    available_indices = [i for i, ch in enumerate(raw.info['ch_names']) if ch in TARGET_CHANNELS]
    if not available_indices:
        if logger:
            logger.warning("None of the target channels found. Using first channel as fallback.")
        available_indices = [0]

    pa_dir = os.path.join(output_dir, 'power_analysis')
    os.makedirs(pa_dir, exist_ok=True)

    fmin, fmax = FMIN, FMAX
    entrainment_band = ENTRAINMENT_BAND

    band_power_diff = []
    entropy_diff = []
    protocol_stats = []
    # List for FFT-based band power differences
    fft_band_power_diff = []

    if logger:
        logger.info("Performing protocol-by-protocol power analysis (Q1 vs Q4) with fixed n_fft and full-window FFT...")

    for prot_idx, (q1_epoch, q4_epoch) in enumerate(zip(q1_stim_epochs, q4_stim_epochs)):
        q1_start, q1_end, prot_num = q1_epoch
        q4_start, q4_end, _ = q4_epoch

        # Average over the target channels
        q1_data = np.mean(data[available_indices, q1_start:q1_end], axis=0)
        q4_data = np.mean(data[available_indices, q4_start:q4_end], axis=0)

        # Compute Welch PSD with fixed n_fft, but handle errors if epoch is too short.
        try:
            psd_q1, freqs = psd_array_welch(
                q1_data[np.newaxis, :],
                sfreq=sf,
                fmin=fmin,
                fmax=fmax,
                n_fft=FIXED_NFFT,
                verbose=False
            )
            psd_q4, _ = psd_array_welch(
                q4_data[np.newaxis, :],
                sfreq=sf,
                fmin=fmin,
                fmax=fmax,
                n_fft=FIXED_NFFT,
                verbose=False
            )
        except Exception as e:
            if logger:
                logger.warning(f"Protocol {prot_idx+1}: Error computing Welch PSD with fixed n_fft={FIXED_NFFT}: {e}. Excluding this protocol.")
            continue

        psd_q1 = psd_q1[0]
        psd_q4 = psd_q4[0]

        if prot_idx == 0 and len(freqs) > 1 and logger:
            freq_res = freqs[1] - freqs[0]
            logger.info(f"Protocol 1 freq resolution = {freq_res:.6f} Hz (n_fft={FIXED_NFFT})")

        # Identify frequency indices within 0.9–1.1 Hz for Welch
        band_idx = np.where((freqs >= entrainment_band[0]) & (freqs <= entrainment_band[1]))[0]
        power_q1 = np.mean(psd_q1[band_idx]) if len(band_idx) else np.nan
        power_q4 = np.mean(psd_q4[band_idx]) if len(band_idx) else np.nan
        diff_power  = power_q4 - power_q1 if not np.isnan(power_q4) else np.nan
        band_power_diff.append(diff_power)

        # 2) Permutation Entropy
        ent_q1 = ant.perm_entropy(q1_data, order=3, delay=1, normalize=True)
        ent_q4 = ant.perm_entropy(q4_data,  order=3, delay=1, normalize=True)
        diff_ent  = ent_q4 - ent_q1
        entropy_diff.append(diff_ent)

        # 3) FFT-based PSD (full window) for Q1 and Q4
        N_q1 = len(q1_data)
        N_q4 = len(q4_data)
        fft_q1 = np.fft.rfft(q1_data)
        fft_freqs_q1 = np.fft.rfftfreq(N_q1, d=1/sf)
        fft_psd_q1 = (np.abs(fft_q1)**2) / (sf * N_q1)
        if N_q1 > 1:
            fft_psd_q1[1:-1] *= 2

        fft_q4 = np.fft.rfft(q4_data)
        fft_freqs_q4 = np.fft.rfftfreq(N_q4, d=1/sf)
        fft_psd_q4 = (np.abs(fft_q4)**2) / (sf * N_q4)
        if N_q4 > 1:
            fft_psd_q4[1:-1] *= 2

        # For FFT, we use the frequency vector from Q1 (assumed similar to Q4)
        band_idx_fft = np.where((fft_freqs_q1 >= entrainment_band[0]) & (fft_freqs_q1 <= entrainment_band[1]))[0]
        power_fft_q1 = np.mean(fft_psd_q1[band_idx_fft]) if len(band_idx_fft) else np.nan
        power_fft_q4 = np.mean(fft_psd_q4[band_idx_fft]) if len(band_idx_fft) else np.nan
        diff_power_fft = power_fft_q4 - power_fft_q1 if not np.isnan(power_fft_q4) else np.nan
        fft_band_power_diff.append(diff_power_fft)

        # Save all protocol stats (both Welch and FFT)
        protocol_stats.append({
            "protocol": prot_idx + 1,
            "power_q1": power_q1,
            "power_q4": power_q4,
            "diff_power": diff_power,
            "ent_q1": ent_q1,
            "ent_q4": ent_q4,
            "diff_ent": diff_ent,
            "freqs": freqs,
            "psd_q1": psd_q1,
            "psd_q4": psd_q4,
            "fft_freqs": fft_freqs_q1,
            "fft_psd_q1": fft_psd_q1,
            "fft_psd_q4": fft_psd_q4,
            "diff_power_fft": diff_power_fft
        })

        # -- Plot Welch PSD for this protocol
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(freqs, psd_q1, label="Q1 (First Quarter) PSD (Welch)", color="orange")
        ax.plot(freqs, psd_q4, label="Q4 (Last Quarter) PSD (Welch)", color="red")
        ax.axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
        ax.axvspan(entrainment_band[0], entrainment_band[1], color='gray', alpha=0.3,
                   label=f"{entrainment_band[0]}–{entrainment_band[1]} Hz band")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Power (uV²/Hz)")
        ax.set_title(f"Protocol {prot_idx+1}: PSD Comparison (Q1 vs Q4, Fixed n_fft={FIXED_NFFT} Welch)")
        ax.legend()
        # Set x-axis to same range as FMIN, FMAX
        ax.set_xlim(fmin, fmax)
        fig.tight_layout()
        fig.savefig(os.path.join(pa_dir, f"protocol_{prot_idx+1}_psd_comparison.png"))
        plt.close(fig)

        # -- Plot FFT PSD for this protocol
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(fft_freqs_q1, fft_psd_q1, label="Q1 (First Quarter) FFT PSD", color="blue")
        ax.plot(fft_freqs_q1, fft_psd_q4, label="Q4 (Last Quarter) FFT PSD", color="purple")
        ax.axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
        ax.axvspan(entrainment_band[0], entrainment_band[1], color='gray', alpha=0.3,
                   label=f"{entrainment_band[0]}–{entrainment_band[1]} Hz band")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Power (uV²/Hz)")
        ax.set_title(f"Protocol {prot_idx+1}: FFT PSD Comparison (Full Window)")
        ax.legend()
        # Set x-axis range to FMIN,FMAX for FFT visualization
        ax.set_xlim(fmin, fmax)
        fig.tight_layout()
        fig.savefig(os.path.join(pa_dir, f"protocol_{prot_idx+1}_fft_psd_comparison.png"))
        plt.close(fig)

        if logger:
            logger.info(
                f"Protocol {prot_idx+1}: Welch Q1 Power={power_q1:.4f}, Q4 Power={power_q4:.4f} => diff={diff_power:.4f} | "
                f"FFT Q1 Power={power_fft_q1:.4f}, Q4 Power={power_fft_q4:.4f} => diff={diff_power_fft:.4f} | "
                f"Entropy diff={diff_ent:.4f}"
            )

    # AVERAGE DIFFS ACROSS PROTOCOLS (Welch)
    avg_power_diff = np.nanmean(band_power_diff) if band_power_diff else 0
    avg_ent_diff   = np.nanmean(entropy_diff)    if entropy_diff else 0

    if logger:
        logger.info(f"Average band power diff (Welch, Q4-Q1) across protocols = {avg_power_diff:.4f}")
        logger.info(f"Average perm entropy diff (Q4-Q1) across protocols = {avg_ent_diff:.4f}")

    # Bar plot for Welch band power differences
    if band_power_diff:
        fig, ax = plt.subplots(figsize=(8, 5))
        protocol_nums = np.arange(1, len(band_power_diff) + 1)
        ax.bar(protocol_nums, band_power_diff, color='blue', alpha=0.7)
        ax.axhline(avg_power_diff, color='red', linestyle='--', 
                   label=f"Avg diff = {avg_power_diff:.4f}")
        ax.set_xlabel("Protocol #")
        ax.set_ylabel("Power Diff (Q4 - Q1) in 0.9–1.1 Hz (Welch)")
        ax.set_title("Differences in Narrow-Band (0.9–1.1 Hz) Welch Power Across Protocols (Q4 vs Q1)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(pa_dir, "band_power_diff_across_protocols.png"))
        plt.close(fig)

    # Bar plot for FFT band power differences
    if fft_band_power_diff:
        avg_power_diff_fft = np.nanmean(fft_band_power_diff)
        if logger:
            logger.info(f"Average band power diff (FFT, Q4-Q1) across protocols = {avg_power_diff_fft:.4f}")
        fig, ax = plt.subplots(figsize=(8, 5))
        protocol_nums = np.arange(1, len(fft_band_power_diff) + 1)
        ax.bar(protocol_nums, fft_band_power_diff, color='purple', alpha=0.7)
        ax.axhline(avg_power_diff_fft, color='red', linestyle='--', 
                   label=f"Avg diff = {avg_power_diff_fft:.4f}")
        ax.set_xlabel("Protocol #")
        ax.set_ylabel("FFT Power Diff (Q4 - Q1) in 0.9–1.1 Hz")
        ax.set_title("Differences in Narrow-Band (0.9–1.1 Hz) FFT Power Across Protocols (Q4 vs Q1)")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(pa_dir, "fft_band_power_diff_across_protocols.png"))
        plt.close(fig)


###############################################################################
# 3) PLOT AVERAGE PSD ACROSS PROTOCOLS (FIXED n_fft) & SAVE DATA for Q1 vs Q4
###############################################################################
def plot_average_psd(raw,
                     pre_stim_epochs,
                     q1_stim_epochs,
                     q4_stim_epochs,
                     post_stim_epochs,
                     output_dir,
                     subject_id=None,
                     condition=None,
                     logger=None):
    """
    Crops each Q1/Q4 window to the same minimum length across protocols,
    computes the PSD for each with a FIXED n_fft, and plots the average PSD 
    (Q1 vs Q4) plus their difference. Also saves the frequency bins and the 
    difference PSD to a CSV file.
    
    The analysis uses the average of available channels from TARGET_CHANNELS.
    
    Additionally, this function now computes the full-window FFT PSD (and average)
    for Q1 vs Q4 and saves a separate plot and CSV file.
    
    NOTE: If an epoch is too short for the fixed n_fft, instead of erroring out,
    the function will pass n_per_seg equal to the epoch length (thus enabling zero-padding)
    so that the epoch can be used. If an epoch still fails, it is skipped.
    """
    sf = raw.info['sfreq']
    data = raw.get_data(units='uV')

    # Determine indices for target channels
    available_indices = [i for i, ch in enumerate(raw.info['ch_names']) if ch in TARGET_CHANNELS]
    if not available_indices:
        available_indices = [0]

    fmin, fmax = FMIN, FMAX
    entrainment_band = ENTRAINMENT_BAND

    pa_dir = os.path.join(output_dir, 'power_analysis')
    os.makedirs(pa_dir, exist_ok=True)

    # Collect Q1/Q4 data windows
    all_q1 = []
    all_q4 = []
    for q1_ep, q4_ep in zip(q1_stim_epochs, q4_stim_epochs):
        q1_start, q1_end, _ = q1_ep
        q4_start, q4_end, _ = q4_ep
        all_q1.append(np.mean(data[available_indices, q1_start:q1_end], axis=0))
        all_q4.append(np.mean(data[available_indices, q4_start:q4_end], axis=0))

    if not all_q1 or not all_q4:
        if logger:
            logger.warning("No valid Q1/Q4 epochs found. Skipping average PSD plot & CSV.")
        return

    # Find the minimum length among all epochs
    min_len_q1 = min(len(x) for x in all_q1)
    min_len_q4 = min(len(x) for x in all_q4)
    common_len = min(min_len_q1, min_len_q4)

    # Crop data to the common length
    cropped_q1 = [x[:common_len] for x in all_q1]
    cropped_q4 = [x[:common_len] for x in all_q4]

    # Compute Welch PSD for each cropped epoch with fixed n_fft.
    # If an epoch is shorter than FIXED_NFFT, set n_per_seg to the epoch length.
    psds_q1 = []
    psds_q4 = []
    valid_freqs = None
    for cq1 in cropped_q1:
        try:
            n_per_seg = len(cq1) if len(cq1) < FIXED_NFFT else None
            psd, freqs = psd_array_welch(
                cq1[np.newaxis, :], sfreq=sf, fmin=fmin, fmax=fmax,
                n_fft=FIXED_NFFT, n_per_seg=n_per_seg, verbose=False
            )
            psds_q1.append(psd[0])
            valid_freqs = freqs
        except Exception as e:
            if logger:
                logger.warning(f"Error computing Welch PSD for a Q1 epoch: {e}. Skipping this epoch.")
    for cq4 in cropped_q4:
        try:
            n_per_seg = len(cq4) if len(cq4) < FIXED_NFFT else None
            psd, _ = psd_array_welch(
                cq4[np.newaxis, :], sfreq=sf, fmin=fmin, fmax=fmax,
                n_fft=FIXED_NFFT, n_per_seg=n_per_seg, verbose=False
            )
            psds_q4.append(psd[0])
        except Exception as e:
            if logger:
                logger.warning(f"Error computing Welch PSD for a Q4 epoch: {e}. Skipping this epoch.")
    if not psds_q1 or not psds_q4:
        if logger:
            logger.warning("No valid PSDs computed with Welch method. Skipping average PSD plot & CSV.")
        return

    avg_psd_q1 = np.mean(psds_q1, axis=0)
    avg_psd_q4 = np.mean(psds_q4, axis=0)
    diff_psd   = avg_psd_q4 - avg_psd_q1

    if logger and valid_freqs is not None and len(valid_freqs) > 1:
        freq_res = valid_freqs[1] - valid_freqs[0]
        logger.info(f"Average Welch PSD freq resolution = {freq_res:.6f} Hz (n_fft={FIXED_NFFT})")

    # Plot average Welch PSD curves
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(valid_freqs, avg_psd_q1, label="Q1 PSD (First Quarter, Welch)", color="orange")
    ax.plot(valid_freqs, avg_psd_q4, label="Q4 PSD (Last Quarter, Welch)", color="red")
    ax.plot(valid_freqs, diff_psd, label="Diff (Q4 - Q1, Welch)", color="blue")
    ax.axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
    ax.axvspan(entrainment_band[0], entrainment_band[1], color='gray', alpha=0.3,
               label=f"{entrainment_band[0]}–{entrainment_band[1]} Hz")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power (uV²/Hz)")
    ax.set_title(f"Average Welch PSD Across Protocols (Q1 vs Q4, n_fft={FIXED_NFFT})")
    ax.legend()
    ax.set_xlim(fmin, fmax)
    fig.tight_layout()
    fig.savefig(os.path.join(pa_dir, "average_psd_q1_vs_q4.png"))
    plt.close(fig)

    if logger:
        logger.info("Saved average Welch PSD (Q1 vs Q4) plot (fixed n_fft).")

    # Save the subject's Welch PSD difference data for group-level analysis
    df_psd = pd.DataFrame([{
        "Subject": subject_id,
        "Condition": condition,
        "freq_bins": list(valid_freqs),
        "psd_diff": list(diff_psd)
    }])
    csv_path = os.path.join(pa_dir, "psd_data.csv")
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path)
        df_psd = pd.concat([df_existing, df_psd], ignore_index=True)
    df_psd.to_csv(csv_path, index=False)

    if logger:
        logger.info(f"Appended average Welch PSD difference data to {csv_path}")

    # -----------------------------
    # Now compute and plot FFT-based PSD (full window) for the cropped epochs
    fft_psds_q1 = []
    fft_psds_q4 = []
    for cq1 in cropped_q1:
        N = len(cq1)
        fft_vals = np.fft.rfft(cq1)
        freqs_fft = np.fft.rfftfreq(N, d=1/sf)
        psd_fft = (np.abs(fft_vals)**2) / (sf * N)
        if N > 1:
            psd_fft[1:-1] *= 2
        fft_psds_q1.append(psd_fft)
    for cq4 in cropped_q4:
        N = len(cq4)
        fft_vals = np.fft.rfft(cq4)
        freqs_fft = np.fft.rfftfreq(N, d=1/sf)
        psd_fft = (np.abs(fft_vals)**2) / (sf * N)
        if N > 1:
            psd_fft[1:-1] *= 2
        fft_psds_q4.append(psd_fft)

    # Average FFT PSD across epochs (note: all epochs have the same length now)
    avg_fft_psd_q1 = np.mean(fft_psds_q1, axis=0)
    avg_fft_psd_q4 = np.mean(fft_psds_q4, axis=0)
    diff_fft_psd   = avg_fft_psd_q4 - avg_fft_psd_q1

    # Plot average FFT PSD curves
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(freqs_fft, avg_fft_psd_q1, label="Q1 FFT PSD (First Quarter)", color="blue")
    ax.plot(freqs_fft, avg_fft_psd_q4, label="Q4 FFT PSD (Last Quarter)", color="purple")
    ax.plot(freqs_fft, diff_fft_psd, label="Diff (Q4 - Q1) FFT", color="green")
    ax.axvline(x=1.0, color="red", linestyle="--", label="1 Hz")
    ax.axvspan(entrainment_band[0], entrainment_band[1], color='gray', alpha=0.3,
               label=f"{entrainment_band[0]}–{entrainment_band[1]} Hz")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power (uV²/Hz)")
    ax.set_title(f"Average FFT PSD Across Protocols (Q1 vs Q4, Full Window FFT)")
    ax.legend()
    ax.set_xlim(fmin, fmax)
    fig.tight_layout()
    fig.savefig(os.path.join(pa_dir, "average_fft_psd_q1_vs_q4.png"))
    plt.close(fig)

    if logger:
        logger.info("Saved average FFT PSD (Q1 vs Q4) plot.")

    # Save the subject's FFT PSD difference data for group-level analysis
    df_fft_psd = pd.DataFrame([{
        "Subject": subject_id,
        "Condition": condition,
        "freq_bins": list(freqs_fft),
        "fft_psd_diff": list(diff_fft_psd)
    }])
    csv_fft_path = os.path.join(pa_dir, "fft_psd_data.csv")
    if os.path.exists(csv_fft_path):
        df_existing = pd.read_csv(csv_fft_path)
        df_fft_psd = pd.concat([df_existing, df_fft_psd], ignore_index=True)
    df_fft_psd.to_csv(csv_fft_path, index=False)

    if logger:
        logger.info(f"Appended average FFT PSD difference data to {csv_fft_path}")


###############################################################################
# 4) PLOT TOPOMAPS FOR Q1-Q4 DIFFERENCE ACROSS CHANNELS (FIXED n_fft)
###############################################################################
def plot_topomaps(raw,
                  pre_stim_epochs,
                  q1_stim_epochs,
                  q4_stim_epochs,
                  post_stim_epochs,
                  output_dir,
                  logger=None):
    """
    Computes channel-wise average power in 0.9–1.1 Hz for Q1 vs Q4 epochs
    across all channels in the raw data, and then plots topomaps for Q1, Q4, 
    and their difference. The Q1 and Q4 maps share a common color scale, and 
    sensor names are displayed.
    
    Two sets of outputs are generated:
      1. Welch-based topomaps (using psd_array_welch with n_fft=epoch_length)
      2. FFT-based topomaps (using full-window FFT computations)
    """
    sf = raw.info['sfreq']
    data = raw.get_data(units='uV')  # shape: (n_channels, n_times)
    n_channels = data.shape[0]
    channel_names = raw.info["ch_names"]

    fmin, fmax = FMIN, FMAX
    entrainment_band = ENTRAINMENT_BAND

    pa_dir = os.path.join(output_dir, 'power_analysis')
    os.makedirs(pa_dir, exist_ok=True)

    # --- Welch-based Topomap Computation ---
    q1_topo = np.zeros(n_channels)
    q4_topo = np.zeros(n_channels)

    if logger:
        logger.info("Computing Welch-based topomap for power in 0.9–1.1 Hz (Q1 vs Q4)...")

    # Loop over channels (each channel is treated separately)
    for ch_idx in range(n_channels):
        q1_vals = []
        q4_vals = []
        for q1_ep, q4_ep in zip(q1_stim_epochs, q4_stim_epochs):
            q1_start, q1_end, _ = q1_ep
            q4_start, q4_end, _ = q4_ep

            q1_data = data[ch_idx, q1_start:q1_end]
            q4_data = data[ch_idx, q4_start:q4_end]

            # Compute PSD using n_fft equal to the epoch length
            try:
                psd_q1, freqs = psd_array_welch(
                    q1_data[np.newaxis, :],
                    sfreq=sf, fmin=fmin, fmax=fmax,
                    n_fft=len(q1_data), verbose=False
                )
            except ZeroDivisionError:
                if logger:
                    logger.warning(f"ZeroDivisionError for channel {channel_names[ch_idx]} in Q1 epoch; skipping this epoch.")
                continue
            try:
                psd_q4, _ = psd_array_welch(
                    q4_data[np.newaxis, :],
                    sfreq=sf, fmin=fmin, fmax=fmax,
                    n_fft=len(q4_data), verbose=False
                )
            except ZeroDivisionError:
                if logger:
                    logger.warning(f"ZeroDivisionError for channel {channel_names[ch_idx]} in Q4 epoch; skipping this epoch.")
                continue

            psd_q1 = psd_q1[0]
            psd_q4 = psd_q4[0]

            # Find frequency indices within the entrainment band (0.9–1.1 Hz)
            band_idx = np.where((freqs >= entrainment_band[0]) & (freqs <= entrainment_band[1]))[0]
            if len(band_idx) == 0:
                continue

            q1_vals.append(np.mean(psd_q1[band_idx]))
            q4_vals.append(np.mean(psd_q4[band_idx]))

        if len(q1_vals) > 0:
            q1_topo[ch_idx] = np.mean(q1_vals)
            q4_topo[ch_idx] = np.mean(q4_vals)
        else:
            q1_topo[ch_idx] = np.nan
            q4_topo[ch_idx] = np.nan

    diff_topo = q4_topo - q1_topo

    # Determine common color scale for the Welch topomaps
    common_vmin = np.nanmin([np.nanmin(q1_topo), np.nanmin(q4_topo)])
    common_vmax = np.nanmax([np.nanmax(q1_topo), np.nanmax(q4_topo)])

    # Plot Welch-based topomaps for Q1, Q4, and the difference.
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    im0, _ = mne.viz.plot_topomap(q1_topo, raw.info, axes=axes[0], show=False, contours=0,
                                  vlim=(common_vmin, common_vmax),
                                  names=channel_names)
    axes[0].set_title("Q1 (0.9–1.1 Hz, Welch)")
    cbar0 = plt.colorbar(im0, ax=axes[0], orientation='vertical', fraction=0.046, pad=0.04)
    cbar0.set_label('Power (uV²/Hz)')

    im1, _ = mne.viz.plot_topomap(q4_topo, raw.info, axes=axes[1], show=False, contours=0,
                                  vlim=(common_vmin, common_vmax),
                                  names=channel_names)
    axes[1].set_title("Q4 (0.9–1.1 Hz, Welch)")
    cbar1 = plt.colorbar(im1, ax=axes[1], orientation='vertical', fraction=0.046, pad=0.04)
    cbar1.set_label('Power (uV²/Hz)')

    im2, _ = mne.viz.plot_topomap(diff_topo, raw.info, axes=axes[2], show=False, contours=0)
    axes[2].set_title("Q4 - Q1 (0.9–1.1 Hz, Welch)")
    cbar2 = plt.colorbar(im2, ax=axes[2], orientation='vertical', fraction=0.046, pad=0.04)
    cbar2.set_label('Power Diff (uV²/Hz)')

    fig.suptitle("Welch Topomaps of Narrow-Band Power (Q1 vs Q4)")
    fig.tight_layout()
    fig.savefig(os.path.join(pa_dir, "topomaps_q1_q4_difference.png"))
    plt.close(fig)

    if logger:
        logger.info("Saved Welch-based topomap figures for Q1, Q4, and their difference.")

    # Save computed Welch topomap data to CSV for group-level analysis.
    df_topo = pd.DataFrame({
        "Channel": channel_names,
        "Q1 Power": q1_topo,
        "Q4 Power": q4_topo,
        "Difference (Q4 - Q1)": diff_topo
    })
    csv_path = os.path.join(pa_dir, "topomap_data.csv")
    df_topo.to_csv(csv_path, index=False)

    if logger:
        logger.info(f"Saved Welch topomap power analysis to {csv_path}")

    # --- FFT-based Topomap Computation ---
    q1_topo_fft = np.zeros(n_channels)
    q4_topo_fft = np.zeros(n_channels)

    if logger:
        logger.info("Computing FFT-based topomap for power in 0.9–1.1 Hz (Q1 vs Q4)...")

    for ch_idx in range(n_channels):
        q1_vals_fft = []
        q4_vals_fft = []
        for q1_ep, q4_ep in zip(q1_stim_epochs, q4_stim_epochs):
            q1_start, q1_end, _ = q1_ep
            q4_start, q4_end, _ = q4_ep

            q1_data = data[ch_idx, q1_start:q1_end]
            q4_data = data[ch_idx, q4_start:q4_end]
            if len(q1_data) == 0 or len(q4_data) == 0:
                continue

            # FFT for Q1
            N1 = len(q1_data)
            fft_vals1 = np.fft.rfft(q1_data)
            freqs_fft1 = np.fft.rfftfreq(N1, d=1/sf)
            psd_fft1 = (np.abs(fft_vals1)**2) / (sf * N1)
            if N1 > 1:
                psd_fft1[1:-1] *= 2
            band_idx_fft1 = np.where((freqs_fft1 >= entrainment_band[0]) & (freqs_fft1 <= entrainment_band[1]))[0]
            if len(band_idx_fft1) == 0:
                continue
            q1_val = np.mean(psd_fft1[band_idx_fft1])
            q1_vals_fft.append(q1_val)

            # FFT for Q4
            N4 = len(q4_data)
            fft_vals4 = np.fft.rfft(q4_data)
            freqs_fft4 = np.fft.rfftfreq(N4, d=1/sf)
            psd_fft4 = (np.abs(fft_vals4)**2) / (sf * N4)
            if N4 > 1:
                psd_fft4[1:-1] *= 2
            band_idx_fft4 = np.where((freqs_fft4 >= entrainment_band[0]) & (freqs_fft4 <= entrainment_band[1]))[0]
            if len(band_idx_fft4) == 0:
                continue
            q4_val = np.mean(psd_fft4[band_idx_fft4])
            q4_vals_fft.append(q4_val)

        if len(q1_vals_fft) > 0:
            q1_topo_fft[ch_idx] = np.mean(q1_vals_fft)
            q4_topo_fft[ch_idx] = np.mean(q4_vals_fft)
        else:
            q1_topo_fft[ch_idx] = np.nan
            q4_topo_fft[ch_idx] = np.nan

    diff_topo_fft = q4_topo_fft - q1_topo_fft

    # Determine common color scale for the FFT topomaps
    common_vmin_fft = np.nanmin([np.nanmin(q1_topo_fft), np.nanmin(q4_topo_fft)])
    common_vmax_fft = np.nanmax([np.nanmax(q1_topo_fft), np.nanmax(q4_topo_fft)])

    # Plot FFT-based topomaps for Q1, Q4, and the difference.
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    im0, _ = mne.viz.plot_topomap(q1_topo_fft, raw.info, axes=axes[0], show=False, contours=0,
                                  vlim=(common_vmin_fft, common_vmax_fft),
                                  names=channel_names)
    axes[0].set_title("Q1 FFT (0.9–1.1 Hz)")
    cbar0 = plt.colorbar(im0, ax=axes[0], orientation='vertical', fraction=0.046, pad=0.04)
    cbar0.set_label('Power (uV²/Hz)')

    im1, _ = mne.viz.plot_topomap(q4_topo_fft, raw.info, axes=axes[1], show=False, contours=0,
                                  vlim=(common_vmin_fft, common_vmax_fft),
                                  names=channel_names)
    axes[1].set_title("Q4 FFT (0.9–1.1 Hz)")
    cbar1 = plt.colorbar(im1, ax=axes[1], orientation='vertical', fraction=0.046, pad=0.04)
    cbar1.set_label('Power (uV²/Hz)')

    im2, _ = mne.viz.plot_topomap(diff_topo_fft, raw.info, axes=axes[2], show=False, contours=0)
    axes[2].set_title("Q4 - Q1 FFT (0.9–1.1 Hz)")
    cbar2 = plt.colorbar(im2, ax=axes[2], orientation='vertical', fraction=0.046, pad=0.04)
    cbar2.set_label('Power Diff (uV²/Hz)')

    fig.suptitle("FFT Topomaps of Narrow-Band Power (Q1 vs Q4)")
    fig.tight_layout()
    fig.savefig(os.path.join(pa_dir, "topomaps_q1_q4_difference_fft.png"))
    plt.close(fig)

    if logger:
         logger.info("Saved FFT-based topomap figures for Q1, Q4, and their difference.")

    # Save computed FFT topomap data to CSV for group-level analysis.
    df_topo_fft = pd.DataFrame({
         "Channel": channel_names,
         "Q1 FFT Power": q1_topo_fft,
         "Q4 FFT Power": q4_topo_fft,
         "Difference FFT (Q4 - Q1)": diff_topo_fft
    })
    csv_fft_path = os.path.join(pa_dir, "topomap_data_fft.csv")
    df_topo_fft.to_csv(csv_fft_path, index=False)
    if logger:
         logger.info(f"Saved FFT topomap power analysis to {csv_fft_path}")

