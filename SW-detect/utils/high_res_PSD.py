
#!/usr/bin/env python
"""
high_res_PSD.py

This script processes one or more EEG .set files. For each file, it:
  1. Splits the raw data into three epochs per stimulation protocol (pre‐stim, stim, post‐stim).
  2. Computes individual PSDs for each protocol using a chosen method:
     Welch’s, multitaper, or full FFT.
  3. Computes average PSDs across protocols (after cropping to a common duration).
  4. Computes PSDs on the concatenated data from all protocols for each stage.
  5. Saves PSD plots (with a red dashed 1 Hz marker, bin resolution, and integration time indicated)
     and CSV files into an output directory (each file gets its own subdirectory).

Usage example:
    python high_res_PSD.py --files /path/to/file1.set /path/to/file2.set --methods welch fft --out /path/to/output --channels E1 E2
If --methods is not specified, it defaults to "welch".
If --out is not specified, the default output directory is "./psd_output" (in the current working directory).
If --channels is not specified, the script will use the average of all channels.
"""

import os
import numpy as np
import mne
import matplotlib.pyplot as plt
import logging
import pandas as pd
import argparse

# =============================================================================
# Analysis parameters
# =============================================================================
FMIN = 0.5       # minimum frequency for PSD
FMAX = 15.0      # maximum frequency for PSD (adjust as needed)
FIXED_NFFT = 10000      # n_fft used for individual protocol PSDs
HIGH_RES_NFFT = 10000   # n_fft used for high-resolution average/concatenated PSDs

MIN_STIM_DURATION_SEC = 100  # minimum stimulation duration (in seconds)

# =============================================================================
# Set up logging
# =============================================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# =============================================================================
# Internal data loading function
# =============================================================================
def load_data(file_path):
    """
    Loads EEG data from an EEGLAB .set file using MNE.
    
    Parameters:
      file_path: str, path to the .set file.
      
    Returns:
      raw: mne.io.Raw object with the data loaded.
      data: numpy array of the EEG data in microvolts.
    """
    logger.info(f"Loading data from {file_path}")
    raw = mne.io.read_raw_eeglab(file_path, preload=True)
    data = raw.get_data(units="uV")
    logger.info(f"Successfully loaded data from {file_path}")
    return raw, data

# =============================================================================
# Helper functions
# =============================================================================
def split_stim_epochs_3parts(raw, min_stim_duration_sec=MIN_STIM_DURATION_SEC):
    """
    Splits the raw data into three epochs per protocol: pre-stim, stim, and post-stim.
    Uses annotations "stim start" (code 2) and "stim end" (code 1).
    
    Returns three lists of epochs, each a tuple: (start_sample, end_sample, protocol_number).
    """
    sf = raw.info['sfreq']
    events, _ = mne.events_from_annotations(raw)
    stim_start_code = 2
    stim_end_code = 1

    filtered_events = [evt for evt in events if evt[2] in (stim_start_code, stim_end_code)]
    
    pre_epochs, stim_epochs, post_epochs = [], [], []
    protocol_number = 1
    previous_end = 0

    for i in range(0, len(filtered_events), 2):
        if i + 1 < len(filtered_events):
            stim_start = filtered_events[i][0]
            stim_end = filtered_events[i+1][0]
            stim_duration = stim_end - stim_start
            if stim_duration < min_stim_duration_sec * sf:
                logger.info(f"Skipping protocol #{protocol_number}: duration < {min_stim_duration_sec} sec")
                continue

            pre_start = stim_start - stim_duration
            pre_end = stim_start
            stim_start_idx = stim_start
            stim_end_idx = stim_end
            post_start = stim_end
            post_end = stim_end + stim_duration

            if pre_start < previous_end:
                continue
            previous_end = post_end

            pre_epochs.append((pre_start, pre_end, protocol_number))
            stim_epochs.append((stim_start_idx, stim_end_idx, protocol_number))
            post_epochs.append((post_start, post_end, protocol_number))
            protocol_number += 1

    logger.info(f"Found {len(stim_epochs)} valid stimulation blocks.")
    return pre_epochs, stim_epochs, post_epochs

