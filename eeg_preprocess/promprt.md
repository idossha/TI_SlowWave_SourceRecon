i want to make a couple of small change to my matlab pipeline and i could use your help again.

This pipeline is about EEG processing using EEGLAB functionality and some custom scripts.

I am going to give you the scripts, and then tell you exactly what I want to do.

Here are the scripts:

%% A clean start is always a good idea.
clear;
clc;

% Add your paths and call EEGLAB for its functionality
addpath('/Users/idohaber/Documents/MATLAB/eeglab2024.0/');
addpath('utils')
eeglab nogui;

%% Define File Handling Parameters

% Base experiment path
experiment_path = '/Users/idohaber/Desktop/EEG';

% Define subjects and nights
subjects = {'107'};
nights = {'N1'};     % {'N1', 'N2', 'N3', ...} as needed

% Ensure that subjects and nights are cell arrays of strings
if ~iscell(subjects)
    subjects = {subjects};
end
if ~iscell(nights)
    nights = {nights};
end

%% Loop through each subject and night
for subjIdx = 1:length(subjects)
    for nightIdx = 1:length(nights)
        
        %% Define Current Subject and Night
        whichSubj = subjects{subjIdx};
        whichSess = nights{nightIdx};
        
        %% Define File Paths and Names
        name_temp = sprintf('Strength_%s_%s_filt_bc_we_rmwk_noZ_rmepoch_rmbs_bc.set', whichSubj, whichSess);
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
        log_message(fid, 'EEG Preprocessing Pipeline Started.');
        log_message(fid, 'Subject: %s, Session: %s, File: %s', whichSubj, whichSess, name_temp);
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
        
        %% Identify NaN Segments
        log_message(fid, 'Identifying NaN segments...');
        try
            [NaNSegments, ~] = identify_nan_segs(EEG, fid);
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
        
        %% Generate Timing Figures (Optional)
        try
            timings_figs(EEG, whichSubj, whichSess);
            timing_figs_with_nan(EEG, whichSubj, whichSess, fid, NaNSegments);
            log_message(fid, 'Timing figures generated.');
        catch ME
            log_message(fid, 'Error generating timing figures: %s', ME.message);
        end
        
        %% Drop Stim Events During Unwanted Sleep Stages
        unwanted_stages = [0 1 2 3 5];
        log_message(fid, 'Removing stim events during unwanted sleep stages: %s', mat2str(unwanted_stages));
        try
            EEG_pruned = remove_stim_unwanted(EEG, unwanted_stages, fid);
            log_message(fid, 'Stim events during unwanted sleep stages removed.');
        catch ME
            log_message(fid, 'Error removing stim events: %s', ME.message);
            fclose(fid);
            continue;
        end
        
        %% Generate Timing Figures After Pruning (Optional)
        try
            timings_figs(EEG_pruned, whichSubj, whichSess);
            timing_figs_with_nan(EEG_pruned, whichSubj, whichSess, fid, NaNSegments);
            log_message(fid, 'Timing figures after pruning generated.');
        catch ME
            log_message(fid, 'Error generating timing figures after pruning: %s', ME.message);
        end
        
        %% Identify & Move Stim Events of Interest
        desired_proto_type = 5;
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
            timings_figs(EEG_pruned_repositioned, whichSubj, whichSess);
            timing_figs_with_nan(EEG_pruned_repositioned, whichSubj, whichSess, fid, NaNSegments);
            log_message(fid, 'Timing figures after event repositioning generated.');
        catch ME
            log_message(fid, 'Error generating timing figures after event repositioning: %s', ME.message);
        end
        
        %% Remove NaNs
        log_message(fid, 'Removing NaN segments from EEG data.');
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
            timings_figs(EEG_wo_nans, whichSubj, whichSess);
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
            timings_figs(EEG_forICA, whichSubj, whichSess);
            log_message(fid, 'Timing figures after removing sleep stages generated.');
        catch ME
            log_message(fid, 'Error generating timing figures after removing sleep stages: %s', ME.message);
        end
        
        %% Save Processed EEG Data as _forICA.set
        new_fileName = sprintf('Strength_%s_%s_forICA.set', whichSubj, whichSess);
        EEG_forICA.filename = new_fileName;
        EEG_forICA.setname = new_fileName;
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

%% Supporting Function: log_message
% Ensure that the function log_message is accessible.
% If not, include it as a nested function or in a separate file.

% Example implementation of log_message:
% function log_message(fid, format, varargin)
%     fprintf(fid, [format '\n'], varargin{:});
%     fprintf([format '\n'], varargin{:});
% end

% identify_nan_segments.m
% Identifies segments in EEG.data that contain NaNs and logs the process.

function [NaNSegments, nanIndices, totalTimeSeconds, totalTimeMinutes] = identify_nan_segs(EEG, fid)
    % Logical array where any channel is NaN
    nanData = any(isnan(EEG.data), 1);

    % Find start and end indices of NaN segments
    d = diff([0 nanData 0]);
    startIdx = find(d == 1);
    endIdx = find(d == -1) - 1;

    NaNSegments = [startIdx; endIdx]';
    nanIndices = nanData;

    totalTimeSeconds = 0; % Initialize total time in seconds

    if isempty(NaNSegments)
        log_message(fid, 'No NaN segments identified.');
        fprintf('No NaN segments identified.\n'); % Print to console
    else
        for i = 1:size(NaNSegments, 1)
            % Calculate the length of the NaN segment in seconds
            segmentLength = (NaNSegments(i, 2) - NaNSegments(i, 1)) / EEG.srate;
            
            % Accumulate total time
            totalTimeSeconds = totalTimeSeconds + segmentLength;
            
            % Prepare the detailed message
            detailedMessage = sprintf('Identified NaN segment #%d from sample %d to %d, with length (%.2f seconds).', ...
                i, NaNSegments(i, 1), NaNSegments(i, 2), segmentLength);
            
            % Log the message to the file
            log_message(fid, '%s', detailedMessage);
            
            % Print the message to the console
            fprintf('%s\n', detailedMessage);
        end
        
        % Convert total time to minutes
        totalTimeMinutes = totalTimeSeconds / 60;
        
        % Prepare the summary message with total time
        summaryMessage = sprintf('Found %d NaN segments with a total length of %.2f seconds (%.2f minutes).', ...
            size(NaNSegments, 1), totalTimeSeconds, totalTimeMinutes);
        
        % Log the summary message to the file
        log_message(fid, '%s', summaryMessage);
        
        % Print the summary message to the console
        fprintf('%s\n', summaryMessage);
    end
