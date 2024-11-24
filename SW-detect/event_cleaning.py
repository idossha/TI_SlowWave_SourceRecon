# event_cleaning.py

import pandas as pd

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
    annotations_df = pd.DataFrame({
        "Onset": raw.annotations.onset,
        "Duration": raw.annotations.duration,
        "Description": raw.annotations.description,
    })

    stim_events = annotations_df[annotations_df["Description"].isin(["stim start", "stim end"])].reset_index(drop=True)

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
            elif expected_event == 'stim end':
                stim_end_event = current_event
                time_diff = stim_end_event["Onset"] - stim_start_event["Onset"]
                if min_duration <= time_diff <= max_duration:
                    cleaned_events.append(stim_start_event)
                    cleaned_events.append(stim_end_event)
                    expected_event = 'stim start'  # Reset expected event
                else:
                    omitted_events.append({
                        'stim_start_index': stim_start_event.name,
                        'stim_start_onset': stim_start_event["Onset"],
                        'stim_end_index': stim_end_event.name,
                        'stim_end_onset': stim_end_event["Onset"],
                        'reason': f'Invalid duration ({time_diff:.2f}s)'
                    })
                    expected_event = 'stim start'  # Reset expected event
            i += 1  # Move to the next event
        else:
            omitted_events.append({
                'event_index': current_event.name,
                'event_onset': current_event["Onset"],
                'event_description': current_event["Description"],
                'reason': f"Unexpected event '{current_event['Description']}'"
            })
            i += 1  # Move to the next event
            expected_event = 'stim start'  # Reset expected event in case of mismatch

    cleaned_events_df = pd.DataFrame(cleaned_events).reset_index(drop=True)
    omitted_events_df = pd.DataFrame(omitted_events)

    # Calculate durations between 'stim start' and 'stim end' in the original data
    durations = []
    i = 0
    while i < len(stim_events) - 1:
        if stim_events.iloc[i]["Description"] == 'stim start' and stim_events.iloc[i+1]["Description"] == 'stim end':
            duration = stim_events.iloc[i+1]["Onset"] - stim_events.iloc[i]["Onset"]
            durations.append(duration)
            i += 2  # Skip to the next pair
        else:
            i += 1  # Move to the next event

    return cleaned_events_df, durations, omitted_events_df
