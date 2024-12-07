%
% File: reject.m

function [EEG, com] = reject(EEG, regions)

    com = '';
    if nargin < 2
        help reject;
        return;
    end
    if nargin < 3
        probadded = [];
    end
    if isempty(regions)
        fprintf('No regions provided for rejection. Exiting function.\n');
        return;
    end

    fprintf('Starting rejection process...\n');

    % Ramon on 5/29/2014 for bug 1619
    if size(regions,2) > 2
        regions = sortrows(regions,3);
    else
        regions = sortrows(regions,1);
    end

    % Handle regions from eegplot
    if size(regions,2) > 2
        regions = regions(:, 3:4);
    end
    regions = combineregions(regions);

    fprintf('Regions after combining:\n');
    disp(regions);

    % ---- Modification Start: Handle prior rejRegions ----
    if isfield(EEG.etc, 'rejRegions') && ~isempty(EEG.etc.rejRegions)
        fprintf('Prior rejection regions detected. Moving them to moved_rejRegions.\n');
        % Initialize moved_rejRegions if it doesn't exist
        if isfield(EEG.etc, 'moved_rejRegions')
            EEG.etc.moved_rejRegions = [EEG.etc.moved_rejRegions; EEG.etc.rejRegions];
            fprintf('Appended existing rejRegions to moved_rejRegions.\n');
        else
            EEG.etc.moved_rejRegions = EEG.etc.rejRegions;
            fprintf('Created moved_rejRegions and moved existing rejRegions.\n');
        end
        % Clear rejRegions
        EEG.etc.rejRegions = [];
        fprintf('Cleared EEG.etc.rejRegions.\n');
    else
        fprintf('No prior rejection regions found.\n');
    end
    % ---- Modification End ----

    % ELS added - quick detour to replace data in rejection regions with NaNs
    % but otherwise keep the rest of the file intact, then save it
    if isfield(EEG.etc, 'saveNaN') && EEG.etc.saveNaN == 1
        fprintf('SaveNaN flag detected. Replacing rejected regions with NaNs.\n');
        rejectFlag = false(1, EEG.pnts);
        for i = 1:size(regions,1)
            rejectFlag(regions(i,1):regions(i,2)) = true;
        end
        EEG.data(:, rejectFlag) = NaN;
        fprintf('Replaced specified regions with NaNs.\n');

        % Keep track of rejection regions for repeat cleaning
        if isfield(EEG.etc, 'rejRegions') && ~isempty(EEG.etc.rejRegions)
            EEG.etc.rejRegions = [EEG.etc.rejRegions; regions];
            fprintf('Appended current regions to existing rejRegions.\n');
        else
            EEG.etc.rejRegions = regions;
            fprintf('Initialized rejRegions with current regions.\n');
        end

        % ---- Modification Start: Move rejRegions to moved_rejRegions ----
        if isfield(EEG.etc, 'moved_rejRegions')
            EEG.etc.moved_rejRegions = [EEG.etc.moved_rejRegions; EEG.etc.rejRegions];
            fprintf('Appended current rejRegions to moved_rejRegions.\n');
        else
            EEG.etc.moved_rejRegions = EEG.etc.rejRegions;
            fprintf('Created moved_rejRegions and moved current rejRegions.\n');
        end
        % Clear rejRegions
        EEG.etc.rejRegions = [];
        fprintf('Cleared EEG.etc.rejRegions after moving to moved_rejRegions.\n');
        % ---- Modification End ----

        regions = EEG.etc.rejRegions;  % Now empty

        % Rename and save data
        new_fileName = split(EEG.filename, '.set');
        new_fileName = strcat(new_fileName{1}, '_rmbs.set');

        % Rename set
        EEG.filename = new_fileName;
        EEG.setname = new_fileName;

        % Save data
        fprintf('Saving rejected data to %s \n', new_fileName);
        pop_saveset(EEG, fullfile(EEG.filepath, new_fileName));
    else
        fprintf('Proceeding with data rejection.\n');

        % Use rejection regions from prior rejections
        if isfield(EEG.etc, 'rejRegions') && ~isempty(EEG.etc.rejRegions)
            EEG.etc.rejRegions = [EEG.etc.rejRegions; regions];
            regions = EEG.etc.rejRegions;
            fprintf('Appended new regions to existing rejRegions.\n');
        end

        % Remove events within regions
        if ~isempty(EEG.event) && isfield(EEG.event, 'latency')
            fprintf('Removing events within rejection regions.\n');
            allEventLatencies = [ EEG.event.latency ];
            allEventFlag      = false(1,length(allEventLatencies));
            for iRegion = 1:size(regions,1)
                allEventFlag = allEventFlag | ( allEventLatencies >= regions(iRegion,1) & allEventLatencies <= regions(iRegion,2));
            end
            boundaryIndices = eeg_findboundaries(EEG);
            allEventFlag(boundaryIndices) = false; % Do not remove boundary events
            EEG.event(allEventFlag) = [];
            fprintf('Events within rejection regions removed.\n');
        end

        % Reject data
        fprintf('Rejecting specified data regions.\n');
        [EEG.data, EEG.xmax, event2, boundevents] = eegrej(EEG.data, regions, EEG.xmax-EEG.xmin, EEG.event);
        oldEEGpnts = EEG.pnts;
        EEG.pnts   = size(EEG.data,2);
        EEG.xmax   = EEG.xmax + EEG.xmin;
        fprintf('Data rejection completed. Updated EEG.pnts and EEG.xmax.\n');

        % --- Update actualTimes and timeIndices ---
        % Check if actualTimes and timeIndices exist
        if isfield(EEG.etc, 'actualTimes') && isfield(EEG.etc, 'timeIndices')
            fprintf('Updating actualTimes and timeIndices in EEG.etc...\n');
            % Create a logical index array for the points to keep
            keep_indices = true(1, oldEEGpnts);
            for iRegion = 1:size(regions, 1)
                keep_indices(regions(iRegion, 1):regions(iRegion, 2)) = false;
            end
            % Update actualTimes and timeIndices
            EEG.etc.actualTimes = EEG.etc.actualTimes(keep_indices);
            EEG.etc.timeIndices = EEG.etc.timeIndices(keep_indices);
            fprintf('actualTimes and timeIndices updated.\n');
        else
            fprintf('Warning: EEG.etc.actualTimes or EEG.etc.timeIndices not found. Cannot update these fields.\n');
        end
        % --- End Modification ---

        % Add boundary events
        fprintf('Adding boundary events.\n');
        [ EEG.event ] = eeg_insertbound(EEG.event, oldEEGpnts, regions);
        EEG = eeg_checkset(EEG, 'eventconsistency');
        if ~isempty(EEG.event) && EEG.trials == 1 && EEG.event(end).latency-0.5 > EEG.pnts
            EEG.event(end) = []; % Remove last event if necessary
            fprintf('Removed last event due to latency inconsistency.\n');
        end

        % Sort events by latency
        [~, sortIdx] = sort([EEG.event.latency]);
        EEG.event = EEG.event(sortIdx);
        fprintf('Events sorted by latency.\n');

        % Double check event latencies
        eeglab_options;
        warnflag = false;
        if isfield(EEG.event, 'latency') && length(EEG.event) < 3000
            alllats = [ EEG.event.latency ];
            if ~isempty(event2)
                otherlatencies = [event2.latency];
                if ~isequal(alllats, otherlatencies)
                    warning(['Discrepancy when checking event latencies using legacy method.' 10 ...
                             'Often the discrepancy is minor and the new method (used here) is correct' 10 ...
                             'Still, try to reproduce the problem and send us your dataset']);
                    warnflag = true;
                end
            end
        end

        % ---- Modification Start: Move current regions to moved_rejRegions ----
        if isfield(EEG.etc, 'moved_rejRegions')
            EEG.etc.moved_rejRegions = [EEG.etc.moved_rejRegions; regions];
            fprintf('Appended current rejection regions to moved_rejRegions.\n');
        else
            EEG.etc.moved_rejRegions = regions;
            fprintf('Created moved_rejRegions and moved current rejection regions.\n');
        end
        % Clear rejRegions
        EEG.etc.rejRegions = [];
        fprintf('Cleared EEG.etc.rejRegions after moving to moved_rejRegions.\n');
        % ---- Modification End ----
    end

    com = sprintf('EEG = reject(EEG, %s);', vararg2str({ regions }));
    fprintf('Rejection command recorded: %s\n', com);

