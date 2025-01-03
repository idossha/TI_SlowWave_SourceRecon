% run_analyze_ica.m
% Usage: run_analyze_ica <input_directory>
function run_analyze_ica(inputPath)
    % This function runs analyze_ica.run_amica on the specified path

    % Add EEGLAB to the MATLAB path
    %addpath('/Users/idohaber/Documents/MATLAB/eeglab2024.0/');  % Replace with the actual path to your EEGLAB folder
    addpath('/home/ihaber@ad.wisc.edu/eeglab2024.2'); % tononi1 path

    % Start EEGLAB without GUI
    eeglab nogui;

    % Call your analyze_ica class
    analyze_ica.run_amica(inputPath);
end
