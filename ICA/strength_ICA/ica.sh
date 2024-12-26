#!/bin/bash
###############################################
# run_ica.sh - Script to run ICA analysis on specific .set files in a given project directory
#
# Ido Haber // ihaber@wisc.edu
#
# Dependencies:
# 1. analyze_ica.m
# 2. run_analyze_ica.m
# 3. EEGLAB
# 4. AMICA plugin
# 5. MATLAB (ideally 2024)
# 6. Parallel Computing Toolbox
###############################################
# Function to display usage
usage() {
    echo "Usage: $0 <project_directory> <subjects_comma_separated> <nights_comma_separated>"
    echo "Example: $0 /path/to/project_dir '123,124,125' 'N1,N2,N3'"
    exit 1
}

# Check if the correct number of arguments is provided
if [ $# -ne 3 ]; then
    echo "Error: Incorrect number of arguments."
    usage
fi

# Assign arguments to variables
PROJECT_DIR="$1"
SUBJECTS="$2"
NIGHTS="$3"

# Validate project directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory '$PROJECT_DIR' does not exist."
    exit 1
fi

# Validate subjects (basic check)
if [[ ! "$SUBJECTS" =~ ^[A-Za-z0-9_,]+$ ]]; then
    echo "Error: Subjects should be a comma-separated list without spaces."
    usage
fi

# Validate nights (basic check)
if [[ ! "$NIGHTS" =~ ^[A-Za-z0-9_,]+$ ]]; then
    echo "Error: Nights should be a comma-separated list without spaces."
    usage
fi

# Convert to MATLAB cell array format
# Simpler, more reliable approach for MATLAB cell array construction
SUBJECTS_MATLAB="{'"
SUBJECTS_MATLAB+=$(echo "$SUBJECTS" | sed "s/,/\',\'/g")
SUBJECTS_MATLAB+="'}"

NIGHTS_MATLAB="{'"
NIGHTS_MATLAB+=$(echo "$NIGHTS" | sed "s/,/\',\'/g")
NIGHTS_MATLAB+="'}"

# Set the full path to the MATLAB executable
MATLAB_CMD="/usr/local/share/apptainer/bin/matlab-r2024a"  # tononi-1 matlab path
# MATLAB_CMD="/Applications/MATLAB_R2024a.app/bin/matlab"    # private mac

# Validate MATLAB executable
if [ ! -x "$MATLAB_CMD" ]; then
    echo "Error: MATLAB executable not found or not executable at '$MATLAB_CMD'"
    exit 1
fi

# Determine the directory where the script resides
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Validate script directory
if [ ! -d "$SCRIPT_DIR" ]; then
    echo "Error: Scripts directory '$SCRIPT_DIR' does not exist."
    exit 1
fi

# Set file template
SET_FILE_TEMPLATE="Strength_%s_%s_forICA.set"
# SET_FILE_TEMPLATE="Strength_%s_%s_filt_bc_we_rmwk_noZ_rmepoch_rmbs_bc.set"

# Build and execute the MATLAB command
"$MATLAB_CMD" -nodisplay -nosplash -sd "$SCRIPT_DIR" -r "run_analyze_ica('$PROJECT_DIR', $SUBJECTS_MATLAB, $NIGHTS_MATLAB, '$SET_FILE_TEMPLATE'); exit;"