end

% Example implementation of log_message (if not already defined)
function log_message(fid, varargin)
    if nargin < 2
        return; % Nothing to log
    end
    fprintf(fid, varargin{:});
    fprintf(fid, '\n'); % Add a newline character at the end
end

% log_message.m
% Logs messages to both the console and a log file.

function log_message(fid, varargin)
    % log_message - Logs messages to both the console and a log file.
    %
    % Usage:
    %   log_message(fid, 'Message: %s', variable);
    %
    % Inputs:
    %   fid      - File identifier for the log file.
    %   varargin - Format string and variables, similar to fprintf.

    % Create the message string
    msg = sprintf(varargin{:});

    % Write to console
    fprintf('%s\n', msg);

    % Write to log file
    if fid ~= -1
        fprintf(fid, '%s\n', msg);
    end
end

%
% File: reject.m

function [EEG, com] = reject(EEG, regions)

    com = '';
    if nargin < 2
        help reject;
        return;
    end
    if nargin < 3
        probadded = [];
    end
    if isempty(regions)
        fprintf('No regions provided for rejection. Exiting function.\n');
        return;
    end

    fprintf('Starting rejection process...\n');

    % Ramon on 5/29/2014 for bug 1619
    if size(regions,2) > 2
        regions = sortrows(regions,3);
    else
        regions = sortrows(regions,1);
    end

    % Handle regions from eegplot
    if size(regions,2) > 2
        regions = regions(:, 3:4);
    end
    regions = combineregions(regions);

    fprintf('Regions after combining:\n');
    disp(regions);

    % ---- Modification Start: Handle prior rejRegions ----
    if isfield(EEG.etc, 'rejRegions') && ~isempty(EEG.etc.rejRegions)
        fprintf('Prior rejection regions detected. Moving them to moved_rejRegions.\n');
        % Initialize moved_rejRegions if it doesn't exist
        if isfield(EEG.etc, 'moved_rejRegions')
            EEG.etc.moved_rejRegions = [EEG.etc.moved_rejRegions; EEG.etc.rejRegions];
            fprintf('Appended existing rejRegions to moved_rejRegions.\n');
        else
            EEG.etc.moved_rejRegions = EEG.etc.rejRegions;
            fprintf('Created moved_rejRegions and moved existing rejRegions.\n');
        end
        % Clear rejRegions
        EEG.etc.rejRegions = [];
        fprintf('Cleared EEG.etc.rejRegions.\n');
    else
        fprintf('No prior rejection regions found.\n');
    end
    % ---- Modification End ----

    % ELS added - quick detour to replace data in rejection regions with NaNs
    % but otherwise keep the rest of the file intact, then save it
    if isfield(EEG.etc, 'saveNaN') && EEG.etc.saveNaN == 1
        fprintf('SaveNaN flag detected. Replacing rejected regions with NaNs.\n');
        rejectFlag = false(1, EEG.pnts);
        for i = 1:size(regions,1)
            rejectFlag(regions(i,1):regions(i,2)) = true;
        end
        EEG.data(:, rejectFlag) = NaN;
        fprintf('Replaced specified regions with NaNs.\n');

        % Keep track of rejection regions for repeat cleaning
        if isfield(EEG.etc, 'rejRegions') && ~isempty(EEG.etc.rejRegions)
            EEG.etc.rejRegions = [EEG.etc.rejRegions; regions];
            fprintf('Appended current regions to existing rejRegions.\n');
        else
            EEG.etc.rejRegions = regions;
            fprintf('Initialized rejRegions with current regions.\n');
        end

        % ---- Modification Start: Move rejRegions to moved_rejRegions ----
        if isfield(EEG.etc, 'moved_rejRegions')
            EEG.etc.moved_rejRegions = [EEG.etc.moved_rejRegions; EEG.etc.rejRegions];
            fprintf('Appended current rejRegions to moved_rejRegions.\n');
        else
            EEG.etc.moved_rejRegions = EEG.etc.rejRegions;
            fprintf('Created moved_rejRegions and moved current rejRegions.\n');
        end
        % Clear rejRegions
        EEG.etc.rejRegions = [];
        fprintf('Cleared EEG.etc.rejRegions after moving to moved_rejRegions.\n');
        % ---- Modification End ----

        regions = EEG.etc.rejRegions;  % Now empty

        % Rename and save data
        new_fileName = split(EEG.filename, '.set');
        new_fileName = strcat(new_fileName{1}, '_rmbs.set');

        % Rename set
        EEG.filename = new_fileName;
        EEG.setname = new_fileName;

        % Save data
        fprintf('Saving rejected data to %s \n', new_fileName);
        pop_saveset(EEG, fullfile(EEG.filepath, new_fileName));
    else
        fprintf('Proceeding with data rejection.\n');

        % Use rejection regions from prior rejections
        if isfield(EEG.etc, 'rejRegions') && ~isempty(EEG.etc.rejRegions)
            EEG.etc.rejRegions = [EEG.etc.rejRegions; regions];
            regions = EEG.etc.rejRegions;
            fprintf('Appended new regions to existing rejRegions.\n');
        end

        % Remove events within regions
        if ~isempty(EEG.event) && isfield(EEG.event, 'latency')
            fprintf('Removing events within rejection regions.\n');
            allEventLatencies = [ EEG.event.latency ];
            allEventFlag      = false(1,length(allEventLatencies));
            for iRegion = 1:size(regions,1)
                allEventFlag = allEventFlag | ( allEventLatencies >= regions(iRegion,1) & allEventLatencies <= regions(iRegion,2));
            end
            boundaryIndices = eeg_findboundaries(EEG);
            allEventFlag(boundaryIndices) = false; % Do not remove boundary events
            EEG.event(allEventFlag) = [];
            fprintf('Events within rejection regions removed.\n');
        end

        % Reject data
        fprintf('Rejecting specified data regions.\n');
        [EEG.data, EEG.xmax, event2, boundevents] = eegrej(EEG.data, regions, EEG.xmax-EEG.xmin, EEG.event);
        oldEEGpnts = EEG.pnts;
        EEG.pnts   = size(EEG.data,2);
        EEG.xmax   = EEG.xmax + EEG.xmin;
        fprintf('Data rejection completed. Updated EEG.pnts and EEG.xmax.\n');

        % --- Update actualTimes and timeIndices ---
        % Check if actualTimes and timeIndices exist
        if isfield(EEG.etc, 'actualTimes') && isfield(EEG.etc, 'timeIndices')
            fprintf('Updating actualTimes and timeIndices in EEG.etc...\n');
            % Create a logical index array for the points to keep
            keep_indices = true(1, oldEEGpnts);
            for iRegion = 1:size(regions, 1)
                keep_indices(regions(iRegion, 1):regions(iRegion, 2)) = false;
            end
            % Update actualTimes and timeIndices
            EEG.etc.actualTimes = EEG.etc.actualTimes(keep_indices);
            EEG.etc.timeIndices = EEG.etc.timeIndices(keep_indices);
            fprintf('actualTimes and timeIndices updated.\n');
        else
            fprintf('Warning: EEG.etc.actualTimes or EEG.etc.timeIndices not found. Cannot update these fields.\n');
        end
        % --- End Modification ---

        % Add boundary events
        fprintf('Adding boundary events.\n');
        [ EEG.event ] = eeg_insertbound(EEG.event, oldEEGpnts, regions);
        EEG = eeg_checkset(EEG, 'eventconsistency');
        if ~isempty(EEG.event) && EEG.trials == 1 && EEG.event(end).latency-0.5 > EEG.pnts
            EEG.event(end) = []; % Remove last event if necessary
            fprintf('Removed last event due to latency inconsistency.\n');
        end

        % Sort events by latency
        [~, sortIdx] = sort([EEG.event.latency]);
        EEG.event = EEG.event(sortIdx);
        fprintf('Events sorted by latency.\n');

        % Double check event latencies
        eeglab_options;
        warnflag = false;
        if isfield(EEG.event, 'latency') && length(EEG.event) < 3000
            alllats = [ EEG.event.latency ];
            if ~isempty(event2)
                otherlatencies = [event2.latency];
                if ~isequal(alllats, otherlatencies)
                    warning(['Discrepancy when checking event latencies using legacy method.' 10 ...
                             'Often the discrepancy is minor and the new method (used here) is correct' 10 ...
                             'Still, try to reproduce the problem and send us your dataset']);
                    warnflag = true;
                end
            end
        end

        % ---- Modification Start: Move current regions to moved_rejRegions ----
        if isfield(EEG.etc, 'moved_rejRegions')
            EEG.etc.moved_rejRegions = [EEG.etc.moved_rejRegions; regions];
            fprintf('Appended current rejection regions to moved_rejRegions.\n');
        else
            EEG.etc.moved_rejRegions = regions;
            fprintf('Created moved_rejRegions and moved current rejection regions.\n');
        end
        % Clear rejRegions
        EEG.etc.rejRegions = [];
        fprintf('Cleared EEG.etc.rejRegions after moving to moved_rejRegions.\n');
        % ---- Modification End ----
    end

    com = sprintf('EEG = reject(EEG, %s);', vararg2str({ regions }));
    fprintf('Rejection command recorded: %s\n', com);

