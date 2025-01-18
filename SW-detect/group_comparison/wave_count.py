
import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ==================== Configuration ====================

# Hardcoded list of input CSV files
CSV_PATHS = [
    '/Volumes/CSC-Ido/Analyze/Group_Analysis/aggregated_wave_data_Active.csv',
    '/Volumes/CSC-Ido/Analyze/Group_Analysis/aggregated_wave_data_SHAM.csv'
]

# Hardcoded list of output directories where plots will be saved
OUTPUT_DIRS = [
    '/Users/idohaber/Desktop/Group_output/wave_count/plots_active',
    '/Users/idohaber/Desktop/Group_output/wave_count/plots_SHAM'
]

# ========================================================

def create_subject_region_plots(df, output_dir):
    """
    Generates bar plots for each subject and each region, showing the total number of waves
    across different stimulation stages. Annotates the exact wave count on top of each bar.
    
    Parameters:
    - df: pandas DataFrame containing the data.
    - output_dir: Directory where the plots will be saved.
    """
    subjects = df['Subject'].unique()
    regions = df['Region'].unique()
    
    for subject in subjects:
        subject_df = df[df['Subject'] == subject]
        for region in regions:
            region_df = subject_df[subject_df['Region'] == region]
            
            if region_df.empty:
                continue  # Skip if no data for this region and subject
            
            # Aggregate Number_of_Waves by Stage (sum)
            agg_df = region_df.groupby('Stage')['Number_of_Waves'].sum().reset_index()
            
            # Ensure the stages are in a specific order
            stage_order = ['pre-stim', 'stim', 'post-stim']
            agg_df['Stage'] = pd.Categorical(agg_df['Stage'], categories=stage_order, ordered=True)
            agg_df = agg_df.sort_values('Stage')
            
            # Create bar plot
            plt.figure(figsize=(8,6))
            ax = sns.barplot(x='Stage', y='Number_of_Waves', data=agg_df, palette='viridis')
            
            # Annotate each bar with the exact count
            for p in ax.patches:
                height = p.get_height()
                ax.annotate(
                    f'{height:.0f}',
                    (p.get_x() + p.get_width() / 2., height),
                    ha='center',
                    va='bottom',
                    xytext=(0, 5),
                    textcoords='offset points'
                )
            
            plt.title(f'Subject {subject} - {region}')
            plt.xlabel('Stage')
            plt.ylabel('Total Number of Waves')
            plt.tight_layout()
            
            # Save plot
            filename = f'subject_{subject}_{region}.png'.replace('/', '_').replace('\\', '_')
            plt.savefig(os.path.join(output_dir, filename))
            plt.close()

def create_group_average_plots(df, output_dir):
    """
    Generates group total wave count bar plots for each region, showing the sum of waves
    across all subjects for each stimulation stage. Also overlays individual subject data
    (dots) so you can see how each subject contributed to the total. Annotates the exact
    wave count on top of each bar.
    
    Parameters:
    - df: pandas DataFrame containing the data.
    - output_dir: Directory where the plots will be saved.
    """
    regions = df['Region'].unique()
    
    for region in regions:
        region_df = df[df['Region'] == region]
        
        if region_df.empty:
            continue  # Skip if no data for this region
        
        # Aggregate Number_of_Waves by (Subject, Stage), then sum across that subject
        # => each row in agg_df is one subject's total waves for a given stage
        agg_df = region_df.groupby(['Subject', 'Stage'])['Number_of_Waves'].sum().reset_index()
        
        # Sum across all subjects to get group-wide total
        group_sum = agg_df.groupby('Stage')['Number_of_Waves'].sum().reset_index()
        
        # Ensure the stages are in a specific order
        stage_order = ['pre-stim', 'stim', 'post-stim']
        group_sum['Stage'] = pd.Categorical(group_sum['Stage'], categories=stage_order, ordered=True)
        group_sum = group_sum.sort_values('Stage')
        
        # Also categorize the Stage in agg_df for consistent plotting
        agg_df['Stage'] = pd.Categorical(agg_df['Stage'], categories=stage_order, ordered=True)
        agg_df = agg_df.sort_values('Stage')
        
        # Create bar plot (group total)
        plt.figure(figsize=(8,6))
        ax = sns.barplot(
            x='Stage', y='Number_of_Waves', data=group_sum,
            palette='magma', capsize=0.1, alpha=0.8
        )
        
        # Annotate each bar with the exact count
        for p in ax.patches:
            height = p.get_height()
            ax.annotate(
                f'{height:.0f}',
                (p.get_x() + p.get_width() / 2., height),
                ha='center',
                va='bottom',
                xytext=(0, 5),
                textcoords='offset points'
            )
        
        # Overlay individual subject data as points
        sns.stripplot(
            x='Stage', y='Number_of_Waves', data=agg_df,
            color='black', alpha=0.7, size=5,
            jitter=True, dodge=False, ax=ax
        )
        
        plt.title(f'Group Total Waves - {region}')
        plt.xlabel('Stage')
        plt.ylabel('Total Number of Waves')
        plt.tight_layout()
        
        # Save plot
        filename = f'group_total_waves_{region}.png'.replace('/', '_').replace('\\', '_')
        plt.savefig(os.path.join(output_dir, filename))
        plt.close()

