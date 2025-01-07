# main.py

import os
import sys
import glob
import logging
import pandas as pd

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
from plot_net_coverage import plot_net_coverage
from interactive_prompt import get_user_choices
from spectrogram_plot import plot_spectrogram_with_annotations
from load_data import load_data
from filter import filter_and_resample



def setup_logging(output_dir):
    """
    Set up logging to both console and a log file in the output directory.
    Ensures that logging configuration is reset each time it's called.
    """
    log_file = os.path.join(output_dir, "processing.log")
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    if logger.hasHandlers():
        logger.handlers.clear()
    
    fh = logging.FileHandler(log_file)
    ch = logging.StreamHandler(sys.stdout)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)


def get_all_filepaths(project_dir, selected_subjects, selected_nights, set_templates):
    """
    Gathers all valid (subject, night, .set file) paths based on user selections.
    Yields tuples of (subject_dir_name, night_dir_name, set_filepath).
    """
    # List all subject directories
    subjects_dirs = [
        d for d in os.listdir(project_dir) 
        if os.path.isdir(os.path.join(project_dir, d))
        ]

    # Iterate over each subject
    for subject_dir_name in subjects_dirs:
        # Skip if the user specified a subset of subjects and this one isn't in it
        if selected_subjects != "all" and subject_dir_name not in selected_subjects:
            continue
        
        subject_dir = os.path.join(project_dir, subject_dir_name)
        all_nights = [
            d for d in os.listdir(subject_dir)
            if os.path.isdir(os.path.join(subject_dir, d))
        ]
        
        if not all_nights:
            print(f"Warning: No nights found for subject '{subject_dir_name}'. Skipping.")
            continue
        
        # If user selected all nights, process them all; otherwise filter
        if selected_nights == "all":
            nights = all_nights
        else:
            nights = [n for n in all_nights if n in selected_nights]
        
        if not nights:
            print(f"Warning: No valid nights found for subject '{subject_dir_name}'. Skipping.")
            continue
        
        # For each selected night
        for night_dir_name in nights:
            night_dir = os.path.join(subject_dir, night_dir_name)
            
            # For each .set pattern provided
            for set_pattern in set_templates:
                # If the pattern includes 'XXX', replace it with the subject number
                if 'XXX' in set_pattern:
                    pattern_to_use = set_pattern.replace('XXX', subject_dir_name)
                else:
                    pattern_to_use = set_pattern

                # Use glob to find .set files that match
                set_filepaths = glob.glob(os.path.join(night_dir, pattern_to_use))
                
                if not set_filepaths:
                    print(
                        f"Warning: No .set files matching pattern '{pattern_to_use}' "
                        f"found in '{night_dir}' for subject '{subject_dir_name}'."
                    )
                    continue
                
                # Yield each matching file path
                for set_filepath in set_filepaths:
                    yield (subject_dir_name, night_dir_name, set_filepath)



