function stim_report = generate_stim_report(EEG, original_actualTimes)
    % GENERATE_STIM_REPORT Generates a stim report for 'stim start' and 'stim end' events.
    % Parameters:
    %   EEG - EEGLAB EEG structure containing event information.
    %   original_actualTimes - Original actualTimes array from the unprocessed EEG data.
    %
    % Returns:
    %   stim_report - Table with event details.

    % Define the event types to include
    desired_event_types = {'stim start', 'stim end'};

    % Initialize lists to store event information
    event_types = {};
    proto_types = [];
    original_latencies = [];
    actual_times = {};
    shift_distances = [];
    moved_flags = [];
    sleep_stages = [];

    % Loop through EEG events
    for i = 1:length(EEG.event)
        event = EEG.event(i);

        % Check if the event type is desired
        if ismember(event.type, desired_event_types)
            % Store event details
            event_types{end+1, 1} = event.type;
            proto_types(end+1, 1) = event.proto_type;
            original_latencies(end+1, 1) = event.latency;

            % Calculate original actual time
            event_sample = round(event.latency);
            if event_sample <= length(original_actualTimes)
                actual_times{end+1, 1} = datestr(original_actualTimes(event_sample), 'HH:MM:SS');
            else
                actual_times{end+1, 1} = 'N/A';
            end

            % Calculate shift distance and moved flag
            if isfield(event, 'shift_distance_sec')
                shift_distances(end+1, 1) = event.shift_distance_sec;
            else
                shift_distances(end+1, 1) = 0;
            end
            if isfield(event, 'moved')
                moved_flags(end+1, 1) = event.moved;
            else
                moved_flags(end+1, 1) = false;
            end

            % Find the sleep stage at the time of the event
            if isfield(EEG, 'srate') && isfield(EEG.etc, 'sleep_stages')
                sleep_stage_latencies = EEG.etc.sleep_stages.latencies;
                sleep_stage_codes = EEG.etc.sleep_stages.codes;

                % Get sleep stage for the event
                idx = find(sleep_stage_latencies <= event.latency, 1, 'last');
                if ~isempty(idx)
                    sleep_stages(end+1, 1) = sleep_stage_codes(idx);
                else
                    sleep_stages(end+1, 1) = NaN; % No sleep stage info available
                end
            else
                sleep_stages(end+1, 1) = NaN; % No sleep stage info available
            end
        end
    end

    % Create a table with event details
    stim_report = table(event_types, proto_types, original_latencies, actual_times, shift_distances, moved_flags, sleep_stages, ...
        'VariableNames', {'Event_Type', 'Proto_Type', 'Original_Latency', 'Original_Actual_Time', 'Shift_Distance_sec', 'Moved', 'Sleep_Stage'});
end
