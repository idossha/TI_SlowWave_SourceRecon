
# epoch_creation.py

import logging
import matplotlib.pyplot as plt
import os
import pandas as pd

# Create a module-level logger
logger = logging.getLogger(__name__)

def create_and_visualize_epochs(cleaned_events_df, output_dir, sf):
    """
    Create pre-stim, stim, and post-stim epochs, adjust for overlaps, and visualize.

    Parameters:
    - cleaned_events_df: pd.DataFrame, DataFrame containing cleaned events.
    - output_dir: str, path to the output directory where images will be saved.
    - sf: float, sampling frequency (Hz) for time-to-hours conversion.

    Returns:
    - pre_stim_epochs: list of tuples for pre-stim epochs.
    - stim_epochs: list of tuples for stim epochs.
    - post_stim_epochs: list of tuples for post-stim epochs.
    - overlaps: list of dictionaries containing overlap information.
    """
    logger.info("Starting epoch creation and visualization process.")

    try:
        # Ensure the DataFrame is sorted by onset time
        cleaned_events_df = cleaned_events_df.sort_values(by='Onset').reset_index(drop=True)
        logger.debug("Cleaned events DataFrame sorted by 'Onset'.")

        # Initialize epoch lists
        pre_stim_epochs = []
        stim_epochs = []
        post_stim_epochs = []

        # Protocol counter
        protocol_number = 1

        # Track the end of the previous post-stim epoch
        prev_post_stim_end = 0

        # List to record overlaps
        overlaps = []

        # Lists to store original epochs for plotting before adjustments
        original_pre_stim_epochs = []
        original_stim_epochs = []
        original_post_stim_epochs = []

        # Iterate through events in pairs (stim_start and stim_end)
        logger.info("Iterating through cleaned events to create epochs.")
        for i in range(0, len(cleaned_events_df), 2):
            if i + 1 >= len(cleaned_events_df):
                logger.warning(f"Unpaired event at index {i}. Skipping.")
                break  # Avoid index out of range

            stim_start_event = cleaned_events_df.iloc[i]
            stim_end_event = cleaned_events_df.iloc[i + 1]

            stim_start = stim_start_event["Onset"]
            stim_end = stim_end_event["Onset"]
            stim_duration = stim_end - stim_start

            logger.debug(f"Processing Protocol {protocol_number}: stim_start at {stim_start}s, stim_end at {stim_end}s, duration {stim_duration}s.")

            # Define original epochs
            orig_pre_start = stim_start - stim_duration
            orig_pre_end = stim_start

            orig_stim_start = stim_start
            orig_stim_end = stim_end

            orig_post_start = stim_end
            orig_post_end = stim_end + stim_duration

            # Store original epochs
            original_pre_stim_epochs.append((orig_pre_start, orig_pre_end, protocol_number))
            original_stim_epochs.append((orig_stim_start, orig_stim_end, protocol_number))
            original_post_stim_epochs.append((orig_post_start, orig_post_end, protocol_number))

            # Check for overlap with previous post-stim epoch
            overlap_amount = prev_post_stim_end - orig_pre_start
            if overlap_amount > 0:
                half_overlap = overlap_amount / 2
                if post_stim_epochs:
                    old_post = post_stim_epochs[-1]
                    new_post = (
                        old_post[0],
                        old_post[1] - half_overlap,
                        old_post[2]
                    )
                    post_stim_epochs[-1] = new_post
                    logger.info(f"Adjusted Protocol {old_post[2]}'s post-stim epoch by reducing {half_overlap}s to remove overlap.")
                orig_pre_start += half_overlap
                overlaps.append({
                    'protocols': (protocol_number - 1, protocol_number),
                    'overlap_amount': overlap_amount,
                    'overlap_start': orig_pre_start - half_overlap,
                    'overlap_end': orig_pre_start
                })
                logger.info(f"Overlap detected between Protocol {protocol_number - 1} and Protocol {protocol_number}: {overlap_amount}s.")

            pre_stim_epochs.append((orig_pre_start, orig_pre_end, protocol_number))
            stim_epochs.append((orig_stim_start, orig_stim_end, protocol_number))
            post_stim_epochs.append((orig_post_start, orig_post_end, protocol_number))

            # Update the end of the previous post-stim epoch
            prev_post_stim_end = orig_post_end
            protocol_number += 1

        logger.info("Epoch creation completed. Proceeding to visualization.")

        # Visualize the epochs
        visualize_epochs(
            original_pre_stim_epochs, original_stim_epochs, original_post_stim_epochs,
            pre_stim_epochs, stim_epochs, post_stim_epochs, overlaps, output_dir, sf
        )

        # Plot durations between "stim start" and "stim end" events
        durations = calculate_durations(cleaned_events_df)
        plot_durations(durations, output_dir)

        logger.info("Epoch creation and visualization process completed successfully.")

        return pre_stim_epochs, stim_epochs, post_stim_epochs, overlaps

    except Exception as e:
        logger.error(f"An error occurred during epoch creation and visualization: {e}", exc_info=True)
        raise  # Re-raise the exception to allow upstream handling


