# wave_detection.py

import yasa

def detect_slow_waves(raw):
    """
    Detect slow waves in the raw EEG data.

    Parameters:
    - raw: mne.io.Raw, the preprocessed raw EEG data.

    Returns:
    - sw_df: pd.DataFrame, DataFrame containing summary of detected slow waves.
    """
    sw = yasa.sw_detect(raw, freq_sw=(0.5, 4), verbose=False, coupling=False)
    sw_df = sw.summary()
    return sw_df
