# wave_detection.py

import logging
import os
import yasa
import pandas as pd

# Create a module-level logger
logger = logging.getLogger(__name__)

def detect_slow_waves(raw, output_dir="output"):
    """
    Detect slow waves in the raw EEG data.

    Parameters:
    - raw: mne.io.Raw, the preprocessed raw EEG data.

    Returns:
    - sw_df: pd.DataFrame, DataFrame containing summary of detected slow waves.
    """
    logger.info("Starting slow wave detection process.")
    
    # Define detection parameters
    freq_sw = (0.5, 2)  
    dur_neg = (0.3, 1.5)
    dur_pos = (0.1, 1)
    amp_neg = (30, 200)
    amp_pos = (10, 150)
    amp_ptp = (40, 350)
    coupling = False
    verbose = False

    logger.debug(f"Detection parameters - Frequency range: {freq_sw} Hz, Coupling: {coupling}, Verbose: {verbose}")
    
    try:
        # Perform slow wave detection using YASA
        logger.info("Detecting slow waves using YASA's sw_detect function.")
        sw = yasa.sw_detect(raw, freq_sw=freq_sw, dur_neg=dur_neg, dur_pos=dur_pos, amp_neg=amp_neg, amp_pos=amp_pos, amp_ptp=amp_ptp, verbose=verbose, coupling=coupling)
        
        # Retrieve the summary DataFrame of detected slow waves
        sw_df = sw.summary()
        logger.info(f"Slow wave detection completed. Number of slow waves detected: {len(sw_df)}")
        
        #Save sw_df to CSV
        csv_path = os.path.join(output_dir, "original_detection.csv")
        sw_df.to_csv(csv_path, index=False)

        return sw_df

    except Exception as e:
        logger.error(f"An error occurred during slow wave detection: {e}", exc_info=True)
        raise  # Re-raise the exception to allow upstream handling

