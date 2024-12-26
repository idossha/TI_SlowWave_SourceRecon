
#!bin/bash




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
"$MATLAB_CMD" -nodisplay -nosplash -sd "$SCRIPT_DIR" -r prep_for_ICA exit;"

# Explanation of MATLAB flags:
# -nodisplay  : Starts MATLAB without initiating any graphical display components.
# -nosplash   : Suppresses the MATLAB splash screen during startup.
# -sd         : Sets the current working directory when MATLAB starts.
# -r          : Executes specified MATLAB commands or scripts immediately after MATLAB starts.
