#!/bin/bash


#File sturcture should be:
#
#BIDS
# |_ sub-xxx
#       |_structural
#       |_DWI
#           |_sub-xxx_dwi.nii.gz
#           |_sub-xxx_dwi.json
#           |_sub-xxx_dwi.bvec
#           |_sub-xxx_dwi.bval
#       |_functional

# Be advised it takes about 3h to compelete a single subject.
# tensors orientation seemed to be fixed. On the surface everything looks good. Must verify.

# Replace data_dir with a path to your own directory
# data_dir=~/Downloads/Sample_DTI
# cd ${data_dir}

# If the file subjList.txt doesn't exist, create it
if [ ! -f subjList.txt ]; then
    ls | grep ^sub- > subjList.txt
fi

# Ensure acqparams.txt exists and is properly formatted
if [ ! -f acqparams.txt ]; then
    echo "0 1 0 0.06996" > acqparams.txt  # Adjust parameters according to your data
    echo "0 -1 0 0.06996" >> acqparams.txt
fi

# Loop over each subject and run preprocessing and DTI fitting
for subj in $(cat subjList.txt); do
    echo "Processing subject: ${subj}"

    # Navigate to the directory containing the diffusion data
    if [ -d "${subj}/dwi" ]; then
        cd ${subj}/dwi

        # Reorient the NIFTI file to RAS coordinate
        if [ -f "${subj}_dwi.nii.gz" ]; then
            echo "Reorienting NIFTI to RAS coordinates..."
            fslswapdim ${subj}_dwi.nii.gz RL PA IS ${subj}_dwi_reoriented.nii.gz
            if [ ! -f "${subj}_dwi_reoriented.nii.gz" ]; then
                echo "Reoriented NIFTI file not created, skipping subject."
                cd ../..
                continue
            fi
        else
            echo "NIFTI file not found, skipping subject."
            cd ../..
            continue
        fi

        # Reorient the gradient directions
        echo "Reorienting gradient directions..."
        mrconvert -fslgrad ${subj}_dwi.bvec ${subj}_dwi.bval ${subj}_dwi_reoriented.nii.gz ${subj}_reoriented.mif -force
        dwigradcheck ${subj}_reoriented.mif -export_grad_mrtrix reoriented.b -force
        mrconvert -grad reoriented.b ${subj}_reoriented.mif ${subj}_dwi_reoriented.nii.gz -export_grad_fsl reoriented.bvec reoriented.bval -force

        # Convert the NIFTI file to MIF format
        echo "Converting NIFTI to MIF format..."
        mrconvert -fslgrad reoriented.bvec reoriented.bval ${subj}_dwi_reoriented.nii.gz ${subj}.mif -force
        if [ ! -f "${subj}.mif" ]; then
            echo "MIF file not created, skipping subject."
            cd ../..
            continue
        fi

        # Denoise the data with a smaller extent value for faster processing
        echo "Denoising data..."
        dwidenoise ${subj}.mif ${subj}_denoised.mif -noise ${subj}_noise.mif -extent 3 -force
        if [ ! -f "${subj}_denoised.mif" ]; then
            echo "Denoised MIF file not created, skipping subject."
            cd ../..
            continue
        fi

        # Create a copy in NIFTI format, in case you want to examine it in fsleyes
        echo "Converting denoised MIF to NIFTI format..."
        mrconvert ${subj}_denoised.mif ${subj}_denoised.nii -force
        if [ ! -f "${subj}_denoised.nii" ]; then
            echo "Denoised NIFTI file not created, skipping subject."
            cd ../..
            continue
        fi

        # Ensure dimensions match before calculating residuals
        if [ "$(mrinfo -size ${subj}_dwi_reoriented.nii.gz)" == "$(mrinfo -size ${subj}_denoised.mif)" ]; then
            echo "Calculating residuals..."
            mrcalc ${subj}_dwi_reoriented.nii.gz ${subj}_denoised.mif -subtract res.nii -force
            if [ ! -f "res.nii" ]; then
                echo "Residuals file not created, skipping subject."
                cd ../..
                continue
            fi
        else
            echo "Dimensions of input images do not match, skipping residual calculation for ${subj}"
            cd ../..
            continue
        fi

        # Create a brain mask using bet2
        echo "Creating brain mask..."
        bet2 ${subj}_denoised.nii ${subj}_mask.nii.gz -m -f 0.2
        mask_file="${subj}_mask.nii.gz"
        if [ ! -f "$mask_file" ]; then
            echo "Mask file not created, skipping subject."
            cd ../..
            continue
        fi

        # Eddy current correction using FSL's eddy_correct
        echo "Running eddy current correction with eddy_correct..."
        eddy_correct ${subj}_denoised.nii eddy_corrected.nii.gz 0
        if [ ! -f "eddy_corrected.nii.gz" ]; then
            echo "Corrected NIFTI file not created, skipping subject."
            cd ../..
            continue
        fi

        # Convert preprocessed file to NIFTI format with gradient information
        if [ -f "eddy_corrected.nii.gz" ] && [ -f "reoriented.bvec" ] && [ -f "reoriented.bval" ]; then
            echo "Converting preprocessed file to NIFTI format with gradient information..."
            mrconvert -fslgrad reoriented.bvec reoriented.bval eddy_corrected.nii.gz ${subj}_corrected.nii.gz -force
            if [ ! -f "${subj}_corrected.nii.gz" ]; then
                echo "Corrected NIFTI file not created, skipping subject."
                cd ../..
                continue
            fi
        else
            echo "Required gradient files not found, skipping subject."
            cd ../..
            continue
        fi

        # Skull strip the data using bet2
        echo "Skull stripping data..."
        bet2 ${subj}_corrected.nii.gz ${subj}_corrected_bet.nii.gz -f 0.2
        if [ ! -f "${subj}_corrected_bet.nii.gz" ]; then
            echo "File ${subj}_corrected_bet.nii.gz not found, skipping skull stripping."
            cd ../..
            continue
        fi

        # Fit the tensors and generate the FA images
        echo "Fitting tensors and generating FA images..."
        dtifit --data=${subj}_corrected.nii.gz --out=dti --mask=${subj}_corrected_bet.nii.gz --bvecs=reoriented.bvec --bvals=reoriented.bval --save_tensor
        if [ ! -f "dti_FA.nii.gz" ]; then
            echo "FA image not created, skipping subject."
            cd ../..
            continue
        fi

        cd ../..
    else
        echo "Required input files not found in ${subj}/dwi, skipping subject."
        cd ../..
    fi
done

echo "Done"
