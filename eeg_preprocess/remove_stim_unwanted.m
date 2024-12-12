function EEG = remove_stim_unwanted(EEG, unwanted_stages, fid, desired_proto_type)
    % REMOVE_STIM_UNWANTED Removes stimulation protocols (stim start/end with desired_proto_type)
    % that immediately follow specified unwanted sleep stages, logs the removals,
    % and creates pretty-printed JSON files with protocol details.
    %
    % Parameters:
    %   EEG                 - EEGLAB EEG structure with events and data
    %   unwanted_stages     - Array of sleep stage codes to consider for removal (e.g., [0 1 2 3])
    %   fid                 - File identifier for logging (opened with fopen)
    %   desired_proto_type  - The proto_type(s) of stim events to highlight (e.g., 4 or [4,5])
    %
    % Returns:
    %   EEG - Updated EEGLAB EEG structure with specified stim protocols removed

    fprintf(fid, '########################################\n');
    fprintf(fid, 'remove_stim_unwanted: START\n');
    fprintf(fid, '########################################\n');

    % Ensure that events are sorted by latency
    [~, sort_idx] = sort([EEG.event.latency]);
    EEG.event = EEG.event(sort_idx);

    % Initialize protocol tracking
    protocols = struct('protocol_num', {}, 'stim_start_idx', {}, 'stim_end_idx', {}, 'stim_start_time', {}, 'stim_end_time', {});
    protocol_num = 1;
    event_protocol_map = zeros(1, length(EEG.event)); % Map event index to protocol number

    % Pair 'stim start' and 'stim end' events
    i = 1;
    while i <= length(EEG.event)
        if strcmp(EEG.event(i).type, 'stim start') && ...
           isfield(EEG.event(i), 'proto_type') && ...
           any(ismember(EEG.event(i).proto_type, desired_proto_type))

            % Search for the corresponding 'stim end'
            j = i + 1;
            foundEnd = false;
            while j <= length(EEG.event)
                if strcmp(EEG.event(j).type, 'stim end') && ...
                   isfield(EEG.event(j), 'proto_type') && ...
                   any(ismember(EEG.event(j).proto_type, desired_proto_type))
                    % Found a matching 'stim end'
                    protocols(end+1).protocol_num = protocol_num;
                    protocols(end).stim_start_idx = i;
                    protocols(end).stim_end_idx = j;
                    protocols(end).stim_start_time = EEG.etc.actualTimes(round(EEG.event(i).latency));
                    protocols(end).stim_end_time = EEG.etc.actualTimes(round(EEG.event(j).latency));
                    event_protocol_map(i) = protocol_num;
                    event_protocol_map(j) = protocol_num;

                    % Assign protocol number to events
                    EEG.event(i).protocol_num = protocol_num;
                    EEG.event(j).protocol_num = protocol_num;

                    protocol_num = protocol_num + 1;
                    foundEnd = true;
                    break;
                end
                j = j + 1;
            end

            if ~foundEnd
                % Log incomplete protocol
                warning('Stim start at index %d has no corresponding stim end. Ignoring incomplete protocol.', i);
                fprintf(fid, 'Warning: Stim start at index %d has no corresponding stim end. Ignoring incomplete protocol.\n', i);
                break; % Exit loop to prevent infinite searching
            end

            i = j + 1; % Move past the 'stim end' event
        else
            i = i + 1;
        end
    end

    total_protocols = protocol_num - 1;

    % Initialize list of protocol numbers to remove
    protocols_to_remove = [];

    % Iterate through events to identify protocols to remove
    for iEv = 1:length(EEG.event) - 1
        current_event = EEG.event(iEv);

        % Check if current_event is 'Sleep Stage'
        if strcmp(current_event.type, 'Sleep Stage')
            % Get the sleep stage code and convert to numeric
            if ischar(current_event.code) || isstring(current_event.code)
                sleep_stage_code = str2double(current_event.code);
            else
                sleep_stage_code = NaN; % Handle non-scalar or unexpected types
                fprintf(fid, 'Warning: Sleep Stage event at index %d has non-scalar code. Setting sleep_stage_code to NaN.\n', iEv);
            end

            if isnan(sleep_stage_code)
                sleep_stage_code = -1; % Unknown or invalid
            end

            % Check if sleep stage is unwanted
            if ismember(sleep_stage_code, unwanted_stages)
                % Get the next event
                next_event = EEG.event(iEv + 1);

                % Check if next_event is 'stim start' or 'stim end' with desired_proto_type
                if (strcmp(next_event.type, 'stim start') || strcmp(next_event.type, 'stim end')) && ...
                   isfield(next_event, 'proto_type') && ...
                   any(ismember(next_event.proto_type, desired_proto_type))

                    % Find the protocol number
                    p_num = event_protocol_map(iEv + 1);
                    if p_num > 0 && ~ismember(p_num, protocols_to_remove)
                        % Mark the protocol for removal
                        protocols_to_remove = [protocols_to_remove, p_num];

                        % Get protocol details
                        protocol = protocols(p_num);
                        if strcmp(next_event.type, 'stim start')
                            stim_action = 'Stim Start';
                        else
                            stim_action = 'Stim End';
                        end

                        % Log the removal with detailed information
                        fprintf(fid, 'Removing Protocol %d (%s of type %d at latency %.2f seconds (sample %d)) during sleep stage %d.\n', ...
                            p_num, stim_action, next_event.proto_type, next_event.latency / EEG.srate, round(next_event.latency), sleep_stage_code);
                        fprintf('Removing Protocol %d (%s of type %d at latency %.2f seconds (sample %d)) during sleep stage %d.\n', ...
                            p_num, stim_action, next_event.proto_type, next_event.latency / EEG.srate, round(next_event.latency), sleep_stage_code);
                    end
                end
            end
        end
    end

    % Remove the identified protocols
    if ~isempty(protocols_to_remove)
        events_to_remove = [];
        for p = protocols_to_remove
            if p <= total_protocols % Safety check
                events_to_remove = [events_to_remove, protocols(p).stim_start_idx, protocols(p).stim_end_idx];
            end
        end
        % Remove events in descending order to avoid indexing issues
        events_to_remove = sort(events_to_remove, 'descend');
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

    % Create JSON structure for all protocols
    all_protocols = struct();
    for p = 1:total_protocols
        stim_start_time = char(protocols(p).stim_start_time); % Convert datetime to char
        stim_end_time = char(protocols(p).stim_end_time);     % Convert datetime to char
        all_protocols.(['protocol_' num2str(p)]) = struct(...
            'stim_start', stim_start_time, ...
            'stim_end', stim_end_time ...
        );
    end

    % Convert to JSON
    json_str = jsonencode(all_protocols);
    json_str_pretty = pretty_json(json_str); % Pretty-print the JSON string

    % Define JSON file path
    json_file_name = sprintf('protocols_%s_%s.json', EEG.setname, datestr(now, 'yyyymmdd_HHMMSS'));
    json_file_path = fullfile(EEG.filepath, 'analysis', 'sleep', json_file_name);

    % Save JSON file
    fid_json = fopen(json_file_path, 'w');
    if fid_json == -1
        warning('Could not open file %s for writing JSON.', json_file_path);
    else
        fwrite(fid_json, json_str_pretty, 'char');
        fclose(fid_json);
        fprintf(fid, 'All protocols have been saved to JSON file: %s\n', json_file_path);
        fprintf('All protocols have been saved to JSON file: %s\n', json_file_path);
    end

    % Create JSON structure for protocols status
    protocols_info = struct();
    for p = 1:total_protocols
        protocols_info(p).protocol_num = p;
        protocols_info(p).stim_start_time = char(protocols(p).stim_start_time);
        protocols_info(p).stim_end_time = char(protocols(p).stim_end_time);
        if ismember(p, protocols_to_remove)
            protocols_info(p).status = 'Removed';
        else
            protocols_info(p).status = 'Remaining';
        end
    end

    % Convert protocols_info to JSON
    protocols_status_json_str = jsonencode(protocols_info);
    protocols_status_json_str_pretty = pretty_json(protocols_status_json_str); % Pretty-print the JSON string

    % Define JSON file path for protocols status
    json_status_file_name = sprintf('protocols_status_%s_%s.json', EEG.setname, datestr(now, 'yyyymmdd_HHMMSS'));
    json_status_file_path = fullfile(EEG.filepath, 'analysis', 'sleep', json_status_file_name);

    % Save protocols status JSON file
    fid_json_status = fopen(json_status_file_path, 'w');
    if fid_json_status == -1
        warning('Could not open file %s for writing protocols status JSON.', json_status_file_path);
    else
        fwrite(fid_json_status, protocols_status_json_str_pretty, 'char');
        fclose(fid_json_status);
        fprintf(fid, 'Protocols status (Removed/Remaining) have been saved to JSON file: %s\n', json_status_file_path);
        fprintf('Protocols status (Removed/Remaining) have been saved to JSON file: %s\n', json_status_file_path);
    end

    % Output a summary of the JSON to the log
    fprintf(fid, '\n########################################\n');
    fprintf(fid, 'Protocols Summary:\n');
    fprintf(fid, '########################################\n');
    for p = 1:total_protocols
        status = protocols_info(p).status;
        fprintf(fid, 'Protocol %d: %s\n', p, status);
        fprintf(fid, '    Stim Start: %s\n', protocols_info(p).stim_start_time);
        fprintf(fid, '    Stim End:   %s\n', protocols_info(p).stim_end_time);
    end
    fprintf(fid, '########################################\n\n');

    fprintf(fid, 'remove_stim_unwanted: END\n');
    fprintf(fid, '########################################\n');
