% clean_data.m
% v.0.0.0 - initial commit
% last ()
% use - functions to clean data during eeg processing

classdef clean_data
    methods(Static)
        % given EEG data, remove bad channels
        function EEG = remove_bad_chans(EEG, auto, check_spec, chans, overwrite, to_save)
            % if _bc.set file exists and no overwrite, load that file
            new_fileName = split(EEG.filename, '.set');
            new_fileName = strcat(new_fileName{1}, '_bc.set');

            if ~exist(fullfile(EEG.filepath, new_fileName)) || overwrite == 1
                if auto
                    fprintf('\n')
                    fprintf('Removing bad chans automatically for %s \n', EEG.filename);

                    % if previously converted to 185 (from 256) below indices are incorrect; throw error
                    if numel(EEG.chanlocs) == 185
                        error('auto mode only available for 256 chans...remove chans manually or do not convert to 185')
                    else
                        chan_inds = [45 64 73 81 82 91 92 101:103 111:113 119 120 121 122 133:137 145 146 156 157 165:168 174:176 186:188 199 200 208:210 216 217 229 233 246 247 256];
                    end
                elseif ~isempty(chans)
                    fprintf('\n')
                    fprintf('Removing bad chans automatically for %s \n', EEG.filename);

                    if isa(chans, 'double')
                        chan_inds = chans;
                    elseif isa(chans, 'cell')
                        % determine ind for chan name
                        chan_inds = [];
                        for iChan = 1:numel(chans)
                            ind = find(ismember({EEG.chanlocs(:).labels}, chans{iChan}));
                            if ~isempty(ind)
                                fprintf('Found channel %s to remove \n', chans{iChan})
                                chan_inds = [chan_inds ind];
                            else
                                fprintf('Could not find channel %s to remove \n', chans{iChan})
                            end
                        end
                    else
                        error('chans variable class not recognized, use double or cell')
                    end
                else
                    fprintf('\n')
                    fprintf('Remove bad chans manually for %s \n', EEG.filename);
                    fprintf('In GUI, scroll over time and click on channels you want to remove \n')
                    fprintf('Close CSC EEG plotter GUI when done')
                    fprintf('\n')

                    % Plot channel data
                    EEG = csc_eeg_plotter(EEG);

                    chan_inds = EEG.csc_hidden_channels;
                    close all
                end

                if check_spec
                    % Plot spectral data
                    pop_spectopo(EEG, 1, [], 'EEG' , 'winsize' , 512, 'plot', 'on', 'freqrange',[1 50],'electrodes','on', 'overlap', 0);
                    fprintf('\n')
                    fprintf('Inspect the power spectrum, click on traces that look bad for chan number \n')
                    fprintf('Type and enter the following: bad_chans = [chans chosen], eg., [1 2:5 10] \n')
                    fprintf('Type dbcont when done \n')
                    fprintf('\n')
                    keyboard;

                    chan_inds = [chan_inds bad_chans];
                    close all
                end

                % sort for neatness
                chan_inds = sort(chan_inds);

                % Keep track of bad channels by name not index
                if ~isfield(EEG, 'badchannels')
                    EEG.badchannels = {EEG.chanlocs(chan_inds).labels};
                else
                    EEG.badchannels = [EEG.badchannels {EEG.chanlocs(chan_inds).labels}];
                end

                % Remove bad channels (do this step once to avoid indexing issues)
                EEG = pop_select(EEG, 'nochannel', chan_inds);

                if to_save == 1
                    % rename set
                    if overwrite == 1
                        EEG.filename = EEG.filename;
                        EEG.setname = EEG.setname;
    
                        % save data
                        fprintf('Saving data with bad channels removed %s \n', EEG.filename);
                        pop_saveset(EEG, fullfile(EEG.filepath, EEG.filename));
                    else
                        EEG.filename = new_fileName;
                        EEG.setname = new_fileName;
    
                        % save data
                        fprintf('Saving data with bad channels removed %s \n', new_fileName);
                        pop_saveset(EEG, fullfile(EEG.filepath, new_fileName));
                    end
                end


            else
                fprintf('%s exists, loading .set file \n', new_fileName);
                EEG = pop_loadset(fullfile(EEG.filepath, new_fileName));
            end
            fprintf('\n');
        end %function

        % given EEG data and time interval indices, replace selected regions with NaNs
        function EEG = replace_region_wnan(EEG, regions, savestr)
            % loop over rejection indices and replace those regions with
            % NaN
            reject = zeros(1, EEG.pnts);
            for i = 1:size(regions,1)
                reject(regions(i,1):regions(i,2)) = 1;
            end
            EEG.data(:,reject == 1) = NaN;

            % keep track of rejection regions 
            EEG.etc.rejRegions = [EEG.etc.rejRegions; regions];
        
            % rename and save data
            new_fileName = split(EEG.filename, '.set');
            new_fileName = strcat(new_fileName{1}, savestr, '.set');
        
            % rename set
            EEG.filename = new_fileName;
            EEG.setname = new_fileName;
        
            % save data
            fprintf('Saving data with NaN %s \n', new_fileName);
            pop_saveset(EEG, fullfile(EEG.filepath, new_fileName));
        end

        % given EEG data with EEG.bad_epochs field, replace rejected epochs
        % with NaN
        function EEG = rej_epochs_from_csc_rej(EEG, winlen)

            % results from artifact rejection are kept in EEG.bad_epochs variable
            % loop over channels to find bad epochs for each channel
            xchan_rej_epoch_inds = [];
            for iChan = 1:EEG.nbchan
                delta_rej_epoch_inds = find(EEG.bad_epochs(iChan,:,1) == 1);
                gamma_rej_epoch_inds = find(EEG.bad_epochs(iChan,:,2) == 1);
                xchan_rej_epoch_inds = [xchan_rej_epoch_inds delta_rej_epoch_inds gamma_rej_epoch_inds];
            end
            
            % find unique epochs across channels
            epochs_to_reject = unique(xchan_rej_epoch_inds);
            
            fprintf('%g percent of data will be rejected \n', (length(epochs_to_reject) / size(EEG.bad_epochs,2)) * 100)
            resp = input('OK to proceed? (y/n) : ', 's');
            if resp == 'y'
                % prepare epochs to reject
                nEpo = floor(EEG.pnts / EEG.srate / winlen);
                starts = []; ends = [];
                for iEpoch = 1:nEpo+1
                    starts = [starts (iEpoch-1) * winlen * EEG.srate + 1];
                    ends = [ends (iEpoch-1) * winlen * EEG.srate + winlen * EEG.srate];
                end
                ranges = [starts' ends'];
                
                % since data is not always perfectly divisible by winlen, very last epoch
                % is excluded in the above loop
                % so, if second to last epoch is in those to reject, also assume you want
                % to reject last epoch
                if ismember(size(EEG.bad_epochs,2), epochs_to_reject)
                    epochs_to_reject = [epochs_to_reject size(EEG.bad_epochs,2)];
                end
                
                % finalize indices to reject
                rej_inds = ranges(epochs_to_reject,:);
    
                % perform NaN replacement
                cd = clean_data;     
                EEG = cd.replace_region_wnan(EEG, rej_inds, '_rmepoch');
            else
                error('Repeat csc_artifact_rejection as needed \n')
            end
        end

        % given EEG data, remove bad segments, prompt user to look within
        % specfic time periods
        function EEG = man_remove_bad_segments(EEG)

            % find starts, ends, types for each protocol
            starts = []; ends = []; types = [];
            for iEv = 1:size(EEG.event,2)
                if strcmp(EEG.event(iEv).type, 'stim start') & EEG.event(iEv).proto_type ~= 0 & EEG.event(iEv).proto_type ~= 1
                    starts = [starts (EEG.event(iEv).latency / EEG.srate) - 180];
                    types = [types EEG.event(iEv).proto_type];
                end
            
                if strcmp(EEG.event(iEv).type, 'stim end') & EEG.event(iEv).proto_type ~= 0 & EEG.event(iEv).proto_type ~= 1
                    ends = [ends (EEG.event(iEv).latency / EEG.srate) + 180];
                end
            end
            n_proto = length(starts);
            proto_lst = [1:n_proto];

            fprintf('Scan data in these time regions of interest: \n')
            t_protos = [starts' ends' types' proto_lst']

            pop_eegplot(EEG, 1, 0, 1);

       end %function

       % plot power values on topoplot to identify bad channels
       function bad_chans_topoplot(EEG, winlen)
            % average ref for visualization only
            if ~strcmp(EEG.ref, 'average')
                EEGtmp = pop_reref(EEG, []);
            else
                EEGtmp = EEG;
            end
        
            % windowing settings
            window = winlen * EEGtmp.srate;
            overlap = 0.75 * window;
            nfft = 2^nextpow2(window);
            
            % freq bands ranges
            freqBands = struct();
            bandNames = {'ultraLow', 'delta', 'theta', 'alpha', 'beta', 'gamma'};
            bandRange = {[0.5 2], [2 4], [4 8], [8 12], [12 25], [25 40]};
            
            for iBand = 1:numel(bandNames)
                freqBands(iBand).name = bandNames{iBand};
                freqBands(iBand).range = bandRange{iBand};
            end
            
            n_bands = size(freqBands,2);
            n_chans = EEGtmp.nbchan;
            
            % include only non-NaN data
            nan_inds = isnan(EEGtmp.data(1,:));
            non_nan_data = EEGtmp.data(:,~nan_inds);
            
            % look at a subset of ~evenly spaced intervals (looking at all data is too slow)
            t_interval = 5; % in min
            n_intervals_to_analyze = 15; % 1 5 min interval takes ~10s
            t_interval_samp = t_interval * 60 * EEGtmp.srate; 
            n_intervals = floor(size(non_nan_data,2) / t_interval_samp);
            interval_step_size = floor(n_intervals / n_intervals_to_analyze);
            interval_inds = [1:interval_step_size:n_intervals];
            interval_samps = reshape([1:n_intervals * t_interval_samp], t_interval_samp, n_intervals);
            inds = interval_samps(:,interval_inds);
            inds = reshape(inds, 1, size(inds,1) * size(inds,2));
    
            %inds = 1:6001;
            
            fprintf('Calculating power for each channel... \n')
            
            pow = nan(n_chans, nfft / 2 + 1);
            % calc power for each chan
            for iChan = 1:n_chans
                [p, f] = pwelch(non_nan_data(iChan, inds), window, overlap, nfft, EEGtmp.srate);
                pow(iChan,:) = 10*log10(p);
            end
            
            % pow bands
            pow_bands = nan(n_chans, n_bands);
            for iBand = 1:n_bands
                inds = find(f > freqBands(iBand).range(1) & f <= freqBands(iBand).range(2));
                for iChan = 1:n_chans
                    % mean f over proto, then mean f over band
                    pow_bands(iChan,iBand) = mean(pow(iChan,inds),2);
                end
            end
            
            % plot topoplots
            figure(3); clf;
            set(gcf, 'Position', [1 300 1800 429], 'Visible', 'on')
            for iBand = 1:n_bands
                subplot_tight(1, n_bands, iBand, 0.01);
            
                % subtract mean to normalize xFreq
                topodata = (pow_bands(:,iBand) - mean(pow_bands(:,iBand))) / std(pow_bands(:,iBand));
                topoplot(topodata, EEGtmp.chanlocs, 'electrodes', 'numbers', 'style', 'both', 'maplimits', [-3 3]);
            
                title(sprintf('%s', freqBands(iBand).name))
            end
            fontsize(gcf,10,'points')
       end
       
       % identify bad channels based on topoplot pow
       function EEG = remove_bad_chans_topo(EEG)
           EEGtmp = EEG;

           % repeat topoplot pow until usr satisfied
           all_chan_names = {};
           while 1
               cd = clean_data;
               cd.bad_chans_topoplot(EEGtmp, 6)

               for iChan = 1:numel(EEG.chanlocs)
                   fprintf('INDEX: %g <> NAME: %s \n', iChan, EEG.chanlocs(iChan).labels)
               end

               resp = input('ACCEPT? (y/n) : ', 's');
               if resp == 'y'
                   break
               else
                   fprintf('\n')
                   fprintf('Zoom in on channels and choose those you want to remove \n')
                   fprintf('Type and enter the following: bad_chans = [chans chosen], eg., [1 2:5 10] \n')
                   fprintf('Type dbcont when done \n')
                   fprintf('\n')
                   keyboard;
                   close

                   chan_inds = bad_chans;
                   for iChan = 1:length(chan_inds)
                       fprintf('Removing chan %s \n', EEGtmp.chanlocs(chan_inds(iChan)).labels)
                   end
                   all_chan_names = [all_chan_names {EEGtmp.chanlocs(chan_inds).labels}];

                   EEGtmp = pop_select(EEGtmp, 'nochannel', chan_inds);
               end
           end
            
           % remove all chans at once

           % check that this saves properly(!)

           if ~isempty(all_chan_names)
               EEG = cd.remove_bad_chans(EEG, 0, 0, all_chan_names, 0, 1);
           end
           close

       end

    end %methods
end %classdef
