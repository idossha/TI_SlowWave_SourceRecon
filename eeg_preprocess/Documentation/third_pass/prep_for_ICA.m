% prep_for_ICA.m
% Main pipeline for EEG preprocessing for ICA with logging.

% Clear workspace and command window
clear; clc;

% File Handling
experiment_path = '/Users/idohaber/Desktop/EEG';

% Add necessary paths
addpath('/Users/idohaber/Documents/MATLAB/eeglab2024.0/');
addpath('/Users/idohaber/Desktop/ti_process-main/');

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

% Ensure EEG.etc.actualTimes exists
if ~isfield(EEG.etc, 'actualTimes')
    error('EEG.etc.actualTimes not found in the EEG data.');
end
original_actualTimes = EEG.etc.actualTimes;

% Step 1: Generate initial stim_report
log_message(fid, 'Step 1: Generating initial stim_report...');
initial_stim_report = generate_stim_report(EEG, original_actualTimes);
writetable(initial_stim_report, fullfile(EEG.filepath, 'initial_stim_report.csv'));
log_message(fid, 'Initial stim_report.csv saved.');

% Step 2: Identify and reject NaN segments
log_message(fid, 'Step 2: Identifying NaN segments...');
[NaNSegments, ~] = identify_nan_segments(EEG, fid);
if isempty(NaNSegments)
    log_message(fid, 'No NaN segments found. Skipping rejection.');
else
    log_message(fid, 'Found %d NaN segments.', size(NaNSegments, 1));
    EEG = eeg_eegrej_custom(EEG, NaNSegments, fid);
    log_message(fid, 'NaN segments rejected.');
end

% Step 3: Remove undesired sleep stages (keep only stages 2 and 3)
log_message(fid, 'Step 3: Removing undesired sleep stages...');
desired_stages = [2, 3];
EEG = sleep_process.remove_spec_stage(EEG, desired_stages, '_NREM', fid);
log_message(fid, 'Unwanted sleep stages removed.');

% Step 4: Filter stim events
log_message(fid, 'Step 4: Filtering stim events by proto_type and sleep stages...');
allowed_proto_types = [4]; % Adjust as needed
EEG = filter_stim_events_by_sleep_stage(EEG, desired_stages, allowed_proto_types, fid);
log_message(fid, 'Stim events filtered.');

% Step 5: Save the pruned EEG as EEG_ICA
EEG_ICA = EEG;
EEG_ICA.filename = sprintf('Strength_%s_%s_forICA.set', whichSubj, whichSess);
EEG_ICA.setname = EEG_ICA.filename;
log_message(fid, 'Step 5: Saving pruned EEG as %s...', EEG_ICA.filename);
pop_saveset(EEG_ICA, fullfile(EEG_ICA.filepath, EEG_ICA.filename));
log_message(fid, 'Pruned EEG saved successfully.');

% Step 6: Generate stim_report for pruned data
log_message(fid, 'Step 6: Generating stim_report for pruned data...');
pruned_stim_report = generate_stim_report(EEG_ICA, original_actualTimes);
writetable(pruned_stim_report, fullfile(EEG_ICA.filepath, 'pruned_stim_report.csv'));
log_message(fid, 'Pruned stim_report.csv saved.');

% Finalize logging
log_message(fid, 'EEG preprocessing pipeline completed successfully.');
fclose(fid);

% Helper Functions
function log_message(fid, formatStr, varargin)
    timestamp = datestr(now, 'yyyy-mm-dd HH:MM:SS');
    fprintf(fid, '[%s] %s\n', timestamp, sprintf(formatStr, varargin{:}));
    fprintf('[%s] %s\n', timestamp, sprintf(formatStr, varargin{:}));
end

function stim_report = generate_stim_report(EEG, original_actualTimes)
    desired_event_types = {'stim start', 'stim end'};
    event_types = {};
    proto_types = [];
    latencies_sec = [];
    actual_times = {};
    sleep_stages = [];

    for i = 1:length(EEG.event)
        event = EEG.event(i);
        if ismember(event.type, desired_event_types)
            event_types{end+1, 1} = event.type;
            proto_types(end+1, 1) = event.proto_type;
            latencies_sec(end+1, 1) = event.latency / EEG.srate;

            event_sample = round(event.latency);
            if event_sample <= length(original_actualTimes)
                actual_times{end+1, 1} = datestr(original_actualTimes(event_sample), 'HH:MM:SS');
            else
                actual_times{end+1, 1} = 'N/A';
            end

            if isfield(EEG.etc, 'sleep_stages') && isfield(EEG.etc.sleep_stages, 'latencies')
                idx = find(EEG.etc.sleep_stages.latencies <= event.latency, 1, 'last');
                if ~isempty(idx)
                    sleep_stages(end+1, 1) = EEG.etc.sleep_stages.codes(idx);
                else
                    sleep_stages(end+1, 1) = NaN;
                end
            else
                sleep_stages(end+1, 1) = NaN;
            end
        end
    end

    stim_report = table(event_types, proto_types, latencies_sec, actual_times, sleep_stages, ...
        'VariableNames', {'Event_Type', 'proto_type', 'Latency_sec', 'Actual_Time', 'Sleep_Stage'});
end
