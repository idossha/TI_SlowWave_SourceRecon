
#!/usr/bin/env bash
# patch_analysis.sh
#
# Minimal script to find peak and average intensity of a field image
# within a specific atlas region. Ensures that volumes share the same grid
# by resampling the mask to the field image's grid with nearest-neighbor.
#
# Usage:
#   ./patch_analysis.sh <atlas_file> <field_file> <region_label>

set -e

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <atlas_file> <field_file> <region_label>"
  exit 1
fi

atlas_file="$1"
field_file="$2"
region_label_input="$3"

# Temporary filenames
tmp_atlas="tmp_atlas.nii.gz"
mask_native="region_mask_native.nii.gz"
mask_resampled="region_mask_resampled.nii.gz"

# -----------------------------------------------------------------------------
# 1. Convert MGZ to NIfTI if needed
ext="${atlas_file##*.}"
atlas_nifti="$atlas_file"
if [ "$ext" = "mgz" ]; then
  echo "Converting atlas from MGZ to NIfTI format..."
  mri_convert "$atlas_file" "$tmp_atlas"
  atlas_nifti="$tmp_atlas"
fi

# -----------------------------------------------------------------------------
# 2. Determine numeric label from region_label_input (if it’s not already numeric)
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

# -----------------------------------------------------------------------------
# 3. Make a binary mask for the region (in the atlas’s native grid)
echo "Creating binary mask for label $region_label ..."
fslmaths "$atlas_nifti" -thr "$region_label" -uthr "$region_label" -bin "$mask_native"

# -----------------------------------------------------------------------------
# 4. Resample that mask into the EXACT grid of the field image
#    using nearest-neighbor. This ensures "Mask and image must be the same size"
#    error is avoided.
#
# Option A: FreeSurfer's mri_vol2vol --regheader
echo "Resampling mask to match field image grid (nearest-neighbor)..."
mri_vol2vol \
  --mov "$mask_native" \
  --targ "$field_file" \
  --o "$mask_resampled" \
  --regheader \
  --nearest

# Option B (alternative): FSL flirt with identity transform
# cat <<EOF > identity.mat
# 1 0 0 0
# 0 1 0 0
# 0 0 1 0
# 0 0 0 1
# EOF
#
# flirt -in "$mask_native" -ref "$field_file" -applyxfm -init identity.mat \
#       -interp nearestneighbour -out "$mask_resampled"

# -----------------------------------------------------------------------------
# 5. Compute overlap, mean, and max in the resampled mask
echo "Computing overlap between field image and resampled mask..."
overlap_vox=$(fslstats "$field_file" -k "$mask_resampled" -V | awk '{print $1}')
echo "Overlap voxel count = $overlap_vox"
if [ "$overlap_vox" -eq 0 ]; then
  echo "Error: No overlapping voxels found. Check your data."
  exit 1
fi

max_val=$(fslstats "$field_file" -k "$mask_resampled" -R | awk '{print $2}')
mean_val=$(fslstats "$field_file" -k "$mask_resampled" -M)

echo "------------------------------"
echo "Region: $region_label_input"
echo "Numeric Label: $region_label"
echo "Peak (Max): $max_val"
echo "Mean:       $mean_val"
echo "------------------------------"

# Cleanup (comment out if you want to keep files for debugging)
# rm -f "$tmp_atlas" "$mask_native" "$mask_resampled"

