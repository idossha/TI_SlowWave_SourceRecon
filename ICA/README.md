
## Automatic ICA Processing 
- Last Update: November 23, 2024
- Erin Schaeffer & Ido Haber

---

### parallel-ICA 

- Takes a path to a directory as an input an performs ICA in parallel based on the number of cores the machine has.
- Up to 64 parallelization maximum, and always has to be no more than half the core number of the machine.
- requires `Parallel Computing Toolbox`
- path to `eeglab` needs to be modified 
- removed thread count. Running one thread as a default

---

### serial-ICA 

- Takes a path to a directory as an input an performs ICA in parallel based on the number of cores the machine has.
- path to `eeglab` needs to be modified 
- Trying to run 2 threads as a default. If fails reduced to one. 

---


