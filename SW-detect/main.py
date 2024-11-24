
# main.py

import os
import sys
import glob
import argparse
import pandas as pd
from data_loading import load_and_preprocess_data
from event_cleaning import clean_events
from epoch_creation import create_epochs
from wave_detection import detect_slow_waves
from wave_classification import classify_and_filter_waves
from wave_filtering import filter_and_save_epochs
from statistical_analysis import perform_statistical_analysis
from annotate_raw import annotate_raw_data
from extract_epochs import extract_and_save_epochs
from plot_average_waveforms import plot_waveforms

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='EEG Data Processing Pipeline')
    parser.add_argument('input_directory', help='Directory containing .set EEG data files')
    parser.add_argument('output_directory', nargs='?', default=None, help='Directory to save outputs (default: input_directory/output)')
    args = parser.parse_args()

    input_dir = args.input_directory
    output_base_dir = args.output_directory

    if output_base_dir is None:
        output_base_dir = os.path.join(input_dir, 'output')

    os.makedirs(output_base_dir, exist_ok=True)

    # Get list of .set files in the input directory
    set_files = glob.glob(os.path.join(input_dir, '*.set'))

    if not set_files:
        print(f"No .set files found in directory: {input_dir}")
        sys.exit(1)

    print(f"Found {len(set_files)} .set file(s) in {input_dir}")

    for fname in set_files:
        # Extract base name without extension for output subdirectory
        base_name = os.path.splitext(os.path.basename(fname))[0]
        output_dir = os.path.join(output_base_dir, base_name)
        os.makedirs(output_dir, exist_ok=True)

        print(f"\nProcessing file: {fname}")
        print(f"Outputs will be saved in: {output_dir}")

        # Load and preprocess data
        print("Loading and preprocessing data...")
        raw, sf = load_and_preprocess_data(fname)

        # Clean events
        print("Cleaning events...")
        cleaned_events_df, durations, omitted_events_df = clean_events(raw)

        # Create epochs and adjust overlaps
        print("Creating epochs and adjusting overlaps...")
        pre_stim_epochs, stim_epochs, post_stim_epochs, overlaps = create_epochs(cleaned_events_df)

        # Detect slow waves
        print("Detecting slow waves...")
        sw_df = detect_slow_waves(raw)

        # Classify and filter waves
        print("Classifying and filtering waves...")
        df_sorted = classify_and_filter_waves(sw_df, pre_stim_epochs, stim_epochs, post_stim_epochs)

        # Save the sorted DataFrame to CSV (optional)
        df_sorted.to_csv(os.path.join(output_dir, 'sorted_slow_waves.csv'), index=False)
        print("Saved sorted slow waves to CSV.")

        # Filter epochs and generate all four CSV files
        print("Filtering epochs and generating CSV files...")
        filter_and_save_epochs(df_sorted, output_dir)

        # *** Select the CSV file to process ***
        # Default is 'filtered_epochs_500ms_most_negative.csv'
        selected_csv_filename = 'filtered_epochs_500ms_most_negative.csv'

        # Load the selected filtered DataFrame
        selected_csv_path = os.path.join(output_dir, selected_csv_filename)
        if not os.path.exists(selected_csv_path):
            print(f"Selected CSV file not found: {selected_csv_path}")
            continue  # Skip to the next file

        df_filtered = pd.read_csv(selected_csv_path)

        # Create a suffix based on the selected CSV filename (without extension)
        suffix = selected_csv_filename.replace('.csv', '')

        print(f"Processing filtered data from {selected_csv_filename}")

        # Perform statistical analysis and plotting using the filtered DataFrame
        print("Performing statistical analysis and plotting...")
        perform_statistical_analysis(df_filtered, output_dir, suffix=suffix)

        # Annotate raw data using the filtered DataFrame
        print("Annotating raw data...")
        annotate_raw_data(raw.copy(), df_filtered, output_dir, suffix=suffix)

        # Extract and save individual epochs and images using the filtered DataFrame
        print("Extracting and saving individual epochs and images...")
        extract_and_save_epochs(raw, df_filtered, sf, output_dir, suffix=suffix)

        # Plot average waveforms using the filtered DataFrame
        print("Plotting average waveforms...")
        plot_waveforms(raw, df_filtered, sf, output_dir, suffix=suffix)

        print(f"Processing of file {fname} completed.\n")

    print("All files have been processed.")

if __name__ == '__main__':
    main()

