% generate_stim_report.m
% Generates a stim_report table with required fields, renames columns, and calculates shift information.

function stim_report = generate_stim_report(EEG, fid)
    % Check if EEG.event exists and is not empty
    if ~isfield(EEG, 'event') || isempty(EEG.event)
        log_message(fid, 'Warning: EEG.event is empty or does not exist.');
        stim_report = table();
        return;
    end

    % Identify stim start and stim end events using ismember
    stim_event_types = {'stim start', 'stim end'};
    isStimEvent = ismember({EEG.event.type}, stim_event_types);
    stim_events = EEG.event(isStimEvent);
    num_events = length(stim_events);

    if num_events == 0
        log_message(fid, 'Warning: No stim events found.');
        stim_report = table();
        return;
    end

    % Initialize report table columns
    Event_Type = {stim_events.type}';
    Proto_Type = [stim_events.proto_type]';
    New_Latency_sec = [stim_events.latency]'/EEG.srate;

    % Initialize Original_Latency_sec and Actual_Time
    Original_Latency_sec = New_Latency_sec;  % default
    Actual_Time = repmat({''}, num_events, 1);  % initialize with empty strings

    % Initialize Sleep_Stage with NaNs to ensure consistent length
    Sleep_Stage = NaN(num_events,1);

    for i = 1:num_events
        stim_latency = stim_events(i).latency;
        log_message(fid, 'Processing stim event %d with latency %.2f.', i, stim_latency);

        % Validate stim_latency
        if ~isscalar(stim_latency) || stim_latency < 1 || stim_latency > length(EEG.etc.actualTimes)
            log_message(fid, 'Error: Invalid latency %.2f for stim event %d. It must be within 1 and %d.', stim_latency, i, length(EEG.etc.actualTimes));
            Sleep_Stage(i) = NaN;
            continue;
        end

        % Check if the event was moved
        if isfield(stim_events(i), 'Moved') && stim_events(i).Moved
            if isfield(stim_events(i), 'Original_Latency') && ~isempty(stim_events(i).Original_Latency)
                Original_Latency_sec(i) = stim_events(i).Original_Latency / EEG.srate;
                if isfield(stim_events(i), 'Original_ActualTime') && ~isempty(stim_events(i).Original_ActualTime)
                    % Handle datetime conversion to string
                    try
                        actual_time_str = datestr(stim_events(i).Original_ActualTime, 'HH:MM:SS');
                        Actual_Time{i} = actual_time_str;
                    catch ME
                        log_message(fid, 'Error converting Original_ActualTime for stim event %d: %s', i, ME.message);
                        Actual_Time{i} = '';
                    end
                else
                    Actual_Time{i} = '';
                end
            end
        else
            % Not moved; keep Original_Latency_sec same as New_Latency_sec
            Original_Latency_sec(i) = New_Latency_sec(i);
            % Get original Actual_Time
            if isfield(EEG.etc, 'actualTimes') && stim_latency <= length(EEG.etc.actualTimes)
                try
                    original_time_str = datestr(EEG.etc.actualTimes(floor(stim_latency)), 'HH:MM:SS');
                    Actual_Time{i} = original_time_str;
                catch ME
                    log_message(fid, 'Error converting Actual_Time for stim event %d: %s', i, ME.message);
                    Actual_Time{i} = '';
                end
            else
                Actual_Time{i} = '';
                log_message(fid, 'Warning: actualTimes missing or incomplete for stim event latency %d.', stim_latency);
            end
        end
    end

    % Initialize Shift_Distance_sec and Moved
    Shift_Distance_sec = New_Latency_sec - Original_Latency_sec;
    Moved = Shift_Distance_sec ~= 0;

    % Convert logical to double for CSV
    Moved = double(Moved);

    % Retrieve Sleep Stage events
    sleep_event_type = 'Sleep Stage';
    isSleepEvent = strcmp({EEG.event.type}, sleep_event_type);
    sleep_events = EEG.event(isSleepEvent);
    sleep_latencies = [sleep_events.latency]';
    sleep_codes = {sleep_events.code}';
    sleep_stages = str2double(sleep_codes);

    for i = 1:num_events
        event_latency = stim_events(i).latency;
        % Validate event_latency
        if ~isscalar(event_latency) || event_latency < 1 || event_latency > length(EEG.etc.actualTimes)
            log_message(fid, 'Error: Invalid latency %d for stim event %d. Cannot determine Sleep Stage.', event_latency, i);
            Sleep_Stage(i) = NaN;
            continue;
        end

        % Find the sleep stage at the time of the event
        stage_idx = find(sleep_latencies <= event_latency, 1, 'last');
        if ~isempty(stage_idx)
            Sleep_Stage(i) = sleep_stages(stage_idx);
        else
            Sleep_Stage(i) = NaN;
            log_message(fid, 'Warning: Stim event at latency %d has no associated Sleep Stage.', event_latency);
        end
    end

    % Check if all variables have the same number of rows
    var_lengths = [length(Event_Type), length(Proto_Type), length(Original_Latency_sec), ...
                  length(New_Latency_sec), length(Actual_Time), length(Shift_Distance_sec), ...
                  length(Moved), length(Sleep_Stage)];

    if length(unique(var_lengths)) ~= 1
        log_message(fid, 'Error: Variable lengths mismatch. Check stim events for inconsistencies.');
        stim_report = table();
        return;
    end

    % Create table with renamed columns
    stim_report = table(Event_Type, Proto_Type, Original_Latency_sec, New_Latency_sec, Actual_Time, Shift_Distance_sec, Moved, Sleep_Stage);

    % Rename columns for clarity
    stim_report.Properties.VariableNames = {'Event_Type', 'Proto_Type', 'Original_Latency', 'New_Latency', 'Actual_Time', 'Shift_Distance_sec', 'Moved', 'Sleep_Stage'};
end
