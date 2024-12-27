
#!/bin/bash
#
# run_ica.sh
# A minimal script that launches "do_ica.m" in batch mode.

# If your HPC uses modules, uncomment or adapt:
# module purge
# module load matlab-r2024a

MATLAB_CMD="/usr/local/share/apptainer/bin/matlab-r2024a"  # HPC path or wrapper
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Optional: check if it exists. If it's a wrapper script, -f might be safer than -x
if [ ! -f "$MATLAB_CMD" ]; then
    echo "MATLAB command '$MATLAB_CMD' not found (or not accessible)."
    exit 1
fi

# Now just run your do_ica.m file
"$MATLAB_CMD" -nodisplay -nosplash -sd "$SCRIPT_DIR" -r "do_ica; exit;"

