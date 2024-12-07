
% File: reposition_events_in_nan_segments.m

function EEG = reposition_events_in_nan_segments(EEG, nan_regions, original_actualTimes)
    % REPOSITION_EVENTS_IN_NAN_SEGMENTS Repositions critical events from NaN segments.
    %
    % Parameters:
    %   EEG                 - EEGLAB EEG structure
    %   nan_regions         - Nx2 matrix of NaN segments [start, end] in samples
    %   original_actualTimes - Original actualTimes array from the unprocessed EEG data
    %
    % Returns:
    %   EEG - Updated EEGLAB EEG structure with moved events and additional fields

    % Define the event types to process
    desired_event_types = {'stim start', 'stim end'};

    % Initialize the 'moved' field and store original information for all events
    for iEv = 1:length(EEG.event)
        EEG.event(iEv).moved = false;
        EEG.event(iEv).shift_distance_sec = 0;
        EEG.event(iEv).original_latency = EEG.event(iEv).latency;

        % Get original actual time from original_actualTimes
        event_sample = round(EEG.event(iEv).latency);
        if length(original_actualTimes) >= event_sample
            EEG.event(iEv).original_actual_time = original_actualTimes(event_sample);
        else
            EEG.event(iEv).original_actual_time = NaT; % Not a Time
        end
    end

    % Loop through each event to check if it falls within NaN segments
    for iEv = 1:length(EEG.event)
        event = EEG.event(iEv);

        % Check if the event type is one of the desired types
        if ismember(event.type, desired_event_types)
            % If the event falls in a NaN segment, reposition it
            [in_nan, nan_region_end] = is_within_nan_segment(event.latency, nan_regions);
            if in_nan
                % Move event to the first valid index after the NaN segment
                new_index = nan_region_end + 1;
                if new_index > size(EEG.data, 2)
                    warning('Event "%s" at latency %d cannot be repositioned beyond data length.', event.type, event.latency);
                    continue; % Skip to the next event
                end

                % Calculate shift distance
                shift_distance = new_index - event.latency;
                shift_distance_sec = shift_distance / EEG.srate;

                % Update event latency
                EEG.event(iEv).latency = new_index;
                EEG.event(iEv).shift_distance_sec = shift_distance_sec;
                EEG.event(iEv).moved = true; % Mark the event as moved
            else
                EEG.event(iEv).shift_distance_sec = 0;
            end
        else
            EEG.event(iEv).shift_distance_sec = 0;
        end
    end

    % After repositioning events, sort EEG.event by latency
    [~, sortIdx] = sort([EEG.event.latency]);
    EEG.event = EEG.event(sortIdx);
end

% Helper Function: Check if latency is within any NaN segment
function [is_nan, nan_region_end] = is_within_nan_segment(latency, nan_regions)
    idx = find(latency >= nan_regions(:,1) & latency <= nan_regions(:,2), 1);
    if ~isempty(idx)
        is_nan = true;
        nan_region_end = nan_regions(idx, 2);
    else
        is_nan = false;
        nan_region_end = [];
    end
end

