
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

    % Loop through each event
    for iEv = 1:length(EEG.event)
        event = EEG.event(iEv);

        if ismember(event.type, desired_event_types)
            % Include only events present in EEG.event (i.e., events remaining after processing)

            % Get original latency and calculate Time_sec
            if isfield(event, 'original_latency')
                original_latency = event.original_latency;
            else
                original_latency = event.latency; % In case original_latency is not available
            end
            time_sec = original_latency / sample_rate;

            % Store event information
            event_types{end+1, 1} = event.type;
            proto_types(end+1, 1) = event.proto_type;
            times_sec(end+1, 1) = round(time_sec, 3);

            % Calculate shifted_time_sec based on updated latency
            shifted_time_sec = event.latency / sample_rate;
            shifted_times_sec(end+1, 1) = round(shifted_time_sec, 3);

            % Get original actual time using original_actualTimes and original_latency
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

    % Create a table with the event information
    stim_table = table(event_types, proto_types, times_sec, shifted_times_sec, actual_times, shift_distances, moved_flags, ...
        'VariableNames', {'Event_Type', 'Proto_Type', 'Time_sec', 'Shifted_Time_sec', 'Actual_Time', 'Shift_Distance_sec', 'Moved'});

    % Define the report file name based on the .set file name
    [folder, base_name, ~] = fileparts(set_file_path);
    stim_report_filename = fullfile(folder, [base_name '_stim_report.txt']);

    % Write the table to a text file with formatting
    fid = fopen(stim_report_filename, 'w');
    fprintf(fid, 'Stim Report for %s\n', base_name);
    fprintf(fid, '================================================================================\n\n');
    fprintf(fid, 'Event_Type\tProto_Type\tTime_sec\tShifted_Time_sec\tActual_Time\tShift_Distance_sec\tMoved\n');
    fprintf(fid, '--------------------------------------------------------------------------------\n');
    for i = 1:height(stim_table)
        fprintf(fid, '%s\t\t%d\t\t%.3f\t\t%.3f\t\t%s\t\t%.3f\t\t%s\n', ...
            stim_table.Event_Type{i}, ...
            stim_table.Proto_Type(i), ...
            stim_table.Time_sec(i), ...
            stim_table.Shifted_Time_sec(i), ...
            stim_table.Actual_Time{i}, ...
            stim_table.Shift_Distance_sec(i), ...
            logical_to_string(stim_table.Moved(i)));
    end
    fclose(fid);

    fprintf('Stim report saved to %s\n', stim_report_filename);
end

% Helper Function to convert logical to 'true' or 'false' string
function str = logical_to_string(val)
    if val
        str = 'true';
    else
        str = 'false';
    end
end

