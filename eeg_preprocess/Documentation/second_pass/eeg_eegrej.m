
% To be placed under eeglab/functions/popfunc/eeg_eegrej.m
% File: eeg_eegrej.m

function [EEG, com] = eeg_eegrej( EEG, regions)

com = '';
if nargin < 2
    help eeg_eegrej;
    return;
end
if nargin<3
    probadded = [];
end
if isempty(regions)
    return;
end

% Ramon on 5/29/2014 for bug 1619
if size(regions,2) > 2
    regions = sortrows(regions,3);
else
    regions = sortrows(regions,1);
end

% Handle regions from eegplot
if size(regions,2) > 2, regions = regions(:, 3:4); end
regions = combineregions(regions);

% ELS added - quick detour to replace data in rejection regions with NaNs
% but otherwise keep the rest of the file intact, then save it
if isfield(EEG.etc, 'saveNaN') && EEG.etc.saveNaN == 1
    reject = zeros(1, EEG.pnts);
    for i = 1:size(regions,1)
        reject(regions(i,1):regions(i,2)) = 1;
    end
    EEG.data(:,reject == 1) = NaN;
    % keep track of rejection regions for repeat cleaning
    if isfield(EEG.etc, 'rejRegions') && ~isempty(EEG.etc.rejRegions)
        EEG.etc.rejRegions = [EEG.etc.rejRegions; regions];
    else
        EEG.etc.rejRegions = regions;
    end
    regions = EEG.etc.rejRegions;

    % rename and save data
    new_fileName = split(EEG.filename, '.set');
    new_fileName = strcat(new_fileName{1}, '_rmbs.set');

    % rename set
    EEG.filename = new_fileName;
    EEG.setname = new_fileName;

    % save data
    fprintf('Saving rejected data %s \n', new_fileName);
    pop_saveset(EEG, fullfile(EEG.filepath, new_fileName));
else

    % use rejection regions from prior rejections
    if isfield(EEG.etc, 'rejRegions') && ~isempty(EEG.etc.rejRegions)
        EEG.etc.rejRegions = [EEG.etc.rejRegions; regions];
        regions = EEG.etc.rejRegions;
    end

    % Remove events within regions
    if ~isempty(EEG.event) && isfield(EEG.event, 'latency')
        allEventLatencies = [ EEG.event.latency ];
        allEventFlag      = false(1,length(allEventLatencies));
        for iRegion = 1:size(regions,1)
            allEventFlag = allEventFlag | ( allEventLatencies >= regions(iRegion,1) & allEventLatencies <= regions(iRegion,2));
        end
        boundaryIndices = eeg_findboundaries(EEG);
        allEventFlag(boundaryIndices) = false; % do not remove boundary events
        EEG.event(allEventFlag) = [];
    end

    % Reject data
    [EEG.data, EEG.xmax, event2, boundevents] = eegrej( EEG.data, regions, EEG.xmax-EEG.xmin, EEG.event);
    oldEEGpnts = EEG.pnts;
    EEG.pnts   = size(EEG.data,2);
    EEG.xmax   = EEG.xmax+EEG.xmin;

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
    else
        fprintf('Warning: EEG.etc.actualTimes or EEG.etc.timeIndices not found. Cannot update these fields.\n');
    end
    % --- End Modification ---

    % Add boundary events
    [ EEG.event ] = eeg_insertbound(EEG.event, oldEEGpnts, regions);
    EEG = eeg_checkset(EEG, 'eventconsistency');
    if ~isempty(EEG.event) && EEG.trials == 1 && EEG.event(end).latency-0.5 > EEG.pnts
        EEG.event(end) = []; % remove last event if necessary
    end

    % Sort events by latency
    [~, sortIdx] = sort([EEG.event.latency]);
    EEG.event = EEG.event(sortIdx);

    % Double check event latencies
    eeglab_options;
    warnflag = false;
    if isfield(EEG.event, 'latency') && length(EEG.event) < 3000
        alllats = [ EEG.event.latency ];
        if ~isempty(event2)
            otherlatencies = [event2.latency];
            if ~isequal(alllats, otherlatencies)
                warning([ 'Discrepancy when checking event latencies using legacy method.' 10 'Often the discrepancy is minor and the new method (used here) is correct' 10 'Still, try to reproduce the problem and send us your dataset' ]);
                warnflag = true;
            end
        end
    end
end

com = sprintf('EEG = eeg_eegrej( EEG, %s);', vararg2str({ regions })); 

% Combine regions if necessary
function newregions = combineregions(regions)
% 9/1/2014 RMC
regions = sortrows(sort(regions,2)); % Sorting regions
allreg = [ regions(:,1)' regions(:,2)'; ones(1,numel(regions(:,1))) -ones(1,numel(regions(:,2)')) ].';
allreg = sortrows(allreg,1); % Sort all start and stop points (column 1),

mboundary = cumsum(allreg(:,2)); % Rationale: regions will start always with 1 and close with 0, since starts=1 end=-1
indx = 0; count = 1;

while indx ~= length(allreg) 
    newregions(count,1) = allreg(indx+1,1);
    [tmp,I]= min(abs(mboundary(indx+1:end)));
    newregions(count,2) = allreg(I + indx,1);
    indx = indx + I ;
    count = count+1;
end

% Verbose
if size(regions,1) ~= size(newregions,1)
    disp('Warning: overlapping regions detected and fixed in eeg_eegrej');
end

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
        if abs( evt1.duration - evt2.duration) < 1e-10
            evt1.duration = 1;
            evt2.duration = 1;
        end
        if isequal(evt1,evt2)
            return;
        end
    end
    if isfield(evt1, 'latency') && isfield(evt2, 'latency')
        if abs( evt1.latency - evt2.latency) < 1e-10
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
