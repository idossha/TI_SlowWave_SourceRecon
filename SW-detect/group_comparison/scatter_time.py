
import os
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


'''
python group_time.py \
    --project_dir /Volumes/CSC-Ido/Analyze  \
    --subjects 101 102 109 112 114 115 116 117 120 121 122 129 131 \
    --nights N1 \
    --output_dir /Users/idohaber/Desktop/output
'''



def load_data_for_subject_night(project_dir, subject, night):
    """
    Load the CSV for a given subject and night.
    File path structure:
      {project_dir}/{subject}/{night}/output/Strength_{subject}_{night}_forSW/filtered_epochs_500ms_first.csv
    """
    csv_path = os.path.join(
        project_dir,
        str(subject),
        str(night),
        "output",
        f"Strength_{subject}_{night}_forSW",
        "filtered_epochs_500ms_first.csv"
    )
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    
    return pd.read_csv(csv_path)

def plot_scatter_with_trend(ax, 
                            x, 
                            y, 
                            label,
                            color, 
                            overall=False,
                            dot_size=1):
    """
    Scatter-plot (x,y) in color with label, 
    then add a linear fit.
    
    Parameters:
    -----------
    ax : matplotlib.axes.Axes
        The axes to plot on.
    x, y : array-like
        Data coordinates.
    label : str
        Label for the scatter/trend line.
    color : str or tuple
        Color of the scatter points and line.
    overall : bool
        If True, use dashed style for the overall trend line.
    dot_size : float
        Size of the scatter dots.
    """
    # Plot scatter with smaller point size
    ax.scatter(x, y, color=color, alpha=0.7, s=dot_size, label=label)
    
    # Trend line
    if len(x) > 1:
        coeffs = np.polyfit(x, y, 1)  # [slope, intercept]
        poly = np.poly1d(coeffs)
        style = '--' if overall else '-'
        # Add a separate label for the trend line if you like,
        # or reuse label (some prefer separate labeling).
        trend_label = None if overall else None
        ax.plot(x, poly(x), style, color=color, label=trend_label)

