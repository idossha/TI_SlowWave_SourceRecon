
import os
import mne
import yasa
import matplotlib.pyplot as plt

def plot_spectrogram_with_annotations(raw, output_dir, preferred_channel_indices=[80, 89, 79, 44]):
    """
    Plot and save a spectrogram for the given EEG data with annotations overlaid.

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

    # Extract the data for the selected channel
    data = raw.get_data(picks=selected_channel).flatten()

    # Log the selected channel
    print(f"Selected Channel: {selected_channel}")

    # Generate the spectrogram
    fig = yasa.plot_spectrogram(
        data,
        sf=raw.info['sfreq'],
        title=f"Spectrogram - {selected_channel}",
        figsize=(15, 7)
    )

    # Overlay annotations
    annotations = raw.annotations
    if len(annotations):
        for annot in annotations:
            onset_sec = annot['onset'] / 3600  # Convert to hours for the x-axis
            # Add a transparent vertical band for the event
            plt.axvline(x=onset_sec, color='yellow', alpha=1, linestyle='--', linewidth=2)
            # Add a marker at the top
            plt.plot(onset_sec, plt.ylim()[1], marker='v', color='red', markersize=10)
        plt.legend(['Stim events'], loc='upper right')

    # Save the spectrogram plot
    spectrogram_path = os.path.join(output_dir, f'spectrogram_{selected_channel}.png')
    fig.savefig(spectrogram_path, dpi=300, bbox_inches='tight')

    # Close the figure
    plt.close(fig)
