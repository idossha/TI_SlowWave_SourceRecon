I need your help with this EEG preprocessing project.

Below you will see a few matlab scripts that I will need you to modify and probably add functionality to based on my insturctions, the flow of processing, and data structure.


The EEG structure is the following:

EEG = 

  struct with fields:

                setname: 'Strength_102_N1_forICA.set'
               filename: 'Strength_102_N1_forICA.set'
               filepath: '/Users/idohaber/Desktop/EEG/102/N1'
                subject: ''
                  group: ''
              condition: ''
                session: []
               comments: ''
                 nbchan: 186
                 trials: 1
                   pnts: 7199455
                  srate: 500
                   xmin: 0
                   xmax: 1.4399e+04
                  times: [0 2.0000 4.0000 6.0000 8.0000 10.0000 12.0000 14.0000 16.0000 18.0000 20.0000 22.0000 24.0000 … ] (1×7199455 double)
                   data: [186×7199455 single]
                 icaact: []
                icawinv: []
              icasphere: []
             icaweights: []
            icachansind: []
               chanlocs: [1×186 struct]
             urchanlocs: [1×260 struct]
               chaninfo: [1×1 struct]
                    ref: 'E257'
                  event: [1×520 struct]
                urevent: []
       eventdescription: {''  ''  ''  ''  ''  ''  ''  ''  ''  ''  ''  ''  ''  ''  ''  ''}
                  epoch: []
       epochdescription: {}
                 reject: [1×1 struct]
                  stats: [1×1 struct]
               specdata: []
             specicaact: []
             splinefile: ''
          icasplinefile: ''
                 dipfit: []
                history: '↵EEG.etc.eeglabvers = '2024.0'; % this tracks which version of EEGLAB is being used, you may ignore it'
                  saved: 'justloaded'
                    etc: [1×1 struct]
                    run: []
                    roi: []
       csc_event_labels: {6×3 cell}
            csc_montage: [1×1 struct]
      csc_marked_trials: 0
    csc_hidden_channels: [20 39 34 50 49 57 56 70 71 73 74 75 51 94 93 92 91 84 83 116 117 123 135 134 133 147 146 145 148 … ] (1×67 double)
            badchannels: {1×77 cell}
              stageData: [1×1 struct]
             bad_epochs: [190×4205×2 logical]
                datfile: 'Strength_102_N1_filt_bc_we_rmwk_noZ_rmepoch_rmbs_bc.fdt'

The event field is:

 EEG.event

ans = 

  1×520 struct array with fields:

    description
    begintime
    classid
    code
    duration
    label
    relativebegintime
    sourcedevice
    name
    tracktype
    latency
    type
    mffkeys
    mffkeysbackup
    proto_ind
    proto_type

EEG.etc

ans = 

  struct with fields:

       eeglabvers: '2024.0'
            info1: [1×1 struct]
            info2: [1×1 struct]
         timezone: '-05:00'
       mffversion: 3
           layout: [1×1 struct]
          subject: [1×1 struct]
    recordingtime: 7.3934e+05
        startTime: 23:06:55
      timeIndices: [1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 … ] (1×12616490 double)
      actualTimes: [23:06:55    23:06:55    23:06:55    23:06:55    23:06:55    23:06:55    23:06:55    …    ] (1×12616490 datetime)
        startDate: '2024-03-26'
       rejRegions: [930×2 double]
          saveNaN: 0
      keepIndices: [960001 960002 960003 960004 960005 960006 960007 960008 960009 960010 960011 960012 960013 960014 … ] (1×7276490 double)

the main flow is as follow:

1. i need to load a .set file, generate a `stim_report`.

2. I want you to identify NaN segments, and also find if there are stim events, `stim start` or `stim end` events. If these types of events are within a NaN segment, I would need to move them to the first non-NaN index after the end of the NaN segement. Then I would like to reject all NaN segments probably using `eeg_eegrej`.

3. After that, I want you to identify segments of undesired sleep stages and remove them from the data. Meaning, reject those regions with `eeg_eegrej`. I only want to keep sleep stages 2 and 3. Sleep stage values can be found under EEG.event.code. There should be a sleep stage every 20 to 30 seconds or so. 

4. I want the new pruned data strcutre to be named EEG_ICA (instead of EEG as the original) and save the file (.set file) as subject_night_forICA

5. Lastly, i want to generate a `stim_report` for the pruned data. 


Important note:
`stim report` should be a .csv

