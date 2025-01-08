# wave_detection.py

import logging
import yasa
import pandas as pd

# Create a module-level logger
logger = logging.getLogger(__name__)

def detect_slow_waves(raw):
    """
    Detect slow waves in the raw EEG data.

    Parameters:
    - raw: mne.io.Raw, the preprocessed raw EEG data.

    Returns:
    - sw_df: pd.DataFrame, DataFrame containing summary of detected slow waves.
    """
    logger.info("Starting slow wave detection process.")
    
    # Define detection parameters
    freq_sw = (0.5, 4)  # Frequency range for slow waves in Hz
    coupling = False
    verbose = False

    logger.debug(f"Detection parameters - Frequency range: {freq_sw} Hz, Coupling: {coupling}, Verbose: {verbose}")
    
    try:
        # Perform slow wave detection using YASA
        logger.info("Detecting slow waves using YASA's sw_detect function.")
        sw = yasa.sw_detect(raw, freq_sw=freq_sw, verbose=verbose, coupling=coupling)
        
        # Retrieve the summary DataFrame of detected slow waves
        sw_df = sw.summary()
        logger.info(f"Slow wave detection completed. Number of slow waves detected: {len(sw_df)}")
        
        return sw_df

    except Exception as e:
        logger.error(f"An error occurred during slow wave detection: {e}", exc_info=True)
        raise  # Re-raise the exception to allow upstream handling

