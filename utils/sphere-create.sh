#!/bin/bash

# Directory setup
output_dir="/Users/idohaber/Desktop/screenshots"
mkdir -p $output_dir

# Volumes to process
volumes=(
   "combined_mask.nii.gz"
)

# Voxel coordinates to check
locations=(
  "95 73 127"
  "95 56 116"
  "95 79 89"
  "101 101 81"
  '95 70 108'
)

# Location names
location_names=(
  "Anterior"
  "Posterior"
  "RSC"
  "thalamus"
  "thransition"
)

# Radius for the spherical region (in voxels)
radius=3

# Initialize the combined ROI volume with zeros
combined_roi_file="${output_dir}/combined_spheres.nii.gz"
fslmaths ${volumes[0]} -mul 0 $combined_roi_file -odt float

# Create spherical ROIs and combine them into the combined ROI volume
for i in "${!locations[@]}"; do
  location="${locations[$i]}"
  location_name="${location_names[$i]}"

  IFS=' ' read -r vx vy vz <<< "$location"

  for volume in "${volumes[@]}"; do
    volume_file=$volume
    volume_name=$(basename $volume_file .nii)
    roi_file="${output_dir}/sphere_${volume_name}_${location_name}.nii.gz"

    # Convert coordinates to integers for the ROI command
    ivx=$(printf "%.0f" $vx)
    ivy=$(printf "%.0f" $vy)
    ivz=$(printf "%.0f" $vz)

    # Create the spherical ROI
    fslmaths $volume_file -mul 0 -add 1 -roi $ivx 1 $ivy 1 $ivz 1 0 1 temp_point -odt float
    fslmaths temp_point -kernel sphere $radius -dilM -bin $roi_file -odt float

    # Add the spherical ROI to the combined volume
    fslmaths $combined_roi_file -add $roi_file $combined_roi_file -odt float
  done
done

# Visualize the original volume and the combined spherical ROIs with Freeview
freeview -v ${volumes[0]}:colormap=grayscale $combined_roi_file:colormap=heat:opacity=0.4 &
