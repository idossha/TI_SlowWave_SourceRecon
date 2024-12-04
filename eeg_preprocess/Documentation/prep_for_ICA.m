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
