import mne

def load_data(fname):
    """
    Load EEG data from an EEGLAB .set file.

    Parameters:
    - fname: str, path to the .set file.

    Returns:
    - raw: mne.io.Raw, raw EEG data.
    """
    # Load the data
    raw = mne.io.read_raw_eeglab(fname, preload=True)
    return raw
