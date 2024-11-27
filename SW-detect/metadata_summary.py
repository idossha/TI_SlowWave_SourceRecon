
# metadata_summary.py

import pandas as pd
import logging

def save_eeg_metadata(raw, cleaned_events_df, omitted_events_df, output_file, filter_type, stim_events_found=True):
    """
    Save EEG metadata to a .txt file.

    Parameters:
        raw (mne.io.Raw): The raw EEG data.
        cleaned_events_df (pd.DataFrame): DataFrame with cleaned events.
        omitted_events_df (pd.DataFrame): DataFrame with omitted events.
        output_file (str): Path to save the metadata file.
        filter_type (str): Type of filter applied to the data.
        stim_events_found (bool): Flag indicating if stim events were found.
    """
    logging.info("Saving EEG metadata to .txt file...")

    try:
        with open(output_file, "w") as f:
            # General information
            f.write("EEG Metadata Summary\n")
            f.write("=====================\n")
            f.write(f"Sampling Frequency: {raw.info['sfreq']} Hz\n")
            f.write(f"Recording Length: {raw.times[-1]:.2f} seconds\n")
            f.write(f"Number of Channels: {len(raw.info['ch_names'])}\n")
            f.write(f"Channel Names: {', '.join(raw.info['ch_names'])}\n\n")
            f.write(f"Filter Type: {filter_type}\n\n")

            # Stim Events Information
            f.write("Stim Events Information\n")
            f.write("========================\n")
            if stim_events_found:
                stim_start_count = (cleaned_events_df["Description"] == "stim start").sum()
                stim_end_count = (cleaned_events_df["Description"] == "stim end").sum()
                f.write(f"Total 'stim start' Events: {stim_start_count}\n")
                f.write(f"Total 'stim end' Events: {stim_end_count}\n\n")

                # Timing of Stim Protocols: Pair start and end
                f.write("Timing of Stim Protocols:\n")
                # Define column headers with fixed widths
                headers = f"{'Set':<10}{'Stim Start (s)':<20}{'Stim End (s)':<20}"
                f.write(headers + "\n")
                f.write(f"{'-' * len(headers)}\n")  # Divider

                stim_starts = cleaned_events_df[cleaned_events_df["Description"] == "stim start"]["Onset"].values
                stim_ends = cleaned_events_df[cleaned_events_df["Description"] == "stim end"]["Onset"].values

                # Iterate over paired stim events
                for i, (start, end) in enumerate(zip(stim_starts, stim_ends), start=1):
                    # Format with two decimal places and 's' suffix
                    start_str = f"{start:.2f}s"
                    end_str = f"{end:.2f}s"
                    set_str = f"{i}"  # Assuming 'Set' refers to the set number
                    f.write(f"{set_str:<10}{start_str:<20}{end_str:<20}\n")
            else:
                f.write("No stim events found.\n\n")

            # Omitted Events Information
            f.write("Omitted or Unexpected Stim Events\n")
            f.write("==================================\n")

            if omitted_events_df.empty:
                f.write("No omitted or unexpected stim events.\n")
            else:
                f.write(f"Total Omitted Events: {len(omitted_events_df)}\n\n")
                # Define column headers with fixed widths
                headers = f"{'Index':<15}{'Onset (s)':<20}{'Description':<30}{'Reason':<50}"
                f.write(headers + "\n")
                f.write(f"{'-' * len(headers)}\n")

                for idx, row in omitted_events_df.iterrows():
                    # Handle different types of omitted events
                    if 'stim_start_index' in row and 'stim_end_index' in row and not pd.isna(row['stim_start_index']) and not pd.isna(row['stim_end_index']):
                        index = f"{row['stim_start_index']} & {row['stim_end_index']}"
                        onset = f"{row['stim_start_onset']:.2f}s & {row['stim_end_onset']:.2f}s"
                        description = "stim start & stim end"
                    else:
                        index = "N/A"
                        onset = "N/A"
                        description = row.get('event_description', 'N/A')

                    reason = row.get('reason', 'N/A')

                    # Replace any remaining NaN with 'N/A'
                    index = index if not pd.isna(index) else 'N/A'
                    onset = onset if not pd.isna(onset) else 'N/A'
                    description = description if not pd.isna(description) else 'N/A'
                    reason = reason if not pd.isna(reason) else 'N/A'

                    # Write each row with fixed widths
                    f.write(f"{index:<15}{onset:<20}{description:<30}{reason:<50}\n")

        logging.info(f"Metadata saved to {output_file}")

    except Exception as e:
        logging.error(f"Failed to save EEG metadata: {e}")

