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
