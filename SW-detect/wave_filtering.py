
# wave_filtering.py

import logging
import pandas as pd
import os

# Create a module-level logger
logger = logging.getLogger(__name__)

def filter_and_save_epochs(df_sorted, output_dir):
    """
    Filter epochs based on specified configurations and save the filtered DataFrames to CSV files.

    Parameters:
    - df_sorted: pd.DataFrame, DataFrame containing sorted and classified slow waves.
    - output_dir: str, path to the output directory where filtered CSV files will be saved.

    Returns:
    - filtered_files: list of tuples, each containing (filename, filtered_epochs_df).
    """
    logger.info("Starting filter and save epochs process.")

    try:
        filtered_files = []
        configurations = [
            {'window_size': 0.5, 'pick_most_negative': False},
            {'window_size': 0.5, 'pick_most_negative': True},
            {'window_size': 1.0, 'pick_most_negative': False},
            {'window_size': 1.0, 'pick_most_negative': True},
        ]

        logger.debug(f"Total configurations to apply: {len(configurations)}")

        for config in configurations:
            window_size = config['window_size']
            pick_most_negative = config['pick_most_negative']
            logger.info(f"Applying filter with window_size={window_size}s and pick_most_negative={pick_most_negative}.")

            filtered_epochs_df = filter_epochs(df_sorted, window_size, pick_most_negative)
            logger.debug(f"Filtered epochs count: {len(filtered_epochs_df)} for window_size={window_size}s and pick_most_negative={pick_most_negative}.")

            # Determine filename based on parameters
            window_ms = int(window_size * 1000)
            suffix = "most_negative" if pick_most_negative else "first"
            filename = f'filtered_epochs_{window_ms}ms_{suffix}.csv'
            output_path = os.path.join(output_dir, filename)

            # Ensure the output directory exists
            os.makedirs(output_dir, exist_ok=True)

            # Save the filtered DataFrame to CSV
            filtered_epochs_df.to_csv(output_path, index=False)
            logger.info(f"Filtered epochs saved to {output_path}.")

            filtered_files.append((filename, filtered_epochs_df))

        logger.info("Filter and save epochs process completed successfully.")
        return filtered_files

    except Exception as e:
        logger.error(f"An error occurred during filter and save epochs process: {e}", exc_info=True)
        raise  # Re-raise the exception to allow upstream handling


def filter_epochs(df, window_size, pick_most_negative):
    """
    Filter epochs based on a time window and selection method.

    Parameters:
    - df: pd.DataFrame, DataFrame containing sorted and classified slow waves.
    - window_size: float, window size in seconds to filter waves.
    - pick_most_negative: bool, if True, select the most negative wave in the window; otherwise, select the first.

    Returns:
    - pd.DataFrame, DataFrame containing filtered epochs.
    """
    logger.info(f"Starting filter_epochs with window_size={window_size}s and pick_most_negative={pick_most_negative}.")

    try:
        filtered_epochs_list = []
        last_end_time = -float('inf')
        current_window = []

        for index, row in df.iterrows():
            start_time = row['Start']
            end_time = row['End']

            logger.debug(f"Processing wave at index {index}: Start={start_time}s, End={end_time}s.")

            if start_time > last_end_time + window_size:
                if current_window:
                    if pick_most_negative:
                        selected_wave = min(current_window, key=lambda x: x['ValNegPeak'])
                        logger.debug(f"Selected most negative wave at Start={selected_wave['Start']}s, ValNegPeak={selected_wave['ValNegPeak']}.")
                    else:
                        selected_wave = current_window[0]
                        logger.debug(f"Selected first wave at Start={selected_wave['Start']}s.")
                    filtered_epochs_list.append(selected_wave)
                current_window = [row]
                last_end_time = end_time
                logger.debug(f"Starting new window with wave at Start={start_time}s.")
            else:
                current_window.append(row)
                logger.debug(f"Added wave to current window. Current window size: {len(current_window)}.")

        # Handle the last window
        if current_window:
            if pick_most_negative:
                selected_wave = min(current_window, key=lambda x: x['ValNegPeak'])
                logger.debug(f"Selected most negative wave at Start={selected_wave['Start']}s, ValNegPeak={selected_wave['ValNegPeak']}.")
            else:
                selected_wave = current_window[0]
                logger.debug(f"Selected first wave at Start={selected_wave['Start']}s.")
            filtered_epochs_list.append(selected_wave)

        filtered_df = pd.DataFrame(filtered_epochs_list)
        logger.info(f"Total filtered epochs: {len(filtered_df)}.")

        return filtered_df

    except Exception as e:
        logger.error(f"An error occurred during epoch filtering: {e}", exc_info=True)
        raise  # Re-raise the exception to allow upstream handling

