
#!/bin/bash
# run_psd.sh
# This script calls high_res_PSD.py on multiple files with specified methods and an output directory.

# Define the list of files (space-separated paths)
FILES="/Volumes/CSC-Ido/Analyze/107/N1/Strength_107_N1_forSW.set
      /Volumes/CSC-Ido/Analyze/101/N1/Strength_101_N1_forSW.set"

# Define the methods to use (e.g., welch and fft)
METHODS="fft welch multitaper"

# Define the output directory
OUT_DIR="/Users/idohaber/Desktop/PSD_output_final2"

# CHANNELS="E37 E33 E32 E31 E25 E18 E28 E11"
CHANNELS="E31 E32"
#

# Call the Python script with the provided arguments.
python high_res_PSD.py --files $FILES --methods $METHODS --out $OUT_DIR --channels $CHANNELS
