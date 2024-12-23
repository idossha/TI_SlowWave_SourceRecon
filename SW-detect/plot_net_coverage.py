
# plot_net_coverage.py

import os
import matplotlib.pyplot as plt
import mne

def plot_net_coverage(raw, output_dir):
    """
    Plot the net coverage of electrodes in 2D and 3D and save the figures as .png files.
    Only electrodes present in raw.info.ch_names are plotted.

    Parameters:
        raw (mne.io.Raw): The raw EEG data object.
        output_dir (str): Directory to save the output plots.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Plot 2D sensors
    print("Plotting 2D net coverage...")
    fig_2d = raw.plot_sensors(kind='topomap', show_names=True, show=False)
    output_file_2d = os.path.join(output_dir, "net_coverage_2D.png")
    fig_2d.savefig(output_file_2d, dpi=300, bbox_inches='tight')
    plt.close(fig_2d)
    print(f"2D net coverage plot saved to {output_file_2d}")

    # Plot 3D sensors
    print("Plotting 3D net coverage...")
    fig_3d = raw.plot_sensors(kind='3d', show_names=True, show=False)
    # Adjust the view angle for better visualization
    ax_3d = fig_3d.axes[0]
    ax_3d.view_init(azim=50, elev=15)
    output_file_3d = os.path.join(output_dir, "net_coverage_3D.png")
    fig_3d.savefig(output_file_3d, dpi=300, bbox_inches='tight')
    plt.close(fig_3d)
    print(f"3D net coverage plot saved to {output_file_3d}")
