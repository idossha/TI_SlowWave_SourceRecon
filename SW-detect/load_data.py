
# load_data.py

import logging
import mne

# Create a module-level logger
logger = logging.getLogger(__name__)

def load_data(fname):
    """
    Load EEG data from an EEGLAB .set file.

    Parameters:
    - fname: str, path to the .set file.

    Returns:
    - raw: mne.io.Raw, raw EEG data.
    """
    logger.info(f"Attempting to load EEG data from file: {fname}")
    
    try:
        # Load the data
        raw = mne.io.read_raw_eeglab(fname, preload=True)
        logger.info(f"Successfully loaded EEG data from: {fname}")
        return raw
    except FileNotFoundError:
        logger.error(f"File not found: {fname}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading file {fname}: {e}", exc_info=True)
        raise

