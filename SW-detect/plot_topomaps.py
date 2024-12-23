
# plot_topomaps.py

import os
import mne
import numpy as np
import matplotlib.pyplot as plt
import logging

def load_data(fname):
    """
    Load EEG data from an EEGLAB .set file.

    Parameters:
    - fname: str, path to the .set file.

    Returns:
    - raw: mne.io.Raw, raw EEG data.
    """
    # Load the data
    raw = mne.io.read_raw_eeglab(fname, preload=True)
    return raw

def get_channel_unit(raw):
    """
    Determine the unit of measurement based on the channel types.

    Parameters:
    - raw: mne.io.Raw
        The Raw object containing channel information.

    Returns:
    - unit_str: str
        A string representing the unit for the colorbar.
    """
    # Define a mapping from channel type to unit
    ch_type_unit_map = {
        'eeg': 'µV',       # Microvolts
        'meg': 'fT',       # FemtoTesla
        'grad': 'fT/cm',   # Example unit for gradiometers
        'mag': 'fT',       # Example unit for magnetometers
        'eog': 'µV',       # Electrooculography
        'ecg': 'µV',       # Electrocardiography
        'emg': 'µV',       # Electromyography
        # Add more mappings as needed
    }

    # Extract unique channel types present in the data
    unique_ch_types = set(raw.get_channel_types())

    # Assume all channels have the same unit; if not, default to 'AU'
    if len(unique_ch_types) == 1:
        ch_type = unique_ch_types.pop()
        unit_str = ch_type_unit_map.get(ch_type, 'AU')  # 'AU' for arbitrary units if unknown
    else:
        unit_str = 'AU'  # Use 'AU' if multiple channel types are present

    return unit_str

