import os
import sys
import json
import pandas as pd

"""
Script Name: extract_data.py

Description:
This script reads JSON output files from a directory structure organized by subjects and conditions.
It extracts the important data (involvement percentages and region percentages) from each JSON file and compiles it into a pandas DataFrame.
The resulting DataFrame is saved to a CSV file for use in further analysis.

Directory Structure Assumption:
data/
├── subject1/
│   ├── condition1.json
│   ├── condition2.json
│   ├── condition3.json
│   └── condition4.json
├── subject2/
│   ├── condition1.json
│   ├── condition2.json
│   ├── condition3.json
│   └── condition4.json
...

Usage:
python extract_data.py /path/to/data_directory /path/to/output_file.csv
"""

def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_data.py /path/to/data_directory /path/to/output_file.csv")
        sys.exit(1)

    data_dir = sys.argv[1]
    output_file = sys.argv[2]

    # Initialize lists to store data
    data_list = []

    # Iterate over subjects (directories in data_dir)
    for subject in os.listdir(data_dir):
        subject_path = os.path.join(data_dir, subject)
        if os.path.isdir(subject_path):
            # Iterate over conditions (JSON files in subject directory)
            for file in os.listdir(subject_path):
                if file.endswith('.json'):
                    filepath = os.path.join(subject_path, file)
                    condition = file.replace('.json', '')
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        # Extract involvement percentage
                        percentage_involved = data['summary']['involvement']['mean_percentage_involved']
                        # Extract region percentages
                        region_percentages = data['summary']['most_significant_regions_of_origin']
                        # Prepare data entry
                        data_entry = {
                            'subject': subject,
                            'condition': condition,
                            'percentage_involved': percentage_involved,
                        }
                        # Add region percentages to data_entry
                        data_entry.update(region_percentages)
                        data_list.append(data_entry)

    # Create DataFrame
    df = pd.DataFrame(data_list)

    # Save DataFrame to a CSV file
    df.to_csv(output_file, index=False)
    print(f"Data extracted and saved to {output_file}")

if __name__ == "__main__":
    main()

