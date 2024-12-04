% prep_for_ICA.m
% Main pipeline for EEG preprocessing for ICA with logging.

% Clear workspace and command window
clear; clc;

% File Handling
% Define experiment path
experiment_path = '/Users/idohaber/Desktop/EEG';

% Add necessary paths
addpath('/Users/idohaber/Documents/MATLAB/eeglab2024.0/');
addpath('/Users/idohaber/Desktop/ti_process-main/');
% addpath('/path/to/jsonlab/');  % Only if using JSON Lab

% Initialize EEGLAB without GUI
eeglab nogui;

% Select subject, session, and file extension
whichSubj = '107';
whichSess = 'N1';
file_ext = '_bc.set';

% Define log file path
log_file_path = fullfile(experiment_path, whichSubj, whichSess, sprintf('preprocessing_%s_%s.log', whichSubj, whichSess));

% Open log file for writing
fid = fopen(log_file_path, 'w');
if fid == -1
    error('Cannot open log file %s for writing.', log_file_path);
end

% Start logging
log_message(fid, 'EEG Preprocessing Pipeline Started.');
log_message(fid, 'Subject: %s, Session: %s, File Extension: %s', whichSubj, whichSess, file_ext);

% Find and load the .set file
subj_sess_filepath = fullfile(experiment_path, whichSubj, whichSess);
dirs = dir(fullfile(subj_sess_filepath, ['*' file_ext]));
if isempty(dirs)
    log_message(fid, 'Error: File not found in %s with extension %s.', subj_sess_filepath, file_ext);
    fclose(fid);
    error('File not found in %s with extension %s.', subj_sess_filepath, file_ext);
end
EEG = pop_loadset(fullfile(subj_sess_filepath, dirs(1).name));
EEG.setname = dirs(1).name;
EEG.filename = dirs(1).name;
log_message(fid, 'Loaded EEG dataset: %s', dirs(1).name);

% Step 1: Generate initial stim_report
log_message(fid, 'Step 1: Generating initial stim_report...');
initial_stim_report = generate_stim_report(EEG, fid);

% Save stim_report as CSV
writetable(initial_stim_report, fullfile(EEG.filepath, 'initial_stim_report.csv'));
log_message(fid, 'Initial stim_report.csv saved.');

% Step 2: Identify and handle NaN segments
log_message(fid, 'Step 2: Identifying NaN segments...');
[NaNSegments, ~] = identify_nan_segments(EEG, fid);
log_message(fid, 'Found %d NaN segments.', size(NaNSegments, 1));

% Move stim events within NaN segments
log_message(fid, 'Moving stim events within NaN segments...');
EEG = move_events_within_nan(EEG, NaNSegments, fid);
log_message(fid, 'Stim events within NaN segments moved.');

% Reject NaN segments using custom eeg_eegrej
log_message(fid, 'Rejecting NaN segments...');
EEG = eeg_eegrej_custom(EEG, NaNSegments, fid);
log_message(fid, 'NaN segments rejected.');

% Step 3: Remove undesired sleep stages (keep only stages 2 and 3)
log_message(fid, 'Step 3: Removing undesired sleep sjsonTexttages...');
desired_stages = [2, 3];
EEG = sleep_process.remove_spec_stage(EEG, desired_stages, '_NREM', fid);
log_message(fid, 'Unwanted sleep stages removed.');

% Step 4: Remove stim events not in desired sleep stages or with unwanted Proto_Type
log_message(fid, 'Step 4: Filtering stim events based on sleep stages and Proto_Type...');
allowed_proto_types = [4];  % Adjust as needed
EEG = filter_stim_events_by_sleep_stage(EEG, desired_stages, allowed_proto_types, fid);
log_message(fid, 'Stim events outside desired sleep stages or with unwanted Proto_Type removed.');

% Step 5: Save the pruned EEG structure as EEG_ICA and save the .set file
EEG_ICA = EEG;  % Rename the pruned EEG structure
new_fileName = sprintf('Strength_%s_%s_forICA.set', whichSubj, whichSess);
EEG_ICA.filename = new_fileName;
EEG_ICA.setname = new_fileName;
log_message(fid, 'Step 5: Saving pruned EEG as %s...', new_fileName);
pop_saveset(EEG_ICA, fullfile(EEG_ICA.filepath, new_fileName));
log_message(fid, 'Pruned EEG saved successfully.');

% Step 6: Generate stim_report for the pruned data
log_message(fid, 'Step 6: Generating stim_report for pruned data...');
pruned_stim_report = generate_stim_report(EEG_ICA, fid);
% Save stim_report as CSV
writetable(pruned_stim_report, fullfile(EEG_ICA.filepath, 'pruned_stim_report.csv'));
log_message(fid, 'Pruned stim_report.csv saved.');

% Finalize logging
log_message(fid, 'EEG preprocessing pipeline completed successfully.');
fclose(fid);