end  % End of main reject function

% Combine regions if necessary
function newregions = combineregions(regions)
    % 9/1/2014 RMC
    regions = sortrows(sort(regions,2)); % Sorting regions
    allreg = [ regions(:,1)' regions(:,2)'; ones(1,numel(regions(:,1))) -ones(1,numel(regions(:,2))) ].';
    allreg = sortrows(allreg,1); % Sort all start and stop points (column 1),

    mboundary = cumsum(allreg(:,2)); % Rationale: regions will start always with 1 and close with 0, since starts=1 end=-1
    indx = 0; count = 1;

    while indx ~= length(allreg) 
        newregions(count,1) = allreg(indx+1,1);
        [tmp,I] = min(abs(mboundary(indx+1:end)));
        newregions(count,2) = allreg(I + indx,1);
        indx = indx + I;
        count = count + 1;
    end

    % Verbose
    if size(regions,1) ~= size(newregions,1)
        disp('Warning: overlapping regions detected and fixed in reject');
    end
end  % End of combineregions function

function res = issameevent(evt1, evt2)

    res = true;
    if isequal(evt1,evt2)
        return;
    else
        if isfield(evt1, 'type') && isnumeric(evt2.type) && ~isnumeric(evt1.type) 
            evt2.type = num2str(evt2.type);
            if isequal(evt1,evt2)
                return;
            end
        end
        if isfield(evt1, 'duration') && isfield(evt2, 'duration')
            if isnan(evt1.duration) && isnan(evt2.duration)
                evt1.duration = 1;
                evt2.duration = 1;
            end
            if abs(evt1.duration - evt2.duration) < 1e-10
                evt1.duration = 1;
                evt2.duration = 1;
            end
            if isequal(evt1,evt2)
                return;
            end
        end
        if isfield(evt1, 'latency') && isfield(evt2, 'latency')
            if abs(evt1.latency - evt2.latency) < 1e-10
                evt1.latency = 1;
                evt2.latency = 1;
            end
            if isequal(evt1,evt2)
                return;
            end
        end
    end
    res = false;
    return;
end  % End of issameevent function
