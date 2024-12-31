# wave_classification.py

import os
import json
import pandas as pd

def load_net_segmentation_json():
    """
    Load the net segmentation JSON file from the 'assets' folder.
    Assumes this script and the 'assets' folder are in the same directory hierarchy.

    Returns:
    - dict: Parsed JSON dictionary of net segmentations.
    """
    script_dir = os.path.dirname(__file__)  # Directory of this script
    json_path = os.path.join(script_dir, 'assets', 'net_segmentation.json')

    with open(json_path, 'r') as f:
        net_seg_data = json.load(f)

    return net_seg_data


def classify_wave_time(start_time, pre_stim_epochs, stim_epochs, post_stim_epochs):
    """
    Classify the wave by time into 'Pre-Stim', 'Stim', or 'Post-Stim', 
    and determine the protocol number if it falls within any epoch range.

    Parameters:
    - start_time (float): The start time of the wave.
    - pre_stim_epochs (list): List of (start, end, protocol) tuples for pre-stim epochs.
    - stim_epochs (list): List of (start, end, protocol) tuples for stim epochs.
    - post_stim_epochs (list): List of (start, end, protocol) tuples for post-stim epochs.

    Returns:
    - tuple: (classification_label, protocol_number) or ('Unknown', None) if not classified.
    """
    for epochs, label in [
        (pre_stim_epochs, 'Pre-Stim'),
        (stim_epochs, 'Stim'),
        (post_stim_epochs, 'Post-Stim')
    ]:
        for start, end, protocol in epochs:
            if start <= start_time <= end:
                return label, protocol

    return 'Unknown', None


def classify_wave_region(channel, net_seg_data):
    """
    Classify the wave by channel location using the net_segmentation.json data.
    The JSON structure is like:
    {
        "Left Frontal": [
            ["E032","E037","E046", ... ]
        ],
        "Right Frontal": [
            ["E025","E018","E010", ... ]
        ],
        "Parietal": [
            ["E084","E085","E086", ...]
        ]
    }

    Parameters:
    - channel (str): The channel name (e.g., "E032").
    - net_seg_data (dict): Dictionary loaded from net_segmentation.json.

    Returns:
    - str: "L_frontal", "R_frontal", "Posterior", or "Unclassified".
    """
    for region_name, list_of_channel_groups in net_seg_data.items():
        # Each value is a list of lists, e.g. [["E032", "E037", ...], ...]
        for channel_group in list_of_channel_groups:
            if channel in channel_group:
                if region_name == "Left Frontal":
                    return "L_frontal"
                elif region_name == "Right Frontal":
                    return "R_frontal"
                elif region_name == "Parietal":
                    return "Posterior"

    return "Unclassified"


def classify_and_filter_waves(df, pre_stim_epochs, stim_epochs, post_stim_epochs):
    """
    Classify each wave both by its start time (Pre-Stim, Stim, Post-Stim) 
    and by region (using the net_segmentation.json), then assign the protocol number.

    Parameters:
    - df (pd.DataFrame): DataFrame containing detected slow waves.
    - pre_stim_epochs (list): List of (start, end, protocol) tuples for pre-stim epochs.
    - stim_epochs (list): List of (start, end, protocol) tuples for stim epochs.
    - post_stim_epochs (list): List of (start, end, protocol) tuples for post-stim epochs.

    Returns:
    - df_sorted (pd.DataFrame): DataFrame containing classified and filtered waves.
    """
    # Load net segmentation data
    net_seg_data = load_net_segmentation_json()

    # 1) Time-based classification and protocol assignment
    time_and_protocol = df['Start'].apply(
        lambda start_time: classify_wave_time(
            start_time,
            pre_stim_epochs, stim_epochs, post_stim_epochs
        )
    )
    df['Classification'], df['Protocol Number'] = zip(*time_and_protocol)

    # 2) Region-based classification
    df['Region_Classification'] = df['Channel'].apply(
        lambda ch: classify_wave_region(ch, net_seg_data)
    )

    # Filter out waves that have time classification = 'Unknown'
    df_filtered = df[df['Classification'] != 'Unknown'].reset_index(drop=True)

    # Create a unique name for each slow wave
    df_filtered['Classification'] = df_filtered['Classification'] \
        .str.lower() \
        .str.replace(' ', '-')
    df_filtered['Slow_Wave_Name'] = (
        'proto' + df_filtered['Protocol Number'].astype(int).astype(str) + '_' +
        df_filtered['Classification'] + '_sw' +
        (df_filtered.groupby(['Protocol Number', 'Classification']).cumcount() + 1).astype(str)
    )

    # Sort the DataFrame by protocol, time classification, and slow wave name
    classification_order = ['pre-stim', 'stim', 'post-stim']
    df_filtered['Classification'] = pd.Categorical(
        df_filtered['Classification'],
        categories=classification_order,
        ordered=True
    )
    df_sorted = df_filtered.sort_values(by=['Protocol Number', 'Classification', 'Slow_Wave_Name'])

    return df_sorted
