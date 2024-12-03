% Define the sample rate
sample_rate = 500; % in Hz

% Step 1: Extract all proto_type values
proto_types = [EEG.event.proto_type];

% Step 2: Extract all event types
event_types = {EEG.event.type};

% Step 3: Create logical indices for proto_type 4 or 5
is_proto_type_4_or_5 = (proto_types == 4) | (proto_types == 5);

% Step 4: Create logical indices for event types 'stim start' and 'stim end'
is_stim_start_or_end = strcmp(event_types, 'stim start') | strcmp(event_types, 'stim end');

% Step 5: Combine both conditions to find desired events
desired_events_idx = is_proto_type_4_or_5 & is_stim_start_or_end;

% Step 6: Extract the desired events
desired_events = EEG.event(desired_events_idx);

% Check if any events match the criteria
if isempty(desired_events)
    fprintf('No events found with proto_type 4 or 5 and type "stim start" or "stim end".\n');
else
    % Step 7: Sort the desired events by latency to ensure order of appearance
    [sorted_latencies, sort_order] = sort([desired_events.latency]);
    sorted_events = desired_events(sort_order);
    
    % Step 8: Extract required fields
    EventType = {sorted_events.type}'; % Column cell array
    Latency_Samples = sorted_latencies'; % Row vector
    Time_sec = Latency_Samples / sample_rate; % Convert samples to seconds
    
    % Step 9: Create a table with the extracted information
    EventTable = table(EventType, Latency_Samples, Time_sec, ...
        'VariableNames', {'Event_Type', 'Latency_Samples', 'Time_sec'});
    
    % Step 10: Display the table
    disp('--- Critical Events Table ---');
    disp(EventTable);
    
    % (Optional) Step 11: Save the table to a CSV file
    % Uncomment the following lines if you wish to save the table
    % output_file = 'critical_events_table.csv';
    % writetable(EventTable, output_file);
    % fprintf('Table saved to %s\n', output_file);
end
