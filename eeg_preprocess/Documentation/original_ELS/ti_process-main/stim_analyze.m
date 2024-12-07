% stim_analysis.m
% v.0.0.0 - initial commit
% last ()
% use - functions to analyze stimulation data

classdef stim_analyze
    methods(Static)
        % given EEG data and stim information, calculate the power in pre,
        % stim, and post windows using pwelch; average across protocols
        % types; and find pow diff in conditions
        function dataOut = pre_post_stim_pow(EEG, dataOut, subj_sess_filepath, to_save, use185, interp)
            % load in stim metadata to be added to big dataOut struct
            dirs    = [dir(fullfile(EEG.filepath, 'processing', 'find_stim'))];
            dir_ind = find(contains({dirs(:).name}, 'stim_metadata.mat'));
            if isempty(dir_ind)
                error('stim_metadata.mat file not found')
            end
            load(fullfile(EEG.filepath, 'processing', 'find_stim', dirs(dir_ind).name))

            % create savepath for data
            if use185 == 1
                chan_str = '185';
            else
                chan_str = '256';
            end
            
            savepath = fullfile(EEG.filepath, 'analysis', 'pow', chan_str);
            if ~exist(savepath)
                mkdir(savepath)
            end
            dataOut.savepath = savepath;

            % analysis window names
            analyze_interval_names = {'pre', 'stim', 'post'};
            
            % time to analyze pre and post, in sec
            analyze_interval = 180;

            % windowing parameters
            win_size = 6;
            win_samp = round(win_size * EEG.srate);
            overlap = 0.90;
            overlap = (1 - overlap) * win_size;
            
            % freq bands ranges
            freqBands = struct();
            bandNames = {'ultraLow', 'delta', 'swa', 'theta', 'alpha', 'sigma', 'beta', 'gamma'};
            bandRange = {[0.5 2], [2 4], [0.5 4], [4 8], [8 12], [10 16], [12 25], [25 40]};
            for iBand = 1:numel(bandNames)
                freqBands(iBand).name = bandNames{iBand};
                freqBands(iBand).range = bandRange{iBand};
            end
            n_bands = size(freqBands,2);
            dataOut.freqInfo = freqBands;
            
            % channel handeling
            if use185 == 1
                load('inside185ch.mat')
                chans_to_rm = [];
                for iChan = 1:size(EEG.chanlocs,2)
                    chan_name = EEG.chanlocs(iChan).labels;
                    chan_num = split(chan_name, 'E');
                    chan_num = str2num(chan_num{2});
                    if isempty(find(ismember(inside185ch, chan_num)))
                        chans_to_rm = [chans_to_rm iChan];
                    end
                end
                
                fprintf('Removing %g channels to obtain inside185 \n', length(chans_to_rm));
                EEG = pop_select(EEG, 'nochannel', chans_to_rm);
            end

            if interp == 1
                if use185 ~= 1
                    error('Must set use185 equal to 1 to interpolate \n')
                end

                if strcmp(EEG.ref, 'average')
                    error('Must start with non-average referenced data to interpolate \n')
                end

                load('chanlocs257.mat')
                chans_present = [];
                for iChan = 1:size(EEG.chanlocs,2)
                    chan_name = EEG.chanlocs(iChan).labels;
                    chan_num = split(chan_name, 'E');
                    chan_num = str2num(chan_num{2});
                    if ~isempty(find(ismember(inside185ch, chan_num)))
                        chans_present = [chans_present chan_num];
                    end
                end
                
                chans_to_interp_inds = find(~ismember(inside185ch, chans_present));
                chans_to_interp = inside185ch(chans_to_interp_inds);

                fprintf('Interpolating %g channels \n', length(chans_to_interp));
                EEG = eeg_interp(EEG, chanlocs257(chans_to_interp));
            end

            % average ref EEG data if not already done
            if ~strcmp(EEG.ref, 'average')
                EEG = pop_reref(EEG, []);
            else
                fprintf('EEG already average referenced \n')
            end

            hc = handle_chans;
            stim_chans = hc.find_stim_chans(subj_sess_filepath);

            n_chans = EEG.nbchan;
            dataOut.chanInfo.n_chans = n_chans;
            dataOut.chanInfo.chanlocs = EEG.chanlocs;
            dataOut.chanInfo.stim_chans = stim_chans;
            dataOut.chanInfo.bad_chans = EEG.badchannels;
            
            % determine what type of protocol to analyze
            % NREM = 4 or REM = 5
            % do this based on the file that is loaded
            fn_str = split(EEG.setname, '.set');
            fn_str = split(fn_str{1}, '_');
            if sum(strcmp(fn_str, 'NREM')) >= 1
                fprintf('Found NREM in setname...analyzing NREM protocols (type 4) \n')
                fieldname = 'nrem';
                proto_type_to_analyze = 4;
            elseif sum(strcmp(fn_str, 'REM')) >= 1
                fprintf('Found REM in setname...analyzing REM protocols (type 5) \n')
                fieldname = 'rem';
                proto_type_to_analyze = 5;
            else
                error('Neither WAKE, NREM, nor REM found in EEG.setname, add to analyze that type of proto')
            end

            % find the stim time intervals for specific type of protos to
            % analyze
            starts = []; ends = []; abs_proto_n = [];
            for iEv = 1:size(EEG.event,2)
                if strcmp(EEG.event(iEv).type, 'stim start')
                    if EEG.event(iEv).proto_type == proto_type_to_analyze
                        starts = [starts (EEG.event(iEv).latency / EEG.srate)];
                        abs_proto_n = [abs_proto_n EEG.event(iEv).proto_ind];
                    end
                end
            
                if strcmp(EEG.event(iEv).type, 'stim end')
                    if EEG.event(iEv).proto_type == proto_type_to_analyze
                        ends = [ends (EEG.event(iEv).latency / EEG.srate)];
                    end
                end
            end
          
            if length(starts) ~= length(ends)
                error('Unequal number of starts and ends, review data to find missing event')
            end

            % for now, exclude protocols less than intended 210 s
            stim_time = ends - starts;
            short_stim_inds = find(stim_time < 180);
            if ~isempty(short_stim_inds)
                starts = starts(setdiff([1:length(starts)], short_stim_inds));
                ends = ends(setdiff([1:length(ends)], short_stim_inds));
                n_proto_exclude = length(short_stim_inds);
            else
                n_proto_exclude = 0;
            end
            fprintf('Excluded %g stim protocols with time <180 s \n', n_proto_exclude)

            n_protos = length(starts);

            fprintf('Found %g protocols of type %g \n', n_protos, proto_type_to_analyze)

            for iAnName = 1:numel(analyze_interval_names)
                analyze_interval_name = analyze_interval_names{iAnName};
                fprintf('\n')
            
                % preallocations for all proto data
                protos_include = []; abs_protos_include = []; 
                all_protos_t_total = []; all_protos_ss = [];
                all_pow = nan(n_protos, n_chans, 400, 1600);
                all_banded_pow = nan(n_protos, n_chans, 400, n_bands);
                all_psd = nan(n_protos, n_chans, 1600);
                all_banded_psd = nan(n_protos, n_chans, n_bands);

                for iProto = 1:n_protos
                    % count for abs_proto_n starts with first sleep protocol
                    dataOut.(fieldname).proto(iProto).abs_proto_n = abs_proto_n(iProto);

                    % init EEG data variable
                    eeg_for_pow = EEG.data;

                    fprintf('\n')
                    fprintf('Calculating power for protocol %g %s \n', iProto, analyze_interval_name)

                    if strcmp(analyze_interval_name, 'pre')
                        t_interval_start = starts(iProto) - analyze_interval;
                        t_interval_end = starts(iProto);

                        if iProto ~= 1
                            t_diff = starts(iProto) - ends(iProto-1);
                            if t_diff < analyze_interval * 2
                                t_missing = analyze_interval * 2 - t_diff;
                                t_to_blank = t_missing / 2;
                                t_end_blank = t_interval_start + t_to_blank;

                                fprintf('Heads up!! Protocol %g PRE overlaps with Protocol %g POST \n', iProto, iProto-1)
                                fprintf('Going to replace overlapping region with NaNs \n')
                                fprintf('First %g s will be replaced with NaN \n', t_to_blank)

                                eeg_for_pow(:, int32(t_interval_start * EEG.srate) : int32(t_end_blank * EEG.srate)) = NaN;

                            end
                        end

                    elseif strcmp(analyze_interval_name, 'stim')
                        % exclude the ramping interval (30 s total)
                        t_interval_start = starts(iProto) + 15;
                        t_interval_end = starts(iProto) + 15 + analyze_interval;
                    elseif strcmp(analyze_interval_name, 'post')
                        t_interval_start = ends(iProto);
                        t_interval_end = ends(iProto) + analyze_interval;
                        
                        if iProto ~= n_protos
                            t_diff = starts(iProto+1) - ends(iProto);
                            if t_diff < analyze_interval * 2
                                t_missing = analyze_interval * 2 - t_diff;
                                t_to_blank = t_missing / 2;
                                t_start_blank = t_interval_end - t_to_blank;

                                fprintf('Heads up!! Protocol %g POST overlaps with Protocol %g PRE \n', iProto, iProto+1)
                                fprintf('Going to replace overlapping region with NaNs \n')
                                fprintf('Last %g s will be replaced with NaN \n', t_to_blank)

                                eeg_for_pow(:, int32(t_start_blank * EEG.srate) : int32(t_interval_end * EEG.srate)) = NaN;

                            end
                        end
                    end

                    dataOut.(fieldname).proto(iProto).(analyze_interval_name).t_start = t_interval_start;
                    dataOut.(fieldname).proto(iProto).(analyze_interval_name).t_end = t_interval_end;

                    % check to see how much non-nan data is in interval
                    % determine sleep stages, t_total for protocol based on
                    % non-naned data
                    data_check = eeg_for_pow(1, int32(t_interval_start * EEG.srate) : int32(t_interval_end * EEG.srate));
                    num_non_nans = length(find(~isnan(data_check)));
                    dataOut.(fieldname).proto(iProto).(analyze_interval_name).t_total = (num_non_nans - 1) / EEG.srate;

                    nan_inds = find(isnan(eeg_for_pow(1,:)));
                    interval_sleep_stages = [];
                    for iEv = 1:size(EEG.event,2)
                        if (EEG.event(iEv).latency / EEG.srate) >= t_interval_start & (EEG.event(iEv).latency / EEG.srate) <= t_interval_end
                            if strcmp(EEG.event(iEv).type, 'Sleep Stage')
                                if ~ismember(nan_inds, EEG.event(iEv).latency)
                                    interval_sleep_stages = [interval_sleep_stages str2num(EEG.event(iEv).code)];
                                end
                            end
                        end
                    end
                    dataOut.(fieldname).proto(iProto).(analyze_interval_name).sleep_stages = interval_sleep_stages;

                    % slightly extend start and end to account for shortening by windowing
                    t_interval_start = t_interval_start - win_size / 2;
                    t_interval_end = t_interval_end + win_size / 2;

                    % create windows in time space
                    lb = [t_interval_start : overlap : t_interval_end - win_size];
                    ub = [t_interval_start + win_size: overlap : t_interval_end];
                    wins = [lb' ub'];
                    
                    % convert win time to samp space
                    wins_samp = wins * EEG.srate + 1;

                    % loop to grab windowed data and calc pow for each electrode
                    n_win = size(wins_samp,1);
                    n_freq = win_samp / 2 + 1;

                    pow = nan(n_chans, n_win, n_freq);
                    for iChan = 1:n_chans
                        for iWin = 1:n_win
                            % grab windowed data;
                            data_win = eeg_for_pow(iChan, int32(wins_samp(iWin,1)) : int32(wins_samp(iWin,2)));
                        
                            % detrend to attenuate super-low frequency artifacts in FFT (per MXC)
                            data_win = detrend(data_win);
                        
                            % create hann taper function
                            hann_win = 0.5 * (1 - cos(2 * pi * (0 : win_samp) / (win_samp)));

                            % account for occaisonal rounding issues
                            if length(data_win) ~= length(hann_win)
                                hann_win = hann(length(data_win));
                            end
                        
                            % apply taper
                            data_win = data_win .* hann_win;
                        
                            % take FFT
                            dfft = fft(data_win);
                        
                            % derive freqs
                            f = linspace(0, EEG.srate / 2, n_freq);
                            
                            % output pow
                            pow(iChan, iWin, :) = abs(dfft(1:n_freq)).^2;
                        end
                    end

                    % calculate psd, then dB scale
                    % units are: dB / Hz
                    psd = squeeze(mean(pow, 2, 'omitnan'));
                    psd = psd / (EEG.srate * sum(hann_win.^2));
                    psd(:,2:end-1) = psd(:,2:end-1) * 2;
                    psd = 10*log10(psd);

                    % dB scale pow data
                    % units are: dB
                    pow = 10*log10(pow);

                    % average pow, psd data for specific freq bands
                    banded_pow = nan(n_chans, n_win, n_bands);
                    banded_psd = nan(n_chans, n_bands);
                    for iBand = 1:n_bands
                        f_inds = find(f > freqBands(iBand).range(1) & f <= freqBands(iBand).range(2));
                        for iChan = 1:n_chans
                            banded_pow(iChan,:,iBand) = mean(pow(iChan,:,f_inds),3,'omitnan');
                            banded_psd(iChan,iBand) = mean(psd(iChan,f_inds),2,'omitnan');
                        end
                    end

                    % output data
                    dataOut.(fieldname).proto(iProto).(analyze_interval_name).eeg_data = eeg_for_pow(:, int32(wins_samp(1,1)) : int32(wins_samp(end,end)));
                    dataOut.(fieldname).proto(iProto).(analyze_interval_name).t_ax = mean(wins,2);
                    dataOut.(fieldname).proto(iProto).(analyze_interval_name).f_ax = f;
                    dataOut.(fieldname).proto(iProto).(analyze_interval_name).psd = psd;
                    dataOut.(fieldname).proto(iProto).(analyze_interval_name).pow = pow;
                    dataOut.(fieldname).proto(iProto).(analyze_interval_name).banded_psd = banded_psd;
                    dataOut.(fieldname).proto(iProto).(analyze_interval_name).banded_pow = banded_pow;
                    dataOut.(fieldname).proto(iProto).(analyze_interval_name).stim_data = ind_proto_metadata(abs_proto_n(iProto));

                    % decide whether to use or not at group level based on
                    % number of nans
                    num_nans = length(find(isnan(data_check)));
                    if num_nans >= int32(length(data_check) / 2)
                        fprintf('Excluding protocol %g from all %s due to >=50 percent NaNs \n', iProto, analyze_interval_name)
                        dataOut.(fieldname).proto(iProto).(analyze_interval_name).include = 0;
                    else
                        dataOut.(fieldname).proto(iProto).(analyze_interval_name).include = 1;
                        protos_include = [protos_include iProto];
                        abs_protos_include = [abs_protos_include abs_proto_n(iProto)];
                        all_protos_t_total = [all_protos_t_total (num_non_nans - 1) / EEG.srate];
                        all_protos_ss = [all_protos_ss interval_sleep_stages];
                        all_pow(iProto, :, 1:n_win, 1:n_freq) = pow;
                        all_banded_pow(iProto, :, 1:n_win, :) = banded_pow;
                        all_psd(iProto, :, 1:n_freq) = psd;
                        all_banded_psd(iProto, :, :) = banded_psd;
                    end
                end
                dataOut.(fieldname).all_protos.(analyze_interval_name).protos_include = protos_include;
                dataOut.(fieldname).all_protos.(analyze_interval_name).abs_protos_include = abs_protos_include;
                dataOut.(fieldname).all_protos.(analyze_interval_name).t_total = sum(all_protos_t_total);
                dataOut.(fieldname).all_protos.(analyze_interval_name).sleep_stages = unique(all_protos_ss);
                t_mu = mean(wins,2);
                dataOut.(fieldname).all_protos.(analyze_interval_name).t_ax = t_mu - t_mu(1);
                dataOut.(fieldname).all_protos.(analyze_interval_name).f_ax = f;
                dataOut.(fieldname).all_protos.(analyze_interval_name).pow = all_pow(:,:,1:n_win,1:n_freq);
                dataOut.(fieldname).all_protos.(analyze_interval_name).banded_pow = all_banded_pow(:,:,1:n_win,:);
                dataOut.(fieldname).all_protos.(analyze_interval_name).psd = all_psd(:,:,1:n_freq);
                dataOut.(fieldname).all_protos.(analyze_interval_name).banded_psd = all_banded_psd;
                dataOut.(fieldname).all_protos.(analyze_interval_name).stim_data = ind_proto_metadata(abs_protos_include);
            end

            % save dataOut as dataOutSave
            if to_save == 1
                dataOutSave = dataOut;

                % remove individual protocol information from what is saved
                if isfield(dataOutSave, 'nrem')
                    dataOutSave.nrem = rmfield(dataOutSave.nrem, 'proto');
                end

                if isfield(dataOutSave, 'rem')
                    dataOutSave.rem = rmfield(dataOutSave.rem, 'proto');
                end

                tic
                fprintf('saving %s \n', fullfile(dataOutSave.savepath, fieldname, 'group', sprintf('dataOutSave_%s_%s.mat', fieldname, chan_str)))
                if ~exist(fullfile(dataOutSave.savepath, fieldname, 'group'))
                    mkdir(fullfile(dataOutSave.savepath, fieldname, 'group'))
                end
                save(fullfile(dataOutSave.savepath, fieldname, 'group', sprintf('dataOutSave_%s_%s.mat', fieldname, chan_str)), 'dataOutSave','-v7.3')
                fprintf('Done! \n')
                toc
            end

        end %function
    end %methods
end %classdef