% Main EEG Preprocessing Script
% Ensure that 'move_critical_events.m' and 'generate_event_table.m' are in the MATLAB path or the current directory.

addpath('/Users/idohaber/Documents/MATLAB/eeglab2024.0/')
addpath('/Users/idohaber/Desktop/ti_process-main/')
eeglab nogui

% Define File Handling Parameters
experiment_path = '/Volumes/CSC-Ido/EEG';
nights = {'N1'};
subjects = {'102'};
%subjects = {'102','107','110','111','115','116','119','121','123','125','127','128'};
critical_events = {'stim start', 'stim end'}; % Events to preserve

% Define the sample rate
sample_rate = 500; % in Hz

% Define the path for the log file
log_file_path = fullfile(experiment_path, 'event_processing_log.txt');

% Start writing to the log file
fid_log = fopen(log_file_path, 'w');
if fid_log == -1
    error('Cannot create log file at %s', log_file_path);
end
fprintf(fid_log, 'EEG Event Processing Log\n');
fprintf(fid_log, '========================\n\n');
fclose(fid_log); % Close temporarily; will append later

% Loop through each subject and night
for subjIdx = 1:length(subjects)
    for nightIdx = 1:length(nights)
        % Select subject and night
        whichSubj = subjects{subjIdx};
        whichSess = nights{nightIdx};
        file_ext = '_bc.set';

        % Construct file path
        subj_sess_filepath = fullfile(experiment_path, whichSubj, whichSess);
        dirs = dir(subj_sess_filepath);

        % Find the .set file
        dir_ind = find(contains({dirs(:).name}, file_ext));
        if isempty(dir_ind)
            fprintf('File not found for Subject %s, Night %s\n', whichSubj, whichSess);
            continue; % Skip to the next iteration
        end

        % Load the original EEG file
        original_set_fullpath = fullfile(subj_sess_filepath, dirs(dir_ind).name);
        EEG_original = pop_loadset(original_set_fullpath);
        fprintf('Processing Subject %s, Night %s\n', whichSubj, whichSess);

        % --- Step 1: Generate Event Table for Original .set File ---
        fprintf('Generating event table for original .set file...\n');
        generate_event_table(EEG_original, sample_rate, original_set_fullpath);

        % --- Step 2: Remove Unwanted Sleep Stages (Keep Only NREM) ---
        fprintf('Removing data from unwanted sleep stages (keeping only NREM)...\n');
        slp = sleep_process;
        % Reminder: remove_spec_stage(EEG, stages, savestr)
        EEG_NREM = slp.remove_spec_stage(EEG_original, [0 1 4 5], '_NREM');

        % Define the NREM .set file name
        [~, original_base_name, ~] = fileparts(dirs(dir_ind).name);
        NREM_set_name = [original_base_name, '_NREM.set'];
        NREM_set_fullpath = fullfile(subj_sess_filepath, NREM_set_name);

        % Save the NREM .set file
        fprintf('Saving NREM .set file: %s\n', NREM_set_fullpath);
        pop_saveset(EEG_NREM, 'filename', NREM_set_name, 'filepath', subj_sess_filepath);

        % --- Step 3: Load NREM .set File ---
        fprintf('Loading NREM .set file for further processing...\n');
        EEG_NREM_loaded = pop_loadset(NREM_set_fullpath);

        % --- Step 4: Generate Event Table for NREM .set File ---
        fprintf('Generating event table for NREM .set file...\n');
        generate_event_table(EEG_NREM_loaded, sample_rate, NREM_set_fullpath);

        % --- Step 5: Identify NaN Segments ---
        fprintf('Identifying NaN segments...\n');
        nan_samples = any(isnan(EEG_NREM_loaded.data), 1); % Logical array indicating NaN in any channel at each time point

        % Find start and end indices of NaN segments
        nan_diff = diff([0 nan_samples 0]);
        nan_starts = find(nan_diff == 1);
        nan_ends = find(nan_diff == -1) - 1;

        % Store NaN regions as [start, end] in samples
        nan_regions = [nan_starts', nan_ends'];

        % --- Step 6: Detect and Move Critical Events ---
        fprintf('Detecting and moving critical events within NaN segments...\n');
        [EEG_NREM_processed, event_log] = move_critical_events(EEG_NREM_loaded, nan_regions, critical_events);

        % --- Step 7: Remove All NaN Segments ---
        fprintf('Removing all NaN segments...\n');
        if isempty(nan_regions)
            fprintf('No NaN segments found.\n');
        else
            % Assign NaN regions to rejection regions
            EEG_NREM_processed.etc.rejRegions = nan_regions;

            % Remove the NaN segments
            EEG_NREM_processed.etc.saveNaN = 0; % Ensure NaNs are not saved
            EEG_NREM_processed = eeg_eegrej(EEG_NREM_processed, EEG_NREM_processed.etc.rejRegions);
            fprintf('Removed %d NaN segments.\n', size(nan_regions,1));
        end

        % --- Step 8: Filter EEG.event to Keep Only Proto_Type = 4 ---
        fprintf('Filtering events to retain only Proto_Type = 4...\n');
        if isfield(EEG_NREM_processed.event, 'proto_type')
            proto_types = [EEG_NREM_processed.event.proto_type];
            desired_event_idx = (proto_types == 4);
            EEG_filtered = EEG_NREM_processed;
            EEG_filtered.event = EEG_NREM_processed.event(desired_event_idx);
            fprintf('Filtered EEG events: retained %d events with Proto_Type = 4.\n', sum(desired_event_idx));
        else
            EEG_filtered = EEG_NREM_processed;
            fprintf('No Proto_Type field found in EEG.event. No filtering applied.\n');
        end

        % --- Step 9: Save the Processed EEG File for ICA ---
        new_fileName = ['Strength_' whichSubj '_' whichSess '_forICA.set'];
        EEG_filtered.filename = new_fileName;
        EEG_filtered.setname = new_fileName;
        fprintf('Saving Processed EEG File for ICA: %s\n', new_fileName);
        pop_saveset(EEG_filtered, 'filename', new_fileName, 'filepath', subj_sess_filepath);

        % --- Step 10: Load forICA .set File ---
        forICA_set_fullpath = fullfile(subj_sess_filepath, new_fileName);
        fprintf('Loading forICA .set file for event table generation...\n');
        EEG_forICA = pop_loadset(forICA_set_fullpath);

        % --- Step 11: Generate Event Table for forICA .set File ---
        fprintf('Generating event table for forICA .set file...\n');
        generate_event_table(EEG_forICA, sample_rate, forICA_set_fullpath);
    end
end

fprintf('Processing completed for all subjects and nights.\n');
fprintf('Event processing log saved to %s\n', log_file_path);
