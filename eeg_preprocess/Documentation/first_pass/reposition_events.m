function reposition_events(EEG, output_path)
    % Initialize variables to store event changes
    event_label = {};
    proto_type = [];
    original_latency = [];
    new_latency = [];
    shift_distance = [];

    % Loop through each event to check if it falls within NaN segments
    for iEv = 1:length(EEG.event)
        event = EEG.event(iEv);
        % If the event falls in a NaN segment, reposition it
        if is_within_nan_segment(event.latency, EEG)
            % Find the first valid index after the NaN segment
            new_index = find_next_valid_index(event.latency, EEG);
            
            % Store event change information
            event_label{end+1, 1} = event.type;
            proto_type(end+1, 1) = event.proto_type;
            original_latency(end+1, 1) = event.latency / EEG.srate;
            new_latency(end+1, 1) = new_index / EEG.srate;
            shift_distance(end+1, 1) = (new_index - event.latency) / EEG.srate;

            % Update event latency
            EEG.event(iEv).latency = new_index;
        end
    end

    % Remove NaNs from EEG data
    EEG = eeg_eegrej(EEG, EEG.etc.rejRegions);

    % Create a table with event information and save it as a .txt file
    event_table = table(event_label, proto_type, original_latency, new_latency, shift_distance, ...
        'VariableNames', {'Event_Label', 'Proto_Type', 'Original_Latency_sec', 'New_Latency_sec', 'Shift_Distance_sec'});
    writetable(event_table, fullfile(output_path, 'event_shift_report.txt'));
end

function is_nan = is_within_nan_segment(latency, EEG)
    % Check if a given latency falls within a NaN segment
    is_nan = any(isnan(EEG.data(:, round(latency))));
end

function valid_index = find_next_valid_index(latency, EEG)
    % Find the next valid index that is not a NaN
    valid_index = latency;
    while any(isnan(EEG.data(:, round(valid_index))))
        valid_index = valid_index + 1;
    end
end