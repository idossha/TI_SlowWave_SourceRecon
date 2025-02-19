
function EEG = harmonize_events(EEG, newEvents)
% harmonize_events - Ensure new events have the same fields as EEG.event.
%
% Syntax:
%   EEG = harmonize_events(EEG, newEvents)
%
% Inputs:
%   EEG       - The EEG structure.
%   newEvents - New event structures (with fields 'type' and 'latency').
%
% Output:
%   EEG - Updated EEG structure with new events appended and sorted.

    if isempty(EEG.event)
        EEG.event = newEvents;
    else
        fieldsEEG = fieldnames(EEG.event);
        fieldsNew = fieldnames(newEvents);
        allFields = union(fieldsEEG, fieldsNew);

        % Add missing fields to existing events.
        for i = 1:length(EEG.event)
            missingFields = setdiff(allFields, fieldnames(EEG.event(i)));
            for j = 1:length(missingFields)
                EEG.event(i).(missingFields{j}) = [];
            end
        end

        % Add missing fields to new events.
        for i = 1:length(newEvents)
            missingFields = setdiff(allFields, fieldnames(newEvents(i)));
            for j = 1:length(missingFields)
                newEvents(i).(missingFields{j}) = [];
            end
        end

        % Append and sort events by latency.
        EEG.event = [EEG.event, newEvents];
    end

    [~, sortIdx] = sort([EEG.event.latency]);
    EEG.event = EEG.event(sortIdx);
end
