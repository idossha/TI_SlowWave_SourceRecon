function EEG = filter_events(EEG, keepEventTypes, desired_proto_type, fid)
% FILTER_EVENTS Filters EEG events by specified types and proto_type.
%
%   EEG = FILTER_EVENTS(EEG, keepEventTypes, desired_proto_type, fid)
%
%   This function removes all events from EEG.event that do not match the given
%   event types and desired_proto_type.
%
%   INPUTS:
%       EEG                 - EEGLAB EEG structure containing EEG.event
%       keepEventTypes      - Cell array of event type strings to keep 
%                             (e.g., {'stim start','stim end'})
%       desired_proto_type  - Numeric proto_type to keep (e.g., 5)
%       fid                 - File identifier for logging (use -1 if no log file)
%
%   OUTPUT:
%       EEG - The modified EEG structure with only the desired events retained.
%
%   EXAMPLE:
%       % Keep only 'stim start' and 'stim end' events with proto_type == 5
%       EEG = filter_events(EEG, {'stim start','stim end'}, 5, fid);

    %------------------------- Debugging/Logging --------------------------%
    log_message(fid, 'filter_events: START');
    log_message(fid, 'Keeping events of types: %s', strjoin(keepEventTypes, ', '));
    log_message(fid, 'Keeping proto_type: %d', desired_proto_type);

    %------------------------- Validation Checks --------------------------%
    if ~isfield(EEG, 'event') || isempty(EEG.event)
        log_message(fid, 'No events found in EEG structure. Nothing to filter.');
        return;
    end

    allTypes = {EEG.event.type};
    hasProtoTypeField = isfield(EEG.event, 'proto_type');
    if ~hasProtoTypeField
        log_message(fid, 'No "proto_type" field found in EEG.event. Filtering only by event type.');
    end

    %------------------------- Filtering Logic ----------------------------%
    typeMatches = ismember(allTypes, keepEventTypes);

    if hasProtoTypeField
        protoMatches = arrayfun(@(x) ...
            isnumeric(x.proto_type) && ...
            numel(x.proto_type) == 1 && ...
            ismember(x.proto_type, desired_proto_type), ...
            EEG.event);
    else
        protoMatches = true(size(typeMatches));
    end

    eventsToKeep = typeMatches & protoMatches;

    %------------------------- Apply Filtering ----------------------------%
    originalCount = length(EEG.event);
    EEG.event = EEG.event(eventsToKeep);
    finalCount = length(EEG.event);

    %------------------------- Clean Output -------------------------------%
    log_message(fid, 'Original number of events: %d', originalCount);
    log_message(fid, 'Number of remaining events: %d', finalCount);

    log_message(fid, 'List:');
    for eIdx = 1:length(EEG.event)
        ev = EEG.event(eIdx);
        if isfield(ev, 'proto_type')
            proto_val = ev.proto_type;
        else
            % If proto_type not available, show as NaN
            proto_val = NaN;
        end
        % Use %g for latency to avoid exponential formatting for large numbers.
        log_message(fid, 'Event %d: ''%s'', proto %d, latency %g', ...
                eIdx, ev.type, proto_val, ev.latency);
    end

    log_message(fid, 'filter_events: END');
end
