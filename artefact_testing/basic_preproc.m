
%% basic_preproc.m
% This script performs basic preprocessing on your EEG dataset:
%   1. Bandpass filters the data from 0.5 to 30 Hz.
%   2. Removes the baseline.
%
% It uses EEGLAB functions and assumes that EEG is already loaded in your workspace.
%
% Usage:
%   Run this script after loading your EEG data.
%   The updated EEG structure will be available in the workspace.

% Check that the EEG structure exists
if ~exist('EEG', 'var')
    error('EEG variable not found in workspace. Please load your EEG dataset first.');
end

%% Bandpass Filtering (0.5 - 30 Hz)
% pop_eegfiltnew is used for filtering. The 'locutoff' sets the low-frequency cutoff,
% and 'hicutoff' sets the high-frequency cutoff.
EEG = pop_eegfiltnew(EEG, 'locutoff', 0.5, 'hicutoff', 30);
EEG.setname = [EEG.setname '_BP'];
disp('Bandpass filtering complete (0.5-30 Hz).');

%% Remove Baseline
% pop_rmbase removes the baseline. An empty vector ([]) as the second argument 
% indicates that the entire epoch is used.
EEG = pop_rmbase(EEG, []);
EEG.setname = [EEG.setname '_BL'];
disp('Baseline removal complete.');

%% Final Check
EEG = eeg_checkset(EEG);
disp('Basic preprocessing complete.');