`stim report` should include: event type, proto_type, latency (s), actualTime, Moved(boolean), shift(s), and sleep stage

Example:

Event_Type	Proto_Type	Latency_original(s)    latency_new(s)		Actual_Time	      Shift_Distance_sec	Moved	Sleep_Stage
stim start   	4	    4400.666	         2400.666          	    23:47:47	        200              yes	       2
stim end     	4	    4616.742	         4616.742	            23:51:23            0	             no             3


The main idea I need you to understand, is that I need to know the original time (both global time and latency in sec) and also the new latency of the events due to the removal of segments from the data. 

I want you to create a main pipeline call prep_ICA.m and a number of helper scripts based on the functionality required. 

Below you will see the current script to modify or get inspired from..

Scripts:

prep_for_ICA.m:

```matlab
% File Handling
% file directory
experiment_path = '/Users/idohaber/Desktop/EEG';

addpath('/Users/idohaber/Documents/MATLAB/eeglab2024.0/')
addpath('/Users/idohaber/Desktop/ti_process-main/')
eeglab nogui

% select subj, session, file_extension
whichSubj = '102';
whichSess = 'N1';
file_ext = '_bc.set';

% find and load files
subj_sess_filepath = fullfile(experiment_path, whichSubj, whichSess);
dirs = dir(subj_sess_filepath);
dir_ind = find(contains({dirs(:).name}, file_ext));
if isempty(dir_ind)
    error('file not found \n')
end
EEG = pop_loadset(fullfile(subj_sess_filepath, dirs(dir_ind).name));

% remove data from unwanted sleep stages
% keep only NREM here
slp = sleep_process;
% reminder: remove_spec_stage(EEG, stages, savestr)
EEG = slp.remove_spec_stage(EEG, [0 1 4 5], '_NREM');

% % (optional) keep only PRE, STIM, POST NREM stimulations
% % find starts, ends, types for each protocol
% starts = []; ends = [];
% for iEv = 1:size(EEG.event,2)
%     if strcmp(EEG.event(iEv).type, 'stim start') & EEG.event(iEv).proto_type == 4
%         starts = [starts EEG.event(iEv).latency - (180 * EEG.srate)];
%     end
% 
%     if strcmp(EEG.event(iEv).type, 'stim end') & EEG.event(iEv).proto_type == 4
%         ends = [ends EEG.event(iEv).latency + (180 * EEG.srate)];
%     end
% end
% 
% % check that number of starts = number of ends
% if length(starts) ~= length(ends)
%     error('Number of stim starts does not match number of stim ends \n')
% end
% 
% % define rej_inds as those not in the above
% rej_starts = [1 ends+1];
% rej_ends = [starts-1 EEG.pnts];
% 
% % perform NaN replacement
% cd = clean_data;     
% EEG = cd.replace_region_wnan(EEG, [rej_starts' rej_ends'], '_stimOnly');

% remove NaNs 
EEG.etc.saveNaN = 0;
EEG = eeg_eegrej(EEG, EEG.etc.rejRegions);

% check event markers stim start == stim end
% find starts, ends, types for each protocol
starts = []; ends = [];
for iEv = 1:size(EEG.event,2)
    if strcmp(EEG.event(iEv).type, 'stim start') & EEG.event(iEv).proto_type == 4
        starts = [starts EEG.event(iEv).latency];
    end

    if strcmp(EEG.event(iEv).type, 'stim end') & EEG.event(iEv).proto_type == 4
        ends = [ends EEG.event(iEv).latency];
    end
end

% check that number of starts = number of ends
if length(starts) ~= length(ends)
    fprintf('\n')
    fprintf('!!HEADS UP!! Number of stim starts does not match number of stim ends \n')
    fprintf('\n')
end

% add event marker for missing stim starts and/or stim ends

% save as _forICA.set
new_fileName = ['Strength_' whichSubj '_' whichSess '_forICA.set'];
EEG.filename = new_fileName;
EEG.setname = new_fileName;
fprintf('Saving %s \n', new_fileName);
pop_saveset(EEG, fullfile(EEG.filepath, new_fileName));

```


eeg_eegrej.m:

```matlab

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

```


sleep_process.m:

