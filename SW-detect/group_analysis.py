
# group_analysis.py

import pandas as pd
import os

def append_to_group_summary(project_dir, subject, night, quant_csv_path):
    """
    Append wave quantification data to the group_summary.csv in the Group_Analysis directory.
    
    Parameters:
        project_dir (str): The root project directory.
        subject (str): Subject number.
        night (str): Night identifier.
        quant_csv_path (str): Path to the wave_quantification.csv file for this subject and night.
    """
    group_analysis_dir = os.path.join(project_dir, 'Group_Analysis')
    os.makedirs(group_analysis_dir, exist_ok=True)
    
    group_summary_csv = os.path.join(group_analysis_dir, 'group_summary.csv')
    
    # Initialize or read the existing group_summary.csv
    if not os.path.exists(group_summary_csv):
        # Define columns
        columns = ['Subject', 'Night', 'Protocol_ID', 'Stage', 'Number_of_Waves', 'Average_Amplitude', 'Max_Amplitude', 'Min_Amplitude', 'Std_Amplitude']
        group_summary_df = pd.DataFrame(columns=columns)
    else:
        group_summary_df = pd.read_csv(group_summary_csv)
    
    # Read the quantification CSV
    try:
        quant_df = pd.read_csv(quant_csv_path)
        
        # Add Subject and Night columns
        quant_df['Subject'] = subject
        quant_df['Night'] = night
        
        # Reorder columns to have Subject and Night first
        cols = ['Subject', 'Night'] + [col for col in quant_df.columns if col not in ['Subject', 'Night']]
        quant_df = quant_df[cols]
        
        # Append to group_summary_df
        group_summary_df = pd.concat([group_summary_df, quant_df], ignore_index=True)
        
        # Save back to group_summary.csv
        group_summary_df.to_csv(group_summary_csv, index=False)
        
        print(f"Appended data to group_summary.csv in {group_analysis_dir}")
    
    except Exception as e:
        print(f"Error appending to group_summary.csv: {e}")
