
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
    - filter_details: str, description of the applied filter.
    """
    # Load the data
    raw = mne.io.read_raw_eeglab(fname, preload=True)

    # Define filter parameters
    low_freq = 0.5
    high_freq = 4.0
    h_trans_bandwidth = 0.2
    l_trans_bandwidth = 0.2
    fir_design = 'firwin'

    # Apply bandpass filter
    raw.filter(
        l_freq=low_freq,
        h_freq=high_freq,
        fir_design=fir_design,
        h_trans_bandwidth=h_trans_bandwidth,
        l_trans_bandwidth=l_trans_bandwidth
    )

    # Resample the data to 100 Hz
    raw.resample(100)

    # Get the new sampling frequency
    sf = raw.info['sfreq']

    # Create a formatted string describing the filter
    filter_details = (
        f"Bandpass Filter: {low_freq}-{high_freq} Hz, "
        f"Design: {fir_design}, "
        f"Transition Bands: {l_trans_bandwidth} Hz (low), {h_trans_bandwidth} Hz (high)"
    )

    return raw, sf, filter_details

