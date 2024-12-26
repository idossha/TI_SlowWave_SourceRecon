%% A clean start is always a good idea.
clear;
clc;

% Add your paths and call EEGLAB for its functionality
% addpath('/Users/idohaber/Documents/MATLAB/eeglab2024.0/'); % private mac
addpath('/home/ihaber@ad.wisc.edu/eeglab2024.2'); % tononi1 eeglab2024
addpath('utils');
eeglab nogui;

%% Define File Handling Parameters

% Base experiment path
% experiment_path = '/Users/idohaber/Data';
experiment_path = '/Volumes/nccam_scratch/NCCAM_scratch/Ido/TI_SourceLocalization/Data'; % project path from tononi1 to scratch

% Define subjects and nights
subjects = {'103','106','108','109','111','112','114','117','118','120','122','124', '129','131','132','133','134'};
%subjects = {'123'};
nights = {'N1'};     % {'N1', 'N2', 'N3', ...} as needed

%% Important Variables

% Set to 1 if want to analyze.
REM = 0;
NREM = 1;

if NREM == 1 
    if REM == 1
        desired_proto_type = [4 5]; % both stim types
        unwanted_stages = 0;      % just drop wake
    else
        desired_proto_type = 4; 
        unwanted_stages = [0 1 4];  % drop wake and NREM
    end 
else
    desired_proto_type = 5;
    unwanted_stages = [0 1 2 3];     % drop wake and REM
end     



