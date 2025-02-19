
% main.m
% clear;
% clc;

%% Load EEG Dataset
% Modify the following line to load your dataset.
% Example: EEG = pop_loadset('filename','yourEEG.set','filepath','your_path');
if ~exist('EEG', 'var')
    error('EEG dataset not loaded. Please load your EEG dataset before running main.m.');
end

%% Module: Basic Preprocessing
% disp('Starting basic preprocessing...');
% basic_preproc;
% disp('Basic preprocessing complete.');
%
%% Module 1: Identify Channels by Label
disp('Identifying channels...');
[trigIdx, siEnvIdx] = identify_channels(EEG);

%% Module 2: Detect Stimulation Events from TRIG Channel
disp('Detecting stimulation events...');
[EEG, trigData, newEvents] = detect_stim_events(EEG, trigIdx);

%% Module 3: Harmonize and Append New Events
disp('Harmonizing events...');
EEG = harmonize_events(EEG, newEvents);

%% Module 4: Separate Extra Channels (TRIG & SI-ENV)
disp('Separating extra channels...');
[EEG, extraIdx] = separate_extra_channels(EEG, trigIdx, siEnvIdx);

%% Module 5: Plot TRIG & SI-ENV Channels with Event Markers
disp('Plotting channels...');
plot_channels(EEG, trigData, siEnvIdx);

%% Module 6: FFT of Each Stimulation Protocol
% Computes the FFT for each protocol (using channel 1 by default).
disp('Computing FFT for each stimulation protocol...');
protocolFFT = protocol_fft(EEG, 1);

%% Module 7: Topographic Map of 1 Hz Power (Whole Dataset)
disp('Computing topographic map of power at 1 Hz for the entire dataset...');
topo_power_1Hz(EEG);

%% Module 8: Topographic Maps for Each Stimulation Protocol (1 Hz)
disp('Computing protocol-specific topographic maps of 1 Hz power...');
protocolTopo = protocol_topo_1Hz(EEG);

disp('All processing complete.');