end  % End of main reject function

% Combine regions if necessary
function newregions = combineregions(regions)
    % 9/1/2014 RMC
    regions = sortrows(sort(regions,2)); % Sorting regions
    allreg = [ regions(:,1)' regions(:,2)'; ones(1,numel(regions(:,1))) -ones(1,numel(regions(:,2))) ].';
    allreg = sortrows(allreg,1); % Sort all start and stop points (column 1),

    mboundary = cumsum(allreg(:,2)); % Rationale: regions will start always with 1 and close with 0, since starts=1 end=-1
    indx = 0; count = 1;

    while indx ~= length(allreg) 
        newregions(count,1) = allreg(indx+1,1);
        [tmp,I] = min(abs(mboundary(indx+1:end)));
        newregions(count,2) = allreg(I + indx,1);
        indx = indx + I;
        count = count + 1;
    end

    % Verbose
    if size(regions,1) ~= size(newregions,1)
        disp('Warning: overlapping regions detected and fixed in reject');
    end
end  % End of combineregions function

function res = issameevent(evt1, evt2)

    res = true;
    if isequal(evt1,evt2)
        return;
    else
        if isfield(evt1, 'type') && isnumeric(evt2.type) && ~isnumeric(evt1.type) 
            evt2.type = num2str(evt2.type);
            if isequal(evt1,evt2)
                return;
            end
        end
        if isfield(evt1, 'duration') && isfield(evt2, 'duration')
            if isnan(evt1.duration) && isnan(evt2.duration)
                evt1.duration = 1;
                evt2.duration = 1;
            end
            if abs(evt1.duration - evt2.duration) < 1e-10
                evt1.duration = 1;
                evt2.duration = 1;
            end
            if isequal(evt1,evt2)
                return;
            end
        end
        if isfield(evt1, 'latency') && isfield(evt2, 'latency')
            if abs(evt1.latency - evt2.latency) < 1e-10
                evt1.latency = 1;
                evt2.latency = 1;
            end
            if isequal(evt1,evt2)
                return;
            end
        end
    end
    res = false;
    return;
end  % End of issameevent function


% remove_spec_stage.m
% Removes unwanted sleep stages based on sequential logic and logs total time removed.

