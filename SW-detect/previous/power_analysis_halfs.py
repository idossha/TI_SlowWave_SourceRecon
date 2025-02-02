
# power_analysis.py

import os
import numpy as np
import pandas as pd
from mne.time_frequency import psd_array_welch
import mne
import matplotlib
import matplotlib.pyplot as plt
import antropy as ant  # pip install antropy if not installed

matplotlib.use('Agg')  # Non-interactive backend for automated scripts

###############################################################################
# Define constants for analysis
###############################################################################
FIXED_NFFT = 4096          # Example: pick 4096 for high freq resolution
FMIN, FMAX = 0.5, 2      # Narrow band of interest (0.9–1.1 Hz)
ENTRAINMENT_BAND = [0.9, 1.1]  # For highlighting in plots, etc.

###############################################################################
# 1) SPLIT STIMULATION EPOCHS
###############################################################################
def split_stim_epochs(raw, min_stim_duration_sec=100, logger=None):
    """
    Extracts pre-stim, early-stim, late-stim, and post-stim epochs from `raw` 
    based on annotations "stim start" and "stim end". Each stim is split into
    two halves (early, late). Pre-stim and post-stim are matched in duration 
    to the entire stim epoch.
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
    early_stim_epochs = []
    late_stim_epochs = []
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
            
            stim_midpoint = (stim_start + stim_end) // 2

            pre_stim_epoch  = (stim_start - stim_duration, stim_start, protocol_number)
            early_stim_epoch = (stim_start, stim_midpoint, protocol_number)
            late_stim_epoch  = (stim_midpoint, stim_end, protocol_number)
            post_stim_epoch  = (stim_end, stim_end + stim_duration, protocol_number)

            if pre_stim_epoch[0] < previous_end:
                # Overlap found, skip
                continue
            
            previous_end = post_stim_epoch[1]

            pre_stim_epochs.append(pre_stim_epoch)
            early_stim_epochs.append(early_stim_epoch)
            late_stim_epochs.append(late_stim_epoch)
            post_stim_epochs.append(post_stim_epoch)
            
            protocol_number += 1

    if logger:
        logger.info(f"Found {len(early_stim_epochs)} valid stimulation blocks.")
    return pre_stim_epochs, early_stim_epochs, late_stim_epochs, post_stim_epochs


###############################################################################
# 2) PROTOCOL-BY-PROTOCOL ANALYSIS (PSD, PERM ENTROPY) + PLOTTING
###############################################################################
def analyze_protocols(raw,
                      pre_stim_epochs,
                      early_stim_epochs,
                      late_stim_epochs,
                      post_stim_epochs,
                      output_dir,
                      subject_id=None,
                      condition=None,
                      logger=None):
    """
    For each protocol block:
      - Compute Welch PSD in [FMIN, FMAX] Hz for the EARLY vs LATE half of the stim epoch
      - Compute average power in [0.9, 1.1] Hz
      - Compute permutation entropy
      - Plot PSD comparisons for each protocol
      - Print and plot distribution of differences across protocols
    """
    sf = raw.info['sfreq']
    data = raw.get_data(units='uV')  # shape: (n_channels, n_times)
    chan_idx = 0  # analyzing single channel as example

    pa_dir = os.path.join(output_dir, 'power_analysis')
    os.makedirs(pa_dir, exist_ok=True)

    # Our global settings
    fmin, fmax = FMIN, FMAX
    entrainment_band = ENTRAINMENT_BAND

    from mne.time_frequency import psd_array_welch

    band_power_diff = []
    entropy_diff = []
    protocol_stats = []

    if logger:
        logger.info("Performing protocol-by-protocol power analysis with fixed n_fft...")

    for prot_idx, (early_epoch, late_epoch) in enumerate(zip(early_stim_epochs, late_stim_epochs)):
        early_start, early_end, prot_num = early_epoch
        late_start, late_end, _ = late_epoch

        early_data = data[chan_idx, early_start:early_end]
        late_data  = data[chan_idx, late_start:late_end]

        # 1) PSD with fixed n_fft
        psd_early, freqs = psd_array_welch(
            early_data[np.newaxis, :],
            sfreq=sf,
            fmin=fmin,
            fmax=fmax,
            n_fft=FIXED_NFFT,  # <--- FIXED
            verbose=False
        )
        psd_late, _ = psd_array_welch(
            late_data[np.newaxis, :],
            sfreq=sf,
            fmin=fmin,
            fmax=fmax,
            n_fft=FIXED_NFFT,  # <--- FIXED
            verbose=False
        )
        psd_early = psd_early[0]
        psd_late  = psd_late[0]

        if prot_idx == 0 and len(freqs) > 1 and logger:
            freq_res = freqs[1] - freqs[0]
            logger.info(f"Protocol 1 freq resolution = {freq_res:.6f} Hz (n_fft={FIXED_NFFT})")

        # Identify frequency indices within 0.9–1.1 (ENTRAINMENT_BAND)
        band_idx = np.where((freqs >= entrainment_band[0]) & (freqs <= entrainment_band[1]))[0]
        power_early = np.mean(psd_early[band_idx]) if len(band_idx) else np.nan
        power_late  = np.mean(psd_late[band_idx])  if len(band_idx) else np.nan
        diff_power  = power_late - power_early if not np.isnan(power_late) else np.nan
        band_power_diff.append(diff_power)

        # 2) Permutation Entropy
        import antropy as ant
        ent_early = ant.perm_entropy(early_data, order=3, delay=1, normalize=True)
        ent_late  = ant.perm_entropy(late_data,  order=3, delay=1, normalize=True)
        diff_ent  = ent_late - ent_early
        entropy_diff.append(diff_ent)

        protocol_stats.append({
            "protocol": prot_idx + 1,
            "power_early": power_early,
            "power_late": power_late,
            "diff_power": diff_power,
            "ent_early": ent_early,
            "ent_late": ent_late,
            "diff_ent": diff_ent,
            "freqs": freqs,
            "psd_early": psd_early,
            "psd_late": psd_late
        })

        # -- Plot PSD for this protocol
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(freqs, psd_early, label="Early Stim PSD", color="orange")
        ax.plot(freqs, psd_late,  label="Late Stim PSD",  color="red")
        ax.axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
        ax.axvspan(entrainment_band[0], entrainment_band[1], color='gray', alpha=0.3,
                   label=f"{entrainment_band[0]}–{entrainment_band[1]} Hz band")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Power (uV²/Hz)")
        ax.set_title(f"Protocol {prot_idx+1}: PSD Comparison (Fixed n_fft={FIXED_NFFT})")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(pa_dir, f"protocol_{prot_idx+1}_psd_comparison.png"))
        plt.close(fig)

        if logger:
            logger.info(
                f"Protocol {prot_idx+1}: Early={power_early:.4f}, Late={power_late:.4f} => diff={diff_power:.4f} | Ent. diff={diff_ent:.4f}"
            )

    # AVERAGE DIFFS ACROSS PROTOCOLS
    avg_power_diff = np.nanmean(band_power_diff) if band_power_diff else 0
    avg_ent_diff   = np.nanmean(entropy_diff)    if entropy_diff else 0

    if logger:
        logger.info(f"Average band power diff (Late-Early) across protocols = {avg_power_diff:.4f}")
        logger.info(f"Average perm entropy diff (Late-Early) across protocols = {avg_ent_diff:.4f}")

    # Bar plot for band power diffs
    if band_power_diff:
        fig, ax = plt.subplots(figsize=(8, 5))
        protocol_nums = np.arange(1, len(band_power_diff) + 1)
        ax.bar(protocol_nums, band_power_diff, color='blue', alpha=0.7)
        ax.axhline(avg_power_diff, color='red', linestyle='--', 
                   label=f"Avg diff = {avg_power_diff:.4f}")
        ax.set_xlabel("Protocol #")
        ax.set_ylabel("Power Diff (Late-Early) in 0.9–1.1 Hz")
        ax.set_title("Differences in Narrow-Band (0.9–1.1 Hz) Power Across Protocols")
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(pa_dir, "band_power_diff_across_protocols.png"))
        plt.close(fig)


###############################################################################
# 3) PLOT AVERAGE PSD ACROSS PROTOCOLS (FIXED n_fft) & SAVE DATA
###############################################################################
def plot_average_psd(raw,
                     pre_stim_epochs,
                     early_stim_epochs,
                     late_stim_epochs,
                     post_stim_epochs,
                     output_dir,
                     subject_id=None,
                     condition=None,
                     logger=None):
    """
    Crops each early/late window to the same minimum length across protocols,
    then computes PSD for each with a FIXED n_fft, and plots the average PSD 
    (EARLY vs LATE) plus their difference. Also saves freq_bins + diff_psd to CSV.
    """
    sf = raw.info['sfreq']
    data = raw.get_data(units='uV')
    chan_idx = 0

    fmin, fmax = FMIN, FMAX
    entrainment_band = ENTRAINMENT_BAND

    from mne.time_frequency import psd_array_welch

    pa_dir = os.path.join(output_dir, 'power_analysis')
    os.makedirs(pa_dir, exist_ok=True)

    # Collect early/late data windows
    all_early = []
    all_late  = []
    for e_ep, l_ep in zip(early_stim_epochs, late_stim_epochs):
        es, ee, _ = e_ep
        ls, le, _ = l_ep
        all_early.append(data[chan_idx, es:ee])
        all_late.append(data[chan_idx, ls:le])

    if not all_early or not all_late:
        if logger:
            logger.warning("No valid early/late epochs found. Skipping average PSD plot & CSV.")
        return

    # Minimum length
    min_len_early = min(len(x) for x in all_early)
    min_len_late  = min(len(x) for x in all_late)
    common_len    = min(min_len_early, min_len_late)

    # Crop
    cropped_early = [x[:common_len] for x in all_early]
    cropped_late  = [x[:common_len] for x in all_late]

    # Compute PSD for each with fixed n_fft
    psds_early = []
    psds_late  = []
    for ce in cropped_early:
        psd, freqs = psd_array_welch(
            ce[np.newaxis, :], sfreq=sf, fmin=fmin, fmax=fmax,
            n_fft=FIXED_NFFT, verbose=False
        )
        psds_early.append(psd[0])
    for cl in cropped_late:
        psd, freqs = psd_array_welch(
            cl[np.newaxis, :], sfreq=sf, fmin=fmin, fmax=fmax,
            n_fft=FIXED_NFFT, verbose=False
        )
        psds_late.append(psd[0])

    avg_psd_early = np.mean(psds_early, axis=0)
    avg_psd_late  = np.mean(psds_late, axis=0)
    diff_psd      = avg_psd_late - avg_psd_early

    if logger and len(freqs) > 1:
        freq_res = freqs[1] - freqs[0]
        logger.info(f"Average PSD freq resolution = {freq_res:.6f} Hz (n_fft={FIXED_NFFT})")

    # Plot
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(freqs, avg_psd_early, label="Early-Stim PSD", color="orange")
    ax.plot(freqs, avg_psd_late,  label="Late-Stim PSD",  color="red")
    ax.plot(freqs, diff_psd,      label="Diff (Late - Early)", color="blue")
    ax.axvline(x=1.0, color="green", linestyle="--", label="1 Hz")
    ax.axvspan(entrainment_band[0], entrainment_band[1], color='gray', alpha=0.3,
               label=f"{entrainment_band[0]}–{entrainment_band[1]} Hz")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power (uV²/Hz)")
    ax.set_title(f"Average PSD Across Protocols (n_fft={FIXED_NFFT})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(pa_dir, "average_psd_early_vs_late.png"))
    plt.close(fig)

    if logger:
        logger.info("Saved average PSD (early vs. late) plot (fixed n_fft).")

    # Save subject's PSD diff array for group-level analysis
    import pandas as pd
    df_psd = pd.DataFrame([{
        "Subject": subject_id,
        "Condition": condition,
        "freq_bins": list(freqs),
        "psd_diff": list(diff_psd)
    }])
    csv_path = os.path.join(pa_dir, "psd_data.csv")
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path)
        df_psd = pd.concat([df_existing, df_psd], ignore_index=True)
    df_psd.to_csv(csv_path, index=False)

    if logger:
        logger.info(f"Appended average PSD difference data to {csv_path}")



###############################################################################
# 4) PLOT TOPOMAPS FOR EARLY-LATE DIFFERENCE ACROSS CHANNELS (FIXED n_fft)
###############################################################################
###############################################################################

def plot_topomaps(raw,
                  pre_stim_epochs,
                  early_stim_epochs,
                  late_stim_epochs,
                  post_stim_epochs,
                  output_dir,
                  logger=None):
    """
    Compute channel-wise average power in 0.9–1.1 Hz for early vs. late epochs
    across all protocols (using the available channels in raw) and then plot
    topomaps for Early, Late, and their difference.
    
    This version does not perform any channel interpolation.
    """
    sf = raw.info['sfreq']
    data = raw.get_data(units='uV')  # EEG data in microvolts
    n_channels = data.shape[0]
    channel_names = raw.info["ch_names"]

    # We will compute the PSD only in the narrow frequency band (0.9–1.1 Hz)
    # using a variable n_fft equal to the epoch length.
    fmin, fmax = FMIN, FMAX
    entrainment_band = ENTRAINMENT_BAND

    pa_dir = os.path.join(output_dir, 'power_analysis')
    os.makedirs(pa_dir, exist_ok=True)

    early_topo = np.zeros(n_channels)
    late_topo  = np.zeros(n_channels)

    if logger:
        logger.info("Computing topomap for power in 0.9–1.1 Hz (no interpolation)...")

    # Loop over channels
    for ch_idx in range(n_channels):
        early_vals = []
        late_vals = []
        # Loop over each pair of early and late epochs
        for e_ep, l_ep in zip(early_stim_epochs, late_stim_epochs):
            es, ee, _ = e_ep
            ls, le, _ = l_ep

            early_data = data[ch_idx, es:ee]
            late_data = data[ch_idx, ls:le]

            # Compute PSD using n_fft equal to the length of the epoch.
            # (This gives a resolution of sfreq/epoch_length)
            try:
                psd_early, freqs = psd_array_welch(
                    early_data[np.newaxis, :],
                    sfreq=sf, fmin=fmin, fmax=fmax,
                    n_fft=len(early_data), verbose=False
                )
            except ZeroDivisionError:
                if logger:
                    logger.warning(f"ZeroDivisionError for channel {channel_names[ch_idx]} in early epoch; skipping this epoch.")
                continue
            try:
                psd_late, _ = psd_array_welch(
                    late_data[np.newaxis, :],
                    sfreq=sf, fmin=fmin, fmax=fmax,
                    n_fft=len(late_data), verbose=False
                )
            except ZeroDivisionError:
                if logger:
                    logger.warning(f"ZeroDivisionError for channel {channel_names[ch_idx]} in late epoch; skipping this epoch.")
                continue

            psd_early = psd_early[0]
            psd_late = psd_late[0]

            # Find frequency indices within the entrainment band (0.9–1.1 Hz)
            band_idx = np.where((freqs >= entrainment_band[0]) & (freqs <= entrainment_band[1]))[0]
            if len(band_idx) == 0:
                continue

            early_vals.append(np.mean(psd_early[band_idx]))
            late_vals.append(np.mean(psd_late[band_idx]))

        if len(early_vals) > 0:
            early_topo[ch_idx] = np.mean(early_vals)
            late_topo[ch_idx] = np.mean(late_vals)
        else:
            early_topo[ch_idx] = np.nan
            late_topo[ch_idx] = np.nan

    diff_topo = late_topo - early_topo

    # Plot topomaps for Early, Late, and Difference
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    im0, _ = mne.viz.plot_topomap(early_topo, raw.info, axes=axes[0], show=False, contours=0)
    axes[0].set_title("Early (0.9–1.1 Hz)")
    cbar0 = plt.colorbar(im0, ax=axes[0], orientation='vertical', fraction=0.046, pad=0.04)
    cbar0.set_label('Power (uV²/Hz)')

    im1, _ = mne.viz.plot_topomap(late_topo, raw.info, axes=axes[1], show=False, contours=0)
    axes[1].set_title("Late (0.9–1.1 Hz)")
    cbar1 = plt.colorbar(im1, ax=axes[1], orientation='vertical', fraction=0.046, pad=0.04)
    cbar1.set_label('Power (uV²/Hz)')

    im2, _ = mne.viz.plot_topomap(diff_topo, raw.info, axes=axes[2], show=False, contours=0)
    axes[2].set_title("Late - Early (0.9–1.1 Hz)")
    cbar2 = plt.colorbar(im2, ax=axes[2], orientation='vertical', fraction=0.046, pad=0.04)
    cbar2.set_label('Power Diff (uV²/Hz)')

    fig.suptitle("Topomaps of Narrow-Band Power")
    fig.tight_layout()
    fig.savefig(os.path.join(pa_dir, "topomaps_early_late_difference.png"))
    plt.close(fig)

    if logger:
        logger.info("Saved topomap figures for early, late, and difference.")

    # Save computed topomap difference data to CSV for group-level analysis.
    # Here we include the channel names for clarity.
    df_topo = pd.DataFrame({
        "Channel": channel_names,
        "Early Power": early_topo,
        "Late Power": late_topo,
        "Difference (Late - Early)": diff_topo
    })
    csv_path = os.path.join(pa_dir, "topomap_data.csv")
    df_topo.to_csv(csv_path, index=False)

    if logger:
        logger.info(f"Saved topomap power analysis to {csv_path}")
