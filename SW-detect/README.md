
# EEG Slow Wave Analysis Pipeline

## Overview
This project contains scripts and modules for analyzing EEG data, specifically focusing on detecting and analyzing slow waves. The pipeline includes data preprocessing, event cleaning, epoch creation, wave detection, classification, and statistical analysis.

---

## Modules and Scripts

- **`main.py`**: entrypoint to the pipeline.
- **`data_loading.py`**: Loads and preprocesses EEG data.
- **`event_cleaning.py`**: Cleans and validates 'stim start' and 'stim end' events to ensure accuracy.
- **`epoch_creation.py`**: Creates epochs based on specified event markers and adjusts overlaps.
- **`wave_detection.py`**: Detects slow waves using the YASA library.
- **`wave_classification.py`**: Classifies detected waves based on protocol and stim stage.
- **`statistical_analysis.py`**: Performs statistical analysis on classified waves and generates summary plots.
- **`annotate_raw.py`**: Annotates the raw EEG data with start,neg-peak,pos-peak, end for every slow wave.
- **`extract_epochs.py`**: Extracts and saves individual epochs as `.set` files.
- **`plot_average_waveforms.py`**: Plots average waveforms for the detected and filtered waves.

---


