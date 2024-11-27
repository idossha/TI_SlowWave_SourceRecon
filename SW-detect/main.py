
# main.py

import os
import sys
import argparse
import glob
import pandas as pd
import logging 
from data_loading import load_and_preprocess_data
from event_cleaning import clean_events
from epoch_creation import create_and_visualize_epochs
from annotate_raw import annotate_raw_data
from extract_epochs import extract_and_save_epochs
from wave_detection import detect_slow_waves
from wave_classification import classify_and_filter_waves
from wave_filtering import filter_and_save_epochs
from plot_average_waveforms import plot_waveforms
from statistical_analysis import perform_statistical_analysis
from metadata_summary import save_eeg_metadata  
from group_analysis import append_to_group_summary

def setup_logging(output_dir):
    """
    Set up logging to both console and a log file in the output directory.
    Ensures that logging configuration is reset each time it's called.
    """
    log_file = os.path.join(output_dir, "processing.log")
    
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove all existing handlers to prevent duplication
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create handlers
    fh = logging.FileHandler(log_file)
    ch = logging.StreamHandler(sys.stdout)
    
    # Create formatter and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    # Add handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='EEG Data Processing Pipeline',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples of usage:
1. Process all subjects, all nights, all .set files matching *.set
   python3 main.py /Volumes/CSC-Ido/EEG/ "*.set"

2. Process all subjects, all nights, specific .set files matching "Strength_XXX_forICA*.set"
   python3 main.py /Volumes/CSC-Ido/EEG/ "Strength_XXX_forICA*.set"

3. Process all subjects for night 'N1', specific .set files matching "Strength_XXX_N1_forICA.set"
   python3 main.py /Volumes/CSC-Ido/EEG/ --night N1 "Strength_XXX_N1_forICA.set"

