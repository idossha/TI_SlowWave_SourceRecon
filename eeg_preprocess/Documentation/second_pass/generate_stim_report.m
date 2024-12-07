% File: generate_stim_report.m

function generate_stim_report(EEG, sample_rate, set_file_path, original_actualTimes)
    % GENERATE_STIM_REPORT Generates a stim report for 'stim start' and 'stim end' events.
    %
    % Parameters:
    %   EEG                 - EEGLAB EEG structure containing event information.
    %   sample_rate         - Sampling rate of the EEG data in Hz (e.g., 500).
    %   set_file_path       - Full path to the EEG .set file.
    %   original_actualTimes - Original actualTimes array from the unprocessed EEG data.

    % Define the event types to include
    desired_event_types = {'stim start', 'stim end'};

    % Initialize lists to store event information
    event_types = {};
    proto_types = [];
    times_sec = [];
    shifted_times_sec = [];
    actual_times = {};
    shift_distances = [];
    moved_flags = [];
    sleep_stages = [];

    % Gather sleep stage information
    sleep_stage_latencies = [EEG.event.latency];
    sleep_stage_codes = [EEG.event.sleep_stage];

    % Process events
    for i = 1:length(EEG.event)
        event = EEG.event(i);

        if ismember(event.type, desired_event_types)
            % Get original latency and calculate Time_sec
            if isfield(event, 'original_latency')
                original_latency = event.original_latency;
            else
                original_latency = event.latency; % Fallback to current latency if not available
            end
            time_sec = original_latency / sample_rate;

            % Store event information
            event_types{end+1, 1} = event.type;
            proto_types(end+1, 1) = event.proto_type;
            times_sec(end+1, 1) = round(time_sec, 3);

            % Calculate shifted_time_sec
            shifted_time_sec = event.latency / sample_rate;
            shifted_times_sec(end+1, 1) = round(shifted_time_sec, 3);

            % Get actual time
            event_sample = round(original_latency);
            if length(original_actualTimes) >= event_sample
                actual_times{end+1, 1} = datestr(original_actualTimes(event_sample), 'HH:MM:SS');
            else
                actual_times{end+1, 1} = 'N/A';
            end

            % Shift distance
            if isfield(event, 'shift_distance_sec')
                shift_distances(end+1, 1) = event.shift_distance_sec;
            else
                shift_distances(end+1, 1) = 0;
            end

            % Moved flag
            if isfield(event, 'moved')
                moved_flags(end+1, 1) = event.moved;
            else
                moved_flags(end+1, 1) = false;
            end

            % Find sleep stage at the time of the event
            idx = find(sleep_stage_latencies <= event.latency);
            if ~isempty(idx)
                sleep_stage = sleep_stage_codes(idx(end));
            else
                sleep_stage = NaN;
            end
            sleep_stages(end+1, 1) = sleep_stage;
        end
    end

    % Sort events by times_sec (original times)
    [times_sec, sortIdx] = sort(times_sec);
    event_types = event_types(sortIdx);
    proto_types = proto_types(sortIdx);
    shifted_times_sec = shifted_times_sec(sortIdx);
    actual_times = actual_times(sortIdx);
    shift_distances = shift_distances(sortIdx);
    moved_flags = moved_flags(sortIdx);
    sleep_stages = sleep_stages(sortIdx);

    % Create a table with the event information
    stim_table = table(event_types, proto_types, times_sec, shifted_times_sec, actual_times, shift_distances, moved_flags, sleep_stages, ...
        'VariableNames', {'Event_Type', 'Proto_Type', 'Time_sec', 'Shifted_Time_sec', 'Actual_Time', 'Shift_Distance_sec', 'Moved', 'Sleep_Stage'});

    % Define the report file name based on the .set file name
    [folder, base_name, ~] = fileparts(set_file_path);

    % Output as CSV
    stim_report_filename_csv = fullfile(folder, [base_name '_stim_report.csv']);
    writetable(stim_table, stim_report_filename_csv);
    fprintf('Stim report saved to %s\n', stim_report_filename_csv);

    % Output as JSON
    stim_report_filename_json = fullfile(folder, [base_name '_stim_report.json']);
    stim_struct = table2struct(stim_table);
    json_text = jsonencode(stim_struct);
    fid = fopen(stim_report_filename_json, 'w');
    fprintf(fid, '%s', json_text);
    fclose(fid);
    fprintf('Stim report saved to %s\n', stim_report_filename_json);
end
