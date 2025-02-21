
import mne
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# List of files
files = [
    '/Volumes/CSC-Ido/Analyze/101/N1/Strength_101_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/102/N1/Strength_102_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/107/N1/Strength_107_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/108/N1/Strength_108_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/109/N1/Strength_109_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/110/N1/Strength_110_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/111/N1/Strength_111_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/112/N1/Strength_112_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/114/N1/Strength_114_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/115/N1/Strength_115_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/116/N1/Strength_116_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/117/N1/Strength_117_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/119/N1/Strength_119_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/120/N1/Strength_120_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/121/N1/Strength_121_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/122/N1/Strength_122_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/127/N1/Strength_127_N1_forSW.set',
    '/Volumes/CSC-Ido/Analyze/132/N1/Strength_132_N1_forSW.set'
]

# Output directory
output_dir = '/Users/idohaber/Desktop/topotools_jan21'
os.makedirs(output_dir, exist_ok=True)

# Function to normalize counts using logarithmic scale
def normalize_counts_log(counts):
    return np.log1p(np.maximum(0, counts))  # log1p ensures no issues with zero counts

# Function to filter electrodes with valid data
def filter_electrodes(channel_names, counts, classification_filter):
    """
    Filter electrodes based on the counts and classification.
    
    Parameters:
    - channel_names: List of channel names.
    - counts: Array of counts for each channel.
    - classification_filter: Boolean array where True indicates electrodes to keep.
    
    Returns:
    - filtered_channel_names: List of filtered channel names.
    - filtered_counts: Array of counts for the filtered channels.
    """
    filtered_channel_names = [ch for ch, keep in zip(channel_names, classification_filter) if keep]
    filtered_counts = np.array([count for count, keep in zip(counts, classification_filter) if keep])
    return filtered_channel_names, filtered_counts

# Loop through files
for fname in files:
    print(f"Processing file: {fname}")

    # Extract subject and night from the file path
    path_parts = fname.split('/')
    subject = path_parts[-3]  # Get the subject (e.g., '101')
    night = path_parts[-2]    # Get the night (e.g., 'N1')

    # Construct the path to the corresponding CSV file
    csv_path = f'/volumes/csc-ido/analyze/{subject}/{night}/output/strength_{subject}_{night}_forsw/filtered_epochs_500ms_most_negative.csv'

    # Check if the CSV file exists
    if not os.path.exists(csv_path):
        print(f"CSV file not found for {fname}. Skipping...")
        continue

    # Load the raw EEG data
    raw = mne.io.read_raw_eeglab(fname, preload=True)

    # Ensure digitization points or montage is available
    if raw.info['dig'] is None:
        print("No digitization points found! Skipping...")
        continue

    # Load the corresponding CSV file
    df = pd.read_csv(csv_path)

    # Exclude rows with 'Region_Classification' == 'Unclassified'
    df = df[df['Region_Classification'] != 'Unclassified']

    # Split data by classification
    overall_count = df['Channel'].value_counts()
    stim_count = df[df['Classification'] == 'stim']['Channel'].value_counts()
    pre_stim_count = df[df['Classification'] == 'pre-stim']['Channel'].value_counts()
    post_stim_count = df[df['Classification'] == 'post-stim']['Channel'].value_counts()

    # Calculate differences
    stim_minus_pre = stim_count.subtract(pre_stim_count, fill_value=0)
    print(stim_minus_pre)
    post_minus_pre = post_stim_count.subtract(pre_stim_count, fill_value=0)

    # Map counts to channels in the raw object
    channel_names = raw.info['ch_names']
    overall_counts = np.array([overall_count.get(ch, 0) for ch in channel_names])
    stim_minus_pre_counts = np.array([stim_minus_pre.get(ch, 0) for ch in channel_names])
    print(stim_minus_pre_counts)
    post_minus_pre_counts = np.array([post_minus_pre.get(ch, 0) for ch in channel_names])

    # Normalize counts using logarithmic scale
    overall_counts_normalized = normalize_counts_log(overall_counts)
    stim_minus_pre_counts_normalized = normalize_counts_log(stim_minus_pre_counts)
    post_minus_pre_counts_normalized = normalize_counts_log(post_minus_pre_counts)

    # Create a filter for electrodes with data
    overall_filter = overall_counts > 0

    # Filter channels and counts
    filtered_channel_names, filtered_overall_counts = filter_electrodes(
        channel_names, overall_counts_normalized, overall_filter
    )
    _, filtered_stim_minus_pre_counts = filter_electrodes(
        channel_names, stim_minus_pre_counts_normalized, overall_filter
    )
    _, filtered_post_minus_pre_counts = filter_electrodes(
        channel_names, post_minus_pre_counts_normalized, overall_filter
    )

    # Get positions for filtered channels
    montage = raw.get_montage()
    if montage is not None:
        pos = montage.get_positions()['ch_pos']
        pos_filtered = np.array(
            [pos[ch] if ch in pos else [np.nan, np.nan, np.nan] for ch in filtered_channel_names]
        )[:, :2]  # Use only x, y for topomap plotting
    else:
        print("No montage available. Setting a standard montage.")
        montage = mne.channels.make_standard_montage('standard_1020')
        raw.set_montage(montage)
        pos = montage.get_positions()['ch_pos']
        pos_filtered = np.array(
            [pos[ch] if ch in pos else [np.nan, np.nan, np.nan] for ch in filtered_channel_names]
        )[:, :2]

    # Create topoplots
    plots = {
        "filtered_overall_count": filtered_overall_counts,
        "stim_minus_pre": filtered_stim_minus_pre_counts,
        "post_minus_pre": filtered_post_minus_pre_counts
    }

    for plot_name, counts in plots.items():
        fig, ax = plt.subplots(figsize=(8, 8))
        mne.viz.plot_topomap(counts, pos_filtered, axes=ax, sphere=None, show=False, cmap='RdBu_r', image_interp='linear')

        # Save the plot with a unique name
        output_file = os.path.join(output_dir, f"{plot_name}_{subject}_{night}.png")
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"{plot_name} topoplot saved to {output_file}")

