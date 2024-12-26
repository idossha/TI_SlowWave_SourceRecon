 run_analyze_ica.m
% Usage: run_analyze_ica(projectDir, subjectsCell, nightsCell, setFileTemplate)
% This function parses input arguments and runs the analyze_ica class method.
function run_analyze_ica(projectDir, subjectsCell, nightsCell, setFileTemplate)
    % Validate inputs
    if nargin ~= 4
        error('run_analyze_ica requires exactly 4 input arguments: projectDir, subjectsCell, nightsCell, setFileTemplate.');
    end
    
    % Validate input types
    if ~ischar(projectDir)
        error('projectDir must be a character array');
    end
    if ~iscell(subjectsCell) || ~all(cellfun(@ischar, subjectsCell))
        error('subjectsCell must be a cell array of strings');
    end
    if ~iscell(nightsCell) || ~all(cellfun(@ischar, nightsCell))
        error('nightsCell must be a cell array of strings');
    end
    if ~ischar(setFileTemplate)
        error('setFileTemplate must be a character array');
    end
    
    % Display the received parameters
    fprintf('\nInitializing ICA Analysis with parameters:\n');
    fprintf('Project Directory: %s\n', projectDir);
    fprintf('Subjects: %s\n', strjoin(subjectsCell, ', '));
    fprintf('Nights/Sessions: %s\n', strjoin(nightsCell, ', '));
    fprintf('Set File Template: %s\n\n', setFileTemplate);
    
    % Add EEGLAB to the MATLAB path
    eeglabPath = '/home/ihaber@wisc.edu/eeglab2024.2';
    
    % Validate EEGLAB path
    if ~exist(eeglabPath, 'dir')
        error('EEGLAB path does not exist: %s', eeglabPath);
    end
    
    % Add EEGLAB to path and start it
    addpath(eeglabPath);
    fprintf('Starting EEGLAB...\n');
    eeglab nogui;
    
    % Verify EEGLAB is properly initialized
    if ~exist('ALLEEG', 'var')
        error('EEGLAB failed to initialize properly');
    end
    
    try
        % Call the analyze_ica class method to process the datasets
        fprintf('Starting ICA analysis...\n');
        analyze_ica.run_amica_project(projectDir, subjectsCell, nightsCell, setFileTemplate);
        fprintf('ICA analysis completed successfully.\n');
    catch ME
        % Handle any errors that occur during processing
        fprintf('\nError during ICA analysis:\n');
        fprintf('Error message: %s\n', ME.message);
        fprintf('Error identifier: %s\n', ME.identifier);
        fprintf('Stack trace:\n');
        disp(ME.stack);
        error('ICA analysis failed. See error details above.');
    end
end
