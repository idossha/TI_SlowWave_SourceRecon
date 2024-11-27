import os
from mne.viz import plot_sensors
import matplotlib.pyplot as plt

def plot_net_coverage(raw, output_file):
    """
    Plot the net coverage of electrodes and save the figure as a .png file.
    
    Parameters:
        raw (mne.io.Raw): The raw EEG data object.
        output_file (str): Path to save the output .png file.
    """
    print("Plotting net coverage of electrodes...")
    fig = plot_sensors(raw.info, show=False)
    fig.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Net coverage plot saved to {output_file}")

