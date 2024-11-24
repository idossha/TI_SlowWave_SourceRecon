
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import sys
import os

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

# Function to plot the first five vertices with local maxima
def plot_local_maxima(time_points, vertex_data):
    time_array = np.array(time_points)
    vertices_to_plot = vertex_data[:5]

    for idx, vertex in enumerate(vertices_to_plot):
        currents = np.array(vertex['currents'])

        if len(time_array) != len(currents):
            print(f"Error: time_array and currents have different lengths ({len(time_array)} vs {len(currents)}) for vertex {idx+1}")
            continue  # Skip plotting this vertex

        plt.figure(figsize=(12, 6))
        plt.plot(time_array, currents, label='Relative Current')

        # Find local maxima
        peaks, _ = find_peaks(currents)
        plt.plot(time_array[peaks], currents[peaks], 'ro', label='Local Maxima')

        plt.title(f"Vertex {idx+1} ({vertex['region']})")
        plt.xlabel('Time (s)')
        plt.ylabel('Relative Current')
        plt.legend()
        plt.grid(True)
        plt.show()

def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_local_maxima.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    if not os.path.isfile(csv_file):
        print(f"File {csv_file} does not exist.")
        sys.exit(1)

    print(f"Processing file: {csv_file}")
    time_points, vertex_data = read_eeg_data(csv_file)

    if time_points and vertex_data:
        plot_local_maxima(time_points, vertex_data)
    else:
        print("Error: Time points or vertex data is empty.")

if __name__ == "__main__":
    main()
   main()
