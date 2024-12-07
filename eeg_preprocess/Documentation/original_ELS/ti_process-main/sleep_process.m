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
