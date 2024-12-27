
#!/bin/bash

###############################################
# run_ica.sh - Script to run ICA analysis on .set files in a given directory
#
# Ido Haber // ihaber@wisc.edu
#
# Dependencies:
# 1. analyze_ica.m & run_analyze_ica.m
# 2. EEGLAB
# 3. AMICA plugin
# 4. MATLAB (ideally 2024)
# 5. Parallel Computing Toolbox
###############################################

if [ $# -eq 0 ]; then
    echo "Usage: $0 path_to_directory"
    exit 1
fi

DIR="$1"

if [ ! -d "$DIR" ]; then
    echo "Directory '$DIR' does not exist."
    exit 1
fi

# Set the full path to the MATLAB executable
# MATLAB_CMD="/Applications/MATLAB_R2024a.app/bin/matlab"    # for private mac
MATLAB_CMD="/usr/local/share/apptainer/bin/matlab-r2024a"  # for Tononi1

if [ ! -x "$MATLAB_CMD" ]; then
    echo "MATLAB executable not found or not executable at '$MATLAB_CMD'"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$SCRIPT_DIR" ]; then
    echo "Scripts directory '$SCRIPT_DIR' does not exist."
    exit 1
fi


"$MATLAB_CMD" -nodisplay -nosplash -sd "$SCRIPT_DIR" -r "run_analyze_ica('$DIR'); exit;"

# -nodsiplay  : starts MATLAB without initiating any graphical display components.
# -nosplash   : suppresses the MATLAB splash screen during startup
# -sd         : Sets the current working directory when MATLAB starts.
# -r          :  Executes specified MATLAB commands or scripts immediately after MATLAB starts


