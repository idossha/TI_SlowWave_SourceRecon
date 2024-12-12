Last update: December 12, 2024 
Ido Haber // ihaber@wisc.edu 

---
# EEG Preprocessing Pipeline

## Overview

This MATLAB script automates the preprocessing of continuous EEG data for multiple subjects and multiple nights/sessions. The pipeline includes steps such as identifying and handling NaN segments, removing unwanted events, repositioning events of interest, and preparing the data for Independent Component Analysis (ICA). Comprehensive logging ensures that each processing step is documented for easy debugging and tracking.

## Table of Contents

- [Entrypoint](#entrypoint)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
  - [Defining Subjects and Nights](#defining-subjects-and-nights)
  - [Running the Script](#running-the-script)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Contact](#contact)

## Entrypoint

`prep_forICA.m` is the entrypoint and the main script. 

## Features

- **Batch Processing:** Handles multiple subjects and multiple nights/sessions in a single run.
- **NaN Segment Identification:** Detects and manages NaN segments within EEG data.
- **Event Management:** Removes unwanted stim events based on specified sleep stages and repositions events of interest.
- **Data Cleaning:** Removes NaN regions and unwanted sleep stages. 
- **Logging:** Generates detailed log files for each subject-night combination to track processing steps and errors.
- **Visualization:** generates hypnograms with stim events and visualization of NaN segments
- **Robust Error Handling:** Utilizes `try-catch` blocks to manage errors gracefully without halting the entire processing pipeline.

## Prerequisites

- **MATLAB:** Ensure you have MATLAB installed (version R2018b or later recommended).
- **EEGLAB:** Version 2024.0 or compatible.
- **Custom Scripts and Functions:** Ensure all custom functions (`identify_nan_segs`, `timings_figs`, `timing_figs_with_nan`, `remove_stim_unwanted`, `repos_events`, `remove_spec_stage`, `log_message`, etc.) are accessible in the MATLAB path.

## Troubleshooting

Make sure to check the .log file created with each iteration of the pipeline.

## Contributing

Erin L. Schaeffer // erinlschaeffer@wisc.edu

## Contact 

Ido Haber // ihaber@wisc.edu 