def main():
    parser = argparse.ArgumentParser(
        description="Script to plot Slow Wave metrics vs. time."
    )
    parser.add_argument(
        "--project_dir", "-p", 
        type=str, 
        required=True, 
        help="Path to the project directory containing CSV files."
    )
    parser.add_argument(
        "--subjects", "-s", 
        nargs="+", 
        required=True, 
        help="List of subject IDs."
    )
    parser.add_argument(
        "--nights", "-n", 
        nargs="+", 
        required=True, 
        help="List of nights to include."
    )
    parser.add_argument(
        "--output_dir", "-o",
        type=str,
        default=None,
        help="(Optional) Output directory for saved figures. If omitted, uses project_dir."
    )
    
    args = parser.parse_args()

    project_dir = args.project_dir
    output_dir = args.output_dir if args.output_dir else project_dir

    subjects = args.subjects
    nights = args.nights

    # Lists to hold combined data across subjects/nights (for overall trend lines)
    all_times_slope = []
    all_slope_vals = []

    all_times_freq = []
    all_freq_vals = []

    all_times_ptp = []
    all_ptp_vals = []

    # Prepare color cycle
    color_cycle = plt.cm.tab10.colors
    color_mapping = {}
    # Ensure enough colors if many subjects
    while len(color_cycle) < len(subjects):
        color_cycle += color_cycle

    # Setup the figure and axes for Slope vs. Time
    fig_slope, ax_slope = plt.subplots(figsize=(8, 5))
    ax_slope.set_title("Slope vs. Time")
    ax_slope.set_xlabel("Time (s)")
    ax_slope.set_ylabel("Slope")

    # Setup the figure and axes for Frequency vs. Time
    fig_freq, ax_freq = plt.subplots(figsize=(8, 5))
    ax_freq.set_title("Frequency vs. Time")
    ax_freq.set_xlabel("Time (s)")
    ax_freq.set_ylabel("Frequency (Hz)")

    # Setup the figure and axes for PTP vs. Time
    fig_ptp, ax_ptp = plt.subplots(figsize=(8, 5))
    ax_ptp.set_title("PTP vs. Time")
    ax_ptp.set_xlabel("Time (s)")
    ax_ptp.set_ylabel("Peak-to-Peak Amplitude")

    # Assign each subject a color
    for i, subject in enumerate(subjects):
        color_mapping[subject] = color_cycle[i]

    # For each subject, collect data across nights
    for subject in subjects:
        subj_color = color_mapping[subject]

        subject_times_slope = []
        subject_slope_vals = []

        subject_times_freq = []
        subject_freq_vals = []

        subject_times_ptp = []
        subject_ptp_vals = []

        for night in nights:
            try:
                df = load_data_for_subject_night(project_dir, subject, night)
            except FileNotFoundError:
                print(f"Warning: Could not find data for {subject}-{night}. Skipping.")
                continue
            
            # Modify column names if your CSV differs:
            # Here we assume columns: "Start", "Slope", "Frequency", "PTP"
            t = df["Start"].values
            slope = df["Slope"].values
            freq = df["Frequency"].values
            ptp = df["PTP"].values

            # Accumulate subject data
            subject_times_slope.extend(t)
            subject_slope_vals.extend(slope)

            subject_times_freq.extend(t)
            subject_freq_vals.extend(freq)

            subject_times_ptp.extend(t)
            subject_ptp_vals.extend(ptp)

            # Also accumulate for overall trend
            all_times_slope.extend(t)
            all_slope_vals.extend(slope)

            all_times_freq.extend(t)
            all_freq_vals.extend(freq)

            all_times_ptp.extend(t)
            all_ptp_vals.extend(ptp)

        # Plot combined data from all nights for this subject
        if subject_times_slope:
            plot_scatter_with_trend(
                ax_slope,
                np.array(subject_times_slope),
                np.array(subject_slope_vals),
                label=f"{subject}",
                color=subj_color,
                dot_size=3
            )
        if subject_times_freq:
            plot_scatter_with_trend(
                ax_freq,
                np.array(subject_times_freq),
                np.array(subject_freq_vals),
                label=f"{subject}",
                color=subj_color,
                dot_size=3
            )
        if subject_times_ptp:
            plot_scatter_with_trend(
                ax_ptp,
                np.array(subject_times_ptp),
                np.array(subject_ptp_vals),
                label=f"{subject}",
                color=subj_color,
                dot_size=3
            )

    # Add overall trend lines (dashed) across all subjects/nights
    # For Slope
    if len(all_times_slope) > 1:
        all_times_slope_arr = np.array(all_times_slope)
        all_slope_vals_arr = np.array(all_slope_vals)
        coeffs_slope = np.polyfit(all_times_slope_arr, all_slope_vals_arr, 1)
        poly_slope = np.poly1d(coeffs_slope)
        ax_slope.plot(all_times_slope_arr, 
                      poly_slope(all_times_slope_arr),
                      '--',
                      color='black',
                      label='Overall Trend')
    # For Frequency
    if len(all_times_freq) > 1:
        all_times_freq_arr = np.array(all_times_freq)
        all_freq_vals_arr = np.array(all_freq_vals)
        coeffs_freq = np.polyfit(all_times_freq_arr, all_freq_vals_arr, 1)
        poly_freq = np.poly1d(coeffs_freq)
        ax_freq.plot(all_times_freq_arr, 
                     poly_freq(all_times_freq_arr),
                     '--',
                     color='black',
                     label='Overall Trend')
    # For PTP
    if len(all_times_ptp) > 1:
        all_times_ptp_arr = np.array(all_times_ptp)
        all_ptp_vals_arr = np.array(all_ptp_vals)
        coeffs_ptp = np.polyfit(all_times_ptp_arr, all_ptp_vals_arr, 1)
        poly_ptp = np.poly1d(coeffs_ptp)
        ax_ptp.plot(all_times_ptp_arr, 
                    poly_ptp(all_times_ptp_arr),
                    '--',
                    color='black',
                    label='Overall Trend')

    # If you'd like legends, do so here with smaller font
    # (comment out if you prefer no legend at all):
    legend_kwargs = {"prop": {"size": 6}}  # significantly smaller text
    ax_slope.legend(**legend_kwargs)
    ax_freq.legend(**legend_kwargs)
    ax_ptp.legend(**legend_kwargs)

    # Save figures
    slope_plot_path = os.path.join(output_dir, "Slope_vs_Time.png")
    freq_plot_path  = os.path.join(output_dir, "Frequency_vs_Time.png")
    ptp_plot_path   = os.path.join(output_dir, "PTP_vs_Time.png")

    fig_slope.savefig(slope_plot_path, dpi=150)
    fig_freq.savefig(freq_plot_path, dpi=150)
    fig_ptp.savefig(ptp_plot_path,  dpi=150)

    print(f"Saved slope plot to: {slope_plot_path}")
    print(f"Saved frequency plot to: {freq_plot_path}")
    print(f"Saved PTP plot to: {ptp_plot_path}")

    # Uncomment if you want to show plots interactively:
    # plt.show()

if __name__ == "__main__":
    main()
