
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

---

### EEG Processing

| Pipeline             | Output                        | Framework         | Developer  |
|----------------------|-------------------------------|-------------------|------------|
| Preprocessing        | Power comparisons             | MATLAB + EEGLAB   | E.S        |
| SW-Detection         | Descriptive stats, `.set` files | Python           | I.H        |
| Source Detection     | `.csv` files                  | MATLAB + Brainstorm | I.H      |
| Source Processing    | Origin, involvement, `.nii`   | Python            |            |

---


