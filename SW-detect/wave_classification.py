
# wave_classification.py

import pandas as pd

def classify_and_filter_waves(df, pre_stim_epochs, stim_epochs, post_stim_epochs):
    """
    Classify each wave based on its start time into 'Pre-Stim', 'Stim', or 'Post-Stim'
    and assign the protocol number.

    Parameters:
    - df: pd.DataFrame, DataFrame containing detected slow waves.
    - pre_stim_epochs: list, list of pre-stim epochs.
    - stim_epochs: list, list of stim epochs.
    - post_stim_epochs: list, list of post-stim epochs.

    Returns:
    - df_filtered: pd.DataFrame, DataFrame containing classified and filtered waves.
    """
    def classify_wave(start_time, pre_stim_epochs, stim_epochs, post_stim_epochs):
        for epochs, label in [(pre_stim_epochs, 'Pre-Stim'), 
                              (stim_epochs, 'Stim'), 
                              (post_stim_epochs, 'Post-Stim')]:
            for start, end, protocol in epochs:
                if start <= start_time <= end:
                    return label, protocol
        return 'Unknown', None

    df[['Classification', 'Protocol Number']] = df['Start'].apply(
        lambda start_time: classify_wave(
            start_time,
            pre_stim_epochs, stim_epochs, post_stim_epochs
        )
    ).apply(pd.Series)

    df_filtered = df[df['Classification'] != 'Unknown'].reset_index(drop=True)

    # Create a unique name for each slow wave
    df_filtered['Slow_Wave_Name'] = (
        'proto' + df_filtered['Protocol Number'].astype(int).astype(str) + '_' +
        df_filtered['Classification'].str.lower().str.replace(' ', '-') + '_sw' +
        (df_filtered.groupby(['Protocol Number', 'Classification']).cumcount() + 1).astype(str)
    )

    # Sort the DataFrame
    classification_order = ['pre-stim', 'stim', 'post-stim']
    df_filtered['Classification'] = df_filtered['Classification'].str.lower().str.replace(' ', '-')
    df_filtered['Classification'] = pd.Categorical(df_filtered['Classification'], categories=classification_order, ordered=True)
    df_sorted = df_filtered.sort_values(by=['Protocol Number', 'Classification', 'Slow_Wave_Name'])

    return df_sorted
