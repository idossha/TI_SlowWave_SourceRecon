
# main.py

import os
import sys
import glob
import logging
import pandas as pd

from interactive_prompt import get_user_choices

def setup_logging(output_dir):
    """
    Set up logging to both console and a log file in the output directory.
    Configures the root logger to capture all logs from all modules.
    
    Parameters:
    - output_dir (str): Path to the output directory where processing.log will be saved.
    """
    log_file = os.path.join(output_dir, "processing.log")

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)  # Set to INFO or DEBUG as needed

    # Remove any existing handlers to prevent duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file, mode='w')  # 'w' overwrites each run; use 'a' to append
    fh.setLevel(logging.INFO)
    
    # Console (stdout) handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    # Common formatter: include time, level, module name, message
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add handlers to the root logger
    root_logger.addHandler(fh)
    root_logger.addHandler(ch)

    # Log the setup completion
    root_logger.info("Logger has been set up. Writing logs to: %s", log_file)


def get_all_filepaths(project_dir, selected_subjects, selected_nights, set_templates):
    """
    Gathers all valid (subject, night, .set file) paths based on user selections.
    Yields tuples of (subject_dir_name, night_dir_name, set_filepath).
    
    Parameters:
    - project_dir (str): Path to the project directory.
    - selected_subjects (list or str): List of selected subjects or "all".
    - selected_nights (list or str): List of selected nights or "all".
    - set_templates (list): List of .set file patterns to look for.
    
    Yields:
    - tuple: (subject_dir_name, night_dir_name, set_filepath)
    """
    logger = logging.getLogger(__name__)

    subjects_dirs = [
        d for d in os.listdir(project_dir) 
        if os.path.isdir(os.path.join(project_dir, d))
    ]
    subjects_dirs.sort(key=lambda x: x.lower())  # Sort alphabetically

    for subject_dir_name in subjects_dirs:
        if selected_subjects != "all" and subject_dir_name not in selected_subjects:
            continue
        
        subject_dir = os.path.join(project_dir, subject_dir_name)
        all_nights = [
            d for d in os.listdir(subject_dir)
            if os.path.isdir(os.path.join(subject_dir, d))
        ]
        all_nights.sort(key=lambda x: x.lower())  # Sort alphabetically

        if selected_nights == "all":
            nights = all_nights
        else:
            nights = [n for n in all_nights if n in selected_nights]
        
        if not nights:
            logger.warning(f"No valid nights found for subject '{subject_dir_name}'. Skipping.")
            continue

        for night_dir_name in nights:
            night_dir = os.path.join(subject_dir, night_dir_name)
            
            for set_pattern in set_templates:
                if 'XXX' in set_pattern:
                    pattern_to_use = set_pattern.replace('XXX', subject_dir_name)
                else:
                    pattern_to_use = set_pattern

                set_filepaths = glob.glob(os.path.join(night_dir, pattern_to_use))
                
                if not set_filepaths:
                    logger.warning(
                        f"No .set files matching pattern '{pattern_to_use}' "
                        f"found in '{night_dir}' for subject '{subject_dir_name}'."
                    )
                    continue
                
                for set_filepath in set_filepaths:
                    yield (subject_dir_name, night_dir_name, set_filepath)


