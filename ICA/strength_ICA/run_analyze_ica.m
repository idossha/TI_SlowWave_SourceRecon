
% run_analyze_ica.m
% Usage: run_analyze_ica(projectDir, subjectsCell, nightsCell, setFileTemplate)
% This function parses input arguments and runs the analyze_ica class method.

function run_analyze_ica(projectDir, subjectsCell, nightsCell, setFileTemplate)
    % Validate inputs
    if nargin ~= 4
        error('run_analyze_ica requires exactly 4 input arguments: projectDir, subjectsCell, nightsCell, setFileTemplate.');
    end

    % Display the received parameters
    fprintf('Project Directory: %s\n', projectDir);
    fprintf('Subjects: %s\n', strjoin(subjectsCell, ', '));
    fprintf('Nights/Sessions: %s\n', strjoin(nightsCell, ', '));
    fprintf('Set File Template: %s\n', setFileTemplate);

    % Add EEGLAB to the MATLAB path
    % eeglabPath = '/Users/idohaber/Documents/MATLAB/eeglab2024.0/';  % Replace with the actual path to your EEGLAB folder
    eeglabPath = '/home/ihaber@wisc.edu/eeglab2024.2'
    if ~exist(eeglabPath, 'dir')
        error('EEGLAB path does not exist: %s', eeglabPath);
    end
    addpath(eeglabPath);

    % Start EEGLAB without GUI
    eeglab nogui;

    % Call the analyze_ica class method to process the datasets
    analyze_ica.run_amica_project(projectDir, subjectsCell, nightsCell, setFileTemplate);
end
