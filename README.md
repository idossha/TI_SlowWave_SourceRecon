
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
| TI-CSC               | `.niftis`, `.txt`, quantified field  | simNIBS, Python, MATLAB, Docker   | I.H        | Complete (?)|

---

### EEG Processing

| Pipeline             | Output                        | Framework         | Developer  | Status |
|----------------------|-------------------------------|-------------------|------------|--------|
| EEG-preproc          | delta power comparison        | MATLAB + EEGLAB   | E.S        | Complete (?)|
| ICA                  | artifact free EEG `.set`      | MATLAB + bash     | E.S + I.H  | Complete (?)| 
| SW-detect            | descriptive stats, wave epochs, `.set` | Python           | I.H       | Complete |
| source-detect        | `.csv` files, time vs location   | MATLAB + Brainstorm | I.H      | in-process |
| source-process       | origin, involvement, `.nii`   | Python            | I.H        | 99% | 

---

### Project Tree Structure:

Project_Name_data/
├── Simulations/
├── Structural/
|   |_m2m_a/
|   |_m2m_b/
├── MRI/
└── EEG_data/
    ├── Subject_A/
    │   ├── Night1/
    │   └── Night2/
    │       ├── {subject_night_erin.set}
    │       ├── {subject_night_forICA.set}
    │       ├── {subject_night_forICA_wcomps.set}
    │       ├── {subject_night_forSW.set}
    │       ├── {subject_night_forSourceRecon.set}
    │       └── Output/
    │           ├── amica/
    │           ├── Adaptation/
    │           ├── ICA/
    │           ├── Slow_Wave/
    │           │   ├── noise_EEG.set
    │           │   ├── channels_EEG.csv
    │           │   └── slow_waves/
    │           │       ├── slow_wave_1.set
    │           │       └── slow_wave_2.set
    │           └── SourceRecon/
    │               ├── slow_wave_recon.csv
    │               ├── image_validation/
    │               ├── image_validation/
    │               └── documentation.log
    └── Subject_B/
        ├── Night1/
        └── Night2/
            ├── {subject_night_erin.set}
            ├── {subject_night_forICA.set}
            ├── {subject_night_forICA_wcomps.set}
            ├── {subject_night_forSW.set}
            ├── {subject_night_forSourceRecon.set}
            └── Output/
                ├── amica/
                ├── Adaptation/
                ├── ICA/
                ├── Slow_Wave/
                │   ├── noise_EEG.set
                │   ├── channels_EEG.csv
                │   └── slow_waves/
                │       ├── slow_wave_1.set
                │       └── slow_wave_2.set
                └── SourceRecon/
                    ├── slow_wave_recon.csv
                    ├── image_validation/
                    ├── image_validation/
                    └── documentation.log
----------------------------------------------