4. Process specific subject '128' for night 'N1', specific .set file "Strength_128_N1_forICA.set"
   python3 main.py /Volumes/CSC-Ido/EEG/ --subject 128 --night N1 "Strength_128_N1_forICA.set"
        """
    )
    
    # Define positional and optional arguments
    parser.add_argument('project_directory', help='Project directory containing subject folders (e.g., EEG)')
    parser.add_argument('set_template', nargs='?', default="*.set", help='Template for .set filenames with "XXX" as placeholder for subject number (e.g., Strength_XXX_forICA*.set)')
    parser.add_argument('--subject', type=str, help='Specific subject number to process (e.g., 128)')
    parser.add_argument('--night', type=str, help='Specific night to process within each subject (e.g., N1)')
    
    args = parser.parse_args()

    project_dir = args.project_directory
    set_template = args.set_template
    subject = args.subject
    night = args.night

    # Validate that project directory exists
    if not os.path.isdir(project_dir):
        print(f"Error: Project directory does not exist: {project_dir}")
        sys.exit(1)

    # List all subject directories within the project directory
    subjects_dirs = [d for d in os.listdir(project_dir) if os.path.isdir(os.path.join(project_dir, d))]
    if not subjects_dirs:
        print(f"No subject directories found in project directory: {project_dir}")
        sys.exit(1)

    # If a specific subject is provided, verify its existence
    if subject and subject not in subjects_dirs:
        print(f"Error: Specified subject '{subject}' not found in project directory.")
        sys.exit(1)

    # Iterate through each subject
    for subject_dir_name in subjects_dirs:
        # If a specific subject is provided, skip others
        if subject and subject_dir_name != subject:
            continue

        subject_dir = os.path.join(project_dir, subject_dir_name)

        # Determine nights to process
        if night:
            nights = [night] if os.path.isdir(os.path.join(subject_dir, night)) else []
            if not nights:
                print(f"Warning: Night '{night}' not found for subject '{subject_dir_name}'. Skipping.")
                continue
        else:
            # Process all nights within the subject
            nights = [d for d in os.listdir(subject_dir) if os.path.isdir(os.path.join(subject_dir, d))]

        if not nights:
            print(f"Warning: No nights found for subject '{subject_dir_name}'. Skipping.")
            continue

        for night_dir_name in nights:
            night_dir = os.path.join(subject_dir, night_dir_name)

            # Replace 'XXX' in set_template with the current subject number
            if 'XXX' not in set_template:
                # No placeholder, use as is
                set_pattern = set_template
            else:
                set_pattern = set_template.replace('XXX', subject_dir_name)

            # Construct the full pattern path
            set_filepaths = glob.glob(os.path.join(night_dir, set_pattern))

            if not set_filepaths:
                print(f"Warning: No .set files matching pattern '{set_pattern}' found in '{night_dir}' for subject '{subject_dir_name}'. Skipping.")
                continue

            for set_filepath in set_filepaths:
                set_filename = os.path.basename(set_filepath)
                print(f"Processing subject '{subject_dir_name}' - Night '{night_dir_name}' - File: {set_filepath}")

                # Define the output directory next to the .set file
                output_dir = os.path.join(night_dir, 'output', os.path.splitext(set_filename)[0])
                os.makedirs(output_dir, exist_ok=True)

                # Initialize logging
                setup_logging(output_dir)
                logging.info(f"Processing file: {set_filepath}")

                try:
                    # Load and preprocess data
                    logging.info("Loading and preprocessing data...")
                    raw, sf, filter_details = load_and_preprocess_data(set_filepath)

                    # Clean events
                    logging.info("Cleaning events...")
                    cleaned_events_df, durations, omitted_events_df = clean_events(raw)

                    # Determine if stim events are present
                    stim_start_count = (cleaned_events_df["Description"] == "stim start").sum()
                    stim_end_count = (cleaned_events_df["Description"] == "stim end").sum()

                    if stim_start_count == 0 and stim_end_count == 0:
                        stim_events_found = False
                        logging.info(f"No stim events found for subject '{subject_dir_name}' and night '{night_dir_name}'.")
                    else:
                        stim_events_found = True

                    # Save metadata
                    logging.info("Saving EEG metadata...")
                    metadata_file = os.path.join(output_dir, "eeg_metadata.txt")
                    save_eeg_metadata(raw, cleaned_events_df, omitted_events_df, metadata_file, filter_type=filter_details, stim_events_found=stim_events_found)

                    # Create epochs and adjust overlaps
                    logging.info("Creating epochs and adjusting overlaps...")
                    pre_stim_epochs, stim_epochs, post_stim_epochs, overlaps = create_and_visualize_epochs(cleaned_events_df, output_dir)

                    # Detect slow waves
                    logging.info("Detecting slow waves...")
                    sw_df = detect_slow_waves(raw)

                    # Classify and filter waves
                    logging.info("Classifying and filtering waves...")
                    df_sorted = classify_and_filter_waves(sw_df, pre_stim_epochs, stim_epochs, post_stim_epochs)

                    # Save the sorted DataFrame to CSV
                    sorted_csv_path = os.path.join(output_dir, 'sorted_slow_waves.csv')
                    df_sorted.to_csv(sorted_csv_path, index=False)
                    logging.info(f"Saved sorted slow waves to {sorted_csv_path}.")

                    # Filter epochs and generate CSV files
                    logging.info("Filtering epochs and generating CSV files...")
                    filter_and_save_epochs(df_sorted, output_dir)

                    # Select the CSV file to process (default: 'filtered_epochs_500ms_most_negative.csv')
                    selected_csv_filename = 'filtered_epochs_500ms_most_negative.csv'
                    selected_csv_path = os.path.join(output_dir, selected_csv_filename)
                    if not os.path.exists(selected_csv_path):
                        logging.warning(f"Selected CSV file not found: {selected_csv_path}")
                        continue  # Skip to the next file

                    df_filtered = pd.read_csv(selected_csv_path)

                    # Perform statistical analysis and plotting
                    logging.info("Performing statistical analysis and plotting...")
                    perform_statistical_analysis(df_filtered, output_dir, project_dir, subject_dir_name, night_dir_name, suffix='filtered')

                    # Annotate raw data using the filtered DataFrame
                    logging.info("Annotating raw data...")
                    annotate_raw_data(raw.copy(), df_filtered, output_dir, suffix='filtered')

                    # Extract and save individual epochs and images
                    logging.info("Extracting and saving individual epochs and images...")
                    extract_and_save_epochs(raw, df_filtered, sf, output_dir, suffix='filtered')

                    # Plot average waveforms
                    logging.info("Plotting average waveforms...")
                    plot_waveforms(raw, df_filtered, sf, output_dir, suffix='filtered')


                    # Append data to group_summary.csv
                    logging.info("Appending to group_summary.csv...")
                    quant_csv_path = os.path.join(output_dir, 'wave_quantification.csv')
                    append_to_group_summary(project_dir, subject_dir_name, night_dir_name, quant_csv_path)

                    logging.info(f"Processing of file '{set_filename}' for subject '{subject_dir_name}' and night '{night_dir_name}' completed.\n")

                except Exception as e:
                    logging.error(f"Error processing file '{set_filename}' for subject '{subject_dir_name}' and night '{night_dir_name}': {e}")
                    continue  # Continue with the next file

if __name__ == '__main__':
    main()

