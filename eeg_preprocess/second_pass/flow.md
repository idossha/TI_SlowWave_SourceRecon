
# EEG Data Processing Workflow

This document outlines the step-by-step processing of EEG data, including input and output files, functions used, and main changes at each step.

## Overview

- **Input Files**: Original EEG `.set` files (e.g., `Strength_102_N1_bc.set`)
- **Output Files**:
  - Processed EEG `.set` files (`_NREM.set`, `_forICA.set`)
  - Stim reports (`*_stim_report.txt`)
  - Hypnogram figures (`*.png`)
- **Main Functions Used**:
  - `reposition_events_in_nan_segments.m`
  - `generate_stim_report.m`
  - `sleep_process.m`
  - Modified `eeg_eegrej.m`
- **Main Script**:
  - `my_ICA.m`

---

## Step-by-Step Processing

### Step 1: Load Original EEG Data

- **Script**: `my_ICA.m`
- **Input**:
  - Original EEG `.set` file (e.g., `Strength_102_N1_bc.set`)
- **Process**:
  - Load the original EEG data using `pop_loadset`.
- **Output**:
  - EEG structure in MATLAB workspace (`EEG`)

### Step 2: Store Original Actual Times

- **Script**: `my_ICA.m`
- **Process**:
  - Extract and store `EEG.etc.actualTimes` from the original EEG data as `original_actualTimes`.
- **Purpose**:
  - Preserve original actual times for use in later steps.

### Step 3: Generate Stim Report for Original Data

- **Function**: `generate_stim_report.m`
- **Input**:
  - `EEG` (original data)
  - `sample_rate` (e.g., 500 Hz)
  - Path to the original `.set` file
  - `original_actualTimes`
- **Process**:
  - Extract stim events (`'stim start'`, `'stim end'`).
  - Use original actual times for events.
  - Generate a stim report including event type, protocol type, time in seconds, actual time, shift distance, and moved flag.
- **Output**:
  - Stim report text file (e.g., `Strength_102_N1_bc_stim_report.txt`)

### Step 4: Remove Unwanted Sleep Stages (Keep Only NREM)

- **Function**: `sleep_process.remove_spec_stage`
- **Input**:
  - `EEG` (original data)
  - Unwanted sleep stages (`[0, 1, 4, 5]`)
  - Save string (`'_NREM'`)
- **Process**:
  - Replace data corresponding to unwanted sleep stages with NaNs.
  - Track indices of data kept (`keepIndices`).
- **Output**:
  - `EEG_NREM` (data with unwanted sleep stages removed)

### Step 5: Update Time Indices and Actual Times

- **Script**: `my_ICA.m`
- **Process**:
  - Update `EEG_NREM.etc.timeIndices` and `EEG_NREM.etc.actualTimes` using `keepIndices`.
- **Purpose**:
  - Ensure time indices and actual times correspond to the modified data.

### Step 6: Save NREM EEG Data

- **Script**: `my_ICA.m`
- **Input**:
  - `EEG_NREM`
- **Process**:
  - Save `EEG_NREM` to a new `.set` file with `_NREM` suffix.
- **Output**:
  - NREM EEG data file (e.g., `Strength_102_N1_bc_NREM.set`)

### Step 7: Generate Stim Report for NREM Data

- **Function**: `generate_stim_report.m`
- **Input**:
  - `EEG_NREM`
  - `sample_rate`
  - Path to the NREM `.set` file
  - `original_actualTimes`
- **Process**:
  - Generate stim report for NREM data, using original actual times.
- **Output**:
  - Stim report text file (e.g., `Strength_102_N1_bc_NREM_stim_report.txt`)

### Step 8: Generate Hypnogram Figure After Removing Sleep Stages

- **Function**: `sleep_process.timings_figs`
- **Input**:
  - `EEG_NREM`
  - Subject ID (`whichSubj`)
  - Session (`whichSess`)
- **Process**:
  - Generate hypnogram figures showing sleep stages and stim events.
- **Output**:
  - Hypnogram image files (e.g., `02_hypno_and_stim.png`)

### Step 9: Identify NaN Segments

- **Script**: `my_ICA.m`
- **Process**:
  - Identify segments with NaNs in `EEG_NREM.data`.
  - Find start and end indices of NaN segments.
  - Store NaN regions as `nan_regions`.
- **Output**:
  - `nan_regions` (matrix of NaN segment indices)

### Step 10: Reposition Events from NaN Segments

- **Function**: `reposition_events_in_nan_segments.m`
- **Input**:
  - `EEG_NREM`
  - `nan_regions`
  - `original_actualTimes`
- **Process**:
  - Reposition critical events that fall within NaN segments.
  - Store original latency and actual time in event structure.
  - Calculate and store shift distance.
- **Output**:
  - `EEG_NREM_repositioned` (EEG data with events repositioned)

### Step 11: Remove NaN Segments to Create EEG_ICA

- **Script**: `my_ICA.m`
- **Process**:
  - Assign `nan_regions` to `EEG_ICA.etc.rejRegions`.
  - Remove NaN segments using modified `eeg_eegrej` function.
  - `eeg_eegrej` updates `EEG.etc.timeIndices` and `EEG.etc.actualTimes`.
- **Output**:
  - `EEG_ICA` (EEG data ready for ICA processing)

### Step 12: Save EEG_ICA Data