def create_overall_stage_plot(df, output_dir):
    """
    Creates a total bar graph for the number of waves across all regions,
    showing total wave counts for each stage (pre-stim, stim, post-stim).
    
    Parameters:
    - df: pandas DataFrame containing the data.
    - output_dir: Directory where the plot will be saved.
    """
    # Sum across all subjects and all regions by stage
    overall_sum = df.groupby('Stage')['Number_of_Waves'].sum().reset_index()
    
    # Ensure the stages are in a specific order
    stage_order = ['pre-stim', 'stim', 'post-stim']
    overall_sum['Stage'] = pd.Categorical(overall_sum['Stage'], categories=stage_order, ordered=True)
    overall_sum = overall_sum.sort_values('Stage')
    
    # Create bar plot
    plt.figure(figsize=(8,6))
    ax = sns.barplot(x='Stage', y='Number_of_Waves', data=overall_sum, palette='Set2')
    
    # Annotate each bar with the exact count
    for p in ax.patches:
        height = p.get_height()
        ax.annotate(
            f'{height:.0f}',
            (p.get_x() + p.get_width() / 2., height),
            ha='center',
            va='bottom',
            xytext=(0, 5),
            textcoords='offset points'
        )

    plt.title('Total Waves Across All Regions')
    plt.xlabel('Stage')
    plt.ylabel('Total Number of Waves')
    plt.tight_layout()
    
    # Save plot
    filename = f'total_waves_all_regions.png'
    plt.savefig(os.path.join(output_dir, filename))
    plt.close()

def process_csv_file(csv_path, out_dir):
    """
    Reads the CSV file, checks for missing columns, and runs all plot-generating functions.
    """
    # Create output directory if it doesn't exist
    os.makedirs(out_dir, exist_ok=True)
    
    # Try reading the CSV
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: The file '{csv_path}' was not found.")
        return
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{csv_path}' is empty.")
        return
    except pd.errors.ParserError:
        print(f"Error: The file '{csv_path}' could not be parsed.")
        return
    
    # Ensure necessary columns are present
    required_columns = [
        'Protocol_Number', 'Stage', 'Number_of_Waves', 'Average_Amplitude',
        'Max_Amplitude', 'Min_Amplitude', 'Std_Amplitude', 'Subject',
        'Night', 'Region'
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: The following required columns are missing from '{csv_path}': {missing_columns}")
        return
    
    # Run all plot functions
    create_subject_region_plots(df, out_dir)
    create_group_average_plots(df, out_dir)
    create_overall_stage_plot(df, out_dir)
    
    print(f"Plots for '{csv_path}' have been successfully saved to: {out_dir}")

def main():
    """
    Main function to execute the plotting tasks for each CSV file and corresponding output directory.
    """
    # Ensure the number of CSV paths matches the number of output directories
    if len(CSV_PATHS) != len(OUTPUT_DIRS):
        print("Error: The number of CSV paths and output directories do not match.")
        return
    
    # Loop over each CSV path / output directory pair
    for csv_path, out_dir in zip(CSV_PATHS, OUTPUT_DIRS):
        process_csv_file(csv_path, out_dir)

if __name__ == '__main__':
    main()