def compute_psd_for_epoch(signal, sf, method='welch', n_fft=None):
    """
    Computes the PSD for a 1D signal (an epoch) using the specified method.
    
    Parameters:
      signal: 1D numpy array (the epoch)
      sf: sampling frequency
      method: 'welch', 'multitaper', or 'fft'
      n_fft: FFT length to use (for welch and fft; ignored for multitaper)
             For FFT, n_fft is ignored and the signal length is used.
      
    Returns:
      psd: 1D numpy array of power values for frequencies between FMIN and FMAX.
      freqs: 1D numpy array of frequency bins.
    """
    if method == 'welch':
        if n_fft is None:
            n_fft = FIXED_NFFT
        psd, freqs = mne.time_frequency.psd_array_welch(signal[np.newaxis, :],
                                                         sfreq=sf,
                                                         fmin=FMIN,
                                                         fmax=FMAX,
                                                         n_fft=n_fft,
                                                         verbose=False)
        return psd[0], freqs
    elif method == 'multitaper':
        psd, freqs = mne.time_frequency.psd_array_multitaper(signal[np.newaxis, :],
                                                              sfreq=sf,
                                                              fmin=FMIN,
                                                              fmax=FMAX,
                                                              adaptive=True,
                                                              normalization='full',
                                                              verbose=False)
        return psd[0], freqs
    elif method == 'fft':
        # For FFT, use the actual length of the signal to compute the FFT.
        n_fft = len(signal)
        X = np.fft.rfft(signal, n=n_fft)
        freqs = np.fft.rfftfreq(n_fft, d=1/sf)
        psd = (np.abs(X)**2) / (sf * n_fft)
        if n_fft % 2 == 0:
            psd[1:-1] *= 2
        else:
            psd[1:] *= 2
        # Restrict to frequencies between FMIN and FMAX.
        idx = (freqs >= FMIN) & (freqs <= FMAX)
        return psd[idx], freqs[idx]
    else:
        raise ValueError("Method must be 'welch', 'multitaper', or 'fft'.")

def plot_and_save_psd(freqs, psd, title, out_filepath, bin_resolution=None, integration_time=None):
    """
    Plots a PSD curve with a clear 1 Hz marker, appends the bin resolution and integration time to the title,
    and saves the plot. The figure size is increased to avoid clipping the title.
    """
    plt.figure(figsize=(12, 8))
    plt.plot(freqs, psd, label='PSD')
    plt.axvline(x=1.0, color='red', linestyle='--', linewidth=2, label='1 Hz')
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Power")
    info_str = ""
    if bin_resolution is not None:
        info_str += f" | Bin res: {bin_resolution:.4f} Hz"
    if integration_time is not None:
        info_str += f" | Time integrated: {integration_time:.2f} s"
    plt.title(title + info_str)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_filepath)
    plt.close()

def save_psd_to_csv(freqs, psd, out_filepath):
    """
    Saves PSD data to a CSV file.
    """
    df = pd.DataFrame({'Frequency': freqs, 'Power': psd})
    df.to_csv(out_filepath, index=False)

