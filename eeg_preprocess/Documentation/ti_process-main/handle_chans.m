% handle_chans.m
% v.0.0.0 - initial commit
% last ()
% use - functions to handle channel data

classdef handle_chans
    methods(Static)
        % remove channels with a specific name
        function EEG = rm_spec_chans(EEG, chan_names)
            % determine ind for chan name
            chan_inds = [];
            for iChan = 1:numel(chan_names)
                ind = find(ismember({EEG.chanlocs(:).labels}, chan_names{iChan}));
                if ~isempty(ind)
                    fprintf('Removing channel %s \n', chan_names{iChan})
                    chan_inds = [chan_inds ind];
                else
                    fprintf('Could not find channel %s \n', chan_names{iChan})
                end
            end

            % Keep track of bad channels by name not index
            EEG.badchannels = [EEG.badchannels {EEG.chanlocs(chan_inds).labels}];
            EEG = pop_select(EEG, 'nochannel', chan_inds);
        end %function

        % read text file and return stimulating electrode locations
        function chans = find_stim_chans(path_to_stim)
            dirs = [dir(fullfile(path_to_stim, 'stim'))];
            dir_ind = find(contains({dirs(:).name}, 'elec_locs.txt'));
            if isempty(dir_ind)
                error('elec_locs.txt file not found')
            end

            % load info in elec_locs.txt file found
            fileID  = fopen(fullfile(path_to_stim, 'stim', dirs(dir_ind).name), 'r');
            lines   = textscan(fileID, '%s', 'Delimiter', '\n'); % Read each line of the entire txt file into a cell array
            lines   = lines{1};  % Extract the data from the cell array; now lines{i} is the i-th line of the file
            fclose(fileID); % Close the file

            chans = {};
            fprintf('\n')
            fprintf('Stimulating electrodes as follows: \n')
            for iLine = 1:numel(lines)
                str = lines{iLine};
                if ~isempty(str)
                    str_split = split(str, ' ');
                    chans = [chans str_split{2}];
                    fprintf('%s \n', str_split{2})
                end
            end
        end

        % plot bad channels removed
        function plot_rm_chans(EEG, subj_sess_filepath)
            savepath = fullfile(EEG.filepath, 'processing');
            if ~exist(savepath)
                mkdir(savepath)
            end
            
            load('chanlocs257.mat')
            % figure out what channels are missing from original 257
            all_chans = {chanlocs257(:).labels};
            chans_present = {EEG.chanlocs(:).labels};
            chans_missing = all_chans(~ismember(all_chans, chans_present));

            % reconcile this with what is in EEG.badchannels
            % if do not match, prompt user to see if they want to add to
            % list
            missing_chans = chans_missing(~ismember(chans_missing, EEG.badchannels));
            fprintf('\n')
            if ~isempty(missing_chans)
                fprintf('Following chans have been removed but are missing from EEG.badchannels \n')
                for iChan = 1:numel(missing_chans)
                    fprintf('%s \n', missing_chans{iChan})
                end
                resp = input('Add these chans to EEG.badchannels? (y/n) : ', 's');
                if resp == 'y'
                    EEG.badchannels = [EEG.badchannels missing_chans];
                    fprintf('Channels ADDED to EEG.badchannels \n')
                else
                    fprintf('Channels NOT ADDED to EEG.badchannels \n')
                end
            else
                fprintf('Yay! EEG.badchannels and chans missing from 257 match! \n')
            end

            % plot removed channels based on what is in EEG.badchannels
            inds = find(ismember(all_chans, EEG.badchannels));
            d = zeros(1,numel(all_chans));
            d(inds) = 1;

            % overlay stimulating electrode locations
            hc = handle_chans;
            stim_chans = hc.find_stim_chans(subj_sess_filepath);
            stim_inds = find(ismember(all_chans, stim_chans));
            ds = zeros(1,numel(all_chans));
            ds(stim_inds) = 1;

            figure(2); clf
            hold on
            set(gcf, 'Position', [20 400 600 500], 'Visible', 'off')
            axis off
            subplot_tight(1,1,1,0.01)
            topoplot(d, chanlocs257, 'style', 'blank', 'emarkercolors', {[1 0 0]});
            topoplot(ds, chanlocs257, 'style', 'blank', 'emarkercolors', {[0 0 1]});
            fontsize(gcf, 16, 'points')
            sgtitle(sprintf('Channels Removed N=%g', length(inds)))
            savestr = 'chans_removed.png';
            fprintf('saving %s \n', fullfile(savepath, savestr))
            saveas(gcf, fullfile(savepath, savestr))
            close
        end %function
                      
    end %methods
end %classdef
