'''
 subject_atlas -m /Volumes/Ido/head_models/head_models/m2m_101 -a 'DK40' -o /Users/idohaber/Desktop/

'''
import numpy as np
import nibabel as nib

input_surface = "/Volumes/Ido/head_models/head_models/m2m_101/surfaces/lh.pial.gii"
output_surface = "/Volumes/Ido/head_models/head_models/m2m_101/surfaces/lh.pial_rotated.gii"


# A -90° rotation about X-axis
rotation_matrix = np.array([
    [1,  0,  0,  0],
    [0,  0,  1,  0],
    [0, -1,  0,  0],
    [0,  0,  0,  1]
], dtype=np.float32)

# Load the GIFTI
surf = nib.load(input_surface)

# Get the Nx3 coordinates
coords = surf.darrays[0].data  # Typically the vertices array

# Homogeneous transform
ones = np.ones((coords.shape[0], 1), dtype=coords.dtype)
homog_coords = np.hstack([coords, ones])  # shape (N,4)
rotated_homog = homog_coords @ rotation_matrix.T
rotated_coords = rotated_homog[:, :3]  # Nx3

# Convert to float32
rotated_coords = rotated_coords.astype(np.float32)

# --------------------
#  In-place update:
# --------------------
surf.darrays[0].data = rotated_coords

# Save
nib.save(surf, output_surface)
print(f"Saved rotated surface to: {output_surface}")

