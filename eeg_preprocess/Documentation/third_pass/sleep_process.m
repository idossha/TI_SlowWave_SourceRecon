% sleep_process.m
% Class to handle sleep-related EEG processing with logging.

classdef sleep_process
    methods(Static)
        % remove_spec_stage.m
        function EEG = remove_spec_stage(EEG, desired_stages, savestr, fid)
            log_message(fid, 'Retaining data staged as %g with NREM stages.', desired_stages);

            % Find sleep scored events not in desired stages
            rej_inds = [];
            for iEv = 1:length(EEG.event)
                if strcmp(EEG.event(iEv).type, 'Sleep Stage')
                    current_stage = str2double(EEG.event(iEv).code);
                    if ~ismember(current_stage, desired_stages)
                        t_start = EEG.event(iEv).latency;
                        t_end = EEG.event(iEv).latency + (30 * EEG.srate) - 1;
                        t_end = min(t_end, EEG.pnts); % Ensure t_end does not exceed data length
                        rej_inds = [rej_inds; [t_start, t_end]];
                        log_message(fid, 'Identified rejection region from sample %d to %d for Sleep Stage %d.', t_start, t_end, current_stage);
                    end
                end
            end

            % Perform NaN replacement using replace_region_wnan
            if ~isempty(rej_inds)
                EEG = replace_region_wnan(EEG, rej_inds, savestr, fid);
                log_message(fid, 'Replaced data in unwanted sleep stages with NaNs.');
            else
                log_message(fid, 'No unwanted sleep stages detected. No data replaced.');
            end
        end
    end
end
