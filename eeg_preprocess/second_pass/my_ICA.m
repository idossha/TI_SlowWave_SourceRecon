% File: my_ICA.m

% Main EEG Preprocessing Script
% Ensure that 'reposition_events_in_nan_segments.m', 'generate_stim_report.m',
% 'sleep_process.m', and the modified 'eeg_eegrej.m' are in the MATLAB path or the current directory.

% File Handling
addpath('/Users/idohaber/Documents/MATLAB/eeglab2024.0/')
addpath('/Users/idohaber/Desktop/ti_process-main/')
eeglab nogui

% Define File Handling Parameters
experiment_path = '/Volumes/CSC-Ido/EEG';
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

        % --- Step 2: Remove Unwanted Sleep Stages (Keep Only NREM) ---
        fprintf('Removing data from unwanted sleep stages (keeping only NREM)...\n');
        slp = sleep_process;
        % Reminder: remove_spec_stage(EEG, stages, savestr)
        EEG_NREM = slp.remove_spec_stage(EEG, [0 1 4 5], '_NREM');

        % Update timeIndices and actualTimes after removing unwanted stages
        if isfield(EEG_NREM.etc, 'keepIndices')
            fprintf('Updating timeIndices and actualTimes after removing unwanted stages...\n');
            EEG_NREM.etc.timeIndices = EEG_NREM.etc.timeIndices(EEG_NREM.etc.keepIndices);
            EEG_NREM.etc.actualTimes = EEG_NREM.etc.actualTimes(EEG_NREM.etc.keepIndices);
        else
            fprintf('Warning: keepIndices not found in EEG_NREM.etc. Cannot update timeIndices and actualTimes.\n');
        end

        % Remove events that were in removed segments
        EEG_NREM = eeg_checkset(EEG_NREM, 'eventconsistency', 'makeur');

        % Sort events by latency
        [~, sortIdx] = sort([EEG_NREM.event.latency]);
        EEG_NREM.event = EEG_NREM.event(sortIdx);

        % --- Step 3: Save the NREM .set File ---
        [~, original_base_name, ~] = fileparts(dirs(dir_ind).name);
        NREM_set_name = [original_base_name, '_NREM.set'];
        NREM_set_fullpath = fullfile(subj_sess_filepath, NREM_set_name);
        fprintf('Saving NREM .set file: %s\n', NREM_set_fullpath);
        pop_saveset(EEG_NREM, 'filename', NREM_set_name, 'filepath', subj_sess_filepath);

        % --- Step 4: Generate Stim Report for NREM .set File ---
        fprintf('Generating stim report for NREM .set file...\n');
        generate_stim_report(EEG_NREM, sample_rate, NREM_set_fullpath, original_actualTimes);

        % --- Step 5: Generate Hypnogram Figure After Removing Sleep Stages ---
        fprintf('Generating hypnogram figure after removing sleep stages...\n');
        slp.timings_figs(EEG_NREM, whichSubj, whichSess);

        % --- Step 6: Identify NaN Segments ---
        fprintf('Identifying NaN segments...\n');
        nan_samples = any(isnan(EEG_NREM.data), 1); % Logical array indicating NaN in any channel at each time point

        % Find start and end indices of NaN segments
        nan_diff = diff([0 nan_samples 0]);
        nan_starts = find(nan_diff == 1);
        nan_ends = find(nan_diff == -1) - 1;

        % Store NaN regions as [start, end] in samples
        nan_regions = [nan_starts', nan_ends'];

        % --- Step 7: Reposition Events from NaN Segments ---
        fprintf('Repositioning critical events from NaN segments...\n');
        EEG_NREM_repositioned = reposition_events_in_nan_segments(EEG_NREM, nan_regions, original_actualTimes);

        % Sort events by latency
        [~, sortIdx] = sort([EEG_NREM_repositioned.event.latency]);
        EEG_NREM_repositioned.event = EEG_NREM_repositioned.event(sortIdx);

        % --- Step 8: Remove All NaN Segments to Create EEG_ICA ---
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

        % --- Step 9: Save the Processed EEG_ICA File for ICA ---
        new_fileName = ['Strength_' whichSubj '_' whichSess '_forICA.set'];
        EEG_ICA.filename = new_fileName;
        EEG_ICA.setname = new_fileName;
        forICA_set_fullpath = fullfile(subj_sess_filepath, new_fileName);
        fprintf('Saving Processed EEG_ICA File for ICA: %s\n', new_fileName);
        pop_saveset(EEG_ICA, 'filename', new_fileName, 'filepath', subj_sess_filepath);

        % --- Step 10: Generate Stim Report for forICA .set File ---
        fprintf('Generating stim report for forICA .set file...\n');
        generate_stim_report(EEG_ICA, sample_rate, forICA_set_fullpath, original_actualTimes);

        % --- Step 11: Generate Hypnogram Figure After Removing NaNs ---
        fprintf('Generating hypnogram figure after removing NaNs...\n');
        slp.timings_figs(EEG_ICA, whichSubj, whichSess);
    end
end

fprintf('Processing completed for all subjects and nights.\n');