function EEG = remove_spec_stage(EEG, unwanted_stages, fid)
    % REMOVE_SPEC_STAGE Removes unwanted sleep stages based on sequential logic and logs total time removed.
    %
    % Parameters:
    %   EEG              - EEGLAB EEG structure
    %   unwanted_stages  - Array of sleep stage codes to remove (e.g., [0, 1, 4, 5])
    %   fid              - File identifier for logging
    %
    % Returns:
    %   EEG - Updated EEGLAB EEG structure with specified sleep stages removed

    % Validate Inputs
    if nargin < 3
        error('All three inputs (EEG, unwanted_stages, fid) must be provided.');
    end

    % Define valid sleep stage codes
    valid_stage_codes = 0:5;

    % Validate unwanted_stages are within valid_stage_codes
    if any(~ismember(unwanted_stages, valid_stage_codes))
        warning('Some unwanted_stages are not within the valid sleep stage codes [0, 1, 2, 3, 4, 5]. They will be ignored.');
        unwanted_stages = unwanted_stages(ismember(unwanted_stages, valid_stage_codes));
    end

    if isempty(unwanted_stages)
        fprintf('No valid unwanted_stages to remove. Exiting function.\n');
        fprintf(fid, 'No valid unwanted_stages to remove. Exiting function.\n');
        return;
    end

    % Initialize rejection indices and time tracking
    rej_inds = [];
    time_removed = zeros(size(unwanted_stages)); % Tracks total time removed for each stage

    % Sort events based on their latencies in ascending order
    [sorted_latencies, sort_idx] = sort([EEG.event.latency]);
    EEG.event = EEG.event(sort_idx);

    % Check for duplicate latencies
    unique_latencies = unique(sorted_latencies);
    if length(unique_latencies) < length(sorted_latencies)
        warning('There are events with duplicate latencies. Please verify event timings.');
        fprintf(fid, 'Warning: There are events with duplicate latencies. Please verify event timings.\n');
    end

    % Iterate through events to find and mark unwanted stages
    for iEv = 1:length(EEG.event) - 1
        event = EEG.event(iEv);

        % Process only 'Sleep Stage' events
        if strcmp(event.type, 'Sleep Stage')
            current_stage = str2double(event.code);

            % Ignore 'Sleep Stage' events with invalid codes
            if ~ismember(current_stage, valid_stage_codes)
                fprintf('Ignoring Sleep Stage event %d with invalid code %d.\n', iEv, current_stage);
                fprintf(fid, 'Ignoring Sleep Stage event %d with invalid code %d.\n', iEv, current_stage);
                continue; % Skip to next event
            end

            % Process only unwanted sleep stages
            if ismember(current_stage, unwanted_stages)
                % Define the rejection interval from this stage to the next
                t_start = round(event.latency);
                next_event = EEG.event(iEv + 1);
                t_end = round(next_event.latency - 1);

                % Ensure indices are within bounds
                t_start = max(t_start, 1);
                t_end = min(t_end, EEG.pnts);

                % Validate that t_end >= t_start
                if t_end < t_start
                    warning('Event %d: t_end (%d) < t_start (%d). Adjusting t_end to t_start.', ...
                            iEv, t_end, t_start);
                    fprintf('Warning: Event %d: t_end (%d) < t_start (%d). Adjusting t_end to t_start.\n', ...
                            iEv, t_end, t_start);
                    fprintf(fid, 'Warning: Event %d: t_end (%d) < t_start (%d). Adjusting t_end to t_start.\n', ...
                            iEv, t_end, t_start);
                    t_end = t_start; % Adjust t_end to ensure valid indexing
                end

                % Append to rejection indices
                rej_inds = [rej_inds; t_start, t_end];

                % Update time removed
                stage_idx = find(unwanted_stages == current_stage, 1);
                if ~isempty(stage_idx)
                    time_removed(stage_idx) = time_removed(stage_idx) + (t_end - t_start + 1) / EEG.srate;
                end

                % Log the removed segment
                fprintf('Event %d: Removing sleep stage %d from %d to %d (%.2f to %.2f seconds).\n', ...
                    iEv, current_stage, t_start, t_end, t_start / EEG.srate, t_end / EEG.srate);
                fprintf(fid, 'Event %d: Removing sleep stage %d from %d to %d (%.2f to %.2f seconds).\n', ...
                    iEv, current_stage, t_start, t_end, t_start / EEG.srate, t_end / EEG.srate);
            end
        end
    end

    % Check if there are any segments to reject
    if isempty(rej_inds)
        fprintf('No unwanted sleep stages found. No data removed.\n');
        fprintf(fid, 'No unwanted sleep stages found. No data removed.\n');
    else
        % Validate rej_inds before passing to reject
        valid_rej_inds = [];
        for i = 1:size(rej_inds, 1)
            start_idx = rej_inds(i, 1);
            end_idx = rej_inds(i, 2);
            if start_idx <= end_idx && start_idx >=1 && end_idx <= EEG.pnts
                valid_rej_inds = [valid_rej_inds; start_idx, end_idx];
            else
                warning('Invalid rejection indices [%d, %d]. Skipping this region.', start_idx, end_idx);
                fprintf('Warning: Invalid rejection indices [%d, %d]. Skipping this region.\n', start_idx, end_idx);
                fprintf(fid, 'Warning: Invalid rejection indices [%d, %d]. Skipping this region.\n', start_idx, end_idx);
            end
        end

        if isempty(valid_rej_inds)
            fprintf('No valid segments to remove after validation. No data removed.\n');
            fprintf(fid, 'No valid segments to remove after validation. No data removed.\n');
        else
            % Use eeg_eegrej to remove the unwanted segments
            fprintf('Removing %d segments using eeg_eegrej...\n', size(valid_rej_inds, 1));
            fprintf(fid, 'Removing %d segments using eeg_eegrej...\n', size(valid_rej_inds, 1));
            EEG = reject(EEG, valid_rej_inds);

            % Debugging output after removal
            fprintf('Segments successfully removed. Remaining data points: %d.\n', EEG.pnts);
            fprintf(fid, 'Segments successfully removed. Remaining data points: %d.\n', EEG.pnts);
        end
    end

    % Log total time removed for each stage
    log_time_removed(fid, unwanted_stages, time_removed);
end

%% Helper Function: Log total time removed
function log_time_removed(fid, unwanted_stages, time_removed)
    fprintf(fid, 'Total time removed for each stage:\n');
    for i = 1:length(unwanted_stages)
        fprintf(fid, '  Stage %d: %.2f seconds\n', unwanted_stages(i), time_removed(i));
    end
    fprintf(fid, '\n'); % Add spacing for clarity
end

