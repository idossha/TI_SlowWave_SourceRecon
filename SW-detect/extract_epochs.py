
# extract_epochs.py

import mne
import os
import numpy as np
import matplotlib.pyplot as plt

def extract_and_save_epochs(raw, extraction_df, sf, output_dir, suffix=''):
    """
    Extract individual epochs from the raw data, save them as .set files, and generate images.

    Parameters:
    - raw: mne.io.Raw, the preprocessed raw EEG data.
    - extraction_df: pd.DataFrame, DataFrame containing the waves to extract.
    - sf: float, sampling frequency.
    - output_dir: str, path to the output directory where epochs and images will be saved.
    - suffix: str, additional suffix to differentiate output files.
    """
    epoch_data_dir = os.path.join(output_dir, f'epoch-data-{suffix}')
    epoch_img_dir = os.path.join(output_dir, f'epoch-imgs-{suffix}')
    os.makedirs(epoch_data_dir, exist_ok=True)
    os.makedirs(epoch_img_dir, exist_ok=True)

    sfreq = sf
    baseline_duration = 0.2  # 0.2 seconds

    for i in range(len(extraction_df)):
        row = extraction_df.iloc[i]

        start_time = row['Start']
        neg_peak_time = row['NegPeak']
        pos_peak_time = row['PosPeak']
        end_time = row['End']

        new_start_time = start_time - baseline_duration
        if new_start_time < 0:
            new_start_time = 0

        new_start_sample = int(new_start_time * sfreq)
        end_sample = int(end_time * sfreq)

        epoch_data = raw.get_data(start=new_start_sample, stop=end_sample + 1)
        info = raw.info

        raw_epoch = mne.io.RawArray(epoch_data, info)

        # Adjust event sample indices
        neg_peak_sample = int((neg_peak_time - new_start_time) * sfreq)
        pos_peak_sample = int((pos_peak_time - new_start_time) * sfreq)
        start_event_sample = int((start_time - new_start_time) * sfreq)

        events = np.array([
            [start_event_sample, 0, 1],  # Start event after the baseline
            [neg_peak_sample, 0, 2],     # NegPeak event
            [pos_peak_sample, 0, 3],     # PosPeak event
        ])

        annotations = mne.Annotations(onset=events[:, 0] / sfreq,
                                      duration=[0, 0, 0],
                                      description=['Start', 'NegPeak', 'PosPeak'])
        raw_epoch.set_annotations(annotations)

        epoch_name = row['Slow_Wave_Name']
        channel_name = row['Channel']

        file_name = f"{epoch_name}_{channel_name}.set"
        epoch_file = os.path.join(epoch_data_dir, file_name)
        mne.export.export_raw(epoch_file, raw_epoch, fmt='eeglab')

        # Generate and save epoch image
        try:
            plot_epoch_waveform(raw, row, sf, output_dir=epoch_img_dir)
        except Exception as e:
            print(f"Error generating image for {epoch_name}: {e}")

def plot_epoch_waveform(raw, row, sf, output_dir):
    """
    Generate and save a waveform image for a single epoch.

    Parameters:
    - raw: mne.io.Raw, the preprocessed raw EEG data.
    - row: pd.Series, a single row from the DataFrame containing epoch info.
    - sf: float, sampling frequency.
    - output_dir: str, path to the output directory where images will be saved.
    """
    start_sample = int(row['Start'] * sf)
    neg_peak_sample = int(row['NegPeak'] * sf)
    pos_peak_sample = int(row['PosPeak'] * sf)
    end_sample = int(row['End'] * sf)

    tmin = 0  # Start aligned at 0
    tmax = (end_sample - start_sample) / sf  # Duration from Start to End

    events = np.array([[start_sample, 0, 1]])  # Event code 1 for 'Start'

    epoch = mne.Epochs(
        raw, events, event_id={'Start': 1},
        tmin=tmin, tmax=tmax, baseline=None, preload=True
    )

    neg_peak_time = (neg_peak_sample - start_sample) / sf
    pos_peak_time = (pos_peak_sample - start_sample) / sf
    end_time = (end_sample - start_sample) / sf

    selected_channel = row['Channel']
    slow_wave_name = row['Slow_Wave_Name']

    if selected_channel not in raw.ch_names:
        print(f"Channel {selected_channel} not found in raw data for {slow_wave_name}. Skipping.")
        return

    channel_idx = raw.ch_names.index(selected_channel)

    fig, ax = plt.subplots(figsize=(10, 4))

    epoch_data = epoch.get_data(picks=[channel_idx])[0, 0, :]  # Get data for the selected channel
    times = epoch.times  # Times corresponding to the epoch

    ax.plot(times, epoch_data, color='black', label='EEG Signal')

    ax.axvline(0, color='black', linestyle='--', label='Start')  # Start event
    ax.axvline(neg_peak_time, color='red', linestyle='--', label='NegPeak')
    ax.axvline(pos_peak_time, color='green', linestyle='--', label='PosPeak')
    ax.axvline(end_time, color='blue', linestyle='--', label='End')

    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Amplitude (V)')
    ax.set_title(f"{slow_wave_name} // {selected_channel}")
    ax.legend(loc='upper right')

    output_path = os.path.join(output_dir, f'{slow_wave_name}_{selected_channel}.png')
    fig.savefig(output_path)
    plt.close(fig)  # Close the figure to save memory

