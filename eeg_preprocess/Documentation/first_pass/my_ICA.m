% Clear workspace and command window
clear; clc;

% File Handling
addpath('/Users/idohaber/Documents/MATLAB/eeglab2024.0/')
addpath('/Users/idohaber/Desktop/ti_process-main/')
eeglab nogui

% Directory containing experiment data
experiment_path = '/Users/idohaber/Desktop/EEG';

% Define lists of nights and subjects
nights = {'N1'};
subjects = {'107'};

% Loop through each subject and night
for subjIdx = 1:length(subjects)
    for nightIdx = 1:length(nights)
        % Select subject and night
        whichSubj = subjects{subjIdx};
        whichSess = nights{nightIdx};
        file_ext = '_bc.set';

        % Construct file path
        subj_sess_filepath = fullfile(experiment_path, whichSubj, whichSess);
        dirs = dir(subj_sess_filepath);

        % Find the .set file
        dir_ind = find(contains({dirs(:).name}, file_ext));
        if isempty(dir_ind)
            fprintf('File not found for Subject %s, Night %s\n', whichSubj, whichSess);
            continue; % Skip to the next iteration
        end

        % Load the EEG file
        EEG = pop_loadset(fullfile(subj_sess_filepath, dirs(dir_ind).name));
        fprintf('Processing Subject %s, Night %s\n', whichSubj, whichSess);

        % Step 1: Reposition events in NaN segments
        EEG = reposition_events_in_nan_segments(EEG, subj_sess_filepath);

        % Step 2: Remove undesired sleep stages (e.g., NREM)
        slp = sleep_process;
        EEG = slp.remove_spec_stage(EEG, [0 1 4 5], '_NREM');

        % Remove NaNs
        EEG.etc.saveNaN = 0;
        EEG = eeg_eegrej(EEG, EEG.etc.rejRegions);

        %% Event Marker Check
        starts = [];
        ends = [];
        for iEv = 1:length(EEG.event)
            if strcmp(EEG.event(iEv).type, 'stim start') && EEG.event(iEv).proto_type == 4
                starts = [starts EEG.event(iEv).latency];
            end
            if strcmp(EEG.event(iEv).type, 'stim end') && EEG.event(iEv).proto_type == 4
                ends = [ends EEG.event(iEv).latency];
            end
        end

        % Check that number of starts == number of ends
        if length(starts) ~= length(ends)
            fprintf('\n');
            fprintf('!!HEADS UP!! Number of stim starts does not match number of stim ends for Subject %s, Night %s\n', whichSubj, whichSess);
            fprintf('\n');
        end

        % Save as _forICA.set
        new_fileName = ['Strength_' whichSubj '_' whichSess '_forICA.set'];
        EEG.filename = new_fileName;
        EEG.setname = new_fileName;
        fprintf('Saving %s \n', new_fileName);
        pop_saveset(EEG, fullfile(subj_sess_filepath, new_fileName));
    end
end

fprintf('Processing completed for all subjects and nights.\n');

%% Nested Functions

function EEG = reposition_events_in_nan_segments(EEG, output_path)
    % Initialize variables to store event changes
    event_label = {};
    proto_type = {}; % Using cell array to accommodate various data types
    original_latency = [];
    new_latency = [];
    shift_distance = [];

    % Define the event types to process
    desired_event_types = {'stim start', 'stim end'};

    % Loop through each event to check if it falls within NaN segments
    for iEv = 1:length(EEG.event)
        event = EEG.event(iEv);
        
        % Check if the event type is one of the desired types
        if ismember(event.type, desired_event_types)
            % If the event falls in a NaN segment, reposition it
            if is_within_nan_segment(event.latency, EEG)
                % Find the first valid index after the NaN segment
                try
                    new_index = find_next_valid_index(event.latency, EEG);
                catch ME
                    warning('Subject: %s, Event: %s at latency %d could not be repositioned. %s', ...
                            EEG.subject, event.type, event.latency, ME.message);
                    continue; % Skip to the next event
                end

                % Store event change information
                event_label{end+1, 1} = event.type;
                proto_type{end+1, 1} = event.proto_type; % Using cell array
                original_latency(end+1, 1) = round(event.latency / EEG.srate, 3); % Rounded to 3 decimals
                new_latency(end+1, 1) = round(new_index / EEG.srate, 3);       % Rounded to 3 decimals
                shift_distance(end+1, 1) = round((new_index - event.latency) / EEG.srate, 3); % Rounded

                % Update event latency
                EEG.event(iEv).latency = new_index;
            end
        end
    end

    % Check if any events were repositioned
    if isempty(event_label)
        fprintf('No stim start or stim end events were repositioned in %s.\n', output_path);
        return;
    end

    % Create a table with event information and save it as a .txt file
    event_table = table(event_label, proto_type, original_latency, new_latency, shift_distance, ...
        'VariableNames', {'Event_Label', 'Proto_Type', 'Original_Latency_sec', 'New_Latency_sec', 'Shift_Distance_sec'});
    
    % Define the output file name
    report_filename = fullfile(output_path, 'event_shift_report.txt');
    
    % Write the table to a text file with proper formatting
    writetable(event_table, report_filename, 'Delimiter', '\t');
    
    fprintf('Event shift report saved to %s\n', report_filename);

    %% Nested Helper Function: Check if latency is within a NaN segment
    function is_nan = is_within_nan_segment(latency, EEG)
        % Ensure latency is within bounds
        if latency < 1 || latency > size(EEG.data, 2)
            is_nan = false;
            return;
        end
        % Check if any channel has NaN at the given latency
        is_nan = any(isnan(EEG.data(:, round(latency))));
    end

    %% Nested Helper Function: Find the next valid index after a NaN segment
    function valid_index = find_next_valid_index(latency, EEG)
        valid_index = latency;
        max_index = size(EEG.data, 2);
        while valid_index <= max_index && any(isnan(EEG.data(:, round(valid_index))))
            valid_index = valid_index + 1;
        end
        if valid_index > max_index
            error('No valid index found after latency %d', latency);
        end
    end
end