function EEG = remove_stim_unwanted(EEG, unwanted_stages, fid)
    % REMOVE_STIM_UNWANTED Removes stimulation protocols (stim start/end with proto_type=4)
    % that immediately follow specified unwanted sleep stages and logs the removals.
    %
    % Parameters:
    %   EEG             - EEGLAB EEG structure with events and data
    %   unwanted_stages - Array of sleep stage codes to consider for removal
    %   fid             - File identifier for logging
    %
    % Returns:
    %   EEG - Updated EEGLAB EEG structure with specified stim protocols removed

    % Ensure that events are sorted by latency
    [~, sort_idx] = sort([EEG.event.latency]);
    EEG.event = EEG.event(sort_idx);

    % Identify protocols: pair 'stim start' and 'stim end'
    protocols = struct('start_idx', {}, 'end_idx', {}, 'protocol_num', {});
    protocol_num = 1;
    event_protocol_map = zeros(1, length(EEG.event)); % Map event index to protocol number

    i = 1;
    while i <= length(EEG.event)
        if strcmp(EEG.event(i).type, 'stim start') && ...
           isfield(EEG.event(i), 'proto_type') && EEG.event(i).proto_type == 5
            % Find the corresponding 'stim end'
            j = i + 1;
            while j <= length(EEG.event)
                if strcmp(EEG.event(j).type, 'stim end') && ...
                   isfield(EEG.event(j), 'proto_type') && EEG.event(j).proto_type == 5
                    % Found a protocol
                    protocols(end+1).start_idx = i;
                    protocols(end).end_idx = j;
                    protocols(end).protocol_num = protocol_num;
                    event_protocol_map(i) = protocol_num;
                    event_protocol_map(j) = protocol_num;
                    protocol_num = protocol_num + 1;
                    break;
                end
                j = j + 1;
            end
            if j > length(EEG.event)
                % 'stim start' without corresponding 'stim end'
                % Handle as needed, here we ignore incomplete protocol
                warning('Stim start at index %d has no corresponding stim end. Ignoring incomplete protocol.', i);
                break;
            end
            i = j + 1;
        else
            i = i + 1;
        end
    end

    total_protocols = protocol_num - 1;

    % Initialize list of protocol numbers to remove
    protocols_to_remove = [];

    % Iterate through events, up to the second last event
    for iEv = 1:length(EEG.event) - 1
        current_event = EEG.event(iEv);

        % Check if current_event is 'Sleep Stage'
        if strcmp(current_event.type, 'Sleep Stage')
            % Get the sleep stage code and convert to numeric
            sleep_stage_code_str = current_event.code;
            sleep_stage_code = str2double(sleep_stage_code_str);
            if isnan(sleep_stage_code)
                sleep_stage_code = -1; % Unknown or invalid
            end

            % Check if sleep stage is unwanted
            if ismember(sleep_stage_code, unwanted_stages)
                % Get the next event
                next_event = EEG.event(iEv + 1);

                % Check if next_event is 'stim start' or 'stim end' with proto_type=4
                if (strcmp(next_event.type, 'stim start') || strcmp(next_event.type, 'stim end')) && ...
                   isfield(next_event, 'proto_type') && next_event.proto_type == 5

                    % Find the protocol number
                    protocol_num = event_protocol_map(iEv + 1);
                    if protocol_num > 0 && ~ismember(protocol_num, protocols_to_remove)
                        % Mark the protocol for removal
                        protocols_to_remove = [protocols_to_remove, protocol_num];

                        % Get protocol events
                        protocol = protocols(protocol_num);

                        % Determine stim action based on which event was found
                        if strcmp(next_event.type, 'stim start')
                            stim_action = 'Stim Start';
                        else
                            stim_action = 'Stim End';
                        end

                        % Log the removal with detailed information
                        fprintf(fid, 'Removing Protocol %d (%s of type %d at latency %.2f seconds (sample %d) and its counterpart) during sleep stage %d.\n', ...
                            protocol_num, stim_action, next_event.proto_type, next_event.latency / EEG.srate, round(next_event.latency), sleep_stage_code);
                        fprintf('Removing Protocol %d (%s of type %d at latency %.2f seconds (sample %d) and its counterpart) during sleep stage %d.\n', ...
                            protocol_num, stim_action, next_event.proto_type, next_event.latency / EEG.srate, round(next_event.latency), sleep_stage_code);
                    end
                end
            end
        end
    end

    % Remove the identified protocols
    if ~isempty(protocols_to_remove)
        events_to_remove = [];
        for p = protocols_to_remove
            events_to_remove = [events_to_remove, protocols(p).start_idx, protocols(p).end_idx];
        end
        EEG.event(events_to_remove) = [];
        fprintf(fid, 'Total protocols removed: %d\n', length(protocols_to_remove));
        fprintf('Total protocols removed: %d\n', length(protocols_to_remove));
    else
        fprintf(fid, 'No stimulation protocols found following specified unwanted sleep stages.\n');
        fprintf('No stimulation protocols found following specified unwanted sleep stages.\n');
    end

    % Log the remaining protocols
    remaining_protocols = total_protocols - length(protocols_to_remove);
    fprintf(fid, 'Total protocols remaining: %d\n', remaining_protocols);
    fprintf('Total protocols remaining: %d\n', remaining_protocols);
end

% repos_events.m
% Adjusts the positions of specific events that fall within NaN segments based on proto_type.

