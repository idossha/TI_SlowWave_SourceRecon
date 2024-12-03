
% File: my_ICA.m

% Main EEG Preprocessing Script
% Ensure that 'reposition_events_in_nan_segments.m', 'generate_stim_report.m',
% 'sleep_process.m', and the modified 'eeg_eegrej.m' are in the MATLAB path or the current directory.

% File Handling
addpath('/Users/idohaber/Documents/MATLAB/eeglab2024.0/')
addpath('/Users/idohaber/Desktop/ti_process-main/')
eeglab nogui

% Define File Handling Parameters
experiment_path = '/Users/idohaber/Desktop/EEG';
nights = {'N1'};
subjects = {'102'};
%subjects = {'102','107','110','111','115','116','119','121','123','125','127','128'};

% Define the sample rate
sample_rate = 500; % in Hz

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
        EEG = pop_loadset(original_set_fullpath);
        fprintf('Processing Subject %s, Night %s\n', whichSubj, whichSess);

        % --- Store Original Actual Times ---
        if isfield(EEG.etc, 'actualTimes')
            original_actualTimes = EEG.etc.actualTimes;
        else
            error('EEG.etc.actualTimes not found in the original EEG data.');
        end

        % --- Step 1: Generate Stim Report for Original .set File ---
        fprintf('Generating stim report for original .set file...\n');
        generate_stim_report(EEG, sample_rate, original_set_fullpath, original_actualTimes);
        fprintf('Generating hypnogram figure for original .set ...\n');
        
        slp = sleep_process;

        % --- Step 2: Remove Unwanted Sleep Stages (Keep Only NREM) ---
        fprintf('Removing data from unwanted sleep stages (keeping only NREM)...\n');
        % Reminder: remove_spec_stage(EEG, stages, savestr)
        EEG_NREM = slp.remove_spec_stage(EEG, [0 1 4 5], '_NREM');

        % --- Step 3: Remove Events in NaN Regions (Unwanted Sleep Stages) ---
        fprintf('Removing events in unwanted sleep stages...\n');
        % Identify NaN segments in EEG_NREM
        nan_samples = any(isnan(EEG_NREM.data), 1);
        nan_diff = diff([0 nan_samples 0]);
        nan_starts = find(nan_diff == 1);
        nan_ends = find(nan_diff == -1) - 1;
        nan_regions = [nan_starts', nan_ends'];

        % Remove events that fall within NaN regions
        EEG_NREM = remove_events_in_nan_regions(EEG_NREM, nan_regions);

        % --- Step 4: Save the NREM .set File ---
        [~, original_base_name, ~] = fileparts(dirs(dir_ind).name);
        NREM_set_name = [original_base_name, '_NREM.set'];
        NREM_set_fullpath = fullfile(subj_sess_filepath, NREM_set_name);
        fprintf('Saving NREM .set file: %s\n', NREM_set_fullpath);
        pop_saveset(EEG_NREM, 'filename', NREM_set_name, 'filepath', subj_sess_filepath);

        % --- Step 5: Generate Stim Report for NREM .set File ---
        fprintf('Generating stim report for NREM .set file...\n');
        generate_stim_report(EEG_NREM, sample_rate, NREM_set_fullpath, original_actualTimes);

        % --- Step 7: Identify NaN Segments ---
        fprintf('Identifying NaN segments...\n');
        nan_samples = any(isnan(EEG_NREM.data), 1); % Logical array indicating NaN in any channel at each time point

        % Find start and end indices of NaN segments
        nan_diff = diff([0 nan_samples 0]);
        nan_starts = find(nan_diff == 1);
        nan_ends = find(nan_diff == -1) - 1;

        % Store NaN regions as [start, end] in samples
        nan_regions = [nan_starts', nan_ends'];

        % --- Step 8: Reposition Events from NaN Segments ---
        fprintf('Repositioning critical events from NaN segments...\n');
        EEG_NREM_repositioned = reposition_events_in_nan_segments(EEG_NREM, nan_regions, original_actualTimes);

        % Sort events by latency
        [~, sortIdx] = sort([EEG_NREM_repositioned.event.latency]);
        EEG_NREM_repositioned.event = EEG_NREM_repositioned.event(sortIdx);

        % --- Step 9: Remove All NaN Segments to Create EEG_ICA ---
        fprintf('Removing all NaN segments to create EEG_ICA...\n');
        if isempty(nan_regions)
            fprintf('No NaN segments found.\n');
            EEG_ICA = EEG_NREM_repositioned;
        else
            EEG_ICA = EEG_NREM_repositioned; % Create a new EEG structure for ICA processing

            % Assign NaN regions to rejection regions
            EEG_ICA.etc.rejRegions = nan_regions;

            % Remove the NaN segments
            EEG_ICA.etc.saveNaN = 0; % Ensure NaNs are not saved
            EEG_ICA = eeg_eegrej(EEG_ICA, EEG_ICA.etc.rejRegions);

            % eeg_eegrej updates timeIndices and actualTimes internally

            % Ensure events are consistent and sorted
            EEG_ICA = eeg_checkset(EEG_ICA, 'eventconsistency', 'makeur');
            [~, sortIdx] = sort([EEG_ICA.event.latency]);
            EEG_ICA.event = EEG_ICA.event(sortIdx);

            fprintf('Removed %d NaN segments.\n', size(nan_regions,1));
        end

        % --- Step 10: Save the Processed EEG_ICA File for ICA ---
        new_fileName = ['Strength_' whichSubj '_' whichSess '_forICA.set'];
        EEG_ICA.filename = new_fileName;
        EEG_ICA.setname = new_fileName;
        forICA_set_fullpath = fullfile(subj_sess_filepath, new_fileName);
        fprintf('Saving Processed EEG_ICA File for ICA: %s\n', new_fileName);
        pop_saveset(EEG_ICA, 'filename', new_fileName, 'filepath', subj_sess_filepath);

        % --- Step 11: Generate Stim Report for forICA .set File ---
        fprintf('Generating stim report for forICA .set file...\n');
        generate_stim_report(EEG_ICA, sample_rate, forICA_set_fullpath, original_actualTimes);

    end
end

fprintf('Processing completed for all subjects and nights.\n');

% Helper Function: Remove events in NaN regions
function EEG = remove_events_in_nan_regions(EEG, nan_regions)
    if isempty(nan_regions)
        return;
    end
    % Remove events that fall within NaN regions
    event_latencies = [EEG.event.latency];
    remove_indices = false(size(event_latencies));
    for iRegion = 1:size(nan_regions, 1)
        remove_indices = remove_indices | (event_latencies >= nan_regions(iRegion,1) & event_latencies <= nan_regions(iRegion,2));
    end
    % Remove the events
    EEG.event(remove_indices) = [];
    % Ensure event consistency
    EEG = eeg_checkset(EEG, 'eventconsistency', 'makeur');
end

