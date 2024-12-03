function generate_event_table(EEG, sample_rate, set_file_path)
    % GENERATE_EVENT_TABLE Generates and saves a table of critical EEG events.
    %
    % This function identifies events within the EEG structure that have
    % Proto_Type 4 or 5 and are of type 'stim start' or 'stim end'.
    % It then creates a table sorted by event latency and saves it as a CSV
    % file next to the provided .set file.
    %
    % Parameters:
    %   EEG           - EEGLAB EEG structure containing event information.
    %   sample_rate   - Sampling rate of the EEG data in Hz (e.g., 500).
    %   set_file_path - Full path to the EEG .set file.
    %
    % Example:
    %   generate_event_table(EEG, 500, '/path/to/file.set');

    % Validate Inputs
    if nargin ~= 3
        error('generate_event_table requires exactly three input arguments: EEG, sample_rate, set_file_path.');
    end

    % Extract Proto_Type and Type from EEG.event
    num_events = length(EEG.event);
    proto_types = NaN(1, num_events);     % Initialize with NaN for missing Proto_Type
    event_types = cell(1, num_events);    % Initialize with empty cells for missing Type

    for i = 1:num_events
        % Extract Proto_Type
        if isfield(EEG.event(i), 'proto_type') && ~isempty(EEG.event(i).proto_type)
            proto_types(i) = EEG.event(i).proto_type;
        else
            proto_types(i) = NaN; % Assign NaN if Proto_Type is missing
        end

        % Extract Type
        if isfield(EEG.event(i), 'type') && ~isempty(EEG.event(i).type)
            event_types{i} = EEG.event(i).type;
        else
            event_types{i} = '';   % Assign empty string if Type is missing
        end
    end

    % Logical Indices for Proto_Type 4 or 5
    is_proto_type_4_or_5 = (proto_types == 4) | (proto_types == 5);

    % Logical Indices for Event Types 'stim start' and 'stim end'
    is_stim_start_or_end = strcmp(event_types, 'stim start') | strcmp(event_types, 'stim end');

    % Combine Both Conditions
    desired_events_idx = is_proto_type_4_or_5 & is_stim_start_or_end;

    % Extract Desired Events
    desired_events = EEG.event(desired_events_idx);

    % Check if Any Events Match the Criteria
    if isempty(desired_events)
        fprintf('No events found with Proto_Type 4 or 5 and type "stim start" or "stim end".\n');
        return;
    end

    % Sort the Desired Events by Latency to Ensure Order of Appearance
    [sorted_latencies, sort_order] = sort([desired_events.latency]);
    sorted_events = desired_events(sort_order);

    % Extract Required Fields
    EventType = {sorted_events.type}';                 % Column cell array
    ProtoType = [sorted_events.proto_type]';           % Column vector
    Latency_Samples = sorted_latencies';               % Row vector
    Time_sec = Latency_Samples / sample_rate;          % Convert samples to seconds

    % Create a Table with the Extracted Information
    EventTable = table(EventType, ProtoType, Latency_Samples, Time_sec, ...
        'VariableNames', {'Event_Type', 'Proto_Type', 'Latency_Samples', 'Time_sec'});

    % Define the CSV File Name Based on the .set File Name
    [folder, base_name, ~] = fileparts(set_file_path);
    csv_file_name = fullfile(folder, [base_name '_critical_events.csv']);

    % Save the Table to a CSV File
    try
        writetable(EventTable, csv_file_name);
        fprintf('Critical events table saved to %s\n', csv_file_name);
    catch ME
        warning('Failed to save the critical events table: %s', E.message);
    end
end
