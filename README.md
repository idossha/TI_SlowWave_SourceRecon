
# Center for Sleep and Consciousness  
**Last update:** November 24, 2024  
**Author:** Ido Haber  

---

## Can temporal interference stimulation influence involvement and origination of slow oscillations during nREM sleep?

---

This repository aims to collect all scripts necessary to fully replicate the processes taken to produce our results.

The project structure has two main components:
- **TI Simulation**
- **EEG Processing**

---

### TI Simulation

- Users should refer to the TI-CSC submodule for further instructions.
- This component allows users to reconstruct head models from MRI data and assess the TI field.
  
| Pipeline             | Output                        | Framework         | Developer  | Status |
|----------------------|-------------------------------|-------------------|------------|--------|
| DWI                  | `.niftis` DTI                 | bash, FSL, MRtrix | I.H        | 99%    |
| TI-CS                | `.niftis`, .txt               | simNIBS, Python, MATLAB   | I.H        | Complete (?)|

---

### EEG Processing

| Pipeline             | Output                        | Framework         | Developer  | Status |
|----------------------|-------------------------------|-------------------|------------|--------|
| Preprocessing        | Power comparisons             | MATLAB + EEGLAB   | E.S        | Complete (?)|
| ICA                  | Clean EEG `.set`              | MATLAB + bash     | E.S + I.H  | Complete (?)| 
| SW-detect            | Descriptive stats, `.set` files | Python           | I.H       | Complete |
| source-detect        | `.csv` files                  | MATLAB + Brainstorm | I.H      | in-process |
| source-process       | Origin, involvement, `.nii`   | Python            | I.H        | 99% | 

---


