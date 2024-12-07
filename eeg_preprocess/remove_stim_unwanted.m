function EEG = remove_stim_unwanted(EEG, unwanted_stages, fid)
    % REMOVE_STIM_UNWANTED Removes stimulation protocols (stim start/end with proto_type=4)
    % that immediately follow specified unwanted sleep stages and logs the removals.
    %
    % Parameters:
    %   EEG             - EEGLAB EEG structure with events and data
    %   unwanted_stages - Array of sleep stage codes to consider for removal
    %   fid             - File identifier for logging
    %
    % Returns:
    %   EEG - Updated EEGLAB EEG structure with specified stim protocols removed

    % Ensure that events are sorted by latency
    [~, sort_idx] = sort([EEG.event.latency]);
    EEG.event = EEG.event(sort_idx);

    % Identify protocols: pair 'stim start' and 'stim end'
    protocols = struct('start_idx', {}, 'end_idx', {}, 'protocol_num', {});
    protocol_num = 1;
    event_protocol_map = zeros(1, length(EEG.event)); % Map event index to protocol number

    i = 1;
    while i <= length(EEG.event)
        if strcmp(EEG.event(i).type, 'stim start') && ...
           isfield(EEG.event(i), 'proto_type') && EEG.event(i).proto_type == 4
            % Find the corresponding 'stim end'
            j = i + 1;
            while j <= length(EEG.event)
                if strcmp(EEG.event(j).type, 'stim end') && ...
                   isfield(EEG.event(j), 'proto_type') && EEG.event(j).proto_type == 4
                    % Found a protocol
                    protocols(end+1).start_idx = i;
                    protocols(end).end_idx = j;
                    protocols(end).protocol_num = protocol_num;
                    event_protocol_map(i) = protocol_num;
                    event_protocol_map(j) = protocol_num;
                    protocol_num = protocol_num + 1;
                    break;
                end
                j = j + 1;
            end
            if j > length(EEG.event)
                % 'stim start' without corresponding 'stim end'
                % Handle as needed, here we ignore incomplete protocol
                warning('Stim start at index %d has no corresponding stim end. Ignoring incomplete protocol.', i);
                break;
            end
            i = j + 1;
        else
            i = i + 1;
        end
    end

    total_protocols = protocol_num - 1;

    % Initialize list of protocol numbers to remove
    protocols_to_remove = [];

    % Iterate through events, up to the second last event
    for iEv = 1:length(EEG.event) - 1
        current_event = EEG.event(iEv);

        % Check if current_event is 'Sleep Stage'
        if strcmp(current_event.type, 'Sleep Stage')
            % Get the sleep stage code and convert to numeric
            sleep_stage_code_str = current_event.code;
            sleep_stage_code = str2double(sleep_stage_code_str);
            if isnan(sleep_stage_code)
                sleep_stage_code = -1; % Unknown or invalid
            end

            % Check if sleep stage is unwanted
            if ismember(sleep_stage_code, unwanted_stages)
                % Get the next event
                next_event = EEG.event(iEv + 1);

                % Check if next_event is 'stim start' or 'stim end' with proto_type=4
                if (strcmp(next_event.type, 'stim start') || strcmp(next_event.type, 'stim end')) && ...
                   isfield(next_event, 'proto_type') && next_event.proto_type == 4

                    % Find the protocol number
                    protocol_num = event_protocol_map(iEv + 1);
                    if protocol_num > 0 && ~ismember(protocol_num, protocols_to_remove)
                        % Mark the protocol for removal
                        protocols_to_remove = [protocols_to_remove, protocol_num];

                        % Get protocol events
                        protocol = protocols(protocol_num);

                        % Determine stim action based on which event was found
                        if strcmp(next_event.type, 'stim start')
                            stim_action = 'Stim Start';
                        else
                            stim_action = 'Stim End';
                        end

                        % Log the removal with detailed information
                        fprintf(fid, 'Removing Protocol %d (%s of type %d at latency %.2f seconds (sample %d) and its counterpart) during sleep stage %d.\n', ...
                            protocol_num, stim_action, next_event.proto_type, next_event.latency / EEG.srate, round(next_event.latency), sleep_stage_code);
                        fprintf('Removing Protocol %d (%s of type %d at latency %.2f seconds (sample %d) and its counterpart) during sleep stage %d.\n', ...
                            protocol_num, stim_action, next_event.proto_type, next_event.latency / EEG.srate, round(next_event.latency), sleep_stage_code);
                    end
                end
            end
        end
    end

    % Remove the identified protocols
    if ~isempty(protocols_to_remove)
        events_to_remove = [];
        for p = protocols_to_remove
            events_to_remove = [events_to_remove, protocols(p).start_idx, protocols(p).end_idx];
        end
        EEG.event(events_to_remove) = [];
        fprintf(fid, 'Total protocols removed: %d\n', length(protocols_to_remove));
        fprintf('Total protocols removed: %d\n', length(protocols_to_remove));
    else
        fprintf(fid, 'No stimulation protocols found following specified unwanted sleep stages.\n');
        fprintf('No stimulation protocols found following specified unwanted sleep stages.\n');
    end

    % Log the remaining protocols
    remaining_protocols = total_protocols - length(protocols_to_remove);
    fprintf(fid, 'Total protocols remaining: %d\n', remaining_protocols);
    fprintf('Total protocols remaining: %d\n', remaining_protocols);
end