function EEG = repos_events(EEG, NaNSegments, original_actualTimes, log_file, desired_proto_type)
    % REPOS_EVENTS Adjusts the positions of specific events that fall within NaN segments.
    %
    % Syntax: EEG = repos_events(EEG, NaNSegments, original_actualTimes, log_file, desired_proto_type)
    %
    % Inputs:
    %   EEG                 - EEGLAB EEG structure
    %   NaNSegments         - Nx2 matrix of NaN segments [start, end] in samples
    %   original_actualTimes- Original actualTimes array from unprocessed EEG data
    %   log_file            - File identifier for logging
    %   desired_proto_type  - Numeric value (e.g., 3 or 4) specifying the proto_type to process
    %
    % Outputs:
    %   EEG - Updated EEGLAB EEG structure with adjusted event latencies

    % Validate desired_proto_type
    if nargin < 5 || isempty(desired_proto_type)
        error('Desired proto_type must be specified as the fifth input argument.');
    end

    % Event types to adjust
    desired_event_types = {'stim start', 'stim end'};

    % Initialize counters for summary
    total_moved_events = 0;
    stim_start_remained = 0;
    stim_end_remained = 0;

    % Print initial message
    fprintf('Repositioning Stim Events if during NaN...\n');

    % Iterate through each event
    for iEv = 1:length(EEG.event)
        event = EEG.event(iEv);
        event_sample = round(event.latency);

        % Check if event type matches desired types and proto_type matches
        if ismember(event.type, desired_event_types) && ...
           isfield(event, 'proto_type') && event.proto_type == desired_proto_type
            
            % Check if the event is within a NaN segment
            [in_nan, nan_region_end] = is_within_nan_segment(event_sample, NaNSegments);

            if in_nan
                % Define a buffer (e.g., 2 samples) to move the event outside the NaN segment
                buffer_samples = 2;
                new_latency = nan_region_end + buffer_samples;

                % Ensure the new latency does not exceed the data length
                if new_latency > size(EEG.data, 2)
                    warning('Event "%s" at latency %d cannot be repositioned beyond data length. Skipping.', ...
                            event.type, event_sample);
                    fprintf('Warning: Event "%s" at latency %d cannot be repositioned beyond data length.\n', ...
                            event.type, event_sample);
                    continue; % Skip to the next event
                end

                % Calculate and log shift details
                shift_distance = new_latency - event.latency;
                shift_distance_sec = shift_distance / EEG.srate;
                fprintf('Moved Event: Type=%s, Proto_Type=%d, Original Latency=%d, New Latency=%d, Shift=%.2f seconds\n', ...
                        event.type, event.proto_type, event_sample, new_latency, shift_distance_sec);

                % Write to the log file
                fprintf(log_file, 'Moved Event: Type=%s, Proto_Type=%d, Original Latency=%d, New Latency=%d, Shift=%.2f seconds\n', ...
                        event.type, event.proto_type, event_sample, new_latency, shift_distance_sec);

                % Update event details
                EEG.event(iEv).latency = new_latency;
                EEG.event(iEv).moved = true;
                EEG.event(iEv).shift_distance_sec = shift_distance_sec;

                % Increment moved events counter
                total_moved_events = total_moved_events + 1;
            else
                EEG.event(iEv).moved = false;
                EEG.event(iEv).shift_distance_sec = 0;
                fprintf('Unmoved Event: Type=%s, Proto_Type=%d, Latency=%d\n', ...
                        event.type, event.proto_type, event_sample);
                fprintf(log_file, 'Unmoved Event: Type=%s, Proto_Type=%d, Latency=%d\n', ...
                        event.type, event.proto_type, event_sample);
                
                % Increment remained counters based on event type
                if strcmp(event.type, 'stim start')
                    stim_start_remained = stim_start_remained + 1;
                elseif strcmp(event.type, 'stim end')
                    stim_end_remained = stim_end_remained + 1;
                end
            end
        else
            % Do not log skipped events
            fprintf('Skipping Event: Type=%s, Proto_Type=%d, Latency=%d\n', ...
                    event.type, event.proto_type, event.latency);
            % No logging for skipped events
        end
    end

    % Prepare and display summary
    fprintf('\nSummary:\n');
    fprintf('Total stim events of proto %d moved: %d\n', desired_proto_type, total_moved_events);
    fprintf('Total stim start of proto %d remained: %d\n', desired_proto_type, stim_start_remained);
    fprintf('Total stim end of proto %d remained: %d\n', desired_proto_type, stim_end_remained);

    % Write summary to log file
    fprintf(log_file, '\nSummary:\n');
    fprintf(log_file, 'Total stim events of proto %d moved: %d\n', desired_proto_type, total_moved_events);
    fprintf(log_file, 'Total stim start of proto %d remained: %d\n', desired_proto_type, stim_start_remained);
    fprintf(log_file, 'Total stim end of proto %d remained: %d\n', desired_proto_type, stim_end_remained);
end

% Helper Function: Check if latency is within any NaN segment
function [is_nan, nan_region_end] = is_within_nan_segment(latency, NaNSegments)
    % Determines if the given latency falls within any of the NaN segments.
    %
    % Inputs:
    %   latency      - Event latency in samples
    %   NaNSegments  - Nx2 matrix of NaN segments [start, end] in samples
    %
    % Outputs:
    %   is_nan        - Boolean indicating if latency is within a NaN segment
    %   nan_region_end - End sample of the NaN segment containing the latency

    idx = find(latency >= NaNSegments(:, 1) & latency <= NaNSegments(:, 2), 1);
    if ~isempty(idx)
        is_nan = true;
        nan_region_end = NaNSegments(idx, 2);
    else
        is_nan = false;
        nan_region_end = [];
    end
end

% timing_figs_with_nan.m
% Creates a figure with sleep stages, stim events, and highlights NaN segments in EEG data.

