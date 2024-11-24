
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import sys
import os


"""
Script Name: plot-origin.py

Description:
This script processes EEG data from a CSV file and visualizes the relative current over time for the top 10% of brain vertices where the signal originates within a specific time window (-50 ms to +50 ms around t = 0).

Key Features:
- Reads EEG data from a CSV file where the first column contains labels (brain region and vertex index), and subsequent columns contain relative current values at different time points.
- Identifies the top 10% of vertices based on the earliest peak times within the specified time window.
- Plots the relative current over time for these vertices, with each line colored according to the brain region the vertex is assigned to.
- Marks the selected peaks (local maxima closest to t = 0) with small dots on the lines.

Usage:
python plot-origin.py /path/to/your/data.csv

"""

# Function to read and parse the EEG data
def read_eeg_data(filename):
    try:
        # Read the CSV file using pandas
        df = pd.read_csv(filename, delimiter=None, engine='python')
    except Exception as e:
        print(f"Error reading CSV file {filename}: {e}")
        return [], []

    try:
        # Extract time points from the header, starting from the second column
        time_labels = df.columns[1:]
        # Remove any columns that are named 'Unnamed' or empty strings
        time_labels = [t.strip() for t in time_labels if not t.startswith('Unnamed') and t.strip() != '']
        time_points = []
        for t in time_labels:
            try:
                time_points.append(float(t))
            except ValueError:
                print(f"Warning: Unable to convert time label '{t}' to float.")
                continue
    except ValueError as e:
        print(f"Error converting time labels to floats in file {filename}: {e}")
        print("Time labels:", time_labels)
        return [], []

    if len(time_points) == 0:
        print(f"No valid time points extracted from the header in file {filename}.")
        return [], []

    vertex_data = []

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        label = str(row.iloc[0]).strip()
        data_values = row.iloc[1:].values

        # Remove any NaN or invalid entries
        data_values = [x for x in data_values if pd.notnull(x) and str(x).strip() != '']

        if len(data_values) != len(time_points):
            print(f"Warning: Mismatch in data length at row {index}. Expected {len(time_points)}, got {len(data_values)}.")
            continue  # Skip this row

        # Convert data_values to floats
        try:
            data_values = [float(str(x).strip()) for x in data_values]
        except ValueError as e:
            print(f"Error converting data values to floats in row {index} in file {filename}: {e}")
            continue  # Skip this row

        # Parse the label to get brain region and vertex index
        label_parts = label.split(' @ ')[0]  # get the part before '@'
        region_vertex = label_parts
        if '.' in region_vertex:
            region, vertex_index = region_vertex.rsplit('.', 1)
        else:
            region = region_vertex
            vertex_index = ''
        vertex_index = vertex_index.strip()
        region = region.strip()

        vertex_data.append({
            'region': region,
            'vertex_index': vertex_index,
            'currents': data_values  # Assuming 'amplitudes' are relative currents
        })

    return time_points, vertex_data

def plot_relative_current_maxima(time_points, vertex_data):
    time_array = np.array(time_points)

    # Define the time window from -0.05 s to +0.05 s
    window_mask = (time_array >= -0.05) & (time_array <= 0.05)
    window_indices = np.where(window_mask)[0]

    if len(window_indices) == 0:
        print("No time points within the specified time window.")
        return

    # Time window array
    time_array_window = time_array[window_indices]

    # Threshold is 25% of the maximum relative current value in the window
    global_max_current = 0

    # First, find the global maximum current in the window
    for vertex in vertex_data:
        currents = np.abs(np.array(vertex['currents']))

        if len(currents) != len(time_array):
            print(f"Warning: Currents length does not match time array length for vertex {vertex['vertex_index']}. Skipping.")
            continue

        currents_in_window = currents[window_indices]

        if len(currents_in_window) == 0:
            continue

        vertex_max = np.max(currents_in_window)
        if vertex_max > global_max_current:
            global_max_current = vertex_max

    if global_max_current == 0:
        print("Global maximum current within the window is zero.")
        return

    threshold = 0.25 * global_max_current

    # Collect selected peaks for each vertex
    vertices_info = []  # Will store (selected_peak_time, selected_peak_current, vertex, currents_in_window, time_array_window, selected_peak_idx)

    t0_time = 0.0  # Reference time

    for vertex in vertex_data:
        currents = np.array(vertex['currents'])

        if len(currents) != len(time_array):
            continue

        currents_in_window = np.abs(currents[window_indices])

        if len(currents_in_window) == 0:
            continue

        # Find local maxima in the currents within the window
        peaks, _ = find_peaks(currents_in_window)

        # Reject peaks that do not exceed the threshold
        valid_peaks = [peak for peak in peaks if currents_in_window[peak] >= threshold]

        if valid_peaks:
            valid_peaks = np.array(valid_peaks)
            # For each vertex, select the peak closest to t=0.0
            peak_times = time_array_window[valid_peaks]
            distances = np.abs(peak_times - t0_time)
            min_index = np.argmin(distances)
            selected_peak_idx = valid_peaks[min_index]
            selected_peak_time = peak_times[min_index]
            selected_peak_current = currents_in_window[selected_peak_idx]

            vertices_info.append((selected_peak_time, selected_peak_current, vertex, currents_in_window, time_array_window, selected_peak_idx))
        else:
            # No valid peaks for this vertex
            continue

    if not vertices_info:
        print("No valid peaks found in any vertex within the window.")
        return

    # Sort vertices by the time their selected peaks occurred
    vertices_info.sort(key=lambda x: x[0])

    num_vertices = len(vertices_info)
    top_10_percent_count = max(int(0.1 * num_vertices), 1)

    # Get the top 10% vertices
    top_vertices = vertices_info[:top_10_percent_count]

    # Get unique brain regions among the top vertices
    regions = [vertex['region'] for _, _, vertex, _, _, _ in top_vertices]
    unique_regions = list(set(regions))

    # Assign colors to regions
    colors = list(mcolors.TABLEAU_COLORS.values())
    if len(unique_regions) > len(colors):
        # If more regions than colors, use a colormap
        cmap = plt.get_cmap('tab20')
        color_list = [cmap(i) for i in np.linspace(0, 1, len(unique_regions))]
    else:
        color_list = colors[:len(unique_regions)]
    region_color_map = dict(zip(unique_regions, color_list))

    # Plotting
    plt.figure(figsize=(12, 6))

    for selected_peak_time, selected_peak_current, vertex, currents_in_window, times_in_window, selected_peak_idx in top_vertices:
        region = vertex['region']
        color = region_color_map[region]

        # Plot the currents over time as a line, make the line thinner
        plt.plot(times_in_window, currents_in_window, linewidth=0.5, color=color)

        # Mark the selected peak with a small dot
        plt.plot(selected_peak_time, selected_peak_current, 'o', markersize=3, color=color)

    # No legend, lines are thinner
    plt.xlabel('Time (s)')
    plt.ylabel('Relative Current')
    plt.title('Relative Current over Time for Top 10% Vertices (Within -50ms to +50ms)')
    # plt.legend()
    plt.grid(True)
    plt.show()

def main():
    if len(sys.argv) < 2:
        print("Usage: python plot-origin.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    if not os.path.isfile(csv_file):
        print(f"File {csv_file} does not exist.")
        sys.exit(1)

    print(f"Processing file: {csv_file}")
    time_points, vertex_data = read_eeg_data(csv_file)

    if time_points and vertex_data:
        plot_relative_current_maxima(time_points, vertex_data)
    else:
        print("Error: Time points or vertex data is empty.")

if __name__ == "__main__":
    main()

