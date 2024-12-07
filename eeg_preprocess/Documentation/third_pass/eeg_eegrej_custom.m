% eeg_eegrej_custom.m
% Custom version of eeg_eegrej to handle rejection with logging.

function EEG = eeg_eegrej_custom(EEG, regions, fid)
    if nargin < 3
        error('Not enough input arguments. Usage: EEG = eeg_eegrej_custom(EEG, regions, fid)');
    end
    if isempty(regions)
        fprintf(fid, 'No regions provided for rejection. Skipping eeg_eegrej_custom.\n');
        return;
    end

    % Sort and combine overlapping or contiguous regions
    regions = sortrows(regions, 1);
    regions = combineregions(regions, fid);
    fprintf(fid, 'Combined and sorted rejection regions.\n');

    % Check if saveNaN flag is set
    if isfield(EEG.etc, 'saveNaN') && EEG.etc.saveNaN == 1
        % Replace data with NaNs
        reject = false(1, EEG.pnts);
        for i = 1:size(regions,1)
            if regions(i,1) < 1 || regions(i,2) > EEG.pnts
                fprintf(fid, 'Error: Rejection region [%d, %d] is out of bounds. Skipping this region.\n', regions(i,1), regions(i,2));
                continue;
            end
            reject(regions(i,1):regions(i,2)) = true;
        end
        EEG.data(:, reject) = NaN;
        fprintf(fid, 'Replaced data in rejection regions with NaNs.\n');

        % Track rejection regions
        if isfield(EEG.etc, 'rejRegions') && ~isempty(EEG.etc.rejRegions)
            EEG.etc.rejRegions = [EEG.etc.rejRegions; regions];
        else
            EEG.etc.rejRegions = regions;
        end
        fprintf(fid, 'Updated EEG.etc.rejRegions with new rejection regions.\n');

        % Rename and save data
        [~, name, ~] = fileparts(EEG.filename);
        new_fileName = sprintf('%s_rmbs.set', name);

        EEG.filename = new_fileName;
        EEG.setname = new_fileName;

        pop_saveset(EEG, 'filename', new_fileName, 'filepath', EEG.filepath);
        fprintf(fid, 'Saved rejected data as %s.\n', new_fileName);
    else
        % Remove data segments using eegrej
        fprintf(fid, 'Removing data segments using eegrej...\n');
        try
            [EEG.data, EEG.xmax, EEG.event, boundevents] = eegrej(EEG, regions);
            EEG.pnts = size(EEG.data,2);
            fprintf(fid, 'Data segments removed successfully using eegrej.\n');
        catch ME
            fprintf(fid, 'Error during eegrej: %s\n', ME.message);
            return;
        end

        % Handle boundary events if necessary
        if ~isempty(boundevents)
            for iBound = 1:length(boundevents)
                % Initialize boundary_event with the same fields as EEG.event
                boundary_event = initialize_boundary_event(EEG.event, boundevents(iBound), fid);

                % Append the boundary_event to EEG.event
                EEG.event(end+1) = boundary_event;
                fprintf(fid, 'Inserted boundary event at latency %d.\n', boundevents(iBound));
            end
            % Sort events by latency
            [~, sortIdx] = sort([EEG.event.latency]);
            EEG.event = EEG.event(sortIdx);
            fprintf(fid, 'Sorted events by latency after inserting boundary events.\n');
        end

        % Check consistency
        EEG = eeg_checkset(EEG, 'eventconsistency');
        fprintf(fid, 'Checked event consistency.\n');

        % Remove last event if necessary
        if ~isempty(EEG.event) && EEG.trials == 1 && (EEG.event(end).latency - 0.5 > EEG.pnts)
            EEG.event(end) = [];
            fprintf(fid, 'Removed last event due to latency exceeding EEG.pnts.\n');
        end
    end

    % Helper function to combine overlapping or contiguous regions
    function newregions = combineregions(regions, fid)
        if isempty(regions)
            newregions = [];
            return;
        end

        newregions = regions(1,:);
        for i = 2:size(regions,1)
            last = newregions(end,:);
            current = regions(i,:);
            if current(1) <= last(2) + 1
                newregions(end,2) = max(last(2), current(2));
            else
                newregions = [newregions; current];
            end
        end

        % Log if regions were combined
        if size(regions,1) ~= size(newregions,1)
            fprintf(fid, 'Warning: Overlapping or contiguous regions detected and combined.\n');
        end
    end

    % Helper function to initialize boundary_event with matching fields
    function boundary_event = initialize_boundary_event(existing_event, latency, fid)
        % Get all field names from the first event
        fields = fieldnames(existing_event);

        % Initialize boundary_event as an empty struct with the same fields
        boundary_event = struct();
        for i = 1:length(fields)
            field = fields{i};
            switch field
                case 'type'
                    boundary_event.type = 'boundary';
                case 'latency'
                    boundary_event.latency = latency;
                case 'duration'
                    boundary_event.duration = 0;
                case 'code'
                    boundary_event.code = ''; % Assign empty or appropriate default
                case 'urevent'
                    boundary_event.urevent = length(EEG.urevent) + 1; % Increment urevent counter
                otherwise
                    % Initialize other fields as empty or with default values
                    boundary_event.(field) = [];
            end
        end
    end
end