def main():
    """
    Main function for the EEG Data Processing Pipeline.
    Gathers user inputs, sets up logging, imports necessary modules,
    and processes each .set file accordingly.
    """
    # 1) Gather user choices interactively
    project_dir, selected_subjects, selected_nights, set_templates = get_user_choices()

    # 2) Set up logging once, with master log file per output_dir
    # Logging will be set up inside the processing loop for each file

    # 3) Loop over the (subject, night, file) tuples
    for subject_dir_name, night_dir_name, set_filepath in get_all_filepaths(
        project_dir, selected_subjects, selected_nights, set_templates
    ):
        set_filename = os.path.basename(set_filepath)
        
        # Define the output directory
        night_dir = os.path.join(project_dir, subject_dir_name, night_dir_name)
        output_dir = os.path.join(night_dir, 'output', os.path.splitext(set_filename)[0])
        os.makedirs(output_dir, exist_ok=True)

        # Set up logging (this creates a fresh log file for EACH subject-file)
        setup_logging(output_dir)
        logger = logging.getLogger(__name__)  # This will be '__main__'

        logger.info("================================================")
        logger.info(
            "Starting pipeline for subject: '%s', night: '%s', file: '%s'",
            subject_dir_name, night_dir_name, set_filename
        )

        try:
            # Import modules after logging is set up
            from event_cleaning import clean_events
            from epoch_creation import create_and_visualize_epochs
            from annotate_raw import annotate_raw_data
            from extract_epochs import extract_and_save_epochs
            from wave_detection import detect_slow_waves
            from wave_classification import classify_and_filter_waves
            from wave_filtering import filter_and_save_epochs
            from plot_average_waveforms import plot_waveforms
            from statistical_analysis import perform_statistical_analysis
            from group_analysis import append_to_group_summary
            from plot_net_coverage import plot_net_coverage
            from spectrogram_plot import plot_spectrogram_with_annotations
            from load_data import load_data
            from filter import filter_and_resample
            from first_vs_last import slopes_first_vs_last
            from my_plotting import (plot_ptp_histogram,plot_ptp_slope_by_classification, plot_parameter_time)

            # 4) Load the data
            logger.info("Loading data...")
            raw = load_data(set_filepath)

            # 5) Plot net coverage
            logger.info("Plotting EEG net coverage...")
            plot_net_coverage(raw, output_dir)

            # 6) Plot spectrogram
            logger.info("Plotting spectrogram...")
            plot_spectrogram_with_annotations(raw, output_dir)

            # 7) Filter and resample the data
            logger.info("Filtering and resampling data...")
            raw, sf, filter_details = filter_and_resample(raw)

            # 8) Clean events
            logger.info("Cleaning events...")
            cleaned_events_df, durations, omitted_events_df = clean_events(raw)

            # 9) Create epochs and adjust overlaps
            logger.info("Creating epochs and adjusting overlaps...")
            pre_stim_epochs, stim_epochs, post_stim_epochs, overlaps = create_and_visualize_epochs(
                cleaned_events_df, output_dir, sf
            )

            # 10) Detect slow waves
            logger.info("Detecting slow waves...")
            sw_df = detect_slow_waves(raw, output_dir)
            
            # 10b) Compare slopes: first vs. last hour
            logger.info("Comparing slopes in the first vs. last hour (original_detection.csv).")
            original_detection_csv = os.path.join(output_dir, "original_detection.csv")
            slopes_first_vs_last(original_detection_csv, output_dir)


            # 11) Classify and filter waves
            logger.info("Classifying and filtering waves...")
            df_sorted = classify_and_filter_waves(
                sw_df, pre_stim_epochs, stim_epochs, post_stim_epochs
            )

            # 12) Save the sorted DataFrame
            sorted_csv_path = os.path.join(output_dir, 'sorted_slow_waves.csv')
            df_sorted.to_csv(sorted_csv_path, index=False)
            logger.info(f"Saved sorted slow waves to {sorted_csv_path}.")

            # 13) Filter epochs and generate CSVs
            logger.info("Filtering epochs and generating CSV files...")
            filter_and_save_epochs(df_sorted, output_dir)

            # 14) Load the default filtered CSV
            selected_csv_filename = 'filtered_epochs_500ms_first.csv'
            logger.info(f"Using: {selected_csv_filename} for statistical analysis")
            selected_csv_path = os.path.join(output_dir, selected_csv_filename)
            if not os.path.exists(selected_csv_path):
                logger.warning(f"Selected CSV file not found: {selected_csv_path}")
                continue

            df_filtered = pd.read_csv(selected_csv_path)
            
            # 15) Statistical analysis & plotting
            logger.info("Performing statistical analysis and plotting...")
            perform_statistical_analysis(
                df_filtered, output_dir, project_dir, 
                subject_dir_name, night_dir_name, suffix='filtered'
            )

            # 16) Annotate raw data
            logger.info("Annotating raw data...")
            annotate_raw_data(raw.copy(), df_filtered, output_dir, suffix='filtered')

            # 17) Extract and save epochs
            logger.info("Extracting and saving individual epochs and images...")
            extract_and_save_epochs(raw, df_filtered, sf, output_dir, suffix='filtered')

            # 18) Plot average waveforms
            logger.info("Plotting average waveforms...")
            plot_waveforms(raw, df_filtered, sf, output_dir, suffix='filtered')
            

            logger.info("STEP 19) Additional plotting...")

            # Plot parameter vs. time (scatter + trend)
            logger.info("Plotting parameters over time...")
            plot_parameter_time(df_filtered, output_dir, logger=logger)

            # Plot PTP vs. Slope by Classification
            logger.info("Plotting PTP vs. Slope by classification...")
            plot_ptp_slope_by_classification(df_filtered, output_dir, logger=logger)

            # Plot PTP histogram
            logger.info("Plotting PTP histogram...")
            plot_ptp_histogram(df_filtered, output_dir, logger=logger)


            # 19) Append data to group_summary
            logger.info("Appending to group_summary.csv...")
            quant_csv_path = os.path.join(output_dir, 'wave_quantification.csv')
            append_to_group_summary(project_dir, subject_dir_name, night_dir_name, quant_csv_path)

            logger.info(
                "Processing of '%s' for subject '%s' / night '%s' completed.\n",
                set_filename, subject_dir_name, night_dir_name
            )

        except Exception as e:
            logger.error(
                "Error processing file '%s' for subject '%s' and night '%s': %s",
                set_filename, subject_dir_name, night_dir_name, e,
                exc_info=True  # This will include stack trace in the log
            )
            # Optionally continue to next file
            continue


if __name__ == '__main__':
    main()