function timing_figs_with_nan(EEG, whichSubj, whichSess, fid, NaNSegments)
    % timing_figs_with_nan - Generates a hypnogram with stim events and highlights NaN segments.
    %
    % Syntax: timing_figs_with_nan(EEG, whichSubj, whichSess, fid, NaNSegments)
    %
    % Inputs:
    %   EEG         - EEG structure containing data, events, sampling rate, and filepath.
    %   whichSubj   - Subject identifier (string).
    %   whichSess   - Session identifier (string).
    %   fid         - File identifier for logging (opened with fopen).
    %   NaNSegments - (Optional) Nx2 matrix where each row represents [startIdx, endIdx] of NaN segments.
    %
    % Outputs:
    %   None (figure is saved to disk).

    % If NaNSegments is not provided, identify them
    if nargin < 5 || isempty(NaNSegments)
        [NaNSegments, ~, ~, ~] = identify_nan_segs(EEG, fid);
    end

    % Create savepath for figures
    savepath = fullfile(EEG.filepath, 'analysis', 'sleep');
    if ~exist(savepath, 'dir')
        mkdir(savepath);
    end

    % Extract sleep stage events
    [all_ss, ss_latencies] = extract_sleep_stages(EEG);

    % Extract stim start and stim end events with proto_type = 4
    [stim_start_times, stim_end_times] = extract_stim_events(EEG);

    % Create figure
    fig = figure;
    set(fig, 'Position', [100 100 1200 600], 'Visible', 'off');
    hold on;

    % Plot NaN segments as shaded purple regions
    if ~isempty(NaNSegments)
        for i = 1:size(NaNSegments, 1)
            % Convert sample indices to time in hours
            start_time_hr = NaNSegments(i, 1) / EEG.srate / 3600;
            end_time_hr = NaNSegments(i, 2) / EEG.srate / 3600;

            % Define y-limits for the shaded area
            y_lower = -5;
            y_upper = 2;

            % Create a patch (shaded area) for the NaN segment
            patch_handle = patch([start_time_hr end_time_hr end_time_hr start_time_hr], ...
                                 [y_lower y_lower y_upper y_upper], ...
                                 [0.5 0 0.5], ... % RGB for purple
                                 'FaceAlpha', 0.3, ... % Transparency
                                 'EdgeColor', 'none', ...
                                 'HandleVisibility', 'off'); % Hide from legend
        end
        % Create a single legend entry for NaN Segments
        nan_patch = patch([0 0 0 0], [0 0 0 0], [0.5 0 0.5], ...
                          'FaceAlpha', 0.3, 'EdgeColor', 'none', ...
                          'DisplayName', 'NaN Segment');
    end

    % Plot sleep stages
    plot_handle_ss = plot(ss_latencies / 3600, -all_ss, 'k', 'LineWidth', 1.5, 'DisplayName', 'Sleep Stage');

    % Plot stim start events as green stars
    if ~isempty(stim_start_times)
        plot_handle_stim_start = plot(stim_start_times / 3600, zeros(size(stim_start_times)), ...
                                      'g*', 'MarkerSize', 8, 'DisplayName', 'Stim Start');
    end

    % Plot stim end events as red stars
    if ~isempty(stim_end_times)
        plot_handle_stim_end = plot(stim_end_times / 3600, zeros(size(stim_end_times)), ...
                                    'r*', 'MarkerSize', 8, 'DisplayName', 'Stim End');
    end

    % Configure plot aesthetics
    ylim([-5 2]);
    yticks([-5:1:2]);
    yticklabels({'', 'REM', 'NREM3', 'NREM2', 'NREM1', 'WAKE', ''});
    xlabel('Time (hours)', 'FontSize', 12);
    ylabel('Sleep Stage', 'FontSize', 12);
    title(sprintf('Subject %s Session %s Struct  %s', whichSubj, whichSess, inputname(1)), 'FontSize', 16);
    grid on;

    % Determine x-axis limits based on sleep stage latencies and NaN segments
    if ~isempty(NaNSegments)
        % Convert end indices of NaN segments to time in seconds
        nan_end_times_sec = NaNSegments(:,2) / EEG.srate;
        % Maximum time from sleep stages and NaN segments
        max_time_sec = max([max(ss_latencies), max(nan_end_times_sec)]);
    else
        max_time_sec = max(ss_latencies);
    end
    max_time_hr = ceil(max_time_sec / 3600);
    xlim([0 max_time_hr]);

    % Create a single legend
    if ~isempty(NaNSegments)
        legend_entries = [plot_handle_ss];
        legend_labels = {'Sleep Stage'};
        if ~isempty(stim_start_times)
            legend_entries(end+1) = plot_handle_stim_start;
            legend_labels{end+1} = 'Stim Start';
        end
        if ~isempty(stim_end_times)
            legend_entries(end+1) = plot_handle_stim_end;
            legend_labels{end+1} = 'Stim End';
        end
        legend_entries(end+1) = nan_patch;
        legend_labels{end+1} = 'NaN Segment';
        legend(legend_entries, legend_labels, 'Location', 'best');
    else
        if ~isempty(stim_start_times) && ~isempty(stim_end_times)
            legend({'Sleep Stage', 'Stim Start', 'Stim End'}, 'Location', 'best');
        elseif ~isempty(stim_start_times)
            legend({'Sleep Stage', 'Stim Start'}, 'Location', 'best');
        elseif ~isempty(stim_end_times)
            legend({'Sleep Stage', 'Stim End'}, 'Location', 'best');
        else
            legend({'Sleep Stage'}, 'Location', 'best');
        end
    end

    % Include EEG structure name in the saved figure name with '_with_NaNs'
    eeg_struct_name = inputname(1); % Gets the variable name of EEG structure
    savestr = sprintf('Stim_Events_%s_%s_%s_with_NaNs.png', whichSubj, whichSess, eeg_struct_name);
    fprintf('Saving figure as %s\n', fullfile(savepath, savestr));
    saveas(fig, fullfile(savepath, savestr));

    % Close the figure
    close(fig);
end

% Helper Function: extract_sleep_stages.m
% Extracts sleep stage codes and their latencies from EEG.events.

function [all_ss, ss_latencies] = extract_sleep_stages(EEG)
    all_ss = []; 
    ss_latencies = []; 
    for iEv = 1:length(EEG.event)
        if strcmp(EEG.event(iEv).type, 'Sleep Stage')
            sleep_stage_code = str2double(EEG.event(iEv).code);
            all_ss = [all_ss sleep_stage_code];
            ss_latencies = [ss_latencies (EEG.event(iEv).latency / EEG.srate)];
        end
    end
end

% Helper Function: extract_stim_events.m
% Extracts stim start and stim end times with proto_type = 4 from EEG.events.

function [stim_start_times, stim_end_times] = extract_stim_events(EEG)
    stim_start_times = [];
    stim_end_times = [];
    for iEv = 1:length(EEG.event)
        if (strcmp(EEG.event(iEv).type, 'stim start') || strcmp(EEG.event(iEv).type, 'stim end')) && ...
           isfield(EEG.event(iEv), 'proto_type') && EEG.event(iEv).proto_type == 5
            if strcmp(EEG.event(iEv).type, 'stim start')
                stim_start_times = [stim_start_times (EEG.event(iEv).latency / EEG.srate)];
            elseif strcmp(EEG.event(iEv).type, 'stim end')
                stim_end_times = [stim_end_times (EEG.event(iEv).latency / EEG.srate)];
            end
        end
    end
