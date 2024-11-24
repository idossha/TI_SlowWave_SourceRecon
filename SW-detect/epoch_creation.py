# epoch_creation.py

def create_epochs(cleaned_events_df):
    """
    Create pre-stim, stim, and post-stim epochs and adjust for overlaps.

    Parameters:
    - cleaned_events_df: pd.DataFrame, DataFrame containing cleaned events.

    Returns:
    - pre_stim_epochs: list, list of tuples for pre-stim epochs.
    - stim_epochs: list, list of tuples for stim epochs.
    - post_stim_epochs: list, list of tuples for post-stim epochs.
    - overlaps: list, list of dictionaries containing overlap information.
    """
    # Ensure that cleaned_events_df is sorted by onset time and reset index
    cleaned_events_df = cleaned_events_df.sort_values(by='Onset').reset_index(drop=True)

    # Initialize lists for epochs
    pre_stim_epochs = []
    stim_epochs = []
    post_stim_epochs = []

    # Protocol counter
    protocol_number = 1

    # Previous protocol's post-stim epoch
    prev_post_stim_end = 0

    # List to keep track of overlaps
    overlaps = []

    # Loop through the cleaned events to define epochs
    for i in range(0, len(cleaned_events_df), 2):
        if i + 1 < len(cleaned_events_df):  # Ensure i+1 is within bounds
            stim_start_event = cleaned_events_df.iloc[i]
            stim_end_event = cleaned_events_df.iloc[i + 1]

            # Extract onset times in seconds
            stim_start = stim_start_event["Onset"]
            stim_end = stim_end_event["Onset"]
            stim_duration = stim_end - stim_start

            # Define initial pre-stim, stim, and post-stim epochs
            pre_stim_start = stim_start - stim_duration
            pre_stim_end = stim_start

            stim_epoch_start = stim_start
            stim_epoch_end = stim_end

            post_stim_start = stim_end
            post_stim_end = stim_end + stim_duration

            # Check for overlap with the previous protocol's post-stim epoch
            overlap_amount = prev_post_stim_end - pre_stim_start
            if overlap_amount > 0:
                # Calculate half of the overlap amount
                half_overlap = overlap_amount / 2

                # Adjust the previous protocol's post-stim epoch
                if len(post_stim_epochs) > 0:
                    prev_protocol = protocol_number - 1
                    prev_post_stim = post_stim_epochs[-1]
                    adjusted_prev_post_stim_end = prev_post_stim[1] - half_overlap
                    if adjusted_prev_post_stim_end < prev_post_stim[0]:
                        adjusted_prev_post_stim_end = prev_post_stim[0]
                    post_stim_epochs[-1] = (prev_post_stim[0], adjusted_prev_post_stim_end, prev_post_stim[2])

                # Adjust the current protocol's pre-stim epoch
                adjusted_pre_stim_start = pre_stim_start + half_overlap
                if adjusted_pre_stim_start > pre_stim_end:
                    adjusted_pre_stim_start = pre_stim_end
                pre_stim_start = adjusted_pre_stim_start

                # Record the overlap details
                overlaps.append({
                    'protocols': (protocol_number - 1, protocol_number),
                    'overlap_amount': overlap_amount,
                    'adjusted_prev_post_stim_end': adjusted_prev_post_stim_end,
                    'adjusted_pre_stim_start': pre_stim_start
                })

            # Update prev_post_stim_end to the end of the current post-stim epoch (after adjustment)
            prev_post_stim_end = post_stim_end

            # Append epochs with protocol number
            pre_stim_epochs.append((pre_stim_start, pre_stim_end, protocol_number))
            stim_epochs.append((stim_epoch_start, stim_epoch_end, protocol_number))
            post_stim_epochs.append((post_stim_start, post_stim_end, protocol_number))

            protocol_number += 1

    return pre_stim_epochs, stim_epochs, post_stim_epochs, overlaps

