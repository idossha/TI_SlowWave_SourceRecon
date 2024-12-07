% filter_stim_events_by_sleep_stage.m
% Removes stim events that are not in specified sleep stages or have unwanted Proto_Type and logs the process.

function EEG = filter_stim_events_by_sleep_stage(EEG, desired_stages, allowed_proto_types, fid)
    % Validate inputs
    if nargin < 4
        error('Insufficient input arguments. Usage: EEG = filter_stim_events_by_sleep_stage(EEG, desired_stages, allowed_proto_types, fid)');
    end

    % Identify Sleep Stage events
    sleep_event_type = 'Sleep Stage';
    isSleepEvent = strcmp({EEG.event.type}, sleep_event_type);

    if ~any(isSleepEvent)
        log_message(fid, 'Warning: No Sleep Stage events found in EEG.event. All stim events will be removed.');
        % Identify stim events to remove
        stim_event_types = {'stim start', 'stim end'};
        isStimEvent = ismember({EEG.event.type}, stim_event_types);
        stim_events_to_remove = find(isStimEvent);
        EEG.event(stim_events_to_remove) = [];
        log_message(fid, 'All stim events removed due to absence of Sleep Stage events.');
        return;
    end

    sleep_events = EEG.event(isSleepEvent);
    sleep_latencies = [sleep_events.latency]';
    sleep_codes = {sleep_events.code}';
    sleep_stages = str2double(sleep_codes);

    % Handle non-numeric sleep stages
    if any(isnan(sleep_stages))
        log_message(fid, 'Warning: Some Sleep Stage codes could not be converted to numbers. These will be treated as NaN.');
    end

    % Identify stim events
    stim_event_types = {'stim start', 'stim end'};
    isStimEvent = ismember({EEG.event.type}, stim_event_types);
    stim_events = EEG.event(isStimEvent);
    stim_latencies = [stim_events.latency]';

    num_stim_events = length(stim_events);
    if num_stim_events == 0
        log_message(fid, 'Warning: No stim start or stim end events found in EEG.event.');
        return;
    end

    % Initialize logical array to determine which stim events to keep
    keepStim = false(num_stim_events, 1);

    % Loop through each stim event to check sleep stage and Proto_Type
    for i = 1:num_stim_events
        event_latency = stim_latencies(i);

        % Validate event_latency
        if ~isscalar(event_latency) || event_latency < 1 || event_latency > length(EEG.etc.actualTimes)
            log_message(fid, 'Error: Invalid latency %d for stim event %d. It must be within 1 and %d.', event_latency, i, length(EEG.etc.actualTimes));
            continue;
        end

        % Find the latest sleep event before or at the stim event latency
        stage_idx = find(sleep_latencies <= event_latency, 1, 'last');

        if isempty(stage_idx)
            % No sleep stage event found before this stim event
            log_message(fid, 'Stim event at latency %d has no preceding Sleep Stage event. It will be removed.', event_latency);
            continue;
        end

        current_stage = sleep_stages(stage_idx);

        % Check if current_stage is in desired_stages
        if ismember(current_stage, desired_stages)
            % Check if Proto_Type is allowed
            current_proto_type = stim_events(i).proto_type;
            if ismember(current_proto_type, allowed_proto_types)
                keepStim(i) = true;
            else
                log_message(fid, 'Removing stim event at latency %d due to Proto_Type %d not being allowed.', event_latency, current_proto_type);
            end
        else
            log_message(fid, 'Removing stim event at latency %d due to Sleep Stage %d not being desired.', event_latency, current_stage);
        end
    end

    % Indices of stim events to keep and remove
    stim_indices = find(isStimEvent);
    stim_events_to_keep = stim_indices(keepStim);
    stim_events_to_remove = stim_indices(~keepStim);

    % Remove stim events that do not meet criteria
    if ~isempty(stim_events_to_remove)
        log_message(fid, 'Removing %d stim events not in desired sleep stages or with unwanted Proto_Type.', length(stim_events_to_remove));
        EEG.event(stim_events_to_remove) = [];
    else
        log_message(fid, 'All stim events meet the desired criteria and are retained.');
    end
end
