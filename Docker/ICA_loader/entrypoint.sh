#!/bin/bash

matlab -batch "addpath('/home/matlab/eeglab'); savepath; eeglab('nogui'); exit;"

# Run MATLAB setup
matlab -batch "run('/home/matlab/setup_eeglab.m');"

# Start an interactive shell
exec /bin/bash

