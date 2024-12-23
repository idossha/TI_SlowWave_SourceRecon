
# epoch_creation.py

import matplotlib.pyplot as plt
import os

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
    # Ensure the DataFrame is sorted by onset time
    cleaned_events_df = cleaned_events_df.sort_values(by='Onset').reset_index(drop=True)

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
    for i in range(0, len(cleaned_events_df), 2):
        if i + 1 >= len(cleaned_events_df):
            print(f"Warning: Unpaired event at index {i}. Skipping.")
            break  # Avoid index out of range

        stim_start_event = cleaned_events_df.iloc[i]
        stim_end_event = cleaned_events_df.iloc[i + 1]

        stim_start = stim_start_event["Onset"]
        stim_end = stim_end_event["Onset"]
        stim_duration = stim_end - stim_start

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
                post_stim_epochs[-1] = (
                    post_stim_epochs[-1][0],
                    post_stim_epochs[-1][1] - half_overlap,
                    post_stim_epochs[-1][2]
                )
            orig_pre_start += half_overlap
            overlaps.append({
                'protocols': (protocol_number - 1, protocol_number),
                'overlap_amount': overlap_amount,
                'overlap_start': orig_pre_start - half_overlap,
                'overlap_end': orig_pre_start
            })

        pre_stim_epochs.append((orig_pre_start, orig_pre_end, protocol_number))
        stim_epochs.append((orig_stim_start, orig_stim_end, protocol_number))
        post_stim_epochs.append((orig_post_start, orig_post_end, protocol_number))

        # Update the end of the previous post-stim epoch
        prev_post_stim_end = orig_post_end
        protocol_number += 1

    # Visualize the epochs
    visualize_epochs(
        original_pre_stim_epochs, original_stim_epochs, original_post_stim_epochs,
        pre_stim_epochs, stim_epochs, post_stim_epochs, overlaps, output_dir, sf
    )

    # Plot durations between "stim start" and "stim end" events
    durations = calculate_durations(cleaned_events_df)
    plot_durations(durations, output_dir)

    return pre_stim_epochs, stim_epochs, post_stim_epochs, overlaps


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
    def seconds_to_hours(seconds):
        return seconds / 3600.0

    # Plot before overlap removal
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
    plt.savefig(os.path.join(output_dir, "before_overlap_removal.png"))
    plt.close(fig)
    print(f"Saved plot before overlap removal to {os.path.join(output_dir, 'before_overlap_removal.png')}")

    # Plot after overlap removal
    fig, ax = plt.subplots(figsize=(15, 4))
    plot_epochs(adjusted_pre, adjusted_stim, adjusted_post, ax, "After Overlap Removal", sf)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "after_overlap_removal.png"))
    plt.close(fig)
    print(f"Saved plot after overlap removal to {os.path.join(output_dir, 'after_overlap_removal.png')}")


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

    # No immediate legend assignment here; handled in visualize_epochs
    # to allow for additional elements like overlaps


def plot_durations(durations, output_dir):
    """
    Plot durations between "stim start" and "stim end" events and save as a .png file.

    Parameters:
    - durations: list of float, durations in seconds.
    - output_dir: str, directory to save the plot.
    """
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
    print(f"Saved durations plot to {durations_plot_path}")


def calculate_durations(cleaned_events_df):
    """
    Calculate durations between 'stim start' and 'stim end' events.

    Parameters:
    - cleaned_events_df: pd.DataFrame, DataFrame containing cleaned events.

    Returns:
    - durations: list of float, durations in seconds.
    """
    stim_starts = cleaned_events_df[cleaned_events_df["Description"] == "stim start"]["Onset"].values
    stim_ends = cleaned_events_df[cleaned_events_df["Description"] == "stim end"]["Onset"].values

    durations = []
    for start, end in zip(stim_starts, stim_ends):
        duration = end - start
        durations.append(duration)

    return durations