```matlab

% sleep_process.m
% v.0.0.0 - initial commit
% last ()
% use - functions to process aspects of sleep in EEG data

classdef sleep_process
    methods(Static)
        % remove data corresponding to a specific sleep stage
        function EEG = remove_spec_stage(EEG, unwanted_stages, savestr)

            fprintf('Replacing data staged as %g with NaN \n', unwanted_stages)

            % find sleep scored events with values in unwanted stages
            % add next 30 sec of data to indexes to be removed
            rej_inds = [];
            for iEv = 1:size(EEG.event,2)
                if strcmp(EEG.event(iEv).type, 'Sleep Stage')
                    if sum(ismember(unwanted_stages, str2num(EEG.event(iEv).code)))
                        t_start = EEG.event(iEv).latency;
                        t_end = EEG.event(iEv).latency + (30 * EEG.srate) - 1;
            
                        rej_inds = [rej_inds; [t_start t_end]];
                    end
                end
            end

            % perform NaN replacement
            cd = clean_data;
            EEG = cd.replace_region_wnan(EEG, rej_inds, savestr)
        end

        % make figure with information about stages and stim timings
        function timings_figs(EEG, whichSubj, whichSess)

            % create savepath for figures
            savepath = fullfile(EEG.filepath, 'analysis', 'sleep');
            if ~exist(savepath)
                mkdir(savepath)
            end

            % grab all sleep stage, stim events
            all_ss = []; ss_latencies = []; ss_nan = [];
            for iEv = 1:size(EEG.event,2)
                if strcmp(EEG.event(iEv).type, 'Sleep Stage')
                    all_ss = [all_ss str2num(EEG.event(iEv).code)];
                    ss_latencies = [ss_latencies (EEG.event(iEv).latency / EEG.srate)];

                    if isnan(EEG.data(1, EEG.event(iEv).latency))
                        ss_nan = [ss_nan 1];
                    else
                        ss_nan = [ss_nan 0];
                    end
                end
            end
            
            starts = []; ends = [];
            pre_starts = []; pre_ends = [];
            post_starts = []; post_ends = [];
            for iEv = 1:size(EEG.event,2)
                if strcmp(EEG.event(iEv).type, 'stim start')
                    starts = [starts (EEG.event(iEv).latency / EEG.srate)];
                    pre_starts = [pre_starts (EEG.event(iEv).latency / EEG.srate) - 180];
                    pre_ends = [pre_ends (EEG.event(iEv).latency / EEG.srate)];
                end
            
                if strcmp(EEG.event(iEv).type, 'stim end')
                    ends = [ends (EEG.event(iEv).latency / EEG.srate)];
                    post_starts = [post_starts (EEG.event(iEv).latency / EEG.srate)];
                    post_ends = [post_ends (EEG.event(iEv).latency / EEG.srate) + 180];
                end
            end

            for i = 1:2
                figure(3); clf
                set(gcf, 'Position', [12 422 1828 450], 'Visible', 'off')
                hold on
                plot(ss_latencies / 60 / 60, -all_ss, 'color', 'k', 'linewidth', 1.5)
                if i == 2
                    plot(ss_latencies(logical(ss_nan)) / 60 / 60, -all_ss(logical(ss_nan)), 'o', 'markerfacecolor', 'r')
                end
                for iProto = 1:length(starts)
                    plot([pre_starts(iProto):1:pre_ends(iProto)] / 60 / 60, ones(length([pre_starts(iProto):1:pre_ends(iProto)])) * 1, 'color', [40 40 230]/255, 'linewidth', 10)
                    plot([starts(iProto):1:ends(iProto)] / 60 / 60, ones(length([starts(iProto):1:ends(iProto)])) * 1, 'color', [230 40 40]/255, 'linewidth', 10)
                    plot([post_starts(iProto):1:post_ends(iProto)] / 60 / 60, ones(length([post_starts(iProto):1:post_ends(iProto)])) * 1, 'color', [40 230 40]/255, 'linewidth', 10)
                end
    
                ylim([-5 2])
                yticks([-5:1:2])
                xlim([0 ss_latencies(end) / 60 / 60])
                xlabel('Time (hours)')
                ylabel('Sleep Stage')
                yticklabels({'', 'REM', 'NREM3', 'NREM2', 'NREM1', 'WAKE', ''})
                sgtitle(sprintf('Subject %s Session %s \n', whichSubj, whichSess))
                fontsize(gcf, 18, 'points')
                if i == 1
                    savestr = sprintf('%02d_hypno_and_stim.png', i);
                else
                    savestr = sprintf('%02d_hypno_and_stim_clean.png', i);
                end
                fprintf('saving %s \n', fullfile(savepath, savestr))
                saveas(gcf, fullfile(savepath, savestr))
                close
            end

        end %function
    end %methods
end %classdef

```
