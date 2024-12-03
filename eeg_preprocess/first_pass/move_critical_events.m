
function [EEG, event_log] = move_critical_events(EEG, nan_regions, critical_events)
    % MOVE_CRITICAL_EVENTS Moves critical events within NaN segments to the end of the segment +1 sample.
    %
    % Parameters:
    %   EEG             - EEGLAB EEG structure
    %   nan_regions     - Nx2 matrix of NaN segments [start, end] in samples
    %   critical_events - Cell array of critical event types to preserve
    %
    % Returns:
    %   EEG       - Updated EEGLAB EEG structure with moved events
    %   event_log - Structure containing event information before and after moving

    % Initialize the event log
    event_log = struct();
    event_log.events_moved = []; % Each row: [event_type, original_latency, new_latency]

    % Find indices of critical events within NaN segments
    for i = 1:length(EEG.event)
        evt_type = EEG.event(i).type;
        evt_lat = EEG.event(i).latency;

        if ismember(evt_type, critical_events)
            % Check if event latency is within any NaN region
            in_nan = false;
            for j = 1:size(nan_regions, 1)
                if evt_lat >= nan_regions(j,1) && evt_lat <= nan_regions(j,2)
                    in_nan = true;
                    break;
                end
            end

            if in_nan
                % Move the event to the end of the NaN segment +1 sample
                new_lat = nan_regions(j,2) + 1;
                if new_lat > EEG.pnts
                    fprintf('Warning: New latency for event "%s" exceeds data length. Moving to the last sample.\n', evt_type);
                    new_lat = EEG.pnts;
                end

                % Log the event movement
                event_log.events_moved = [event_log.events_moved; {evt_type}, evt_lat, new_lat];

                % Move the event latency
                EEG.event(i).latency = new_lat;
            end
        end
    end
end
