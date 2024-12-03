% File Handling

addpath('/Users/idohaber/Documents/MATLAB/eeglab2024.0/')
addpath('/Users/idohaber/Desktop/ti_process-main/')
eeglab nogui

% Directory containing experiment data
experiment_path = '/Volumes/CSC-Ido/EEG';

% Define lists of nights and subjects
nights = {'N1'};
subjects = {'119'};

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

        % Remove data from unwanted sleep stages (keep only NREM)
        slp = sleep_process;
        % Reminder: remove_spec_stage(EEG, stages, savestr)
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

        %% CSV Export of Event Information

        % Initialize cell arrays to store event data
        Event_Type = {};
        Proto_Type = [];
        Latency_Samples = [];
        Time_sec = [];

        % Loop through each event to ensure consistency
        for iEv = 1:length(EEG.event)
            event = EEG.event(iEv);
            % Check if required fields exist
            if isfield(event, 'type') && isfield(event, 'proto_type') && isfield(event, 'latency')
                % Optionally, filter for specific event types
                if strcmp(event.type, 'stim start') || strcmp(event.type, 'stim end')
                    Event_Type{end+1,1} = event.type;
                    Proto_Type(end+1,1) = event.proto_type;
                    Latency_Samples(end+1,1) = event.latency;
                    Time_sec(end+1,1) = event.latency / EEG.srate; % Convert samples to seconds
                end
            else
                fprintf('Event %d is missing required fields and will be skipped.\n', iEv);
            end
        end

        % Ensure that all variables have the same length
        numEvents = length(Event_Type);
        if length(Proto_Type) ~= numEvents || length(Latency_Samples) ~= numEvents || length(Time_sec) ~= numEvents
            fprintf('Mismatch in event data lengths for Subject %s, Night %s. Skipping CSV export.\n', whichSubj, whichSess);
            continue; % Skip CSV export for this iteration
        end

        % Create a table
        eventTable = table(Event_Type, Proto_Type, Latency_Samples, Time_sec, ...
            'VariableNames', {'Event_Type', 'Proto_Type', 'Latency_Samples', 'Time_sec'});

        % Define CSV file name
        [~, baseFileName, ~] = fileparts(new_fileName);
        csvFileName = [baseFileName '_events.csv'];
        csvFilePath = fullfile(subj_sess_filepath, csvFileName);

        % Write table to CSV
        try
            writetable(eventTable, csvFilePath);
            fprintf('Event information saved to %s\n', csvFileName);
        catch ME
            fprintf('Failed to write CSV for Subject %s, Night %s: %s\n', whichSubj, whichSess, ME.message);
        end
    end
end

fprintf('Processing completed for all subjects and nights.\n');
