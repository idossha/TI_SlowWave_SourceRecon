% move_events_within_nan.m
% Moves stim events within NaN segments to the first non-NaN index after the segment and logs the process.

function EEG = move_events_within_nan(EEG, NaNSegments, fid)
    % Identify stim start and stim end event indices using ismember
    stim_event_types = {'stim start', 'stim end'};
    stim_events_idx = find(ismember({EEG.event.type}, stim_event_types));

    log_message(fid, 'Total stim events identified for potential moving: %d', length(stim_events_idx));

    for i = 1:length(stim_events_idx)
        ev = EEG.event(stim_events_idx(i));
        ev_lat = ev.latency;
        
        % Log the original latency
        log_message(fid, 'Processing stim event %d with original latency %.2f.', i, ev_lat);
        
        % Initialize moved flag and shift
        EEG.event(stim_events_idx(i)).Moved = false;
        EEG.event(stim_events_idx(i)).Shift = 0;
        EEG.event(stim_events_idx(i)).Original_Latency = ev_lat;
        
        % Convert ev_lat to integer
        ev_lat_int = floor(ev_lat);
        
        % Check if ev_lat is within bounds
        if ev_lat_int < 1 || ev_lat_int > length(EEG.etc.actualTimes)
            log_message(fid, 'Error: Stim event %d has latency %d out of bounds (1 to %d). Skipping this event.', ...
                i, ev_lat_int, length(EEG.etc.actualTimes));
            EEG.event(stim_events_idx(i)).Original_ActualTime = '';
            continue;
        end
        
        % Assign Original_ActualTime as string
        try
            actual_time_str = datestr(EEG.etc.actualTimes(ev_lat_int), 'HH:MM:SS');
            EEG.event(stim_events_idx(i)).Original_ActualTime = actual_time_str;
        catch ME
            log_message(fid, 'Error converting actualTime for stim event %d: %s', i, ME.message);
            EEG.event(stim_events_idx(i)).Original_ActualTime = '';
        end

        % Check if event is within any NaN segment
        event_moved = false;
        for j = 1:size(NaNSegments,1)
            if ev_lat_int >= NaNSegments(j,1) && ev_lat_int <= NaNSegments(j,2)
                % Move to first non-NaN index after the NaN segment
                new_lat = NaNSegments(j,2) + 1;
                if new_lat > EEG.pnts
                    log_message(fid, 'Warning: Stim event %d cannot be moved beyond EEG.pnts (%d). Keeping original latency.', ...
                        i, EEG.pnts);
                    break;
                end
                
                % Convert new_lat to integer
                new_lat_int = floor(new_lat);
                
                % Validate new_lat_int
                if new_lat_int < 1 || new_lat_int > length(EEG.etc.actualTimes)
                    log_message(fid, 'Error: New latency %d for stim event %d is out of bounds. Skipping moving.', ...
                        new_lat_int, i);
                    break;
                end
                
                % Update event latency
                EEG.event(stim_events_idx(i)).latency = new_lat_int;
                
                % Assign Actual_Time as string
                try
                    new_actual_time_str = datestr(EEG.etc.actualTimes(new_lat_int), 'HH:MM:SS');
                    EEG.event(stim_events_idx(i)).actualTime = new_actual_time_str;
                catch ME
                    log_message(fid, 'Error converting new actualTime for stim event %d: %s', i, ME.message);
                    EEG.event(stim_events_idx(i)).actualTime = '';
                end
                
                % Indicate that the event was moved
                EEG.event(stim_events_idx(i)).Moved = true;
                EEG.event(stim_events_idx(i)).Shift = (new_lat_int - ev_lat_int)/EEG.srate;
                log_message(fid, 'Moved stim event %d from latency %d to %d (Shift: %.3f sec).', ...
                    i, ev_lat_int, new_lat_int, EEG.event(stim_events_idx(i)).Shift);
                
                event_moved = true;
                break; % Event has been moved; no need to check other NaN segments
            end
        end
        
        if ~event_moved
            log_message(fid, 'Stim event %d at latency %d is not within any NaN segment.', i, ev_lat_int);
        end
    end
end
