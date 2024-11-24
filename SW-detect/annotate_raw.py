
# annotate_raw.py

import mne
import os

def annotate_raw_data(raw, df_filtered, output_dir, suffix=''):
    """
    Annotate the raw EEG data with slow wave events from the filtered DataFrame.

    Parameters:
    - raw: mne.io.Raw, the preprocessed raw EEG data.
    - df_filtered: pd.DataFrame, DataFrame containing filtered and classified slow waves.
    - output_dir: str, path to the output directory where annotated data will be saved.
    - suffix: str, additional suffix to differentiate output files.
    """
    onsets, durations, descriptions = [], [], []

    for _, row in df_filtered.iterrows():
        onsets.append(row['Start'])  # Start time in seconds
        durations.append(0)  # Instantaneous event
        descriptions.append("Start")

        onsets.append(row['NegPeak'])  # Time of negative peak
        durations.append(0)
        descriptions.append("NegPeak")

        onsets.append(row['PosPeak'])  # Time of positive peak
        durations.append(0)
        descriptions.append("PosPeak")

        onsets.append(row['End'])  # End time in seconds
        durations.append(0)
        descriptions.append("End")

    annotations = mne.Annotations(onset=onsets, duration=durations, description=descriptions)
    raw.set_annotations(annotations)

    # Save annotated raw data
    output_fname = os.path.join(output_dir, f'annotated_raw_{suffix}.set')
    mne.export.export_raw(output_fname, raw, fmt='eeglab')
    print(f"Annotated raw data saved to {output_fname}")

