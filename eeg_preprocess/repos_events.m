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
