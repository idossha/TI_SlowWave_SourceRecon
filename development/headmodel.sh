
#!/bin/bash
#
# This script creates head model directories for subjects in a project,
# processing subjects either in serial (default) or in parallel (if --parallel is given).
#
# Usage:
#   ./headmodel_parallel.sh <project_dir> [recon-all] [--parallel] [--quiet]
#
#   <project_dir> : The project directory containing "dicoms/" subfolder.
#   recon-all     : Optional; if provided, FreeSurfer recon-all is run afterward.
#   --parallel    : Optional; if provided, subjects are processed in parallel.
#   --quiet       : Optional; if provided, output is suppressed.
#

###############################################################################
#                      PARSE ARGUMENTS AND OPTIONS
###############################################################################

# Default values for optional flags
RUN_RECON=false
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
        echo "Usage: $0 <project_dir> [recon-all] [--parallel] [--quiet]"
        exit 1
      fi
      shift
      ;;
  esac
done

# Validate project directory
if [[ -z "$PROJECT_DIR" ]]; then
  echo "Error: <project_dir> is required."
  echo "Usage: $0 <project_dir> [recon-all] [--parallel] [--quiet]"
  exit 1
fi

# If --quiet is set, redirect all output (stdout and stderr) to /dev/null
# If you want to keep errors visible but hide normal output, use: exec 1>/dev/null
if $QUIET; then
  exec &>/dev/null
fi

###############################################################################
#                    CHECK REQUIRED COMMANDS AND DIRECTORIES
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

if ! command -v parallel &>/dev/null && $PARALLEL; then
  echo "Error: GNU Parallel is not installed, but --parallel was requested." >&2
  exit 1
fi

###############################################################################
#                     DEFINE DIRECTORIES AND ENVIRONMENT
###############################################################################

DICOM_DIR="${PROJECT_DIR}/dicoms"
MRI_DIR="${PROJECT_DIR}/MRIs"
HEAD_MODEL_DIR="${PROJECT_DIR}/head_models"

# Create output directories if they don't exist
mkdir -p "$MRI_DIR" "$HEAD_MODEL_DIR"

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

  # --- Identify T1 and T2 images ---
  T1_file="${subj_mri_dir}/T1.nii"
  T2_file="${subj_mri_dir}/T2.nii"

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
    recon-all -subject "$subject" -i "$T1_file" -all
  fi

  echo "Finished processing subject: $subject"
}

# Export variables and function so Parallel (if used) can see them
export -f process_subject
export MRI_DIR
export HEAD_MODEL_DIR
export RUN_RECON

###############################################################################
#                           RUN IN SERIAL OR PARALLEL
###############################################################################

# Find all subject directories
SUBJECT_DIRS=$(find "$DICOM_DIR" -mindepth 1 -maxdepth 1 -type d | sort)

if ! $PARALLEL; then
  # ------------------------ SERIAL PROCESSING (DEFAULT) -----------------------
  echo "Running in SERIAL mode."
  while IFS= read -r subj_dir; do
    process_subject "$subj_dir"
  done <<< "$SUBJECT_DIRS"
else
  # ------------------------ PARALLEL PROCESSING -------------------------------
  echo "Running in PARALLEL mode."

  # Determine number of cores
  CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu)

  # Run the process_subject function in parallel
  # --line-buffer + --tagstring to label lines by subject name
  # --progress + --eta to show overall progress
  # --halt now,fail=1 to kill all jobs if one fails or on Ctrl+C
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

