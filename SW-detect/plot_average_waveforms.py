
# plot_average_waveforms.py

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

def plot_waveforms(raw, df_filtered, sf, output_dir, suffix=''):
    """
    Plot average waveforms per stimulation condition and save the plot.

    Parameters:
    - raw: mne.io.Raw, the preprocessed raw EEG data.
    - df_filtered: pd.DataFrame, DataFrame containing filtered and classified slow waves.
    - sf: float, sampling frequency.
    - output_dir: str, path to the output directory where the plot will be saved.
    - suffix: str, additional suffix to differentiate output files.
    """
    waveform_length = 1  # 1 second
    n_samples = int(waveform_length * sf)  # Convert to samples

    waveforms_by_condition = {}
    for stim_condition in df_filtered['Classification'].unique():
        condition_data = df_filtered[df_filtered['Classification'] == stim_condition]
        waveforms = []
        for _, row in condition_data.iterrows():
            start_sample = int(row['Start'] * sf)
            end_sample = start_sample + n_samples  # Ensure fixed length

            if end_sample > raw.n_times:
                continue  # Skip if beyond data length

            channel_idx = raw.ch_names.index(row['Channel'])
            waveform = raw.get_data(picks=[channel_idx], start=start_sample, stop=end_sample).flatten()

            waveform_uV = waveform * 1e6  # Convert from V to μV
            waveform_centered = waveform_uV - waveform_uV[0]
            waveforms.append(waveform_centered)

        waveforms_by_condition[stim_condition] = np.array(waveforms)

    sns.set(style="whitegrid")
    plt.figure(figsize=(12, 6))
    time = np.linspace(0, waveform_length, n_samples)  # Time vector

    colors = {'pre-stim': 'blue', 'stim': 'orange', 'post-stim': 'green'}
    for stim_condition, waveforms in waveforms_by_condition.items():
        if waveforms.size > 0:
            avg_waveform = waveforms.mean(axis=0)
            std_waveform = waveforms.std(axis=0)
            plt.plot(time, avg_waveform, label=f'{stim_condition.capitalize()} (n={waveforms.shape[0]})', color=colors.get(stim_condition, 'gray'))
            plt.fill_between(time, avg_waveform - std_waveform, avg_waveform + std_waveform, alpha=0.2, color=colors.get(stim_condition, 'gray'))

    plt.axvline(0, color='black', linestyle='--', label='Start')
    plt.title(f'Average Waveforms Per Stimulation Condition ({suffix})')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude (μV)')
    plt.legend(loc='upper right')
    plt.tight_layout()

    output_path = os.path.join(output_dir, f'average_waveforms_{suffix}.png')
    plt.savefig(output_path)
    plt.close()
    print(f"Average waveforms plot saved to {output_path}")