def plot_topomaps(set_file, output_dir, suffix=''):
    """
    Create and save topographical plots for each negative peak event,
    and an average topomap across all negative peak events.

    Parameters:
    - set_file: str, path to the annotated EEGLAB .set file.
    - output_dir: str, path to the output directory where plots will be saved.
    - suffix: str, additional suffix to differentiate output files.

    Returns:
    - None
    """
    logging.info(f"plot_topomaps called with set_file: {set_file}, output_dir: {output_dir}, suffix: {suffix}")

    # Load the raw data
    try:
        raw = load_data(set_file)
        logging.info(f"Loaded raw data from {set_file}.")
    except Exception as e:
        logging.error(f"Failed to load raw data from {set_file}: {e}")
        return

    # Determine the unit for the colorbar
    unit_str = get_channel_unit(raw)
    logging.info(f"Data unit determined as: {unit_str}")

    # Ensure the raw data has a montage
    if raw.get_montage() is None:
        try:
            # Setting a standard 10-20 montage; adjust as needed
            montage = mne.channels.make_standard_montage('standard_1020')
            raw.set_montage(montage)
            logging.info("Standard 10-20 montage set for raw data.")
        except Exception as e:
            logging.error(f"Failed to set montage: {e}")
            return
    else:
        logging.info("Montage already set for raw data.")

    # Ensure output directory exists
    topomap_dir = os.path.join(output_dir, f'topomaps_{suffix}')
    os.makedirs(topomap_dir, exist_ok=True)
    logging.info(f"Topomap output directory: {topomap_dir}")

    # Extract annotations labeled as 'NegPeak'
    neg_peak_annotations = [annot for annot in raw.annotations if 'NegPeak' in annot['description']]
    logging.info(f"Found {len(neg_peak_annotations)} negative peak annotations.")

    if not neg_peak_annotations:
        logging.warning("No negative peak annotations found. No topoplots will be generated.")
        return

    # Initialize a list to collect data for averaging
    all_data_at_peak = []

    for idx, annot in enumerate(neg_peak_annotations, start=1):
        peak_time = annot['onset']  # Time in seconds
        logging.debug(f"Processing NegPeak annotation {idx} at {peak_time:.2f}s.")

        # Convert peak_time to sample index
        peak_sample = int(raw.time_as_index(peak_time)[0])
        
        # Ensure peak_sample is within the data range
        if peak_sample < 0 or peak_sample >= raw.n_times:
            logging.error(f"Peak time {peak_time:.2f}s is out of data range.")
            continue

        # Extract data at the peak sample
        try:
            data_at_peak = raw.get_data(time=peak_time).flatten()
            all_data_at_peak.append(data_at_peak)
            logging.debug(f"Extracted data at peak {idx}: shape {data_at_peak.shape}.")
        except Exception as e:
            logging.error(f"Error extracting data at peak {idx} ({peak_time:.2f}s): {e}")
            continue

        # Determine appropriate color scaling using percentile-based method
        lower_percentile = 2
        upper_percentile = 98
        try:
            vmin, vmax = np.percentile(data_at_peak, [lower_percentile, upper_percentile])
            # Ensure symmetric limits around zero
            max_abs = max(abs(vmin), abs(vmax))
            vlim = (-max_abs, max_abs)
            logging.debug(f"Setting color limits for event {idx}: vlim={vlim} {unit_str}")
        except Exception as e:
            logging.error(f"Error computing percentiles for event {idx}: {e}")
            continue

        # Plot the topomap
        fig, ax = plt.subplots(figsize=(6, 5))
        try:
            im, _ = mne.viz.plot_topomap(
                data_at_peak,
                raw.info,
                axes=ax,
                show=False,
                cmap='RdBu_r',
                sensors=True,
                contours=0,
                vlim=vlim  # Use vlim as a tuple
            )

            # Add colorbar with units
            cbar = plt.colorbar(im, ax=ax, shrink=0.7)
            cbar.set_label(f'Amplitude ({unit_str})', fontsize=10)

            fig.suptitle(f"Topomap at {peak_time:.2f}s (Event {idx})", fontsize=12)

            # Generate a unique filename
            # Assuming description format: 'NegPeak_<additional_info>'
            description_parts = annot['description'].split('_')
            wave_name = '_'.join(description_parts[1:]) if len(description_parts) > 1 else f'NegPeak_{idx}'
            plot_filename = f"NegPeak_{wave_name}_topomap_{idx}.png"
            plot_path = os.path.join(topomap_dir, plot_filename)

            # Save the figure
            fig.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            logging.info(f"Saved topomap for event {idx} at {peak_time:.2f}s to {plot_path}.")
        except Exception as e:
            logging.error(f"Error plotting topomap for event {idx} at {peak_time:.2f}s: {e}")
            plt.close(fig)
            continue

    # Compute and plot the average topomap
    if all_data_at_peak:
        logging.info(f"Computing average topomap across {len(all_data_at_peak)} events.")
        try:
            # Convert list to NumPy array and compute the mean
            average_data = np.mean(all_data_at_peak, axis=0)

            # Determine appropriate color scaling for the average topomap
            lower_percentile = 2
            upper_percentile = 98
            vmin, vmax = np.percentile(average_data, [lower_percentile, upper_percentile])
            # Ensure symmetric limits around zero
            max_abs = max(abs(vmin), abs(vmax))
            vlim_avg = (-max_abs, max_abs)
            logging.debug(f"Setting color limits for average topomap: vlim={vlim_avg} {unit_str}")

            # Plot the average topomap
            fig_avg, ax_avg = plt.subplots(figsize=(6, 5))
            im_avg, _ = mne.viz.plot_topomap(
                average_data,
                raw.info,
                axes=ax_avg,
                show=False,
                cmap='RdBu_r',
                sensors=True,
                contours=0,
                vlim=vlim_avg  # Use vlim as a tuple
            )

            # Add colorbar with units
            cbar_avg = plt.colorbar(im_avg, ax=ax_avg, shrink=0.7)
            cbar_avg.set_label(f'Amplitude ({unit_str})', fontsize=10)

            fig_avg.suptitle(f"Average Topomap Across {len(all_data_at_peak)} Events", fontsize=12)

            # Generate a filename for the average topomap
            plot_filename_avg = f"Average_NegPeak_Topomap.png"
            plot_path_avg = os.path.join(topomap_dir, plot_filename_avg)

            # Save the average topomap figure
            fig_avg.savefig(plot_path_avg, dpi=300, bbox_inches='tight')
            plt.close(fig_avg)
            logging.info(f"Saved average topomap to {plot_path_avg}.")
        except Exception as e:
            logging.error(f"Error computing or plotting average topomap: {e}")
    else:
        logging.warning("No data available to compute average topomap.")

    logging.info(f"All topoplots saved to {topomap_dir}.")

# Example usage:
if __name__ == "__main__":
    import logging

    # Configure logging to display info and higher level messages
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Define paths
    set_file_path = '/Users/idohaber/Data/116/N1/output/Strength_116_N1_forSW/annotated_raw_filtered.set'
    output_directory = '/Users/idohaber/Data/116/N1/output/Strength_116_N1_forSW'
    file_suffix = 'filtered'  # Optional

    # Plot and save topomaps, including the average topomap
    plot_topomaps(set_file=set_file_path, output_dir=output_directory, suffix=file_suffix)

