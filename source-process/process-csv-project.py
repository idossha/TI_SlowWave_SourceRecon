
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import os
import sys
import json
from collections import Counter, defaultdict

"""
Script Name: process.py

Description:
This script processes EEG data from CSV files located in a directory tree containing multiple subjects and conditions.
It calculates the involvement of brain regions and detects the origin of neural signals within a specific time window (-50 ms to +50 ms around t = 0).
It computes summary statistics and outputs the results to a JSON file.

Key Features:
- Recursively traverses the directory tree starting from the provided project directory.
- Reads EEG data from CSV files where the first column contains labels (brain region and vertex index), and subsequent columns contain relative current values at different time points.
- Extracts subject and condition information from the directory structure.
- Calculates the number and percentage of involved vertices within the 100 ms window, using a threshold-based method (25% of the maximum relative current).
- Detects the origin of neural signals by identifying the earliest 10% of vertices with significant peaks.
- Aggregates results across all files to produce summary statistics, including mean, standard deviation, and range of involvement percentages, as well as the most frequent and significant brain regions of origin.
- Outputs the results and summary to 'output_results.json' in the specified project directory.

Usage:
python process.py <project_directory_path>
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
        # Remove any columns that are named 'Unnamed' (e.g., 'Unnamed: 22')
        time_labels = [t.strip() for t in time_labels if not t.startswith('Unnamed')]
        time_points = [float(t) for t in time_labels]
    except ValueError as e:
        print(f"Error converting time labels to floats in file {filename}: {e}")
        print("Time labels:", time_labels)
        return [], []

    vertex_data = []

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        label = str(row.iloc[0]).strip()
        data_values = row.iloc[1:]

        # Convert data_values to floats, handling any errors
        try:
            data_values = data_values.apply(lambda x: float(str(x).strip()))
            data_values = data_values.tolist()
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

# Involvement calculation using method 2 (threshold-based)
def calculate_involvement(time_points, vertex_data):
    if not time_points:
        print("No time points available for involvement calculation.")
        return 0, 0.0

    time_array = np.array(time_points)
    # Time window of 100ms centered on t=0.0
    window_mask = (time_array >= -0.05) & (time_array <= 0.05)
    window_indices = np.where(window_mask)[0]

    if len(window_indices) == 0:
        print("No time points within the specified time window for involvement calculation.")
        return 0, 0.0

    # Threshold is 25% of the maximum relative current value in the window
    global_max_current = 0
    vertex_max_currents = []

    # Find the maximum absolute current for each vertex within the window
    for vertex in vertex_data:
        currents_in_window = np.abs(np.array(vertex['currents'])[window_indices])
        vertex_max = np.max(currents_in_window)
        vertex_max_currents.append(vertex_max)
        if vertex_max > global_max_current:
            global_max_current = vertex_max

    if global_max_current == 0:
        print("Global maximum current within the window is zero.")
        return 0, 0.0

    # Determine involvement using threshold
    vertex_max_currents = np.array(vertex_max_currents)
    threshold = 0.25 * global_max_current
    involved = vertex_max_currents >= threshold
    number_involved = np.sum(involved)
    percentage_involved = (number_involved / len(vertex_data)) * 100

    return number_involved, percentage_involved

# Origin detection based on earliest significant peaks
def detect_origin(time_points, vertex_data):
    if not time_points:
        print("No time points available for origin detection.")
        return {}, 0, None, {}, [], []

    time_array = np.array(time_points)
    # Time window of 100ms centered on t=0.0 (negative voltage peak)
    t0_time = 0.0  # Assuming t=0.0 is the negative voltage peak
    window_mask = (time_array >= (t0_time - 0.05)) & (time_array <= (t0_time + 0.05))
    window_indices = np.where(window_mask)[0]

    if len(window_indices) == 0:
        print("No time points within the specified time window for origin detection.")
        return {}, 0, None, {}, [], []

    # Threshold is 25% of the maximum relative current value in the window
    global_max_current = 0
    for vertex in vertex_data:
        currents_in_window = np.abs(np.array(vertex['currents'])[window_indices])
        vertex_max = np.max(currents_in_window)
        if vertex_max > global_max_current:
            global_max_current = vertex_max

    if global_max_current == 0:
        print("Global maximum current within the window is zero.")
        return {}, 0, None, {}, [], []

    threshold = 0.25 * global_max_current

    vertex_peak_times = []

    for vertex in vertex_data:
        currents_in_window = np.abs(np.array(vertex['currents'])[window_indices])
        # Find local maxima in the currents
        peaks, _ = find_peaks(currents_in_window)
        # Reject peaks that do not exceed the threshold
        valid_peaks = [peak for peak in peaks if currents_in_window[peak] >= threshold]
        if valid_peaks:
            valid_peaks = np.array(valid_peaks)
            # For each vertex, select the peak closest to t=0.0
            peak_times = time_array[window_indices][valid_peaks]
            distances = np.abs(peak_times - t0_time)
            min_index = np.argmin(distances)
            selected_peak_idx = valid_peaks[min_index]
            selected_peak_time = peak_times[min_index]
            selected_peak_current = currents_in_window[selected_peak_idx]
            vertex_peak_times.append((vertex, selected_peak_time, selected_peak_idx, selected_peak_current))
        else:
            # No valid peaks for this vertex
            pass

    if len(vertex_peak_times) == 0:
        print("No valid peaks found in any vertex within the window.")
        return {}, 0, None, {}, [], []

    # Sort the peaks by the time they occurred
    vertex_peak_times.sort(key=lambda x: x[1])

    # Define the probabilistic origin as the earliest 10% of vertices
    num_vertices = len(vertex_peak_times)
    top_10_percent_count = max(int(0.1 * num_vertices), 1)
    top_vertices = vertex_peak_times[:top_10_percent_count]

    # Collect regions and count occurrences
    region_counts = {}
    for vertex, peak_time, peak_idx, peak_current in top_vertices:
        region = vertex['region']
        region_counts[region] = region_counts.get(region, 0) + 1

    # Calculate percentages for each region with two decimal places
    region_percentages = {region: round((count / top_10_percent_count) * 100, 2) for region, count in region_counts.items()}

    # The earliest peak time among the top vertices
    earliest_peak_time = top_vertices[0][1]

    return region_counts, top_10_percent_count, earliest_peak_time, region_percentages, top_vertices, window_indices

# Helper Function to Convert NumPy Types to Native Python Types
def convert_numpy_types(obj):
    """
    Recursively convert NumPy data types in a data structure to native Python types.
    """
    if isinstance(obj, dict):
        return {convert_numpy_types(k): convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

# Main function
def main():
    if len(sys.argv) < 2:
        print("Usage: python process.py <project_directory_path>")
        sys.exit(1)

    project_directory = sys.argv[1]
    if not os.path.isdir(project_directory):
        print(f"Directory {project_directory} does not exist.")
        sys.exit(1)

    # Prepare to collect outputs and summary data
    results = []
    involvement_percentages = []
    regions_counter = Counter()
    regions_percentage_sums = defaultdict(float)
    regions_percentage_counts = defaultdict(int)

    # Traverse the directory tree starting from project_directory
    for root, dirs, files in os.walk(project_directory):
        for file in files:
            if file.endswith('.csv'):
                full_path = os.path.join(root, file)
                # Extract subject and condition from the directory structure
                path_parts = os.path.relpath(full_path, project_directory).split(os.sep)
                if len(path_parts) >= 3:
                    subject = path_parts[0]
                    condition = path_parts[1]
                else:
                    print(f"Could not extract subject and condition from path: {full_path}")
                    subject = 'Unknown'
                    condition = 'Unknown'

                print(f"\nProcessing file: {full_path}")
                print(f"Subject: {subject}, Condition: {condition}")
                try:
                    time_points, vertex_data = read_eeg_data(full_path)
                    # Proceed only if data is correctly loaded
                    if time_points and vertex_data:
                        # Calculate involvement
                        number_involved, percentage_involved = calculate_involvement(time_points, vertex_data)
                        print(f"Number of involved vertices within the window: {number_involved}")
                        print(f"Percentage of total brain: {percentage_involved:.2f}%")

                        # Append to involvement_percentages for summary
                        involvement_percentages.append(percentage_involved)

                        # Detect origin
                        origin_regions, num_top_vertices, peak_time, region_percentages, top_vertices, window_indices = detect_origin(time_points, vertex_data)
                        if origin_regions:
                            print(f"Earliest peak time among top vertices: {peak_time*1000:.3f} milliseconds")
                            print(f"Number of top vertices (10%): {num_top_vertices}")
                            print("Brain regions where the signal originated (top 10% of vertices):")
                            for region, percentage in region_percentages.items():
                                print(f"- {region}: {percentage:.2f}%")

                            # Collect output for this file
                            output = {
                                'subject': subject,
                                'condition': condition,
                                'filename': os.path.relpath(full_path, project_directory),
                                'number_involved': number_involved,
                                'percentage_involved': percentage_involved,
                                'earliest_peak_time_ms': peak_time * 1000 if peak_time is not None else None,
                                'num_top_vertices': num_top_vertices,
                                'region_percentages': region_percentages
                            }

                            # Convert NumPy types to native Python types before appending
                            output = convert_numpy_types(output)

                            results.append(output)

                            # Update summary data
                            for region, percentage in region_percentages.items():
                                regions_counter[region] += 1
                                regions_percentage_sums[region] += percentage
                                regions_percentage_counts[region] += 1

                        else:
                            print("No origin regions detected.")
                            # Collect output for this file
                            output = {
                                'subject': subject,
                                'condition': condition,
                                'filename': os.path.relpath(full_path, project_directory),
                                'number_involved': number_involved,
                                'percentage_involved': percentage_involved,
                                'earliest_peak_time_ms': None,
                                'num_top_vertices': 0,
                                'region_percentages': {}
                            }
                            # Convert NumPy types to native Python types before appending
                            output = convert_numpy_types(output)
                            results.append(output)
                    else:
                        print(f"Error: Time points or vertex data is empty for file {full_path}.")
                        # Collect output for this file
                        output = {
                            'subject': subject,
                            'condition': condition,
                            'filename': os.path.relpath(full_path, project_directory),
                            'error': "Time points or vertex data is empty."
                        }
                        # Convert NumPy types to native Python types before appending
                        output = convert_numpy_types(output)
                        results.append(output)
                except Exception as e:
                    print(f"An error occurred while processing {full_path}: {e}")
                    # Collect output for this file
                    output = {
                        'subject': subject,
                        'condition': condition,
                        'filename': os.path.relpath(full_path, project_directory),
                        'error': str(e)
                    }
                    # Convert NumPy types to native Python types before appending
                    output = convert_numpy_types(output)
                    results.append(output)

    # After processing all files, compute the summary
    if involvement_percentages:
        mean_involvement = round(float(np.mean(involvement_percentages)), 2)
        std_involvement = round(float(np.std(involvement_percentages, ddof=1)), 2) if len(involvement_percentages) > 1 else 0.0
        min_involvement = round(float(np.min(involvement_percentages)), 2)
        max_involvement = round(float(np.max(involvement_percentages)), 2)
        range_involvement = [min_involvement, max_involvement]
    else:
        mean_involvement = std_involvement = min_involvement = max_involvement = 0.0
        range_involvement = [0.0, 0.0]

    # Most Frequent Regions of Origin
    most_frequent_regions = dict(regions_counter.most_common())

    # Most Significant Regions of Origin based on average percentages
    most_significant_regions = {}
    for region, total_percentage in regions_percentage_sums.items():
        count = regions_percentage_counts[region]
        average_percentage = round(total_percentage / count, 2)
        most_significant_regions[region] = average_percentage

    # Sort most_significant_regions by average_percentage descending
    most_significant_regions = dict(sorted(most_significant_regions.items(), key=lambda item: item[1], reverse=True))

    # Compile summary
    summary = {
        "summary": {
            "involvement": {
                "mean_percentage_involved": mean_involvement,
                "std_percentage_involved": std_involvement,
                "range_percentage_involved": range_involvement
            },
            "most_frequent_regions_of_origin": most_frequent_regions,
            "most_significant_regions_of_origin": most_significant_regions
        },
        "results": results
    }

    # Convert NumPy types in summary to native Python types before saving
    summary = convert_numpy_types(summary)

    # Save outputs to a single file
    output_filename = os.path.join(project_directory, 'output_results.json')
    try:
        with open(output_filename, 'w') as f:
            json.dump(summary, f, indent=4)
        print(f"\nAll outputs saved to {output_filename}")
    except Exception as e:
        print(f"Failed to write output to {output_filename}: {e}")

if __name__ == "__main__":
    main()
