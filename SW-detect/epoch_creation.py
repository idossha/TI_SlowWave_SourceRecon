
# epoch_creation.py

import matplotlib.pyplot as plt
import os

def create_and_visualize_epochs(cleaned_events_df, output_dir):
    """
    Create pre-stim, stim, and post-stim epochs, adjust for overlaps, and visualize.

    Parameters:
    - cleaned_events_df: pd.DataFrame, DataFrame containing cleaned events.
    - output_dir: str, path to the output directory where images will be saved.

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
            # Define the exact overlap region before adjustments
            overlap_start = orig_pre_start
            overlap_end = orig_pre_start + overlap_amount
            overlaps.append({
                'protocols': (protocol_number - 1, protocol_number),
                'overlap_amount': overlap_amount,
                'overlap_start': overlap_start,
                'overlap_end': overlap_end
            })

            # Adjust the previous post-stim epoch only if there is a previous epoch
            if post_stim_epochs:
                # Calculate half of the overlap amount
                half_overlap = overlap_amount / 2

                # Adjust the previous post-stim epoch
                prev_protocol_num = post_stim_epochs[-1][2]
                prev_post_stim = post_stim_epochs[-1]
                adjusted_prev_post_stim_end = prev_post_stim[1] - half_overlap

                # Prevent negative duration
                if adjusted_prev_post_stim_end < prev_post_stim[0]:
                    print(f"Warning: Negative duration for post-stim epoch of Protocol {prev_protocol_num}. Setting to original start time.")
                    adjusted_prev_post_stim_end = prev_post_stim[0]

                # Update the last post-stim epoch with the adjusted end time
                post_stim_epochs[-1] = (prev_post_stim[0], adjusted_prev_post_stim_end, prev_protocol_num)

                # Adjust the current pre-stim epoch
                adjusted_pre_start = orig_pre_start + half_overlap
                if adjusted_pre_start > orig_pre_end:
                    print(f"Warning: Negative duration for pre-stim epoch of Protocol {protocol_number}. Setting to original end time.")
                    adjusted_pre_start = orig_pre_end

                pre_stim_start = adjusted_pre_start
                pre_stim_end = orig_pre_end

                print(f"Overlap detected between Protocol {prev_protocol_num} and Protocol {protocol_number}: {overlap_amount:.2f}s")
                print(f"  Adjusting Post-Stim End Time of Protocol {prev_protocol_num} by {-half_overlap:.2f}s to {adjusted_prev_post_stim_end:.2f}s")
                print(f"  Adjusting Pre-Stim Start Time of Protocol {protocol_number} by {half_overlap:.2f}s to {pre_stim_start:.2f}s\n")
            else:
                # No previous post-stim epoch to adjust
                print(f"Overlap detected for Protocol {protocol_number}, but no previous post-stim epoch to adjust.\n")
                # Adjust current pre-stim epoch by half the overlap
                half_overlap = overlap_amount / 2
                adjusted_pre_start = orig_pre_start + half_overlap
                if adjusted_pre_start > orig_pre_end:
                    print(f"Warning: Negative duration for pre-stim epoch of Protocol {protocol_number}. Setting to original end time.")
                    adjusted_pre_start = orig_pre_end
                pre_stim_start = adjusted_pre_start
                pre_stim_end = orig_pre_end

        else:
            # No overlap; keep original pre-stim epoch
            pre_stim_start = orig_pre_start
            pre_stim_end = orig_pre_end
            print(f"No overlap detected before Protocol {protocol_number}.\n")

        # Append adjusted epochs
        pre_stim_epochs.append((pre_stim_start, pre_stim_end, protocol_number))
        stim_epochs.append((orig_stim_start, orig_stim_end, protocol_number))
        post_stim_epochs.append((orig_post_start, orig_post_end, protocol_number))

        # Update the end of the previous post-stim epoch
        prev_post_stim_end = orig_post_end

        protocol_number += 1

    # Visualize the epochs
    visualize_epochs(
        original_pre_stim_epochs, original_stim_epochs, original_post_stim_epochs,
        pre_stim_epochs, stim_epochs, post_stim_epochs, overlaps, output_dir
    )

    # Plot durations between "stim start" and "stim end" events
    durations = calculate_durations(cleaned_events_df)
    plot_durations(durations, output_dir)

    return pre_stim_epochs, stim_epochs, post_stim_epochs, overlaps

def visualize_epochs(original_pre, original_stim, original_post,
                    adjusted_pre, adjusted_stim, adjusted_post, overlaps, output_dir):
    """
    Visualize epochs before and after overlap adjustments.

    Parameters:
    - original_pre, original_stim, original_post: lists of tuples for original epochs.
    - adjusted_pre, adjusted_stim, adjusted_post: lists of tuples for adjusted epochs.
    - overlaps: list of overlap information.
    - output_dir: directory to save plots.
    """
    # --- Plot 1: Before Overlap Removal ---
    fig, ax = plt.subplots(figsize=(15, 4))
    plot_epochs(original_pre, original_stim, original_post, ax, title="Protocols Before Overlap Removal")

    # Highlight overlaps
    for overlap in overlaps:
        ax.axvspan(overlap['overlap_start'], overlap['overlap_end'], color='red', alpha=0.5, label='Overlap')

    # Remove duplicate labels in the legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = {}
    for handle, label in zip(handles, labels):
        if label not in by_label:
            by_label[label] = handle
    ax.legend(by_label.values(), by_label.keys(), loc='upper right')

    # Save the "Before Overlap Removal" plot
    overlap_plot_path = os.path.join(output_dir, "protocols_before_overlap_removal.png")
    plt.tight_layout()
    plt.savefig(overlap_plot_path)
    plt.close(fig)
    print(f"Saved plot before overlap removal to {overlap_plot_path}")

    # --- Plot 2: After Overlap Removal ---
    fig, ax = plt.subplots(figsize=(15, 4))
    plot_epochs(adjusted_pre, adjusted_stim, adjusted_post, ax, title="Protocols After Overlap Removal")

    # Remove duplicate labels in the legend
    handles, labels = ax.get_legend_handles_labels()
    by_label = {}
    for handle, label in zip(handles, labels):
        if label not in by_label:
            by_label[label] = handle
    ax.legend(by_label.values(), by_label.keys(), loc='upper right')

    # Save the "After Overlap Removal" plot
    removal_plot_path = os.path.join(output_dir, "protocols_after_overlap_removal.png")
    plt.tight_layout()
    plt.savefig(removal_plot_path)
    plt.close(fig)
    print(f"Saved plot after overlap removal to {removal_plot_path}")

def plot_epochs(pre_stim_epochs, stim_epochs, post_stim_epochs, ax, title=""):
    """
    Helper function to plot pre-stim, stim, and post-stim epochs on a given axis.

    Parameters:
    - pre_stim_epochs: list of tuples, pre-stim epochs.
    - stim_epochs: list of tuples, stim epochs.
    - post_stim_epochs: list of tuples, post-stim epochs.
    - ax: matplotlib axis, axis to plot on.
    - title: str, title for the plot.
    """
    # To avoid duplicate labels in the legend
    pre_stim_plotted = False
    stim_plotted = False
    post_stim_plotted = False

    # Plot pre-stim epochs
    for (start, end, protocol) in pre_stim_epochs:
        if not pre_stim_plotted:
            ax.axvspan(start, end, color='blue', alpha=0.3, label='Pre-Stim')
            pre_stim_plotted = True
        else:
            ax.axvspan(start, end, color='blue', alpha=0.3)

    # Plot stim epochs
    for (start, end, protocol) in stim_epochs:
        if not stim_plotted:
            ax.axvspan(start, end, color='orange', alpha=0.3, label='Stim')
            stim_plotted = True
        else:
            ax.axvspan(start, end, color='orange', alpha=0.3)
        # Add protocol number
        ax.text((start + end) / 2, 0.5, f'P{protocol}', color='black', fontsize=9, ha='center', va='bottom')

    # Plot post-stim epochs
    for (start, end, protocol) in post_stim_epochs:
        if not post_stim_plotted:
            ax.axvspan(start, end, color='green', alpha=0.3, label='Post-Stim')
            post_stim_plotted = True
        else:
            ax.axvspan(start, end, color='green', alpha=0.3)

    # Set labels and title
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('')
    ax.set_title(title)
    ax.set_yticks([])  # Hide y-axis ticks for a cleaner look
    ax.grid(True, linestyle='--', alpha=0.5)

def plot_durations(durations, output_dir):
    """
    Plot durations between "stim start" and "stim end" events and save as a .png file.

    Parameters:
    - durations: list of float, durations in seconds.
    - output_dir: str, directory to save the plot.
    """
    plt.figure(figsize=(10, 5))
    plt.plot(durations, marker='o', linestyle='-', color='purple')
    plt.axhline(y=170, color='r', linestyle='--', label='Min Duration (170s)')
    plt.axhline(y=220, color='r', linestyle='--', label='Max Duration (220s)')
    plt.xlabel('Stim Pair Index')
    plt.ylabel('Duration (s)')
    plt.title('Durations Between "stim start" and "stim end" Events')
    plt.legend()
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

