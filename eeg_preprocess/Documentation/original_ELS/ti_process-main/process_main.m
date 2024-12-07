% process_main.m
% v.0.0.0 - initial commit
% last ()
% use - calls functions for processing DARPA STRENGTHEN data

% add path to dependencies: eeglab, csc-eeg-tools, ti
addpath(genpath('C:\Users\elschaeffer\sandbox\els_eeg_process\ti_process'))
addpath(genpath('C:\Users\elschaeffer\sandbox\eeglab2024.0'))
addpath(genpath('C:\Users\elschaeffer\sandbox\csc-eeg-tools-develop'))

% note: eeg_eegrej.m will need to be replaced with modified version
% settings
% window length for fft calculation and epoch-ing
winlen = 6; % in sec

% (1) File Handling
% file directory
experiment_path = 'C:\Users\elschaeffer\repo\ti\STRENGTHEN';
dirItems = dir(experiment_path);

% select subjs and sessions
whichSubj = '101';
whichSess = 'N1';

% loop over dir items in exp path
for dirIdx = 1:length(dirItems)
    % check if subj is present
    if strcmp(dirItems(dirIdx).name, whichSubj)
        subDirItems = dir(fullfile(experiment_path, whichSubj));
        for subDirIdx = 1:length(subDirItems)
            if strcmp(subDirItems(subDirIdx).name, whichSess)
                fprintf('\n')
                fprintf('Starting to process SUBJECT %s, SESSION %s \n', whichSubj, whichSess)
                fprintf('\n')

                subj_sess_filepath = fullfile(experiment_path, whichSubj, whichSess);
                
                % check to see if ind_proto_metadata.mat file present
                % if not, parse individual .mat files output from python script
                stp = stim_process;
                stp.parse_stim_pkl_metadata(subj_sess_filepath)

                % check to see if EEG data for this subj/session is loaded
                % if so, skip loading steps
                if exist('EEG') == 1
                    if isfield(EEG, 'filepath')
                        if contains(EEG.filepath, subj_sess_filepath) & contains(EEG.filename, strcat('Strength_', whichSubj, '_', whichSess))
                            fprintf('.set file already loaded in workspace \n')
                            fprintf('%s \n', fullfile(EEG.filepath, EEG.filename))
                        end
                    end
                else
                    % check to see if initial .set file exists in path
                    % if so, load it
                    % if not, look for .mff and convert if present
                    init_set_filename = strcat('Strength_', whichSubj, '_', whichSess, '.set');
                    if exist(fullfile(subj_sess_filepath, init_set_filename)) == 2
                        fprintf('%s file found, loading now \n', init_set_filename)
                        EEG = pop_loadset(fullfile(subj_sess_filepath, init_set_filename))
                    else
                        fprintf('%s not found, looking for .mff instead \n', init_set_filename)
                        mff_filenames = dir(fullfile(subj_sess_filepath, '*.mff'));
                        if isempty(mff_filenames)
                            error('No .mff file found in directory %s \n', subj_sess_filepath) 
                        elseif size(mff_filenames,1) > 1
                            error('More than 1 .mff file found; choose correct file')
                        else
                            fprintf('%s found, converting to .set \n', mff_filenames(1).name)

                            hf = handle_files;
                            new_fileName = strcat('Strength_', whichSubj, '_', whichSess, '.set');
                            EEG = hf.convert_mff_to_set(subj_sess_filepath, mff_filenames(1).name, new_fileName);
                        end 
                    end
                end
            end
        end
    end
end

%% (2) Filter EEG data
% High pass, then low pass
eb = eeg_basics;
EEG = eb.apply_filters(EEG);

%% (3) Remove bad channels, including non-trig PIB channels
hc = handle_chans;
chans = hc.find_stim_chans(subj_sess_filepath);

cd = clean_data;
% reminder: remove_bad_chans(EEG, auto, check_spec, chans, overwrite, to_save)
% perform manual bad channel rejection
EEG = cd.remove_bad_chans(EEG, 0, 0, [], 0, 1);

% remove non-trig PIB channels if not done in above step
EEG = cd.remove_bad_chans(EEG, 0, 0, {'EOG', 'EOG_2', 'CHIN', 'ECG'}, 1, 1);

%% (4) Incorporate sleep stage information
he = handle_events;
EEG = he.add_sleep_stage(EEG);

%% (5) Find and align stimulation protocols 
stp = stim_process;
ind_proto_metadata = stp.find_and_align_protos(EEG);

%% (6) Incorporate stim protocol information
he = handle_events;
EEG = he.add_stim_timings(EEG, ind_proto_metadata);

%% (7) Remove trig channels
cd = clean_data;
EEG = cd.remove_bad_chans(EEG, 0, 0, {'SI-ENV', 'TRIG'}, 1, 1);

%% (8) Begin removing bad segments by removing wake
slp = sleep_process;
% reminder: remove_spec_stage(EEG, stages, savestr)
EEG = slp.remove_spec_stage(EEG, [0 5], '_rmwk');

%% (9) Remove impedance check protocols
stp = stim_process;
EEG = stp.remove_z_checks(EEG);

%% (10) Perform manual epoch rejection
% call csc_artifact_rejection GUI and allow user to manually
% set thresholds for epoch rejection
EEG = csc_artifact_rejection(EEG, 'wispic', 'epoch_length', winlen);

