
# filter.py

import logging
import mne

# Create a module-level logger
logger = logging.getLogger(__name__)

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
    logger.info("Starting filter and resample process.")
    logger.debug(f"Initial sampling frequency: {raw.info['sfreq']} Hz")
    logger.debug(f"Filter parameters - Low freq: {low_freq} Hz, High freq: {high_freq} Hz, "
                 f"Resample freq: {resample_freq} Hz")

    try:
        # Define filter parameters
        h_trans_bandwidth = 0.2
        l_trans_bandwidth = 0.2
        fir_design = 'firwin'
        logger.debug(f"Filter design parameters - "
                     f"h_trans_bandwidth: {h_trans_bandwidth} Hz, "
                     f"l_trans_bandwidth: {l_trans_bandwidth} Hz, "
                     f"fir_design: {fir_design}")

        # Resample the data
        logger.info(f"Resampling data from {raw.info['sfreq']} Hz to {resample_freq} Hz.")
        raw.resample(resample_freq)
        # Get the new sampling frequency
        sf = raw.info['sfreq']
        logger.debug(f"New sampling frequency after resampling: {sf} Hz")

        # Apply bandpass filter
        logger.info(f"Applying bandpass filter: {low_freq}-{high_freq} Hz.")
        raw.filter(
            l_freq=low_freq,
            h_freq=high_freq,
            fir_design=fir_design,
            h_trans_bandwidth=h_trans_bandwidth,
            l_trans_bandwidth=l_trans_bandwidth
        )
        logger.info("Bandpass filter applied successfully.")

        # Create a formatted string describing the filter
        filter_details = (
            f"Bandpass Filter: {low_freq}-{high_freq} Hz, "
            f"Design: {fir_design}, "
            f"Transition Bands: {l_trans_bandwidth} Hz (low), {h_trans_bandwidth} Hz (high), "
            f"Resampled to {resample_freq} Hz"
        )
        logger.debug(f"Filter details: {filter_details}")

        logger.info("Filter and resample process completed successfully.")

        return raw, sf, filter_details

    except Exception as e:
        logger.error(f"An error occurred during filtering and resampling: {e}", exc_info=True)
        raise  # Re-raise the exception after logging

