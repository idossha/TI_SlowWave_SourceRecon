
# event_cleaning.py

import logging
import pandas as pd

# Create a module-level logger
logger = logging.getLogger(__name__)

def clean_events(raw):
    """
    Clean and validate 'stim start' and 'stim end' events from the raw EEG data.

    Parameters:
    - raw: mne.io.Raw, the preprocessed raw EEG data.

    Returns:
    - cleaned_events_df: pd.DataFrame, DataFrame containing cleaned events.
    - durations: list, list of durations between 'stim start' and 'stim end'.
    - omitted_events_df: pd.DataFrame, DataFrame containing omitted events.
    """
    logger.info("Starting event cleaning process.")

    try:
        # Extract annotations from raw data
        annotations_df = pd.DataFrame({
            "Onset": raw.annotations.onset,
            "Duration": raw.annotations.duration,
            "Description": raw.annotations.description,
        })
        logger.debug(f"Total annotations extracted: {len(annotations_df)}")

        # Filter for 'stim start' and 'stim end' events
        stim_events = annotations_df[annotations_df["Description"].isin(["stim start", "stim end"])].reset_index(drop=True)
        logger.info(f"Number of 'stim start' and 'stim end' events found: {len(stim_events)}")

        cleaned_events = []
        expected_event = 'stim start'  # The sequence should start with 'stim start'
        min_duration = 170  # Minimum acceptable duration in seconds
        max_duration = 220  # Maximum acceptable duration in seconds
        i = 0  # Index counter

        omitted_events = []

        while i < len(stim_events):
            current_event = stim_events.iloc[i]
            if current_event["Description"] == expected_event:
                if expected_event == 'stim start':
                    stim_start_event = current_event
                    expected_event = 'stim end'
                    logger.debug(f"Found expected event: '{expected_event}' at onset {stim_start_event['Onset']}s")
                elif expected_event == 'stim end':
                    stim_end_event = current_event
                    time_diff = stim_end_event["Onset"] - stim_start_event["Onset"]
                    logger.debug(f"Duration between 'stim start' and 'stim end': {time_diff:.2f}s")

                    if min_duration <= time_diff <= max_duration:
                        cleaned_events.append(stim_start_event)
                        cleaned_events.append(stim_end_event)
                        logger.info(f"Valid event pair added: 'stim start' at {stim_start_event['Onset']}s and 'stim end' at {stim_end_event['Onset']}s")
                        expected_event = 'stim start'  # Reset expected event
                    else:
                        omitted_events.append({
                            'stim_start_index': stim_start_event.name,
                            'stim_start_onset': stim_start_event["Onset"],
                            'stim_end_index': stim_end_event.name,
                            'stim_end_onset': stim_end_event["Onset"],
                            'reason': f'Invalid duration ({time_diff:.2f}s)'
                        })
                        logger.warning(
                            f"Omitted event pair due to invalid duration ({time_diff:.2f}s): "
                            f"'stim start' at {stim_start_event['Onset']}s and 'stim end' at {stim_end_event['Onset']}s"
                        )
                        expected_event = 'stim start'  # Reset expected event
                i += 1  # Move to the next event
            else:
                omitted_events.append({
                    'event_index': current_event.name,
                    'event_onset': current_event["Onset"],
                    'event_description': current_event["Description"],
                    'reason': f"Unexpected event '{current_event['Description']}'"
                })
                logger.warning(
                    f"Omitted unexpected event: '{current_event['Description']}' at {current_event['Onset']}s"
                )
                i += 1  # Move to the next event
                expected_event = 'stim start'  # Reset expected event in case of mismatch

        cleaned_events_df = pd.DataFrame(cleaned_events).reset_index(drop=True)
        omitted_events_df = pd.DataFrame(omitted_events)

        logger.info(f"Total cleaned events: {len(cleaned_events_df)}")
        logger.info(f"Total omitted events: {len(omitted_events_df)}")

        # Calculate durations between 'stim start' and 'stim end' in the original data
        durations = []
        i = 0
        while i < len(stim_events) - 1:
            if stim_events.iloc[i]["Description"] == 'stim start' and stim_events.iloc[i+1]["Description"] == 'stim end':
                duration = stim_events.iloc[i+1]["Onset"] - stim_events.iloc[i]["Onset"]
                durations.append(duration)
                logger.debug(f"Calculated duration: {duration:.2f}s between events at {stim_events.iloc[i]['Onset']}s and {stim_events.iloc[i+1]['Onset']}s")
                i += 2  # Skip to the next pair
            else:
                i += 1  # Move to the next event

        logger.info("Event cleaning process completed successfully.")
        return cleaned_events_df, durations, omitted_events_df

    except Exception as e:
        logger.error(f"An error occurred during event cleaning: {e}", exc_info=True)
        raise  # Re-raise the exception to allow upstream handling