end

% Helper function for pretty-printing JSON
function prettyStr = pretty_json(jsonStr)
    % PRETTY_JSON Formats a JSON string with indentation and line breaks.
    %
    % Parameters:
    %   jsonStr - The JSON string to format.
    %
    % Returns:
    %   prettyStr - The formatted JSON string.

    indentLevel = 0;
    prettyStr = '';
    inString = false;

    for i = 1:length(jsonStr)
        char = jsonStr(i);

        switch char
            case '"'
                % Toggle inString status unless escaped
                if i > 1 && jsonStr(i-1) == '\'
                    prettyStr(end+1) = char; %#ok<AGROW>
                else
                    inString = ~inString;
                    prettyStr(end+1) = char; %#ok<AGROW>
                end
            case '{', '['
                prettyStr(end+1) = char; %#ok<AGROW>
                if ~inString
                    indentLevel = indentLevel + 1;
                    prettyStr = [prettyStr, newline, repmat('    ', 1, indentLevel)]; %#ok<AGROW>
                end
            case '}', ']'
                if ~inString
                    indentLevel = indentLevel - 1;
                    prettyStr = [prettyStr, newline, repmat('    ', 1, indentLevel)]; %#ok<AGROW>
                end
                prettyStr(end+1) = char; %#ok<AGROW>
            case ','
                prettyStr(end+1) = char; %#ok<AGROW>
                if ~inString
                    prettyStr = [prettyStr, newline, repmat('    ', 1, indentLevel)]; %#ok<AGROW>
                end
            case ':'
                if ~inString
                    prettyStr(end+1) = char; %#ok<AGROW>
                    prettyStr(end+1) = ' '; %#ok<AGROW>
                else
                    prettyStr(end+1) = char; %#ok<AGROW>
                end
            otherwise
                prettyStr(end+1) = char; %#ok<AGROW>
        end
    end
end
