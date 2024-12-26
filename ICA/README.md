
## Automatic ICA Processing 
- Last Update: November 23, 2024
- Erin Schaeffer & Ido Haber


In both cases the entrypoint is `run_ica.sh`
- path to `eeglab` & `MATLAB` need to be modified 

---


### new_parallel_ica 

- made to accomodate the STRENGTHEN dir strucutre containing the data.


/Users/idohaber/project_dir/
├── 123/
│   └── N1/
│       ├── Strength_123_N1_filt_bc_we_rmwk_noZ_rmepoch_rmbs_bc.set
│       ├── Strength_123_N1_filt_bc_we_rmwk_noZ_rmepoch_rmbs_bc_wcomps.set
│       └── amicaout/
│           └── Strength_123_N1_filt_bc_we_rmwk_noZ_rmepoch_rmbs_bc/
│               ├── status.txt
│               ├── [AMICA output files]
│               └── [Temporary files deleted]
├── 124/
│   └── N1/
│       └── ...
└── 125/
    └── N1/
        └── ...

---

### parallel-ICA 

- Takes a path to a directory as an input an performs ICA in parallel based on the number of cores the machine has.
- Up to 64 parallelization maximum, and always has to be no more than half the core number of the machine.
- requires `Parallel Computing Toolbox`
- removed thread count. Running one thread as a default


In this case you will need to have all your .set files in the same path.


---

### serial-ICA 

- Takes a path to a directory as an input an performs ICA in parallel based on the number of cores the machine has.
- Trying to run 2 threads as a default. If fails reduced to one. 


In this case you will need to have all your .set files in the same path.

---

data transfer:

Before running the actual transfer, you can test with a dry run:

```bash
rsync -avh --progress --dry-run /path/to/local/dir username@remote_host:/path/to/remote/dir
```

```bash
rsync -avh --progress /path/to/local/dir username@remote_host:/path/to/remote/dir
```


Options Explained
-a: Archive mode; preserves symbolic links, permissions, timestamps, etc.
-v: Verbose; shows details of the transfer.
-h: Human-readable output.
--progress: Displays progress for each file.
/path/to/local/dir: Path to the directory or files on your local machine.
username@remote_host:/path/to/remote/dir: Destination on the remote server.



---


```
error:

. done. Execution time: -12.37 h                                                                         │
 output directory =                                                                                        │
 /Volumes/nccam_scratch/NCCAM_scratch/Ido/TI_SourceLocalization/ICA/amicaout/Str                           │
 ength_115_N1_forICA/                                                                                      │
Scaling components to RMS microvolt                                                                        │
Scaling components to RMS microvolt                                                                        │
Saving dataset...                                                                                          │
Error processing Strength_115_N1_forICA.set: Transparency violation error.                                 │
See <a href="matlab: helpview([docroot '/matlab/matlab_prog/matlab_prog.map'],'TransparencyViolation')">Wor│
kspace Transparency in MATLAB Statements</a>.                                                              │
Warning: The following error was caught while executing 'onCleanup' class destructor:                      │
Undefined function 'cleanup_temp_files' for input arguments of type 'char'.                                │
                                                                                                           │
Error in <a href="matlab:matlab.lang.internal.introspective.errorDocCallback('analyze_ica>@()cleanup_temp_f│
iles(outdir)')" style="font-weight:bold">analyze_ica>@()cleanup_temp_files(outdir)</a>                     │
                                                                                                           │
Error in <a href="matlab:matlab.lang.internal.introspective.errorDocCallback('onCleanup/delete', '/usr/loca│
l/bin/matlab-r2024a/toolbox/matlab/lang/onCleanup.m', 25)" style="font-weight:bold">onCleanup/delete</a> (<│
a href="matlab: opentoline('/usr/local/bin/matlab-r2024a/toolbox/matlab/lang/onCleanup.m',25,0)">line 25</a│
>)                                                                                                         │
            obj.task();            


```
