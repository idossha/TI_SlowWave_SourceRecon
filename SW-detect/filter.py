
def filter_and_resample(raw, low_freq=0.5, high_freq=4.0, resample_freq=100):
    """
    Apply a bandpass filter and resample the EEG data.

    Parameters:
    - raw: mne.io.Raw, raw EEG data.
    - low_freq: float, lower frequency for the bandpass filter.
    - high_freq: float, upper frequency for the bandpass filter.
    - resample_freq: float, frequency to resample the data to.

    Returns:
    - raw: mne.io.Raw, filtered and resampled EEG data.
    - sf: float, sampling frequency after resampling.
    - filter_details: str, description of the applied filter.
    """
    # Define filter parameters
    h_trans_bandwidth = 0.2
    l_trans_bandwidth = 0.2
    fir_design = 'firwin'

    # Resample the data
    raw.resample(resample_freq)
    # Get the new sampling frequency
    sf = raw.info['sfreq']
    
    # Apply bandpass filter
    raw.filter(
        l_freq=low_freq,
        h_freq=high_freq,
        fir_design=fir_design,
        h_trans_bandwidth=h_trans_bandwidth,
        l_trans_bandwidth=l_trans_bandwidth
    )

    # Create a formatted string describing the filter
    filter_details = (
        f"Bandpass Filter: {low_freq}-{high_freq} Hz, "
        f"Design: {fir_design}, "
        f"Transition Bands: {l_trans_bandwidth} Hz (low), {h_trans_bandwidth} Hz (high), "
        f"Resampled to {resample_freq} Hz"
    )

    return raw, sf, filter_details
