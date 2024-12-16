function EEG = filter_events(EEG, keepEventTypes, keepProtoType)
% FILTER_EVENTS Filters EEG events by specified types and proto_type.
%
%   EEG = FILTER_EVENTS(EEG, keepEventTypes, keepProtoType)
%
%   This function removes all events from EEG.event that do not match the given
%   event types and proto_type. This is useful for retaining only the subset of
%   events you are interested in.
%
%   INPUTS:
%       EEG             - EEGLAB EEG structure containing EEG.event
%       keepEventTypes  - Cell array of event type strings to keep 
%                         (e.g., {'stim start','stim end'})
%       keepProtoType   - Numeric proto_type to keep (e.g., 5)
%
%   OUTPUT:
%       EEG - The modified EEG structure with only the desired events retained.
%
%   EXAMPLE:
%       % Keep only 'stim start' and 'stim end' events with proto_type == 5
%       EEG = filter_events(EEG, {'stim start','stim end'}, 5);

    %------------------------- Debugging/Logging --------------------------%
    fprintf('filter_events: START\n');
    fprintf('Keeping events of types: %s\n', strjoin(keepEventTypes, ', '));
    fprintf('Keeping proto_type: %d\n', keepProtoType);

    %------------------------- Validation Checks --------------------------%
    if ~isfield(EEG, 'event') || isempty(EEG.event)
        warning('No events found in EEG structure. Nothing to filter.');
        return;
    end

    % Ensure event types are cell strings for consistent handling
    allTypes = {EEG.event.type};

    % Check if proto_type field exists in events. If not, we must skip filtering by proto_type.
    hasProtoTypeField = isfield(EEG.event, 'proto_type');
    if ~hasProtoTypeField
        warning('No "proto_type" field found in EEG.event. Filtering only by event type.');
    end

    %------------------------- Filtering Logic ----------------------------%
    % 1. Filter by type
    typeMatches = ismember(allTypes, keepEventTypes);

    % 2. Filter by proto_type (if available)
    if hasProtoTypeField
        protoMatches = arrayfun(@(x) x.proto_type == keepProtoType, EEG.event);
    else
        protoMatches = true(1, length(EEG.event)); % Keep all if proto_type field is missing
    end

    % Combine the two criteria
    eventsToKeep = typeMatches & protoMatches;

    %------------------------- Apply Filtering ----------------------------%
    originalCount = length(EEG.event);
    EEG.event = EEG.event(eventsToKeep);
    finalCount = length(EEG.event);

    %------------------------- Debugging Output ---------------------------%
    fprintf('Original number of events: %d\n', originalCount);
    fprintf('Number of events kept: %d\n', finalCount);
    fprintf('filter_events: END\n');

end
