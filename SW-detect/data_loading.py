# data_loading.py

import mne

def load_and_preprocess_data(fname):
    """
    Load EEG data from an EEGLAB .set file and preprocess it.

    Parameters:
    - fname: str, path to the .set file.

    Returns:
    - raw: mne.io.Raw, preprocessed raw EEG data.
    - sf: float, sampling frequency after resampling.
    """
    # Load the data
    raw = mne.io.read_raw_eeglab(fname, preload=True)

    # Apply bandpass filter between 0.5 Hz and 4 Hz
    raw.filter(0.5, 4, fir_design='firwin', h_trans_bandwidth=0.2, l_trans_bandwidth=0.2)

    # Resample the data to 100 Hz
    raw.resample(100)

    # Get the new sampling frequency
    sf = raw.info['sfreq']

    return raw, sf