def main():
    """
    Main function for the EEG Data Processing Pipeline.
    Uses interactive_prompt to gather user inputs, and a helper function
    to yield all relevant filepaths, reducing nested loops.
    """
    # 1) Gather user choices interactively
    project_dir, selected_subjects, selected_nights, set_templates = get_user_choices()

    # 2) Loop over the (subject, night, file) tuples from get_all_filepaths
    for subject_dir_name, night_dir_name, set_filepath in get_all_filepaths(
        project_dir, selected_subjects, selected_nights, set_templates
    ):
        set_filename = os.path.basename(set_filepath)
        print(f"Processing subject '{subject_dir_name}' - Night '{night_dir_name}' - File: {set_filepath}")

        # Define the output directory
        night_dir = os.path.join(project_dir, subject_dir_name, night_dir_name)
        output_dir = os.path.join(night_dir, 'output', os.path.splitext(set_filename)[0])
        os.makedirs(output_dir, exist_ok=True)

        # Set up logging
        setup_logging(output_dir)
        logging.info(f"Processing file: {set_filepath}")

        try:
            # 3) Load the data
            logging.info("Loading data...")
            raw = load_data(set_filepath)

             # 6) Plot net coverage
            logging.info("Plotting EEG net coverage...")
            plot_net_coverage(raw, output_dir)

            # 4) Plot spectrogram
            logging.info("Plotting spectrogram...")
            plot_spectrogram_with_annotations(raw, output_dir)

            # 5) Filter and resample the data
            logging.info("Filtering and resampling data...")
            raw, sf, filter_details = filter_and_resample(raw)

            # 7) Clean events
            logging.info("Cleaning events...")
            cleaned_events_df, durations, omitted_events_df = clean_events(raw)

            # 8) Check stim events
            stim_start_count = (cleaned_events_df["Description"] == "stim start").sum()
            stim_end_count = (cleaned_events_df["Description"] == "stim end").sum()
            stim_events_found = (stim_start_count > 0 or stim_end_count > 0)
            if not stim_events_found:
                logging.info(f"No stim events found for subject '{subject_dir_name}' and night '{night_dir_name}'.")

            # 9) Save metadata
            logging.info("Saving EEG metadata...")
            metadata_file = os.path.join(output_dir, "eeg_metadata.txt")
            save_eeg_metadata(raw, cleaned_events_df, omitted_events_df, 
                              metadata_file, 
                              filter_type=filter_details, 
                              stim_events_found=stim_events_found)

            # 10) Create epochs and adjust overlaps
            logging.info("Creating epochs and adjusting overlaps...")
            pre_stim_epochs, stim_epochs, post_stim_epochs, overlaps = create_and_visualize_epochs(
                cleaned_events_df, output_dir, sf
            )

            # 11) Detect slow waves
            logging.info("Detecting slow waves...")
            sw_df = detect_slow_waves(raw)

            # 12) Classify and filter waves
            logging.info("Classifying and filtering waves...")
            df_sorted = classify_and_filter_waves(
                sw_df, pre_stim_epochs, stim_epochs, post_stim_epochs
            )

            # 13) Save the sorted DataFrame
            sorted_csv_path = os.path.join(output_dir, 'sorted_slow_waves.csv')
            df_sorted.to_csv(sorted_csv_path, index=False)
            logging.info(f"Saved sorted slow waves to {sorted_csv_path}.")

            # 14) Filter epochs and generate CSVs
            logging.info("Filtering epochs and generating CSV files...")
            filter_and_save_epochs(df_sorted, output_dir)

            # 15) Load the default filtered CSV
            selected_csv_filename = 'filtered_epochs_500ms_first.csv'
            selected_csv_path = os.path.join(output_dir, selected_csv_filename)
            if not os.path.exists(selected_csv_path):
                logging.warning(f"Selected CSV file not found: {selected_csv_path}")
                continue

            df_filtered = pd.read_csv(selected_csv_path)
            
            # 16) Statistical analysis & plotting
            logging.info("Performing statistical analysis and plotting...")
            perform_statistical_analysis(
                df_filtered, output_dir, project_dir, 
                subject_dir_name, night_dir_name, suffix='filtered'
            )

            # 17) Annotate raw data
            logging.info("Annotating raw data...")
            annotate_raw_data(raw.copy(), df_filtered, output_dir, suffix='filtered')

            # # 18) Create topographical plots for negative peaks
            # logging.info("Creating topographical plots for negative peaks...")
            # # Path to the annotated raw data .set file
            # annotated_set_file = os.path.join(output_dir, "annotated_raw_filtered.set")
            # plot_topomaps(annotated_set_file, output_dir, suffix='filtered')

            # 19) Extract and save epochs
            logging.info("Extracting and saving individual epochs and images...")
            extract_and_save_epochs(raw, df_filtered, sf, output_dir, suffix='filtered')

            # 20) Plot average waveforms
            logging.info("Plotting average waveforms...")
            plot_waveforms(raw, df_filtered, sf, output_dir, suffix='filtered')

            # 21) Append data to group_summary
            logging.info("Appending to group_summary.csv...")
            quant_csv_path = os.path.join(output_dir, 'wave_quantification.csv')
            append_to_group_summary(project_dir, subject_dir_name, night_dir_name, quant_csv_path)

            logging.info(f"Processing of '{set_filename}' for subject '{subject_dir_name}' / night '{night_dir_name}' completed.\n")

        except Exception as e:
            logging.error(
                f"Error processing file '{set_filename}' for subject '{subject_dir_name}' "
                f"and night '{night_dir_name}': {e}"
            )
            continue


if __name__ == '__main__':
    main()
