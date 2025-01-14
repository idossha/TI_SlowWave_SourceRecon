
# compare_slopes.py

import os
import json
import pandas as pd
import matplotlib.pyplot as plt

def create_violin_plot(param, data1, data2, label1, label2, save_name, save_dir):
    """
    Creates and saves a violin plot comparing 'param' in data1 vs data2.
    data1/data2 are Series; label1/label2 are axis labels; save_name is filename;
    save_dir is directory to store the figure.
    """
    data_groups = []
    labels = []

    # Prepare data1
    if data1 is not None and not data1.empty:
        data_groups.append(data1)
        labels.append(label1)
        mean1 = data1.mean()
    else:
        mean1 = float('nan')

    # Prepare data2
    if data2 is not None and not data2.empty:
        data_groups.append(data2)
        labels.append(label2)
        mean2 = data2.mean()
    else:
        mean2 = float('nan')

    # If we have data to plot, create the figure
    if data_groups:
        plt.figure(figsize=(8, 5))  # Slightly larger to accommodate title
        plt.violinplot(data_groups, showmeans=True)

        # Label the x positions manually (violinplot doesn't auto-label)
        if len(data_groups) == 2:
            plt.xticks([1, 2], labels)
        else:
            plt.xticks([1], labels)

        # Multi-line title to avoid truncation; wrap=True helps break long text
        title_str = (
            f"{param} Comparison\n"
            f"Mean({label1})={mean1:.2f}, Mean({label2})={mean2:.2f}"
        )
        plt.title(title_str, wrap=True)

        plt.ylabel(param)
        plt.tight_layout()

        # Ensure the directory exists
        os.makedirs(save_dir, exist_ok=True)

        # Save figure
        plot_path = os.path.join(save_dir, save_name)
        plt.savefig(plot_path)
        plt.close()
        print(f"Plot saved -> {plot_path}")
    else:
        print(f"No valid data to plot for {param} in {save_name} (check recording duration).")


def slopes_first_vs_last(csv_path, output_dir):
    """
    Loads 'original_detection.csv', selects waves in the first hour and last hour,
    then compares and plots the Slope, PTP, and Frequency values as violin plots.

    Three .png files will be created in:
        output_dir/first_vs_last/
    Each file shows how a parameter changes between the first and last hour.
    The plots also display the mean values in the title.

    Additionally, it will attempt to read the channel -> region mapping from
    assets/net_segmentation.json (in the same directory as this script),
    and create 3 more plots per region.
    """

    # 1) Load the data
    df = pd.read_csv(csv_path)

    # 2) Determine overall recording duration (assuming 'Start' is in seconds)
    max_time = df["Start"].max()

    # 3) Define cutoffs for first hour and last hour
    first_hour_cutoff = 3600
    last_hour_cutoff = max_time - 3600

    # 4) Subset DataFrame for first and last hour (all channels)
    first_hour_df = df[df["Start"] < first_hour_cutoff]
    last_hour_df  = df[df["Start"] > last_hour_cutoff]

    print(f"Total waves in first hour (all channels): {len(first_hour_df)}")
    print(f"Total waves in last hour  (all channels): {len(last_hour_df)}")

    # 5) Create base directory for these plots
    images_dir = os.path.join(output_dir, "first_vs_last")
    os.makedirs(images_dir, exist_ok=True)

    # 6) Generate the three global plots (all channels)
    for param_col in ["Slope", "PTP", "Frequency"]:
        save_file = f"{param_col}_first_vs_last_hour.png"
        create_violin_plot(
            param=param_col,
            data1=first_hour_df[param_col],
            data2=last_hour_df[param_col],
            label1="First Hour (All)",
            label2="Last Hour (All)",
            save_name=save_file,
            save_dir=images_dir
        )

    # 7) Load region definitions from JSON in ./assets/net_segmentation.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "assets", "net_segmentation.json")

    if not os.path.isfile(json_path):
        print(f"Warning: {json_path} not found. Skipping region-based plots.")
        return

    with open(json_path, "r") as f:
        region_dict = json.load(f)

    # For each region, flatten the list-of-lists, subset df, then do the same first/last hour split
    for region_name, channel_lists in region_dict.items():
        # Flatten channel lists
        region_channels = []
        for sublist in channel_lists:
            region_channels.extend(sublist)

        # Subset the main DataFrame by these channels
        region_df = df[df["Channel"].isin(region_channels)]

        # Subset region into first and last hour
        region_first_df = region_df[region_df["Start"] < first_hour_cutoff]
        region_last_df  = region_df[region_df["Start"] > last_hour_cutoff]

        print(f"\nRegion: {region_name}")
        print(f"Total waves in first hour ({region_name}): {len(region_first_df)}")
        print(f"Total waves in last hour  ({region_name}): {len(region_last_df)}")

        # Create a subdirectory for region-specific plots
        region_images_dir = os.path.join(images_dir, region_name.replace(" ", "_"))
        os.makedirs(region_images_dir, exist_ok=True)

        # Plot the same parameters (Slope, PTP, Frequency)
        for param_col in ["Slope", "PTP", "Frequency"]:
            save_file = f"{param_col}_first_vs_last_{region_name.replace(' ', '_')}.png"
            create_violin_plot(
                param=param_col,
                data1=region_first_df[param_col],
                data2=region_last_df[param_col],
                label1=f"First Hour ({region_name})",
                label2=f"Last Hour ({region_name})",
                save_name=save_file,
                save_dir=region_images_dir
            )


if __name__ == "__main__":
    # Example usage
    csv_file = "original_detection.csv"
    out_dir = "output"
    slopes_first_vs_last(csv_file, out_dir)

