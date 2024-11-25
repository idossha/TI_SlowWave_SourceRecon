Center for Sleep and Consciousness 
Last update: November 24, 2024
Ido Haber

---
Can temporal interference stimulation influence involvement and origination of slow oscillations during nREM sleep? 

---

- This repo aims to collect all scripts to be able to fully replicate the process taken to produce our results. 

There project structure has two arms
- TI Simulation
- EEG processing

---

### Simulation

- Users should refer to the TI-CSC submodule for further instructions. 
- Allows users to reconstruct head models from MRI data and assess TI field. 

---

### EEG

| Pipeline      |    Output     |  Framework | Developer |
-----------------------------------------------
| Preprocessing Pipeline | power comparisons | MATLAB + EEGLAB  | E.S |
-----------------------------------------------
| SW-detection | Discriptive stats, .set files | Python | I.H |
-----------------------------------------------
| source-detect | .csv files | MATLAB + Brainstorm | I.H |
-----------------------------------------------
source-process | origin, involvment, nifti | Python | 
-----------------------------------------------

---
