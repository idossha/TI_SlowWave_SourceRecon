
# wave_classification.py

import logging
import os
import json
import pandas as pd

# Create a module-level logger
logger = logging.getLogger(__name__)

def load_net_segmentation_json():
    """
    Load the net segmentation JSON file from the 'assets' folder.
    Assumes this script and the 'assets' folder are in the same directory hierarchy.

    Returns:
    - dict: Parsed JSON dictionary of net segmentations.
    """
    logger.info("Loading net segmentation JSON file.")
    
    try:
        script_dir = os.path.dirname(__file__)  # Directory of this script
        json_path = os.path.join(script_dir, 'assets', 'net_segmentation.json')
        
        if not os.path.exists(json_path):
            logger.error(f"Net segmentation JSON file not found at path: {json_path}")
            raise FileNotFoundError(f"Net segmentation JSON file not found at path: {json_path}")
        
        with open(json_path, 'r') as f:
            net_seg_data = json.load(f)
        
        logger.info(f"Net segmentation data loaded successfully from {json_path}.")
        return net_seg_data

    except Exception as e:
        logger.error(f"An error occurred while loading net segmentation JSON: {e}", exc_info=True)
        raise  # Re-raise the exception to allow upstream handling


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
    logger.debug(f"Classifying wave at start_time={start_time}s.")
    
    for epochs, label in [
        (pre_stim_epochs, 'Pre-Stim'),
        (stim_epochs, 'Stim'),
        (post_stim_epochs, 'Post-Stim')
    ]:
        for start, end, protocol in epochs:
            if start <= start_time <= end:
                logger.debug(f"Wave at {start_time}s classified as '{label}' under protocol {protocol}.")
                return label, protocol

    logger.debug(f"Wave at {start_time}s could not be classified and is labeled as 'Unknown'.")
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
    logger.debug(f"Classifying wave region for channel '{channel}'.")
    
    for region_name, list_of_channel_groups in net_seg_data.items():
        for channel_group in list_of_channel_groups:
            if channel in channel_group:
                classification = ""
                if region_name == "Left Frontal":
                    classification = "L_frontal"
                elif region_name == "Right Frontal":
                    classification = "R_frontal"
                elif region_name == "Parietal":
                    classification = "Posterior"
                else:
                    classification = "Unclassified"
                
                logger.debug(f"Channel '{channel}' classified as '{classification}'.")
                return classification

    logger.debug(f"Channel '{channel}' could not be classified and is labeled as 'Unclassified'.")
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
    logger.info("Starting wave classification and filtering process.")

    try:
        # Load net segmentation data
        net_seg_data = load_net_segmentation_json()
    
        # 1) Time-based classification and protocol assignment
        logger.info("Classifying waves based on time and assigning protocol numbers.")
        time_and_protocol = df['Start'].apply(
            lambda start_time: classify_wave_time(
                start_time,
                pre_stim_epochs, stim_epochs, post_stim_epochs
            )
        )
        df['Classification'], df['Protocol Number'] = zip(*time_and_protocol)
        logger.debug("Time-based classification and protocol assignment completed.")
    
        # 2) Region-based classification
        logger.info("Classifying waves based on region.")
        df['Region_Classification'] = df['Channel'].apply(
            lambda ch: classify_wave_region(ch, net_seg_data)
        )
        logger.debug("Region-based classification completed.")
    
        # Filter out waves that have time classification = 'Unknown'
        initial_count = len(df)
        df_filtered = df[df['Classification'] != 'Unknown'].reset_index(drop=True)
        filtered_count = len(df_filtered)
        logger.info(f"Filtered out {initial_count - filtered_count} waves labeled as 'Unknown'.")
    
        # Create a unique name for each slow wave
        logger.info("Creating unique names for each slow wave.")
        df_filtered['Classification'] = df_filtered['Classification'] \
            .str.lower() \
            .str.replace(' ', '-', regex=False)
        df_filtered['Slow_Wave_Name'] = (
            'proto' + df_filtered['Protocol Number'].astype(int).astype(str) + '_' +
            df_filtered['Classification'] + '_sw' +
            (df_filtered.groupby(['Protocol Number', 'Classification']).cumcount() + 1).astype(str)
        )
        logger.debug("Unique slow wave names created.")
    
        # Sort the DataFrame by protocol, time classification, and slow wave name
        classification_order = ['pre-stim', 'stim', 'post-stim']
        df_filtered['Classification'] = pd.Categorical(
            df_filtered['Classification'],
            categories=classification_order,
            ordered=True
        )
        df_sorted = df_filtered.sort_values(by=['Protocol Number', 'Classification', 'Slow_Wave_Name']).reset_index(drop=True)
        logger.info("DataFrame sorted by Protocol Number, Classification, and Slow_Wave_Name.")
    
        logger.info("Wave classification and filtering process completed successfully.")
        return df_sorted

    except Exception as e:
        logger.error(f"An error occurred during wave classification and filtering: {e}", exc_info=True)
        raise  # Re-raise the exception to allow upstream handling

