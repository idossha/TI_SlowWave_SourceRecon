
#!/usr/bin/env python3
"""
test_pipeline.py

Example script showing how to test the entire EEG pipeline with mock data.
"""

import os
import numpy as np
import pandas as pd

# Local imports (make sure epoch_creation.py and early_late_power.py are in the same folder)
from epoch_creation import create_and_visualize_epochs
from early_late_power import (
    split_stim_epochs,
    analyze_protocols,
    plot_average_psd
)

def main():
    # ------------------------
    # 1) MOCK DATA CREATION
    # ------------------------
    sf = 100.0  # Sampling frequency: 100 Hz
    duration_sec = 1000  # 2 minutes
    n_samples = int(sf * duration_sec)
    
    # Create a single-channel random signal (shape: 1 x n_samples)
    rng = np.random.default_rng(seed=42)  # for reproducible randomness
    data = rng.normal(loc=0, scale=1, size=(1, n_samples))  # 1 channel, 12000 samples

    # Make a small DataFrame with "stim start"/"stim end" events
    # We'll define 3 pairs of events at different times in seconds.
    events = [
        # description, onset (in seconds)
        ("stim start", 100),
        ("stim end",   280),
        ("stim start", 640),
        ("stim end",   820)
    ]
    cleaned_events_df = pd.DataFrame(events, columns=["Description", "Onset"])

    # Create an output directory
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)

    # ------------------------
    # 2) EPOCH CREATION
    # ------------------------
    print("Creating epochs...")
    # This returns times in SECONDS for each epoch
    pre_stim_epochs, stim_epochs, post_stim_epochs, overlaps = create_and_visualize_epochs(
        cleaned_events_df,
        output_dir,
        sf
    )
    # You should see images: before_overlap_removal.png / after_overlap_removal.png / stim_durations.png
    # in the 'test_output' folder.

    print(f"\nPre-Stim Epochs: {pre_stim_epochs}")
    print(f"Stim Epochs: {stim_epochs}")
    print(f"Post-Stim Epochs: {post_stim_epochs}")
    print(f"Overlaps: {overlaps}")

    # ------------------------
    # 3) SPLIT STIM EPOCHS
    # ------------------------
    print("\nSplitting stim epochs into early and late...")
    from early_late_power import split_stim_epochs
    early_stim_epochs, late_stim_epochs = split_stim_epochs(stim_epochs)
    print(f"Early Stim Epochs: {early_stim_epochs}")
    print(f"Late  Stim Epochs: {late_stim_epochs}")

    # ------------------------
    # 4) ANALYZE PROTOCOLS (POWER / ENTROPY)
    # ------------------------
    print("\nAnalyzing protocols (power, entropy)...")
    from early_late_power import analyze_protocols
    protocol_stats, avg_band_diff, avg_entropy_diff = analyze_protocols(
        data=data,
        sf=sf,
        early_stim_epochs=early_stim_epochs,
        late_stim_epochs=late_stim_epochs,
        output_dir=output_dir,
        chan_idx=0,
        fmin=0.5,
        fmax=2.0,
        entrainment_band=[0.95, 1.05],
        perm_order=3,
        perm_delay=1
    )
    print(f"\nProtocol Stats: {protocol_stats}")
    print(f"Average Band Power Difference: {avg_band_diff}")
    print(f"Average Entropy Difference: {avg_entropy_diff}")
    # This should create:
    #   - psd_protocol_1.png (etc) and
    #   - band_power_differences.png
    #   - protocol_summary.txt

    # ------------------------
    # 5) PLOT AVERAGE PSD
    # ------------------------
    print("\nPlotting average PSD across protocols...")
    from early_late_power import plot_average_psd
    plot_average_psd(
        data=data,
        sf=sf,
        early_stim_epochs=early_stim_epochs,
        late_stim_epochs=late_stim_epochs,
        output_dir=output_dir,
        chan_idx=0,
        fmin=0.5,
        fmax=2.0,
        entrainment_band=[0.95, 1.05]
    )
    # This should create "average_psd.png" in 'test_output'.

    print("\nTest pipeline complete. Check 'test_output' folder for generated plots & logs.")

if __name__ == "__main__":
    main()
