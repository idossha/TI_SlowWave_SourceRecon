function get_proto4_stim_events(EEG,stim_type)
    % GET_PROTO4_STIM_EVENTS Finds and displays stim start and stim end events for protocol 4.
    %
    % Parameters:
    %   EEG - EEGLAB EEG structure
    %
    % Displays:
    %   Number of stim starts and ends for protocol 4.
    %   Latencies of stim start and stim end events for protocol 4.
    %
    % Note:
    %   Prints a warning if the number of stim starts does not match the number of stim ends.

    % Initialize arrays to store latencies
    starts = [];
    ends = [];

    % Iterate through events to find protocol 4 stim start and stim end
    for iEv = 1:length(EEG.event)
        event = EEG.event(iEv);
        
        % Check if proto_type field exists and equals 4
        if isfield(event, 'proto_type') && ~isempty(event.proto_type) && event.proto_type == stim_type
            if strcmp(event.type, 'stim start')
                starts = [starts, event.latency];
            elseif strcmp(event.type, 'stim end')
                ends = [ends, event.latency];
            end
        end
    end

    % Calculate number of starts and ends
    num_starts = length(starts);
    num_ends = length(ends);

    % Check that the number of starts equals the number of ends
    if num_starts ~= num_ends
        fprintf('\n');
        fprintf('!!HEADS UP!! Number of stim starts (%d) does not match number of stim ends (%d) \n', num_starts, num_ends);
        fprintf('\n');
    end

    % Display results
    fprintf('Number of stim start events for protocol 4: %d\n', num_starts);
    fprintf('Number of stim end events for protocol 4: %d\n', num_ends);
    fprintf('Stim start latencies (samples): %s\n', mat2str(starts));
    fprintf('Stim end latencies (samples): %s\n', mat2str(ends));
end