%% (11) Remove rejected epochs 
cd = clean_data;
EEG = cd.rej_epochs_from_csc_rej(EEG, winlen);

%% (12) Manually inspect and remove bad segments
% only during specific times listed, replace with NaN
cd = clean_data;

EEG.etc.saveNaN = 1;
EEG = cd.man_remove_bad_segments(EEG);

%% (12.1) Load the rmbs.set file 
% eeglab gui file-handling otherwise results in files saved in wrong
% directory
dirs = [dir(fullfile(subj_sess_filepath))];
dir_ind = find(contains({dirs(:).name}, '_rmbs.set'));
if isempty(dir_ind)
    error('_rmbs.set file not found')
end

EEG = pop_loadset(fullfile(subj_sess_filepath, dirs(dir_ind).name))

%% (13) Remove additional bad channels based on topography
cd = clean_data;
EEG = cd.remove_bad_chans_topo(EEG);

%% (14) Plot all removed channels
hc = handle_chans;
hc.plot_rm_chans(EEG, subj_sess_filepath)

%% (15) Power Analysis - 256 channels, no interp
% grab only NREM data
close all
slp = sleep_process;
EEGtmp = EEG;

% reminder: remove_spec_stage(EEG, stages, savestr)
EEG_NREM = slp.remove_spec_stage(EEGtmp, [0 1 4 5], '_NREM');

sta = stim_analyze;
% initialize dataOut struct and perform power analysis
dataOut = struct();
dataOut.subj = whichSubj;
dataOut.sess = whichSess;

% reminder: dataOut = pre_post_stim_pow(EEG, dataOut, subj_sess_filepath, to_save, use185, interp)
dataOut = sta.pre_post_stim_pow(EEG_NREM, dataOut, subj_sess_filepath, 0, 0, 0);

% plot stim summary for protocols in analysis
stp = stim_process;
stp.stim_summary_figs(EEG, dataOut, 'nrem')

% plot analysis results
pp = pow_plots;
pp.pow_results(dataOut, 'nrem', 'individual');
pp.pow_results(dataOut, 'nrem', 'group');
clear EEG_NREM

close all
slp = sleep_process;
EEGtmp = EEG;

% grab only REM data
% reminder: remove_spec_stage(EEG, stages, savestr)
EEG_REM = slp.remove_spec_stage(EEGtmp, [0 1 2 3 5], '_REM');

sta = stim_analyze;
% initialize dataOut struct and perform power analysis
dataOut = struct();
dataOut.subj = whichSubj;
dataOut.sess = whichSess;

% reminder: dataOut = pre_post_stim_pow(EEG, dataOut, subj_sess_filepath, to_save, use185, interp)
dataOut = sta.pre_post_stim_pow(EEG_REM, dataOut, subj_sess_filepath, 0, 0, 0);

stp = stim_process;
% plot stim summary for protocols in analysis
stp.stim_summary_figs(EEG, dataOut, 'rem')

% plot analysis results
pp = pow_plots;
pp.pow_results(dataOut, 'rem', 'individual');
pp.pow_results(dataOut, 'rem', 'group');
clear EEG_REM

close all
% (16) Power Analysis - 185 channels with interp
% grab only NREM data
slp = sleep_process;
EEGtmp = EEG;

% reminder: remove_spec_stage(EEG, stages, savestr)
EEG_NREM = slp.remove_spec_stage(EEGtmp, [0 1 4 5], '_NREM');

sta = stim_analyze;
% initialize dataOut struct and perform power analysis
dataOut = struct();
dataOut.subj = whichSubj;
dataOut.sess = whichSess;

% reminder: dataOut = pre_post_stim_pow(EEG, dataOut, subj_sess_filepath, to_save, use185, interp)
dataOut = sta.pre_post_stim_pow(EEG_NREM, dataOut, subj_sess_filepath, 1, 1, 1);

% plot analysis results
pp = pow_plots; 
pp.pow_results(dataOut, 'nrem', 'group');
clear EEG_NREM

close all
% grab only REM data
slp = sleep_process;
EEGtmp = EEG;

% reminder: remove_spec_stage(EEG, stages, savestr)
EEG_REM = slp.remove_spec_stage(EEGtmp, [0 1 2 3 5], '_REM');

sta = stim_analyze;
% initialize dataOut struct and perform power analysis
dataOut = struct();
dataOut.subj = whichSubj;
dataOut.sess = whichSess;

% reminder: dataOut = pre_post_stim_pow(EEG, dataOut, subj_sess_filepath, to_save, use185, interp)
dataOut = sta.pre_post_stim_pow(EEG_REM, dataOut, subj_sess_filepath, 1, 1, 1);

% plot analysis results
pp = pow_plots; 
pp.pow_results(dataOut, 'rem', 'group');
clear EEG_REM

% (17) Generate hypnogram with stim timing
close all
slp = sleep_process;
slp.timings_figs(EEG, whichSubj, whichSess);

%% (18) Place figures in subject's powerpoint

%% (19) Review powerpoint

%% (20) Remove non-essential files generated
% (!) ONLY RUN WHEN FINISHED PROCESSING
hf = handle_files;
hf.remove_processing_files(subj_sess_filepath)

%% (21) Update Data Processing Log
