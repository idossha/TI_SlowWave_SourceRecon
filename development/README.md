

this development folder is concerned with the final stages of TI paper of 2025


1. patch_analysis.sh:

- [ ] make sure resampling is done correctly. Can you create a debugging/valiation process?
- [ ] consider comparing it to the original sphere script.

2. reorient.py:
- [ ] was develop to solve the pial misoreientation problem in the m2m_XXX folders. Did not solve it but did the correct job.

3. headmodel.sh:
- [ ] improve parallelization 
- [ ] test with two subjects. and time it. 


---

Improtant to document:

1. there is an undeclared CLI in simnibs called `subject_atlas` that gives a .annot file registered to subject space.

useage: `subject_atlas -m /Volumes/Ido/head_models/head_models/m2m_101 -a 'DK40' -o /Users/idohaber/Desktop/`

2. the T1 in m2m_XXX and T1 in freesurfer/subjects/ are the same. Therefore this can be used in concernts for atlas registration.

---

to do:

- [ ] add nifti processing in subject space for TI-CSC 
- [ ] have `subject_space_niftis` & `mni_space_niftis` ??? or all in one folder?
- [ ] add input for varying stimulation intensities 


