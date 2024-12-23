import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mne.viz import plot_topomap
import logging

# Configure logging to print debug information to the console
logging.basicConfig(
    level=logging.DEBUG,  # Set logging to DEBUG level for verbose output
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Ensure logs are printed to the console
)

def generate_topoplots(raw, df_filtered, output_dir):
    """
    Generate MNE-style topoplots for averaged EEG voltages at NegPeak times
    within each protocol and across all protocols.

    Parameters:
    - raw: mne.io.Raw object containing EEG data.
    - df_filtered: DataFrame with 'IdxChannel', 'NegPeak', and 'Protocol Number'.
    - output_dir: Directory to save plots.
    """
    try:
        logging.info("Starting topoplot generation.")
        
        # Ensure the output directory exists
        logging.debug("Creating output directory if it doesn't exist.")
        os.makedirs(output_dir, exist_ok=True)

        # Extract channel names and positions from the raw object
        logging.debug("Extracting channel names and positions from the raw object.")
        ch_names = raw.info['ch_names']
        pos = np.array([ch['loc'][:2] for ch in raw.info['chs'] if not np.isnan(ch['loc'][:2]).any()])
        n_channels = len(ch_names)

        logging.debug(f"Number of channels: {n_channels}")
        logging.debug(f"Channel positions extracted: {pos}")

        # Verify required columns in df_filtered
        required_columns = {'NegPeak', 'Protocol Number'}
        if not required_columns.issubset(df_filtered.columns):
            logging.error(f"df_filtered must contain the columns: {required_columns}")
            raise ValueError(f"df_filtered must contain the columns: {required_columns}")

        # Convert NegPeak times to sample indices
        logging.debug("Converting NegPeak times to sample indices.")
        df_filtered['SampleIndex'] = (df_filtered['NegPeak'] * raw.info['sfreq']).astype(int)

        # Group data by Protocol Number
        protocols = df_filtered['Protocol Number'].unique()
        logging.info(f"Unique protocols found: {protocols}")

        # Global min and max for color scaling
        global_min, global_max = float('inf'), float('-inf')

        # Collect averaged data for each protocol
        protocol_topomaps = {}

        for protocol in protocols:
            logging.debug(f"Processing protocol: {protocol}")
            protocol_data = df_filtered[df_filtered['Protocol Number'] == protocol]

            # Initialize array to store the voltage data
            eeg_data = np.zeros((len(protocol_data), n_channels))

            # Extract EEG data at NegPeak times
            for i, row in protocol_data.iterrows():
                sample_idx = row['SampleIndex']
                if 0 <= sample_idx < raw._data.shape[1]:
                    eeg_data[i, :] = raw._data[:, sample_idx]
                else:
                    logging.warning(f"Sample index {sample_idx} is out of bounds for protocol {protocol}.")

            # Average EEG data across all NegPeak times for the protocol
            protocol_avg = eeg_data.mean(axis=0)
            protocol_topomaps[protocol] = protocol_avg

            # Update global min and max
            global_min = min(global_min, protocol_avg.min())
            global_max = max(global_max, protocol_avg.max())

        # Generate topoplots for each protocol
        for protocol, protocol_avg in protocol_topomaps.items():
            logging.debug(f"Generating topoplot for protocol {protocol}.")
            fig, ax = plt.subplots(figsize=(6, 6))
            plot_topomap(
                protocol_avg, pos, axes=ax, cmap="viridis", show=False,
                sphere="auto", vmin=global_min, vmax=global_max, extrapolate='head', contours=0
            )
            plt.colorbar(ax.collections[0], ax=ax, orientation="horizontal", pad=0.05)
            plt.title(f"Protocol {protocol} Average EEG Topoplot")
            protocol_file = os.path.join(output_dir, f'protocol_{protocol}_topoplot.png')
            plt.savefig(protocol_file, dpi=300)
            plt.close(fig)
            logging.info(f"Saved protocol {protocol} topoplot to {protocol_file}")

        # Compute overall average topoplot across all protocols
        overall_avg = np.mean(list(protocol_topomaps.values()), axis=0)
        logging.debug("Generating overall average topoplot.")

        # Generate overall topoplot
        fig, ax = plt.subplots(figsize=(6, 6))
        plot_topomap(
            overall_avg, pos, axes=ax, cmap="viridis", show=False,
            sphere="auto", vmin=global_min, vmax=global_max, extrapolate='head', contours=0
        )
        plt.colorbar(ax.collections[0], ax=ax, orientation="horizontal", pad=0.05)
        plt.title("Overall Average EEG Topoplot")
        overall_file = os.path.join(output_dir, 'overall_topoplot.png')
        plt.savefig(overall_file, dpi=300)
        plt.close(fig)
        logging.info(f"Saved overall average topoplot to {overall_file}")

        logging.info("Topoplot generation completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred during topoplot generation: {e}", exc_info=True)
        raise

# Example usage:
from mne import create_info
from mne.io import RawArray

# Dummy raw object for testing
n_channels = 5
sfreq = 256  # Sampling frequency
ch_names = [f"Ch{i}" for i in range(n_channels)]
info = create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")
data = np.random.rand(n_channels, sfreq * 10)  # 10 seconds of random EEG data
raw = RawArray(data, info)

# Example DataFrame with 'NegPeak' (times in seconds) and 'Protocol Number'
df_filtered = pd.DataFrame({
    'NegPeak': [1.0, 2.5, 4.0, 1.5, 3.0],
    'Protocol Number': [1, 1, 1, 2, 2]
})

output_dir = "eeg_topoplots"
generate_topoplots(raw, df_filtered, output_dir)