def visualize_epochs(original_pre, original_stim, original_post,
                     adjusted_pre, adjusted_stim, adjusted_post, overlaps, output_dir, sf):
    """
    Visualize epochs before and after overlap adjustments with time in hours.

    Parameters:
    - original_pre, original_stim, original_post: lists of tuples for original epochs.
    - adjusted_pre, adjusted_stim, adjusted_post: lists of tuples for adjusted epochs.
    - overlaps: list of overlap information. Each overlap is a dict with 'overlap_start' and 'overlap_end' in seconds.
    - output_dir: directory to save plots.
    - sf: Sampling frequency (in Hz).
    """
    logger.info("Starting visualization of epochs.")

    def seconds_to_hours(seconds):
        return seconds / 3600.0

    try:
        # Plot before overlap removal
        logger.debug("Plotting epochs before overlap removal.")
        fig, ax = plt.subplots(figsize=(15, 4))
        plot_epochs(original_pre, original_stim, original_post, ax, "Before Overlap Removal", sf)
        for overlap in overlaps:
            ax.axvspan(
                seconds_to_hours(overlap['overlap_start']),
                seconds_to_hours(overlap['overlap_end']),
                color='red', alpha=0.5, label='Overlap'
            )
        # Deduplicate legend entries
        handles, labels = ax.get_legend_handles_labels()
        unique_labels = {}
        for handle, label in zip(handles, labels):
            if label not in unique_labels:
                unique_labels[label] = handle
        ax.legend(unique_labels.values(), unique_labels.keys(), loc='upper right')
        plt.tight_layout()
        before_overlap_path = os.path.join(output_dir, "before_overlap_removal.png")
        plt.savefig(before_overlap_path)
        plt.close(fig)
        logger.info(f"Saved plot before overlap removal to {before_overlap_path}")

        # Plot after overlap removal
        logger.debug("Plotting epochs after overlap removal.")
        fig, ax = plt.subplots(figsize=(15, 4))
        plot_epochs(adjusted_pre, adjusted_stim, adjusted_post, ax, "After Overlap Removal", sf)
        plt.tight_layout()
        after_overlap_path = os.path.join(output_dir, "after_overlap_removal.png")
        plt.savefig(after_overlap_path)
        plt.close(fig)
        logger.info(f"Saved plot after overlap removal to {after_overlap_path}")

    except Exception as e:
        logger.error(f"An error occurred during epoch visualization: {e}", exc_info=True)
        raise  # Re-raise the exception to allow upstream handling


