
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

# Hardcode the .set file template
# Adjust the naming pattern as required
# Example Template: 'Strength_%s_%s_filt_bc_we_rmwk_noZ_rmepoch_rmbs_bc.set'
SET_FILE_TEMPLATE="Strength_%s_%s_forICA.set"

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

# Convert SUBJECTS and NIGHTS comma-separated strings to MATLAB cell array format
# Replace commas with "','"
SUBJECTS_FORMATTED=$(echo "$SUBJECTS" | sed "s/,/','/g")
NIGHTS_FORMATTED=$(echo "$NIGHTS" | sed "s/,/','/g")

# Wrap each in single quotes and enclose in curly braces
SUBJECTS_MATLAB="{'"$SUBJECTS_FORMATTED"'}"
NIGHTS_MATLAB="{'"$NIGHTS_FORMATTED"'}"


# Set the full path to the MATLAB executable
#MATLAB_CMD="/usr/local/share/apptainer/bin/matlab-r2024a"  # private mac
MATLAB_CMD="/usr/local/share/apptainer/bin/matlab-r2024a"  # tononi-1 matlab path



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

# Execute MATLAB with the specified parameters
"$MATLAB_CMD" -nodisplay -nosplash -sd "$SCRIPT_DIR" -r "run_analyze_ica('$PROJECT_DIR', $SUBJECTS_MATLAB, $NIGHTS_MATLAB, '$SET_FILE_TEMPLATE'); exit;"

# Explanation of MATLAB flags:
# -nodisplay  : Starts MATLAB without initiating any graphical display components.
# -nosplash   : Suppresses the MATLAB splash screen during startup.
# -sd         : Sets the current working directory when MATLAB starts.
# -r          : Executes specified MATLAB commands or scripts immediately after MATLAB starts.