# =============================================================================
# Main processing function
# =============================================================================
def main(args):
    # Get the list of files, methods, output directory, and channels (if provided) from the command line.
    file_list = args.files
    methods = [m.lower() for m in args.methods]
    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    
    for fname in file_list:
        base_name = os.path.splitext(os.path.basename(fname))[0]
        file_out_dir = os.path.join(out_dir, base_name)
        os.makedirs(file_out_dir, exist_ok=True)
        logger.info(f"Processing file: {fname}")
        
        # Load data.
        raw, _ = load_data(fname)
        sf = raw.info['sfreq']
        

        # Determine which channels to use.
        all_data = raw.get_data(units="uV")  # shape: (n_channels, n_times)
        if args.channels:
            provided_channels = args.channels
            available_channels = raw.info['ch_names']
            # Get indices for the channels that are provided and available.
            selected_indices = [i for i, ch in enumerate(available_channels) if ch in provided_channels]
            # Identify any channels that were provided but are missing.
            missing_channels = [ch for ch in provided_channels if ch not in available_channels]
            if missing_channels:
                logger.info(f"Missing channels: {missing_channels}")
            if not selected_indices:
                logger.error("None of the specified channels were found in the data. Exiting.")
                raise ValueError("No valid channels provided.")
            else:
                avg_signal = np.mean(all_data[selected_indices, :], axis=0)
                logger.info(f"Using channels: {[available_channels[i] for i in selected_indices]}")
        else:
            # Use all channels (default behavior)
            avg_signal = np.mean(all_data, axis=0)

        
        # Split data into epochs.
        pre_epochs, stim_epochs, post_epochs = split_stim_epochs_3parts(raw, min_stim_duration_sec=MIN_STIM_DURATION_SEC)
        
        # Prepare lists for later averaging and concatenation.
        pre_epoch_signals, stim_epoch_signals, post_epoch_signals = [], [], []
        
        num_protocols = len(pre_epochs)
        logger.info(f"Computing individual PSDs for {num_protocols} protocols in file {base_name} using methods: {methods}")
        
        for i in range(num_protocols):
            pre_start, pre_end, prot_num = pre_epochs[i]
            stim_start, stim_end, _ = stim_epochs[i]
            post_start, post_end, _ = post_epochs[i]
            
            pre_start, pre_end = int(pre_start), int(pre_end)
            stim_start, stim_end = int(stim_start), int(stim_end)
            post_start, post_end = int(post_start), int(post_end)
            
            epoch_pre = avg_signal[pre_start:pre_end]
            epoch_stim = avg_signal[stim_start:stim_end]
            epoch_post = avg_signal[post_start:post_end]
            
            pre_epoch_signals.append(epoch_pre)
            stim_epoch_signals.append(epoch_stim)
            post_epoch_signals.append(epoch_post)
            
            # For each protocol, loop over chosen methods.
            for method in methods:
                psd, freqs = compute_psd_for_epoch(epoch_pre, sf, method=method, n_fft=FIXED_NFFT)
                prot_dir = os.path.join(file_out_dir, f"protocol_{prot_num}")
                os.makedirs(prot_dir, exist_ok=True)
                int_time = len(epoch_pre) / sf
                bin_res = freqs[1] - freqs[0] if len(freqs) > 1 else 0
                plot_and_save_psd(freqs, psd,
                                  f"Protocol {prot_num} Pre-stim ({method.capitalize()})",
                                  os.path.join(prot_dir, f"pre_{method}.png"),
                                  bin_resolution=bin_res,
                                  integration_time=int_time)
                save_psd_to_csv(freqs, psd, os.path.join(prot_dir, f"pre_{method}.csv"))
                
                psd, freqs = compute_psd_for_epoch(epoch_stim, sf, method=method, n_fft=FIXED_NFFT)
                int_time = len(epoch_stim) / sf
                bin_res = freqs[1] - freqs[0] if len(freqs) > 1 else 0
                plot_and_save_psd(freqs, psd,
                                  f"Protocol {prot_num} Stim ({method.capitalize()})",
                                  os.path.join(prot_dir, f"stim_{method}.png"),
                                  bin_resolution=bin_res,
                                  integration_time=int_time)
                save_psd_to_csv(freqs, psd, os.path.join(prot_dir, f"stim_{method}.csv"))
                
                psd, freqs = compute_psd_for_epoch(epoch_post, sf, method=method, n_fft=FIXED_NFFT)
                int_time = len(epoch_post) / sf
                bin_res = freqs[1] - freqs[0] if len(freqs) > 1 else 0
                plot_and_save_psd(freqs, psd,
                                  f"Protocol {prot_num} Post-stim ({method.capitalize()})",
                                  os.path.join(prot_dir, f"post_{method}.png"),
                                  bin_resolution=bin_res,
                                  integration_time=int_time)
                save_psd_to_csv(freqs, psd, os.path.join(prot_dir, f"post_{method}.csv"))
        
        # ----------------------------------------------------------------------------
        # Compute average PSDs from cropped epochs.
        min_len_pre = min(len(sig) for sig in pre_epoch_signals)
        min_len_stim = min(len(sig) for sig in stim_epoch_signals)
        min_len_post = min(len(sig) for sig in post_epoch_signals)
        logger.info(f"File {base_name}: Minimum epoch lengths: pre={min_len_pre}, stim={min_len_stim}, post={min_len_post}")
        
        pre_cropped = [sig[:min_len_pre] for sig in pre_epoch_signals]
        stim_cropped = [sig[:min_len_stim] for sig in stim_epoch_signals]
        post_cropped = [sig[:min_len_post] for sig in post_epoch_signals]
        
        epoch_types = {'pre': (pre_cropped, min_len_pre),
                       'stim': (stim_cropped, min_len_stim),
                       'post': (post_cropped, min_len_post)}
        
        for epoch_type, (epoch_list, common_len) in epoch_types.items():
            for method in methods:
                psd_list = []
                for sig in epoch_list:
                    psd, freqs = compute_psd_for_epoch(sig, sf, method=method, n_fft=HIGH_RES_NFFT)
                    psd_list.append(psd)
                avg_psd = np.mean(np.array(psd_list), axis=0)
                int_time = common_len / sf
                bin_res = freqs[1] - freqs[0] if len(freqs) > 1 else 0
                title = f"Average {epoch_type.capitalize()} PSD ({method.capitalize()})"
                fig_filepath = os.path.join(file_out_dir, f"avg_{epoch_type}_{method}.png")
                csv_filepath = os.path.join(file_out_dir, f"avg_{epoch_type}_{method}.csv")
                plot_and_save_psd(freqs, avg_psd, title, fig_filepath,
                                  bin_resolution=bin_res, integration_time=int_time)
                save_psd_to_csv(freqs, avg_psd, csv_filepath)
                logger.info(f"Saved average PSD ({epoch_type}, {method}) to {fig_filepath} and {csv_filepath}")
        
        # ----------------------------------------------------------------------------
        # Compute concatenated PSDs for each epoch type.
        for epoch_type, signals in [('pre', pre_epoch_signals), 
                                    ('stim', stim_epoch_signals), 
                                    ('post', post_epoch_signals)]:
            if signals:
                concat_signal = np.concatenate(signals)
                integration_time_concat = len(concat_signal) / sf
                for method in methods:
                    psd_concat, freqs_concat = compute_psd_for_epoch(concat_signal, sf, method=method, n_fft=HIGH_RES_NFFT)
                    bin_res_concat = freqs_concat[1] - freqs_concat[0] if len(freqs_concat) > 1 else 0
                    title = f"Concatenated {epoch_type.capitalize()} PSD ({method.capitalize()})"
                    fig_filepath = os.path.join(file_out_dir, f"concat_{epoch_type}_{method}.png")
                    csv_filepath = os.path.join(file_out_dir, f"concat_{epoch_type}_{method}.csv")
                    plot_and_save_psd(freqs_concat, psd_concat, title, fig_filepath,
                                      bin_resolution=bin_res_concat, integration_time=integration_time_concat)
                    save_psd_to_csv(freqs_concat, psd_concat, csv_filepath)
                    logger.info(f"Saved concatenated PSD ({epoch_type}, {method}) to {fig_filepath} and {csv_filepath}")
        
        logger.info(f"Finished processing file: {fname}")
    
    logger.info("High-resolution PSD computation and saving completed for all files.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Compute PSD for one or more EEG .set files using specified methods and channels."
    )
    parser.add_argument("--files", nargs='+', required=True,
                        help="Paths to one or more EEG .set files")
    parser.add_argument("--methods", nargs='+', default=["welch"],
                        choices=["welch", "multitaper", "fft"],
                        help="Method(s) for PSD calculation (default: welch)")
    parser.add_argument("--out", default=os.path.join(os.getcwd(), "psd_output"),
                        help="Output directory path (default: ./psd_output)")
    parser.add_argument("--channels", nargs='+', default=None,
                        help="Optional list of channel names to use (if not provided, average over all channels)")
    args = parser.parse_args()
    main(args)

