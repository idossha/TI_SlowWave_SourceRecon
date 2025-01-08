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