- **Script**: `my_ICA.m`
- **Input**:
  - `EEG_ICA`
- **Process**:
  - Save `EEG_ICA` to a new `.set` file with `_forICA` suffix.
- **Output**:
  - EEG data file (e.g., `Strength_102_N1_forICA.set`)

### Step 13: Generate Stim Report for EEG_ICA Data

- **Function**: `generate_stim_report.m`
- **Input**:
  - `EEG_ICA`
  - `sample_rate`
  - Path to the EEG_ICA `.set` file
  - `original_actualTimes`
- **Process**:
  - Generate stim report for EEG_ICA data, including shift distances and original actual times.
- **Output**:
  - Stim report text file (e.g., `Strength_102_N1_forICA_stim_report.txt`)

### Step 14: Generate Hypnogram Figure After Removing NaNs

- **Function**: `sleep_process.timings_figs`
- **Input**:
  - `EEG_ICA`
  - Subject ID (`whichSubj`)
  - Session (`whichSess`)
- **Process**:
  - Generate hypnogram figures reflecting data after NaN removal.
- **Output**:
  - Hypnogram image files (e.g., `02_hypno_and_stim_clean.png`)

---

## Main Changes and Modifications

- **Modified `eeg_eegrej.m`**:
  - Added code to update `EEG.etc.timeIndices` and `EEG.etc.actualTimes` when data is rejected.
- **Modified `reposition_events_in_nan_segments.m`**:
  - Removed event shift report generation.
  - Stored original latency and actual time in event structure.
  - Added shift distance calculation.
- **Modified `generate_stim_report.m`**:
  - Added 'Shift_Distance_sec' column to the stim report.
  - Used original actual times for the 'Actual_Time' column.
- **Adjusted `my_ICA.m` (Main Script)**:
  - Stored original `actualTimes` before any processing.
  - Passed `original_actualTimes` to functions.
  - Removed manual updates to `timeIndices` and `actualTimes` after data rejection.
  - Ensured consistency between event data and time fields.

---

## Input and Output Files

### Input Files

- Original EEG `.set` files:
  - e.g., `Strength_102_N1_bc.set`

### Intermediate Output Files

- NREM EEG data files:
  - e.g., `Strength_102_N1_bc_NREM.set`
- Stim reports for NREM data:
  - e.g., `Strength_102_N1_bc_NREM_stim_report.txt`
- Hypnogram figures after removing sleep stages:
  - e.g., `02_hypno_and_stim.png`

### Final Output Files

- EEG data files ready for ICA:
  - e.g., `Strength_102_N1_forICA.set`
- Stim reports for EEG_ICA data:
  - e.g., `Strength_102_N1_forICA_stim_report.txt`
- Hypnogram figures after removing NaNs:
  - e.g., `02_hypno_and_stim_clean.png`

---

## Functions Used

### `reposition_events_in_nan_segments.m`

- **Purpose**:
  - Repositions critical events that fall within NaN segments.
  - Stores original latency and actual time in event structure.
  - Calculates and stores shift distances.
- **Key Changes**:
  - Removed event shift report generation.
  - Added handling of `original_actualTimes`.

### `generate_stim_report.m`

- **Purpose**:
  - Generates stim reports including event information, shift distances, and original actual times.
- **Key Changes**:
  - Added 'Shift_Distance_sec' column.
  - Used `original_actualTimes` to display original actual times in the report.

### `sleep_process.m`

- **Methods**:
  - `remove_spec_stage`:
    - Removes data corresponding to specific sleep stages.
    - Tracks indices of data kept (`keepIndices`).
  - `timings_figs`:
    - Generates hypnogram figures showing sleep stages and stim events.

### Modified `eeg_eegrej.m`

- **Purpose**:
  - Rejects portions of continuous data in an EEGLAB dataset.
  - Updates `EEG.etc.timeIndices` and `EEG.etc.actualTimes` when data is rejected.
- **Key Changes**:
  - Added code to update `EEG.etc.timeIndices` and `EEG.etc.actualTimes` during data rejection.

---

## Notes

- **Data Structures**:
  - **`EEG`**: Original EEG data.
  - **`EEG_NREM`**: EEG data after removing unwanted sleep stages.
  - **`EEG_NREM_repositioned`**: EEG data after repositioning events from NaN segments.
  - **`EEG_ICA`**: Final EEG data ready for ICA processing.

- **Event Fields**:
  - `type`: Event type (e.g., `'stim start'`, `'stim end'`).
  - `proto_type`: Protocol type identifier.
  - `latency`: Event latency in samples.
  - `moved`: Boolean flag indicating if the event was moved.
  - `shift_distance_sec`: Shift distance in seconds.
  - `original_latency`: Original latency before any changes.
  - `original_actual_time`: Original actual time before any changes.

- **Time Fields**:
  - `EEG.etc.timeIndices`: Indices of time points in the EEG data.
  - `EEG.etc.actualTimes`: Actual times corresponding to each sample in the EEG data.

- **Processing Flow**:
  1. Load original data and store original actual times.
  2. Generate stim report for original data.
  3. Remove unwanted sleep stages and update time indices.
  4. Generate stim report and hypnogram for NREM data.
  5. Identify NaN segments and reposition events.
  6. Remove NaN segments to create data ready for ICA.
  7. Generate stim report and hypnogram for final data.

---

