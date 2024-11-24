Modules and Scripts
data_loading.py: Loads and preprocesses EEG data.
event_cleaning.py: Cleans and validates 'stim start' and 'stim end' events.
epoch_creation.py: Creates epochs and adjusts overlaps.
wave_detection.py: Detects slow waves using YASA.
wave_classification.py: Classifies and filters waves.
statistical_analysis.py: Performs statistical analysis and generates plots.
annotate_raw.py: Annotates raw EEG data with events.
extract_epochs.py: Extracts and saves individual epochs.
plot_average_waveforms.py: Plots average waveforms.
main.py: Orchestrates the execution of all modules.


project_directory/
├── main.py
├── data_loading.py
├── event_cleaning.py
├── epoch_creation.py
├── wave_detection.py
├── wave_classification.py
├── wave_filtering.py
├── statistical_analysis.py
├── annotate_raw.py
├── extract_epochs.py
├── plot_average_waveforms.py
└── output/
    ├── filtered_epochs_500ms_first.csv
    ├── filtered_epochs_500ms_most_negative.csv    # Default CSV used in the pipeline
    ├── filtered_epochs_1000ms_first.csv
    ├── filtered_epochs_1000ms_most_negative.csv
    ├── annotated_raw_filtered_epochs_500ms_most_negative.set
    ├── average_waveforms_filtered_epochs_500ms_most_negative.png
    ├── overall_mean_values_filtered_epochs_500ms_most_negative.png
    ├── epoch-data-filtered_epochs_500ms_most_negative/
    │   └── *.set
    ├── epoch-imgs-filtered_epochs_500ms_most_negative/
    │   └── *.png
    └── other_output_files...

