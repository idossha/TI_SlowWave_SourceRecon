#!/bin/bash

# Define the directory containing your NIfTI files of simulations
DIR="/Volumes/CSC-Ido/analysis/TI_MNI/"

# Define the threshold value
THRESHOLD=0.6

# Loop through each NIfTI file in the directory
for file in ${DIR}/*.nii.gz; do
    # Define the output filename
    output_file="${file%.nii.gz}_mask.nii.gz"

    # Apply threshold and create a mask
    fslmaths $file -thr $THRESHOLD -bin $output_file

    # Echo the file name for confirmation
    echo "Created mask for $file"
done
