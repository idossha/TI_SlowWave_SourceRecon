
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
    """
    log_file = os.path.join(output_dir, "processing.log")

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove any existing handlers to prevent duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file, mode='w')  # 'w' overwrites each run
    fh.setLevel(logging.INFO)
    
    # Console (stdout) handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    # Common formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    root_logger.addHandler(fh)
    root_logger.addHandler(ch)

    root_logger.info("Logger has been set up. Writing logs to: %s", log_file)


def get_all_filepaths(project_dir, selected_subjects, selected_nights, set_templates):
    """
    Gathers all valid (subject, night, .set file) paths based on user selections.
    Yields tuples of (subject_dir_name, night_dir_name, set_filepath).
    """
    logger = logging.getLogger(__name__)

    subjects_dirs = [
        d for d in os.listdir(project_dir) 
        if os.path.isdir(os.path.join(project_dir, d))
    ]
    subjects_dirs.sort(key=lambda x: x.lower())

    for subject_dir_name in subjects_dirs:
        if selected_subjects != "all" and subject_dir_name not in selected_subjects:
            continue
        
        subject_dir = os.path.join(project_dir, subject_dir_name)
        all_nights = [
            d for d in os.listdir(subject_dir)
            if os.path.isdir(os.path.join(subject_dir, d))
        ]
        all_nights.sort(key=lambda x: x.lower())

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

    # -------------------------------------------------------------------------
    # LOAD SUBJECT CONDITION CSV (subject_condition.csv) WITH COLUMNS: subject, condition
    # Make sure the 'subject' column matches the naming convention in subject_dir_name.
    # -------------------------------------------------------------------------
    conditions_df = pd.read_csv(os.path.join(project_dir, "subject_condition.csv"))
    conditions_df["subject"] = conditions_df["subject"].astype(str)

    # 2) Loop over the (subject, night, file) tuples
    for subject_dir_name, night_dir_name, set_filepath in get_all_filepaths(
        project_dir, selected_subjects, selected_nights, set_templates
    ):
        set_filename = os.path.basename(set_filepath)
        
        # Define the output directory
        night_dir = os.path.join(project_dir, subject_dir_name, night_dir_name)
        output_dir = os.path.join(night_dir, 'output', os.path.splitext(set_filename)[0])
        os.makedirs(output_dir, exist_ok=True)

        # Set up logging (this creates a fresh log file for EACH file)
        setup_logging(output_dir)
        logger = logging.getLogger(__name__)

        logger.info("================================================")
        logger.info(
            "Starting pipeline for subject: '%s', night: '%s', file: '%s'",
            subject_dir_name, night_dir_name, set_filename
        )

        try:
            # Determine subject_id and condition from CSV
            subject_id = subject_dir_name  # e.g. "101" or "sub-101"
            row_matches = conditions_df[conditions_df["subject"] == subject_id]
            if len(row_matches) == 0:
                subject_condition = "UNKNOWN"
                logger.warning(f"No condition found for subject {subject_id}; using 'UNKNOWN'.")
            else:
                subject_condition = row_matches["condition"].iloc[0]
                logger.info(f"Subject {subject_id} is in condition: {subject_condition}")

            # Import modules AFTER logging is set up
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
            from my_plotting import (
                plot_ptp_histogram,
                plot_ptp_slope_by_classification,
                plot_parameter_time
            )

            # Import new power analysis functions from power_analysis.py
            from power_analysis import (
                split_stim_epochs,
                analyze_protocols,
                plot_average_psd,
                plot_topomaps,
                get_quarters
            )
            from periodic_power_analysis import (
                    split_stim_epochs, analyze_protocols_irasa, 
                    plot_average_irasa_components, plot_irasa_topomaps
                    )

            from wavelet_power_analysis import split_stim_epochs, plot_protocol_wavelet_power, compute_average_trend_slopes

            # 4) Load the data
            logger.info("STEP 4) Loading data...")
            raw, data = load_data(set_filepath)

            # 5) Plot net coverage
            logger.info("STEP 5) Plotting EEG net coverage...")
            plot_net_coverage(raw, output_dir)

            # 6) Plot spectrogram
            logger.info("STEP 6) Plotting spectrogram...")
            plot_spectrogram_with_annotations(raw, output_dir)

            # --------------------------------------------------
            # Morlet POWER ANALYSIS
            # --------------------------------------------------
            #
            # # Create the subdirectory for time-domain power outputs.
            # time_power_dir = os.path.join(output_dir, "time_domain_power")
            # os.makedirs(time_power_dir, exist_ok=True)
            #
            # pre_stim_epochs, q1_stim_epochs, q4_stim_epochs, post_stim_epochs = split_stim_epochs(raw, logger=logger)
            #
            # protocol_slopes = []
            # for pre_ep, q1_ep, q4_ep, post_ep in zip(pre_stim_epochs, q1_stim_epochs, q4_stim_epochs, post_stim_epochs):
            #     _, _, _, slopes = plot_protocol_wavelet_power(raw, pre_ep, post_ep, q1_ep, q4_ep, time_power_dir, pre_ep[2], logger=logger)
            #     protocol_slopes.append(slopes)
            #
            # compute_average_trend_slopes(protocol_slopes, time_power_dir, logger=logger)

            # --------------------------------------------------
            # POWER ANALYSIS
            # --------------------------------------------------

            logger.info("STEP 8.5) Running power analysis (PSD comparisons)...")
            pre_stim_epochs, q1_stim_epochs, q4_stim_epochs, post_stim_epochs = split_stim_epochs(raw, logger=logger)
            # Run protocol-by-protocol analysis (this function creates PSD plots per protocol and saves CSV stats)
            analyze_protocols(raw, pre_stim_epochs, q1_stim_epochs, q4_stim_epochs,
                              post_stim_epochs, output_dir, subject_id, subject_condition, logger)
            # Average PSD plots:
            # For stim epochs (difference = Q4 - Q1)
            plot_average_psd(raw, q1_stim_epochs, q4_stim_epochs, output_dir,
                             subject_id, subject_condition, epoch_type="stim", logger=logger)
            # For poststim epochs (difference = Q1 - Q4) – first, split each post-stim epoch:
            q1_post_epochs, q4_post_epochs = [], []
            for post_epoch in post_stim_epochs:
                q1_post, q4_post = get_quarters(post_epoch)
                q1_post_epochs.append(q1_post)
                q4_post_epochs.append(q4_post)
            plot_average_psd(raw, q1_post_epochs, q4_post_epochs, output_dir,
                             subject_id, subject_condition, epoch_type="poststim", logger=logger)
            # Topoplots:
            # For stim epochs:
            plot_topomaps(raw, q1_stim_epochs, q4_stim_epochs, output_dir,
                          epoch_type="stim", method="welch", logger=logger)
            plot_topomaps(raw, q1_stim_epochs, q4_stim_epochs, output_dir,
                          epoch_type="stim", method="fft", logger=logger)
            # For poststim epochs:
            plot_topomaps(raw, q1_post_epochs, q4_post_epochs, output_dir,
                          epoch_type="poststim", method="welch", logger=logger)
            plot_topomaps(raw, q1_post_epochs, q4_post_epochs, output_dir,
                          epoch_type="poststim", method="fft", logger=logger)


            # 12) Analyze IRASA for periodic and aperiodic components
            pre_stim_epochs, q1_stim_epochs, q4_stim_epochs, post_stim_epochs = split_stim_epochs(raw, logger=logger)
            analyze_protocols_irasa(raw, q1_stim_epochs, q4_stim_epochs, post_stim_epochs, output_dir, logger=logger)

            # 13) Compute and plot average IRASA components across protocols (for stimulation epochs)
            plot_average_irasa_components(raw, q1_stim_epochs, q4_stim_epochs, output_dir, epoch_type="stim", logger=logger)
            plot_average_irasa_components(raw, q1_stim_epochs, q4_stim_epochs, output_dir, epoch_type="poststim", logger=logger)

            # 14) Generate topoplots for the IRASA components across defined entrainment bands (for stimulation epochs)
            plot_irasa_topomaps(raw, q1_stim_epochs, q4_stim_epochs, output_dir, epoch_type="stim", logger=logger)
            plot_irasa_topomaps(raw, q1_stim_epochs, q4_stim_epochs, output_dir, epoch_type="poststim", logger=logger)



            pre_stim_epochs_old, stim_epochs, post_stim_epochs_old, overlaps = create_and_visualize_epochs(
                cleaned_events_df, output_dir, sf
            )

            # 11) Detect slow waves
            logger.info("STEP 11) Detecting slow waves...")
            sw_df = detect_slow_waves(raw, output_dir)
            
            # 11b) Compare slopes: first vs. last hour
            logger.info("STEP 11b) Comparing slopes in the first vs. last hour (original_detection.csv).")
            original_detection_csv = os.path.join(output_dir, "original_detection.csv")
            slopes_first_vs_last(original_detection_csv, output_dir)

            # 12) Classify and filter waves
            logger.info("STEP 12) Classifying and filtering waves...")
            df_sorted = classify_and_filter_waves(
                sw_df, pre_stim_epochs_old, stim_epochs, post_stim_epochs_old
            )

            # 13) Save the sorted DataFrame
            logger.info("STEP 13) Saving the sorted slow waves DataFrame...")
            sorted_csv_path = os.path.join(output_dir, 'sorted_slow_waves.csv')
            df_sorted.to_csv(sorted_csv_path, index=False)
            logger.info(f"Saved sorted slow waves to {sorted_csv_path}.")

            # 14) Filter epochs and generate CSVs
            logger.info("STEP 14) Filtering epochs and generating CSV files...")
            filter_and_save_epochs(df_sorted, output_dir)

            # 15) Load the default filtered CSV
            logger.info("STEP 15) Using 'filtered_epochs_500ms_first.csv' for statistical analysis...")
            selected_csv_filename = 'filtered_epochs_500ms_first.csv'
            selected_csv_path = os.path.join(output_dir, selected_csv_filename)
            if not os.path.exists(selected_csv_path):
                logger.warning(f"Selected CSV file not found: {selected_csv_path}")
                continue
            df_filtered = pd.read_csv(selected_csv_path)

            # 16) Statistical analysis & plotting
            logger.info("STEP 16) Performing statistical analysis and plotting...")
            perform_statistical_analysis(
                df_filtered, output_dir, project_dir, 
                subject_dir_name, night_dir_name, suffix='filtered'
            )

            # 17) Annotate raw data
            logger.info("STEP 17) Annotating raw data...")
            annotate_raw_data(raw.copy(), df_filtered, output_dir, suffix='filtered')

            # 18) Extract epochs
            logger.info("STEP 18) Extracting and saving individual epochs and images...")
            extract_and_save_epochs(raw, df_filtered, sf, output_dir, suffix='filtered')

            # 19) Plot average waveforms
            logger.info("STEP 19) Plotting average waveforms...")
            plot_waveforms(raw, df_filtered, sf, output_dir, suffix='filtered')
            
            # 20) Additional plotting & group summary
            logger.info("STEP 20) Additional plotting and group summary...")
            
            # Plot parameter vs. time
            logger.info("Plotting parameters over time...")
            plot_parameter_time(df_filtered, output_dir, logger=logger)

            # Plot PTP vs. slope by classification
            logger.info("Plotting PTP vs. Slope by classification...")
            plot_ptp_slope_by_classification(df_filtered, output_dir, logger=logger)

            # Plot PTP histogram
            logger.info("Plotting PTP histogram...")
            plot_ptp_histogram(df_filtered, output_dir, logger=logger)

            # Append data to group_summary
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
                exc_info=True  # Stack trace in the log
            )
            continue

    # -------------------------------------------------------------------------
    # AFTER PROCESSING ALL SUBJECTS, YOU MAY CALL THE GROUP COMPARISON FUNCTION:
    # -------------------------------------------------------------------------
    logger = logging.getLogger(__name__)
    logger.info("All subjects processed. Running group-level PSD and topomap comparisons...")

    from group_PSD import group_power_psd

    group_power_psd(project_dir)

    logger.info("Group-level PSD and topomap comparisons are complete.")


if __name__ == '__main__':
    main()

