
## Automatic ICA Processing 
- Last Update: November 23, 2024
- Erin Schaeffer & Ido Haber


In both cases the entrypoint is `run_ica.sh`
- path to `eeglab` & `MATLAB` need to be modified 

---

### parallel-ICA 

- Takes a path to a directory as an input an performs ICA in parallel based on the number of cores the machine has.
- Up to 64 parallelization maximum, and always has to be no more than half the core number of the machine.
- requires `Parallel Computing Toolbox`
- removed thread count. Running one thread as a default

---

### serial-ICA 

- Takes a path to a directory as an input an performs ICA in parallel based on the number of cores the machine has.
- Trying to run 2 threads as a default. If fails reduced to one. 

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
