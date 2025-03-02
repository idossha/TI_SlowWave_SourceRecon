
#!/bin/bash
#
# This script creates head model directories for subjects in a project,
# processing subjects either in serial (default) or in parallel (if --parallel is given).
#
# Additionally, it now supports a --recon-only option to run just the FreeSurfer recon-all
# function (which requires that subject-specific T1 images already exist in the MRIs/ folder)
# without performing DICOM conversion or head model generation.
#
# Usage:
#   ./headmodel_parallel.sh <project_dir> [recon-all] [--recon-only] [--parallel] [--quiet]
#
#   <project_dir> : The project directory containing a "dicoms/" subfolder and/or an "MRIs/" subfolder.
#   recon-all     : Optional; if provided (and not in --recon-only mode), FreeSurfer recon-all is run after head model creation.
#   --recon-only  : Optional; if provided, only recon-all is run (all other processing is skipped).
#   --parallel    : Optional; if provided, subjects are processed in parallel.
#   --quiet       : Optional; if provided, output is suppressed.
#

###############################################################################
#                      PARSE ARGUMENTS AND OPTIONS
###############################################################################

# Default values for optional flags
RUN_RECON=false
RECON_ONLY=false
PARALLEL=false
QUIET=false
PROJECT_DIR=""

# Loop over all arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --parallel)
      PARALLEL=true
      shift
      ;;
    --quiet)
      QUIET=true
      shift
      ;;
    --recon-only)
      RECON_ONLY=true
      shift
      ;;
    recon-all)
      RUN_RECON=true
      shift
      ;;
    *)
      # Assume first unknown argument is the PROJECT_DIR
      if [[ -z "$PROJECT_DIR" ]]; then
        PROJECT_DIR="$1"
      else
        echo "Unknown argument: $1"
        echo "Usage: $0 <project_dir> [recon-all] [--recon-only] [--parallel] [--quiet]"
        exit 1
      fi
      shift
      ;;
  esac
done

# Validate project directory
if [[ -z "$PROJECT_DIR" ]]; then
  echo "Error: <project_dir> is required."
  echo "Usage: $0 <project_dir> [recon-all] [--recon-only] [--parallel] [--quiet]"
  exit 1
fi

# If --quiet is set, redirect all output (stdout and stderr) to /dev/null
if $QUIET; then
  exec &>/dev/null
fi

###############################################################################
#                   RECON-ONLY MODE: JUST RUN recon-all
###############################################################################
if $RECON_ONLY; then
  echo "Running in recon-all only mode (skipping DICOM conversion and head model creation)."

  if ! command -v recon-all &>/dev/null; then
    echo "Error: recon-all (FreeSurfer) is not installed." >&2
    exit 1
  fi

  # Define directories used for recon-all only
  MRI_DIR="${PROJECT_DIR}/MRIs"
  FS_RECON_DIR="${PROJECT_DIR}/fs_recon"   # Directory for FreeSurfer output

  # Ensure the necessary directories exist
  mkdir -p "$MRI_DIR" "$FS_RECON_DIR"

  run_recon_only() {
    subj_dir="$1"
    subject=$(basename "$subj_dir")
    T1_file="${subj_dir}/T1.nii"
    if [ ! -f "$T1_file" ]; then
      echo "  [$subject] Error: T1.nii not found in ${subj_dir}, skipping recon-all for this subject."
      return
    fi
    echo "  [$subject] Running FreeSurfer recon-all..."
    recon-all -subject "$subject" -i "$T1_file" -all -sd "$FS_RECON_DIR"
    echo "Finished processing subject: $subject"
  }

  if ! $PARALLEL; then
    echo "Running recon-all in SERIAL mode."
    for subj_dir in "$MRI_DIR"/*; do
      if [ -d "$subj_dir" ]; then
        run_recon_only "$subj_dir"
      fi
    done
  else
    echo "Running recon-all in PARALLEL mode."
    if ! command -v parallel &>/dev/null; then
      echo "Error: GNU Parallel is not installed, but --parallel was requested." >&2
      exit 1
    fi
    export FS_RECON_DIR
    export MRI_DIR
    export -f run_recon_only
    find "$MRI_DIR" -mindepth 1 -maxdepth 1 -type d | sort | \
      parallel \
        --line-buffer \
        --tagstring '[{= s:.*/:: =}] ' \
        --progress \
        --eta \
        --halt now,fail=1 \
        run_recon_only {}
  fi

  echo "Recon-all only mode completed."
  exit 0
fi

###############################################################################
#                 CHECK REQUIRED COMMANDS AND DIRECTORIES
###############################################################################

if ! command -v dcm2niix &>/dev/null; then
  echo "Error: dcm2niix is not installed." >&2
  exit 1
fi

if ! command -v charm &>/dev/null; then
  echo "Error: charm (SimNIBS) is not installed." >&2
  exit 1
fi

if $RUN_RECON; then
  if ! command -v recon-all &>/dev/null; then
    echo "Error: recon-all (FreeSurfer) is not installed." >&2
    exit 1
  fi
fi