def plot_epochs(pre_stim_epochs, stim_epochs, post_stim_epochs, ax, title, sf):
    """
    Helper function to plot pre-stim, stim, and post-stim epochs on a given axis with time in hours.

    Parameters:
    - pre_stim_epochs: list of tuples, pre-stim epochs. Each tuple: (start, end, protocol)
    - stim_epochs: list of tuples, stim epochs. Each tuple: (start, end, protocol)
    - post_stim_epochs: list of tuples, post-stim epochs. Each tuple: (start, end, protocol)
    - ax: matplotlib axis, axis to plot on.
    - title: str, title for the plot.
    - sf: Sampling frequency (in Hz). Used to convert time from seconds to hours.
    """
    logger.debug(f"Plotting epochs: {title}")

    def seconds_to_hours(seconds):
        return seconds / 3600.0

    # Flags to check if labels have been added
    pre_stim_label_added = False
    stim_label_added = False
    post_stim_label_added = False

    # Plot pre-stim epochs
    for start, end, _ in pre_stim_epochs:
        if not pre_stim_label_added:
            ax.axvspan(seconds_to_hours(start), seconds_to_hours(end), color='blue', alpha=0.3, label='Pre-Stim')
            pre_stim_label_added = True
        else:
            ax.axvspan(seconds_to_hours(start), seconds_to_hours(end), color='blue', alpha=0.3)

    # Plot stim epochs
    for start, end, protocol in stim_epochs:
        if not stim_label_added:
            ax.axvspan(seconds_to_hours(start), seconds_to_hours(end), color='orange', alpha=0.3, label='Stim')
            stim_label_added = True
        else:
            ax.axvspan(seconds_to_hours(start), seconds_to_hours(end), color='orange', alpha=0.3)
        # Optionally, add protocol number
        ax.text((seconds_to_hours(start) + seconds_to_hours(end)) / 2, 0.5, f'P{protocol}', color='black', fontsize=9, ha='center', va='bottom')

    # Plot post-stim epochs
    for start, end, _ in post_stim_epochs:
        if not post_stim_label_added:
            ax.axvspan(seconds_to_hours(start), seconds_to_hours(end), color='green', alpha=0.3, label='Post-Stim')
            post_stim_label_added = True
        else:
            ax.axvspan(seconds_to_hours(start), seconds_to_hours(end), color='green', alpha=0.3)

    ax.set_title(title)
    ax.set_xlabel("Time (hours)")
    ax.set_ylabel("Epochs")
    # No need to set y-ticks as epochs are represented by spans
    ax.set_yticks([])
    ax.grid(True, linestyle='--', alpha=0.5)

    logger.debug(f"Completed plotting epochs: {title}")


def plot_durations(durations, output_dir):
    """
    Plot durations between "stim start" and "stim end" events and save as a .png file.

    Parameters:
    - durations: list of float, durations in seconds.
    - output_dir: str, directory to save the plot.
    """
    logger.info("Starting to plot durations between 'stim start' and 'stim end' events.")

    try:
        plt.figure(figsize=(10, 5))
        plt.plot(durations, marker='o', linestyle='-', color='purple', label='Duration')
        plt.axhline(y=170, color='r', linestyle='--', label='Min Duration (170s)')
        plt.axhline(y=220, color='r', linestyle='--', label='Max Duration (220s)')
        plt.xlabel('Stim Pair Index')
        plt.ylabel('Duration (s)')
        plt.title('Durations Between "stim start" and "stim end" Events')
        # Deduplicate legend entries
        handles, labels = plt.gca().get_legend_handles_labels()
        unique_labels = {}
        for handle, label in zip(handles, labels):
            if label not in unique_labels:
                unique_labels[label] = handle
        plt.legend(unique_labels.values(), unique_labels.keys())
        plt.grid(True)
        durations_plot_path = os.path.join(output_dir, "stim_durations.png")
        plt.tight_layout()
        plt.savefig(durations_plot_path)
        plt.close()
        logger.info(f"Saved durations plot to {durations_plot_path}")

    except Exception as e:
        logger.error(f"An error occurred while plotting durations: {e}", exc_info=True)
        raise  # Re-raise the exception to allow upstream handling


def calculate_durations(cleaned_events_df):
    """
    Calculate durations between 'stim start' and 'stim end' events.

    Parameters:
    - cleaned_events_df: pd.DataFrame, DataFrame containing cleaned events.

    Returns:
    - durations: list of float, durations in seconds.
    """
    logger.info("Calculating durations between 'stim start' and 'stim end' events.")

    try:
        stim_starts = cleaned_events_df[cleaned_events_df["Description"] == "stim start"]["Onset"].values
        stim_ends = cleaned_events_df[cleaned_events_df["Description"] == "stim end"]["Onset"].values

        durations = []
        for start, end in zip(stim_starts, stim_ends):
            duration = end - start
            durations.append(duration)
            logger.debug(f"Calculated duration: {duration:.2f}s between {start}s and {end}s.")

        logger.info(f"Total durations calculated: {len(durations)}")
        return durations

    except Exception as e:
        logger.error(f"An error occurred while calculating durations: {e}", exc_info=True)
        raise  # Re-raise the exception to allow upstream handling

