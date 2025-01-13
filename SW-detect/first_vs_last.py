
# compare_slopes.py

import os
import pandas as pd
import matplotlib.pyplot as plt


def slopes_first_vs_last(csv_path, output_dir):
    """
    Loads 'original_detection.csv', selects waves in the first hour and last hour,
    then compares and plots the Slope, PTP, and Frequency values as violin plots.

    Three .png files will be created in:
        output_dir/first_vs_last/images/
    Each file shows how a parameter changes between the first and last hour.
    The plots also display the mean values in the title.
    """

    # 1) Load the data
    df = pd.read_csv(csv_path)

    # 2) Determine overall recording duration (assuming 'Start' is in seconds)
    max_time = df["Start"].max()

    # 3) Define cutoffs for first hour and last hour
    first_hour_cutoff = 3600
    last_hour_cutoff = max_time - 3600

    # 4) Subset DataFrame for first and last hour
    first_hour_df = df[df["Start"] < first_hour_cutoff]
    last_hour_df = df[df["Start"] > last_hour_cutoff]

    print(f"Total waves in first hour: {len(first_hour_df)}")
    print(f"Total waves in last hour:  {len(last_hour_df)}")

    # 5) Create base directory for these plots
    images_dir = os.path.join(output_dir, "first_vs_last")
    os.makedirs(images_dir, exist_ok=True)

    # 6) We'll make a small helper function to do the plotting for each parameter
    def create_violin_plot(param):
        """Creates and saves a violin plot comparing param in first vs last hour."""
        # Gather data
        data_groups = []
        labels = []

        first_data = first_hour_df[param] if not first_hour_df.empty else None
        last_data  = last_hour_df[param]  if not last_hour_df.empty  else None

        if first_data is not None and not first_data.empty:
            data_groups.append(first_data)
            labels.append("First Hour")

        if last_data is not None and not last_data.empty:
            data_groups.append(last_data)
            labels.append("Last Hour")

        # Compute means
        mean_first = first_data.mean() if first_data is not None and not first_data.empty else float('nan')
        mean_last  = last_data.mean()  if last_data is not None  and not last_data.empty  else float('nan')

        # If we have data to plot, create the figure
        if data_groups:
            plt.figure(figsize=(6, 4))
            plt.violinplot(data_groups, showmeans=True)
            # Label the x positions manually (violinplot doesn't auto-label)
            plt.xticks([1, 2] if len(data_groups) == 2 else [1], labels)

            # Title with mean values
            plt.title(f"{param} Comparison: First vs Last Hour\n"
                      f"Mean(1st)={mean_first:.2f}, Mean(Last)={mean_last:.2f}")

            plt.ylabel(param)
            plt.tight_layout()

            # Save figure
            save_name = f"{param}_first_vs_last_hour.png"
            plot_path = os.path.join(images_dir, save_name)
            plt.savefig(plot_path)
            plt.close()
            print(f"Plot saved -> {plot_path}")
        else:
            print(f"No valid data to plot for {param} (check recording duration).")

    # 7) Call the helper for each parameter you want to compare
    for param_col in ["Slope", "PTP", "Frequency"]:
        create_violin_plot(param_col)


if __name__ == "__main__":
    # Example usage (if run directly from the command line)
    csv_file = "original_detection.csv"
    out_dir = "output"
    slopes_first_vs_last(csv_file, out_dir)

