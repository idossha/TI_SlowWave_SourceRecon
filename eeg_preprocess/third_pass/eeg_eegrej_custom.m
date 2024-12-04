% eeg_eegrej_custom.m
% Custom version of eeg_eegrej to handle rejection without saving intermediate files and logs the process.

function EEG = eeg_eegrej_custom(EEG, regions, fid)
    if nargin < 3
        error('Not enough input arguments. Usage: EEG = eeg_eegrej_custom(EEG, regions, fid)');
    end
    if isempty(regions)
        log_message(fid, 'No regions provided for rejection. Skipping eeg_eegrej_custom.');
        return;
    end

    % Sort and combine regions
    regions = sortrows(regions,1);
    regions = combineregions(regions);

    log_message(fid, 'Combined NaN regions for rejection.');

    % Replace data in rejection regions with NaNs
    if isfield(EEG.etc, 'saveNaN') && EEG.etc.saveNaN == 1
        reject = false(1, EEG.pnts);
        for i = 1:size(regions,1)
            reject(regions(i,1):regions(i,2)) = true;
        end
        EEG.data(:, reject) = NaN;
        % Track rejection regions
        if isfield(EEG.etc, 'rejRegions') && ~isempty(EEG.etc.rejRegions)
            EEG.etc.rejRegions = [EEG.etc.rejRegions; regions];
        else
            EEG.etc.rejRegions = regions;
        end
        log_message(fid, 'Replaced data in rejection regions with NaNs.');
    else
        % Remove events within regions
        if ~isempty(EEG.event) && isfield(EEG.event, 'latency')
            allEventLatencies = [EEG.event.latency];
            allEventFlag = false(1, length(allEventLatencies));
            for iRegion = 1:size(regions,1)
                allEventFlag = allEventFlag | (allEventLatencies >= regions(iRegion,1) & allEventLatencies <= regions(iRegion,2));
            end
            boundaryIndices = eeg_findboundaries(EEG);
            allEventFlag(boundaryIndices) = false; % Do not remove boundary events
            EEG.event(allEventFlag) = [];
            log_message(fid, 'Removed events within rejection regions.');
        end

        % Reject data using EEGLAB's pop_eegrej
        EEG = pop_eegrej(EEG, regions, 0);  % 0 indicates no plotting
        log_message(fid, 'Rejected data in specified regions using eegrej.');

        % Update actualTimes and timeIndices if they exist
        if isfield(EEG.etc, 'actualTimes') && isfield(EEG.etc, 'timeIndices')
            % Determine indices to keep
            keep_indices = true(1, length(EEG.etc.timeIndices));
            for iRegion = 1:size(regions, 1)
                keep_indices(regions(iRegion,1):regions(iRegion,2)) = false;
            end
            EEG.etc.actualTimes = EEG.etc.actualTimes(keep_indices);
            EEG.etc.timeIndices = EEG.etc.timeIndices(keep_indices);
            log_message(fid, 'Updated actualTimes and timeIndices after rejection.');
        else
            log_message(fid, 'Warning: EEG.etc.actualTimes or EEG.etc.timeIndices not found. Cannot update these fields.');
        end

        % Sort events by latency
        [~, sortIdx] = sort([EEG.event.latency]);
        EEG.event = EEG.event(sortIdx);
        log_message(fid, 'Sorted events by latency.');
    end
end

% Helper function to combine overlapping or contiguous regions
function newregions = combineregions(regions)
    if isempty(regions)
        newregions = [];
        return;
    end

    regions = sortrows(regions,1);
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
end