end

% Helper Function: identify_nan_segs.m
% Identifies segments in EEG.data that contain NaNs and logs the process.

function [NaNSegments, nanIndices, totalTimeSeconds, totalTimeMinutes] = identify_nan_segs(EEG, fid)
    % Logical array where any channel is NaN
    nanData = any(isnan(EEG.data), 1);

    % Find start and end indices of NaN segments
    d = diff([0 nanData 0]);
    startIdx = find(d == 1);
    endIdx = find(d == -1) - 1;

    NaNSegments = [startIdx; endIdx]';
    nanIndices = nanData;

    totalTimeSeconds = 0; % Initialize total time in seconds

    if isempty(NaNSegments)
        log_message(fid, 'No NaN segments identified.');
        fprintf('No NaN segments identified.\n'); % Print to console
    else
        for i = 1:size(NaNSegments, 1)
            % Calculate the length of the NaN segment in seconds
            segmentLength = (NaNSegments(i, 2) - NaNSegments(i, 1)) / EEG.srate;

            % Accumulate total time
            totalTimeSeconds = totalTimeSeconds + segmentLength;

            % Prepare the detailed message
            detailedMessage = sprintf('Identified NaN segment #%d from sample %d to %d, with length (%.2f seconds).', ...
                i, NaNSegments(i, 1), NaNSegments(i, 2), segmentLength);

            % Log the message to the file
            log_message(fid, '%s', detailedMessage);

            % Print the message to the console
            fprintf('%s\n', detailedMessage);
        end

        % Convert total time to minutes
        totalTimeMinutes = totalTimeSeconds / 60;

        % Prepare the summary message with total time
        summaryMessage = sprintf('Found %d NaN segments with a total length of %.2f seconds (%.2f minutes).', ...
            size(NaNSegments, 1), totalTimeSeconds, totalTimeMinutes);

        % Log the summary message to the file
        log_message(fid, '%s', summaryMessage);

        % Print the summary message to the console
        fprintf('%s\n', summaryMessage);
    end
end

% Helper Function: log_message.m
% Logs messages to a specified file.

function log_message(fid, varargin)
    if nargin < 2
        return; % Nothing to log
    end
    fprintf(fid, varargin{:});
    fprintf(fid, '\n'); % Add a newline character at the end
end

% make figure with information about stages and stim timings
function timings_figs(EEG, whichSubj, whichSess)

    % Create savepath for figures
    savepath = fullfile(EEG.filepath, 'analysis', 'sleep');
    if ~exist(savepath, 'dir')
        mkdir(savepath)
    end

    % Grab all sleep stage events
    all_ss = []; 
    ss_latencies = []; 
    ss_nan = [];
    for iEv = 1:length(EEG.event)
        if strcmp(EEG.event(iEv).type, 'Sleep Stage')
            sleep_stage_code = str2double(EEG.event(iEv).code);
            all_ss = [all_ss sleep_stage_code];
            ss_latencies = [ss_latencies (EEG.event(iEv).latency / EEG.srate)];
            
            if isnan(EEG.data(1, EEG.event(iEv).latency))
                ss_nan = [ss_nan 1];
            else
                ss_nan = [ss_nan 0];
            end
        end
    end

    % Grab all stim start and stim end events with proto_type = 4
    stim_start_times = [];
    stim_end_times = [];
    for iEv = 1:length(EEG.event)
        if (strcmp(EEG.event(iEv).type, 'stim start') || strcmp(EEG.event(iEv).type, 'stim end')) && ...
           isfield(EEG.event(iEv), 'proto_type') && EEG.event(iEv).proto_type == 5
            if strcmp(EEG.event(iEv).type, 'stim start')
                stim_start_times = [stim_start_times (EEG.event(iEv).latency / EEG.srate)];
            elseif strcmp(EEG.event(iEv).type, 'stim end')
                stim_end_times = [stim_end_times (EEG.event(iEv).latency / EEG.srate)];
            end
        end
    end

    % Create figure
    figure;
    set(gcf, 'Position', [100 100 1200 600], 'Visible', 'off');
    hold on;

    % Plot sleep stages
    plot(ss_latencies / 3600, -all_ss, 'k', 'LineWidth', 1.5);
    
    % Plot stim start events as green stars
    if ~isempty(stim_start_times)
        plot(stim_start_times / 3600, zeros(size(stim_start_times)), 'g*', 'MarkerSize', 8, 'DisplayName', 'Stim Start');
    end

    % Plot stim end events as red stars
    if ~isempty(stim_end_times)
        plot(stim_end_times / 3600, zeros(size(stim_end_times)), 'r*', 'MarkerSize', 8, 'DisplayName', 'Stim End');
    end

    % Configure plot aesthetics
    ylim([-5 2]);
    yticks([-5:1:2]);
    xlim([0 ceil(max(ss_latencies) / 3600)]);
    xlabel('Time (hours)');
    ylabel('Sleep Stage');
    yticklabels({'', 'REM', 'NREM3', 'NREM2', 'NREM1', 'WAKE', ''});
    title(sprintf('Subject %s Session %s Struct  %s', whichSubj, whichSess, inputname(1)), 'FontSize', 16);
    legend('Location', 'best');
    grid on;

    % Include EEG structure name in the saved figure name
    eeg_struct_name = inputname(1); % Gets the variable name of EEG structure
    savestr = sprintf('Stim_Events_%s_%s_%s.png', whichSubj, whichSess, eeg_struct_name);
    fprintf('Saving figure as %s\n', fullfile(savepath, savestr));
    saveas(gcf, fullfile(savepath, savestr));

    % Close the figure
    close;

end %function


these are all the scripts.

Now, needed changes:


1. i want the `desired_proto_type` variable to be implemenet in the rest of the scripts. some scripts have the number 4 or 5 hardcoded. Example, in the figures scripts, so i want to to be dynamic based on the desired_proto_type.

2. i want to have the logging be implemeneted in a more visdually appealing fashion. Maybe with ###### as spacers between sections or something along these lines.

3. In both figure types, i want the legned to be fixed to the upper right corner of the plot.

4. in both figure types, i want to see the protocol number next to each pair of stim start/end events.