%% Loop through each subject and night
for subjIdx = 1:length(subjects)
    for nightIdx = 1:length(nights)
        
        %% Define Current Subject and Night
        whichSubj = subjects{subjIdx};
        whichSess = nights{nightIdx};
        
        %% Define File Paths and Names
        name_temp = sprintf('Strength_%s_%s_forAdapt.set', whichSubj, whichSess);
        %name_temp = sprintf('Strength_%s_%s_forSW.set', whichSubj, whichSess);
        filepath = fullfile(experiment_path, whichSubj, whichSess, name_temp);
        
        % Define log file path
        log_file_name = sprintf('preprocessing_%s_%s.log', whichSubj, whichSess);
        log_file_path = fullfile(experiment_path, whichSubj, whichSess, log_file_name);
        
        %% Create Necessary Directories if They Don't Exist
        if ~exist(fullfile(experiment_path, whichSubj, whichSess), 'dir')
            mkdir(fullfile(experiment_path, whichSubj, whichSess));
            fprintf('Created directory: %s\n', fullfile(experiment_path, whichSubj, whichSess));
        end
        
        %% Open Log File for Writing
        fid = fopen(log_file_path, 'w');
        if fid == -1
            fprintf('Cannot open log file %s for writing. Skipping this subject-night.\n', log_file_path);
            continue; % Skip to next iteration
        end
        
        %% Log Start of Processing
        log_message(fid, '########################################');
        log_message(fid, 'EEG Preprocessing Pipeline Started.');
        log_message(fid, 'Subject: %s, Session: %s, File: %s', whichSubj, whichSess, name_temp);
        log_message(fid, '########################################');
        fprintf('Processing Subject: %s, Night: %s\n', whichSubj, whichSess);
        
        %% Load EEG Data
        try
            EEG = pop_loadset(filepath);
            log_message(fid, 'EEG data loaded successfully from %s.', filepath);
            original_actualTimes = EEG.etc.actualTimes; % Store Original Actual Times
        catch ME
            log_message(fid, 'Error loading EEG data: %s', ME.message);
            fclose(fid);
            continue; % Skip to next iteration
        end

        
        %% Invert EEG Polarity due to LPF architecture

        EEG.data = -EEG.data;
        log_message(fid, 'Inverted polarity of EEG.data');

        %% Generate Timing Figures (Optional)
        try
            timings_figs(EEG, whichSubj, whichSess, desired_proto_type);
            log_message(fid, 'Timing figures generated.');
        catch ME
            log_message(fid, 'Error generating timing figures: %s', ME.message);
        end

         %% Drop Stim Events During Unwanted Sleep Stages
        
        log_message(fid, '########################################');
        log_message(fid, 'Removing stim events during unwanted sleep stages: %s', mat2str(unwanted_stages));
        try
            EEG_pruned = remove_stim_unwanted(EEG, unwanted_stages, fid, desired_proto_type);
            log_message(fid, 'Stim events during unwanted sleep stages removed.');
        catch ME
            log_message(fid, 'Error removing stim events: %s', ME.message);
            fclose(fid);
            continue;
        end

        %% Generate Timing Figures (Optional)
        try
            timings_figs(EEG_pruned, whichSubj, whichSess, desired_proto_type);
            log_message(fid, 'Timing figures generated.');
        catch ME
            log_message(fid, 'Error generating timing figures: %s', ME.message);
        end

        %% Identify NaN Segments
        
        log_message(fid, '########################################');
        log_message(fid, 'Identifying NaN segments...');
        try
            [NaNSegments, ~] = identify_nan_segs(EEG_pruned, fid);
            if isempty(NaNSegments)
                log_message(fid, 'No NaN segments found. Skipping rejection.');
            else
                log_message(fid, 'Found %d NaN segments.', size(NaNSegments, 1));
            end
        catch ME
            log_message(fid, 'Error identifying NaN segments: %s', ME.message);
            fclose(fid);
            continue;
        end

        
        %% Generate Timing Figures After Pruning (Optional)
        try
            timing_figs_with_nan(EEG_pruned, whichSubj, whichSess, fid, NaNSegments,desired_proto_type);
            log_message(fid, 'Timing figures after pruning generated.');
        catch ME
            log_message(fid, 'Error generating timing figures after pruning: %s', ME.message);
        end
        
        %% Identify & Move Stim Events of Interest
        
        log_message(fid, '########################################');
        log_message(fid, 'Repositioning Stim Events of type %d if during NaN...', desired_proto_type);
        try
            EEG_pruned_repositioned = repos_events(EEG_pruned, NaNSegments, original_actualTimes, fid, desired_proto_type);
            log_message(fid, 'Stim events repositioned.');
        catch ME
            log_message(fid, 'Error repositioning stim events: %s', ME.message);
            fclose(fid);
            continue;
        end
        
        %% Generate Timing Figures After Repositioning (Optional)
        try
            timings_figs(EEG_pruned_repositioned, whichSubj, whichSess,desired_proto_type);
            timing_figs_with_nan(EEG_pruned_repositioned, whichSubj, whichSess, fid, NaNSegments,desired_proto_type);
            log_message(fid, 'Timing figures after event repositioning generated.');
        catch ME
            log_message(fid, 'Error generating timing figures after event repositioning: %s', ME.message);
        end
        
        %% Remove NaNs

        log_message(fid, '########################################')
        log_message(fid, 'sRemoving NaN segments from EEG data.');
        try
            EEG_pruned_repositioned.etc.saveNaN = 0;
            EEG_wo_nans = reject(EEG_pruned_repositioned, NaNSegments);
            log_message(fid, 'NaN segments removed.');
        catch ME
            log_message(fid, 'Error removing NaN segments: %s', ME.message);
            fclose(fid);
            continue;
        end
        
        %% Generate Timing Figures After Removing NaNs (Optional)
        try
            timings_figs(EEG_wo_nans, whichSubj, whichSess,desired_proto_type);
            log_message(fid, 'Timing figures after removing NaNs generated.');
        catch ME
            log_message(fid, 'Error generating timing figures after removing NaNs: %s', ME.message);
        end
        
        %% Remove Data from Unwanted Sleep Stages
        log_message(fid, 'Removing data from unwanted sleep stages: %s', mat2str(unwanted_stages));
        try
            EEG_wo_nans.etc.saveNaN = 0;
            EEG_forICA = remove_spec_stage(EEG_wo_nans, unwanted_stages, fid);
            log_message(fid, 'Data from unwanted sleep stages removed.');
        catch ME
            log_message(fid, 'Error removing data from unwanted sleep stages: %s', ME.message);
            fclose(fid);
            continue;
        end
        
        %% Generate Timing Figures After Removing Sleep Stages (Optional)
        try
            timings_figs(EEG_forICA, whichSubj, whichSess,desired_proto_type);
            log_message(fid, 'Timing figures after removing sleep stages generated.');
        catch ME
            log_message(fid, 'Error generating timing figures after removing sleep stages: %s', ME.message);
        end
        %% Remove all other necessary events
        keepEventTypes = { 'stim start', 'stim end'};
        EEG_forICA = filter_events(EEG_forICA, keepEventTypes, desired_proto_type, fid);
        
        %% Save Processed EEG Data as _forICA.set
        new_fileName = sprintf('Strength_%s_%s_forICA.set', whichSubj, whichSess);
        EEG_forICA.filename = new_fileName;
        EEG_forICA.setname = new_fileName;
        
        %new_fileName = sprintf('Strength_%s_%s_forSW_repolarized.set', whichSubj, whichSess);
        %EEG_forSW_repolarized.filename = new_fileName;
        %EEG_forSW_repolarized.setname = new_fileName;


        log_message(fid, '########################################')
        log_message(fid, 'Saving processed EEG data as %s.', new_fileName);
        try
            pop_saveset(EEG_forICA, fullfile(EEG_forICA.filepath, new_fileName));
            log_message(fid, 'Processed EEG data saved successfully.');
        catch ME
            log_message(fid, 'Error saving processed EEG data: %s', ME.message);
        end
        
        %% Close Log File
        fclose(fid);
        fprintf('Finished processing Subject: %s, Night: %s. Log saved to %s\n', whichSubj, whichSess, log_file_path);
        
    end % End of nights loop
end % End of subjects loop

fprintf('All subjects and nights have been processed.\n');
