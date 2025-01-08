
# spectrogram_plot.py

import os
import logging
import mne
import yasa
import matplotlib.pyplot as plt

# Create a module-level logger
logger = logging.getLogger(__name__)

def plot_spectrogram_with_annotations(raw, output_dir, preferred_channel_indices=[80, 89, 79, 44]):
    """
    Plot and save a spectrogram for the given EEG data with annotations overlaid,
    specifically highlighting "stim start" or "stim end" events.
    The plot is saved as 'spectrogram.png' and includes the channel name in the title.

    Parameters:
        raw (mne.io.Raw): The raw EEG data object.
        output_dir (str): Directory to save the spectrogram plot.
        preferred_channel_indices (list): List of preferred channel indices to use.

    Returns:
        None
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Define channel names from preferred indices
    channels = raw.info['ch_names']

    # Select the first available preferred channel
    selected_channel = None
    for idx in preferred_channel_indices:
        if idx < len(channels):
            selected_channel = channels[idx]
            break

    # If no preferred channel is found, use the first channel
    if selected_channel is None:
        selected_channel = channels[0]

    logger.info(f"Selected Channel for spectrogram: {selected_channel}")

    # Extract the data for the selected channel
    data = raw.get_data(picks=selected_channel).flatten()

    # Generate the spectrogram
    fig = yasa.plot_spectrogram(
        data,
        sf=raw.info['sfreq'],
        fmin=0.5, fmax=25, trimperc=2.5, cmap='RdBu_r', vmin=None, vmax=None,
        figsize=(15, 7)
    )

    # Access the spectrogram axes (assuming it's the first and only axes)
    ax = fig.axes[0]

    # Set a meaningful title including the channel name
    ax.set_title(f"Spectrogram - {selected_channel}", fontsize=10)

    # Overlay annotations that are "stim start" or "stim end"
    annotations = raw.annotations
    found_stim = False
    if len(annotations):
        for annot in annotations:
            description = annot['description'].lower()
            if description in ["stim start", "stim end"]:
                found_stim = True
                # Convert onset from seconds to hours for the spectrogram's x-axis
                onset_hr = annot['onset'] / 3600
                ax.axvline(x=onset_hr, color='yellow', alpha=0.8, linestyle='--', linewidth=2)
                ax.plot(onset_hr, ax.get_ylim()[1], marker='v', color='red', markersize=10)
                logger.info(f"Added stim marker for annotation: '{annot['description']}' at {annot['onset']}s")

        if found_stim:
            ax.legend(['Stim events'], loc='upper right')
        else:
            logger.info("No 'stim start' or 'stim end' annotations found to overlay.")

    # Save the spectrogram plot (always named "spectrogram.png")
    spectrogram_path = os.path.join(output_dir, 'spectrogram.png')
    fig.savefig(spectrogram_path, dpi=300, bbox_inches='tight')
    logger.info(f"Spectrogram saved to {spectrogram_path}")

    # Close the figure to free up memory
    plt.close(fig)

