
#!/usr/bin/env bash
# group_patch_analysis.sh
#
# This script performs patch analysis for a list of subjects.
#
# Usage:
#   ./group_patch_analysis.sh [subject_list] [atlas_name] <region_label>
#
#   - subject_list: Optional. A space-separated list of subject IDs in quotes.
#                   If not provided, the default list defined below will be used.
#   - atlas_name:   Optional. Defaults to "aparc.DKTatlas+aseg.mgz" if not provided.
#   - region_label: Required. Can be a region name or numeric label.
#
# Assumptions:
#   - Each subject’s atlas file is located at: fs_recon/<subject>/mri/<atlas_name>
#   - Each subject’s field image is located at: Simulations/sim_<subject>/niftis/simulation.nii
#
# Output:
#   A report is written to Group_analysis/<region_label>.txt containing per-subject stats and
#   group-average values.
#
set -e

# -------------------------------
# Default variables (modify as needed)
DEFAULT_SUBJECTS=("101" "102" "103" "106" "107" "109" "108" "110" "111" "112" "114" "115" "116" "117" "118" "119" "119" "120""121""122""123""124" "125" "127" "128" "129" "130" "131" "132" "133" "134" "136" "137" "139" "140" "141" "142")
DEFAULT_ATLAS="aparc.DKTatlas+aseg.mgz"

# -------------------------------
# Parse command-line arguments.
#
# Cases:
# 1. Only region_label is provided -> use default subjects and default atlas.
# 2. Two arguments provided -> use provided atlas and region_label; default subjects.
# 3. Three arguments provided -> first argument is subject list (space-separated),
#    second is atlas name, third is region label.
if [ "$#" -eq 1 ]; then
    region_label_input="$1"
    subjects=("${DEFAULT_SUBJECTS[@]}")
    atlas_name="$DEFAULT_ATLAS"
elif [ "$#" -eq 2 ]; then
    atlas_name="$1"
    region_label_input="$2"
    subjects=("${DEFAULT_SUBJECTS[@]}")
elif [ "$#" -eq 3 ]; then
    # The first argument should be a space-separated string of subject IDs.
    IFS=' ' read -r -a subjects <<< "$1"
    atlas_name="$2"
    region_label_input="$3"
else
    echo "Usage:"
    echo "   ./group_patch_analysis.sh [subject_list] [atlas_name] <region_label>"
    echo "Notes:"
    echo "   - subject_list: Optional. Provide a space-separated list of subject IDs in quotes."
    echo "   - atlas_name:   Optional. Defaults to 'aparc.DKTatlas+aseg.mgz'."
    echo "   - region_label: Required."
    exit 1
fi

# -------------------------------
# Define project directories (assumes the script is run from project_dir)
PROJECT_DIR=$(pwd)
FS_RECON_DIR="${PROJECT_DIR}/fs_recon"
SIMULATIONS_DIR="${PROJECT_DIR}/Simulations"
GROUP_ANALYSIS_DIR="${PROJECT_DIR}/Group_analysis"
mkdir -p "${GROUP_ANALYSIS_DIR}"

# -----------------------------------------------------------------------------
# Convert region label to numeric if necessary (do it once for all subjects)
if [[ "$region_label_input" =~ ^[0-9]+$ ]]; then
  region_label="$region_label_input"
else
  if [ -z "$FREESURFER_HOME" ]; then
    echo "Error: FREESURFER_HOME not set. Please source your FreeSurfer setup."
    exit 1
  fi

  lut_file="$FREESURFER_HOME/FreeSurferColorLUT.txt"
  if [ ! -f "$lut_file" ]; then
    echo "Error: Lookup table not found at $lut_file"
    exit 1
  fi

  found_line=$(awk -v region="$(echo "$region_label_input" | tr '[:upper:]' '[:lower:]')" \
    'tolower($2) == region {print $0}' "$lut_file" | head -n1)
  
  if [ -z "$found_line" ]; then
    echo "Error: Region name '$region_label_input' not found in LUT."
    exit 1
  fi

  region_label=$(echo "$found_line" | awk '{print $1}')
  echo "Found region '$region_label_input' -> numeric label $region_label"
fi