if $PARALLEL; then
  if ! command -v parallel &>/dev/null; then
    echo "Error: GNU Parallel is not installed, but --parallel was requested." >&2
    exit 1
  fi
fi

###############################################################################
#                     DEFINE DIRECTORIES AND ENVIRONMENT
###############################################################################

DICOM_DIR="${PROJECT_DIR}/dicoms"
MRI_DIR="${PROJECT_DIR}/MRIs"
HEAD_MODEL_DIR="${PROJECT_DIR}/head_models"
FS_RECON_DIR="${PROJECT_DIR}/fs_recon"   # Directory for FreeSurfer output

# Create output directories if they don't exist
mkdir -p "$MRI_DIR" "$HEAD_MODEL_DIR" "$FS_RECON_DIR"

###############################################################################
#                         DEFINE PROCESSING FUNCTION
###############################################################################

process_subject() {
  subj_path="$1"
  if [ ! -d "$subj_path" ]; then
    return
  fi

  subject=$(basename "$subj_path")
  echo "Processing subject: $subject"

  # Create subject-specific MRI directory
  subj_mri_dir="${MRI_DIR}/${subject}"
  mkdir -p "$subj_mri_dir"

  # Process each series folder (e.g., T1 and T2 series)
  for series_path in "$subj_path"/*; do
    if [ -d "$series_path" ]; then
      # Look for the .tgz file in the series folder
      for tgz_file in "$series_path"/*.tgz; do
        if [ -e "$tgz_file" ]; then
          echo "  [$subject] Unzipping archive: $(basename "$tgz_file")"
          # Create a temporary directory for extraction
          temp_dir=$(mktemp -d)
          # Extract the archive
          tar -xzf "$tgz_file" -C "$temp_dir"

          echo "  [$subject] Converting DICOM to NIfTI with dcm2niix..."
          # Run dcm2niix on the unzipped folder (output will be placed in temp_dir)
          ( cd "$temp_dir" && dcm2niix . )

          # Determine series type from the series folder name
          filetype="unknown"
          if echo "$series_path" | grep -qi "T1"; then
            filetype="T1"
          elif echo "$series_path" | grep -qi "T2"; then
            filetype="T2"
          fi

          # Find the first generated .nii file and move/rename it into the subject's MRI folder
          nii_file=$(find "$temp_dir" -maxdepth 1 -type f -name "*.nii" | head -n 1)
          if [ -n "$nii_file" ] && [ "$filetype" != "unknown" ]; then
            echo "  [$subject] Renaming converted file to ${filetype}.nii and moving to ${subj_mri_dir}"
            mv "$nii_file" "$subj_mri_dir/${filetype}.nii"
          else
            echo "  [$subject] Warning: Could not determine series type or no NIfTI file found in $(basename "$tgz_file")"
          fi

          # Clean up temporary extraction directory
          rm -rf "$temp_dir"
        fi
      done
    fi
  done

  # --- Identify T1 and T2 images using absolute paths ---
  T1_file=$(realpath "${subj_mri_dir}/T1.nii" 2>/dev/null)
  T2_file=$(realpath "${subj_mri_dir}/T2.nii" 2>/dev/null)

  if [ ! -f "$T1_file" ]; then
    echo "  [$subject] Error: T1.nii not found."
    return
  fi

  # --- Run the charm function from HEAD_MODEL_DIR ---
  if [ -f "$T2_file" ]; then
    echo "  [$subject] Running charm with T1 and T2 images..."
    ( cd "$HEAD_MODEL_DIR" && charm "$subject" "$T1_file" "$T2_file" )
  else
    echo "  [$subject] Running charm with T1 image only..."
    ( cd "$HEAD_MODEL_DIR" && charm "$subject" "$T1_file" )
  fi

  # --- Optionally run FreeSurfer recon-all ---
  if $RUN_RECON; then
    echo "  [$subject] Running FreeSurfer recon-all..."
    recon-all -subject "$subject" -i "$T1_file" -all -sd "$FS_RECON_DIR"
  fi

  echo "Finished processing subject: $subject"
}

# Export variables and function so Parallel (if used) can see them
export -f process_subject
export MRI_DIR
export HEAD_MODEL_DIR
export FS_RECON_DIR
export RUN_RECON

###############################################################################
#                           RUN IN SERIAL OR PARALLEL
###############################################################################

# Find all subject directories in the dicoms folder
SUBJECT_DIRS=$(find "$DICOM_DIR" -mindepth 1 -maxdepth 1 -type d | sort)

if ! $PARALLEL; then
  echo "Running in SERIAL mode."
  while IFS= read -r subj_dir; do
    process_subject "$subj_dir"
  done <<< "$SUBJECT_DIRS"
else
  echo "Running in PARALLEL mode."

  # Determine number of cores
  CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu)

  # Run the process_subject function in parallel
  echo "$SUBJECT_DIRS" | \
    parallel \
      --line-buffer \
      --tagstring '[{= s:.*/:: =}] ' \
      --progress \
      --eta \
      --halt now,fail=1 \
      -j "$CORES" \
      process_subject {}
fi

echo "All subjects processed."

