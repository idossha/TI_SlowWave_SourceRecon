
# wave_filtering.py

import pandas as pd
import os

def filter_and_save_epochs(df_sorted, output_dir):
    """
    Filter epochs based on specified configurations and save the filtered DataFrames to CSV files.

    Parameters:
    - df_sorted: pd.DataFrame, DataFrame containing sorted and classified slow waves.
    - output_dir: str, path to the output directory where filtered CSV files will be saved.

    Returns:
    - filtered_files: list of tuples, each containing (filename, filtered_epochs_df).
    """
    filtered_files = []
    configurations = [
        {'window_size': 0.5, 'pick_most_negative': False},
        {'window_size': 0.5, 'pick_most_negative': True},
        {'window_size': 1.0, 'pick_most_negative': False},
        {'window_size': 1.0, 'pick_most_negative': True},
    ]

    for config in configurations:
        window_size = config['window_size']
        pick_most_negative = config['pick_most_negative']
        filtered_epochs_df = filter_epochs(df_sorted, window_size, pick_most_negative)

        # Determine filename based on parameters
        window_ms = int(window_size * 1000)
        suffix = "most_negative" if pick_most_negative else "first"
        filename = f'filtered_epochs_{window_ms}ms_{suffix}.csv'
        output_path = os.path.join(output_dir, filename)

        # Save the filtered DataFrame to CSV
        filtered_epochs_df.to_csv(output_path, index=False)
        print(f"Filtered epochs saved to {output_path}")

        filtered_files.append((filename, filtered_epochs_df))

    return filtered_files

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
    filtered_epochs_list = []
    last_end_time = -float('inf')
    current_window = []

    for _, row in df.iterrows():
        if row['Start'] > last_end_time + window_size:
            if current_window:
                selected_wave = (
                    min(current_window, key=lambda x: x['ValNegPeak'])
                    if pick_most_negative else current_window[0]
                )
                filtered_epochs_list.append(selected_wave)
            current_window = [row]
            last_end_time = row['End']
        else:
            current_window.append(row)

    if current_window:
        selected_wave = (
            min(current_window, key=lambda x: x['ValNegPeak'])
            if pick_most_negative else current_window[0]
        )
        filtered_epochs_list.append(selected_wave)

    return pd.DataFrame(filtered_epochs_list)