# Define the group output file
output_file="${GROUP_ANALYSIS_DIR}/${region_label_input}.txt"
{
  echo "Group Analysis Report for Region: $region_label_input (Numeric Label: $region_label)"
  echo "Subject_ID   Overlap_Voxels   Mean_Value   Max_Value"
  echo "---------------------------------------------------------------"
} > "$output_file"

# Initialize accumulators for group averages
total_mean=0
total_max=0
subject_count=0

# -----------------------------------------------------------------------------
# Loop over each subject in the subjects array
for subject in "${subjects[@]}"; do
  echo "Processing subject: $subject"

  # Define file paths for this subject
  subject_atlas="${FS_RECON_DIR}/${subject}/mri/${atlas_name}"
  subject_field="${SIMULATIONS_DIR}/sim_${subject}/niftis/simulation.nii"

  # Check that necessary files exist
  if [ ! -f "$subject_atlas" ]; then
    echo "Warning: Atlas file '$subject_atlas' not found for subject $subject. Skipping."
    continue
  fi
  if [ ! -f "$subject_field" ]; then
    echo "Warning: Field file '$subject_field' not found for subject $subject. Skipping."
    continue
  fi

  # Prepare temporary filenames (unique for each subject)
  tmp_atlas="tmp_atlas_${subject}.nii.gz"
  mask_native="region_mask_native_${subject}.nii.gz"
  mask_resampled="region_mask_resampled_${subject}.nii.gz"

  # -----------------------------------------------------------------------------
  # 1. Convert atlas from MGZ to NIfTI if needed
  ext="${subject_atlas##*.}"
  atlas_nifti="$subject_atlas"
  if [ "$ext" = "mgz" ]; then
    echo "[$subject] Converting atlas from MGZ to NIfTI format..."
    mri_convert "$subject_atlas" "$tmp_atlas"
    atlas_nifti="$tmp_atlas"
  fi

  # -----------------------------------------------------------------------------
  # 2. Create a binary mask for the region (in atlas native grid)
  echo "[$subject] Creating binary mask for label $region_label ..."
  fslmaths "$atlas_nifti" -thr "$region_label" -uthr "$region_label" -bin "$mask_native"

  # -----------------------------------------------------------------------------
  # 3. Resample the mask into the EXACT grid of the field image using nearest-neighbor
  echo "[$subject] Resampling mask to match field image grid..."
  mri_vol2vol \
    --mov "$mask_native" \
    --targ "$subject_field" \
    --o "$mask_resampled" \
    --regheader \
    --nearest

  # -----------------------------------------------------------------------------
  # 4. Compute overlap, mean, and max within the resampled mask
  overlap_vox=$(fslstats "$subject_field" -k "$mask_resampled" -V | awk '{print $1}')
  if [ "$overlap_vox" -eq 0 ]; then
    echo "[$subject] Error: No overlapping voxels found. Skipping subject."
    rm -f "$tmp_atlas" "$mask_native" "$mask_resampled"
    continue
  fi

  max_val=$(fslstats "$subject_field" -k "$mask_resampled" -R | awk '{print $2}')
  mean_val=$(fslstats "$subject_field" -k "$mask_resampled" -M)

  # Append this subject's results to the group output file
  printf "%-12s %-16s %-12s %-10s\n" "$subject" "$overlap_vox" "$mean_val" "$max_val" >> "$output_file"

  # Accumulate totals for group averaging
  total_mean=$(echo "$total_mean + $mean_val" | bc -l)
  total_max=$(echo "$total_max + $max_val" | bc -l)
  subject_count=$((subject_count+1))

  # Cleanup temporary files
  rm -f "$tmp_atlas" "$mask_native" "$mask_resampled"

done

# -----------------------------------------------------------------------------
# Compute group averages if at least one subject was processed
if [ "$subject_count" -gt 0 ]; then
  avg_mean=$(echo "$total_mean / $subject_count" | bc -l)
  avg_max=$(echo "$total_max / $subject_count" | bc -l)
else
  echo "No valid subjects processed. Exiting."
  exit 1
fi

# Append group average summary to the output file
{
  echo "---------------------------------------------------------------"
  echo "Group Average of Mean Field Values: $avg_mean"
  echo "Group Average of Max Field Values:  $avg_max"
} >> "$output_file"

echo "Group analysis complete. Results saved in $output_file"

