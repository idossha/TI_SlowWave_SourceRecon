function timings_figs(EEG, whichSubj, whichSess, desired_proto_type)
    % TIMINGS_FIGS Plots event timings for EEG data without NaN segments.
    %
    % Parameters:
    %   EEG               - EEGLAB EEG structure
    %   whichSubj         - Subject ID (string)
    %   whichSess         - Session/Night ID (string)
    %   desired_proto_type - The proto_type(s) of stim events to highlight

    % Create savepath for figures
    savepath = fullfile(EEG.filepath, 'output', 'adaptation_step');
    if ~exist(savepath, 'dir')
        mkdir(savepath)
    end

    % Grab all sleep stage events
    all_ss = [];
    ss_latencies = [];
    ss_nan = [];
    for iEv = 1:length(EEG.event)
        if strcmp(EEG.event(iEv).type, 'Sleep Stage')
            sleep_stage_code = str2double(EEG.event(iEv).code);
            all_ss = [all_ss sleep_stage_code];
            ss_latencies = [ss_latencies (EEG.event(iEv).latency / EEG.srate)];

            if isnan(EEG.data(1, EEG.event(iEv).latency))
                ss_nan = [ss_nan 1];
            else
                ss_nan = [ss_nan 0];
            end
        end
    end

    % Grab all stim start and stim end events with desired_proto_type
    stim_start_times = [];
    stim_start_evIdx = [];
    stim_end_times = [];
    stim_end_evIdx = [];
    for iEv = 1:length(EEG.event)
        if (strcmp(EEG.event(iEv).type, 'stim start') || strcmp(EEG.event(iEv).type, 'stim end')) && ...
                isfield(EEG.event(iEv), 'proto_type') && ...
                ismember(EEG.event(iEv).proto_type, desired_proto_type)
            if strcmp(EEG.event(iEv).type, 'stim start')
                stim_start_times = [stim_start_times (EEG.event(iEv).latency / EEG.srate)];
                stim_start_evIdx = [stim_start_evIdx iEv];
            elseif strcmp(EEG.event(iEv).type, 'stim end')
                stim_end_times = [stim_end_times (EEG.event(iEv).latency / EEG.srate)];
                stim_end_evIdx = [stim_end_evIdx iEv];
            end
        end
    end

    % Create figure
    figure;
    set(gcf, 'Position', [100 100 1200 600], 'Visible', 'off');
    hold on;

    % Plot sleep stages
    plot(ss_latencies / 3600, -all_ss, 'k', 'LineWidth', 1.5, 'DisplayName', 'Sleep Stages');

    % Plot stim start events as green stars
    if ~isempty(stim_start_times)
        plot(stim_start_times / 3600, zeros(size(stim_start_times)), 'g*', 'MarkerSize', 8, 'DisplayName', 'Stim Start');
        % Annotate with protocol numbers if available
        for iIdx = 1:length(stim_start_evIdx)
            evIdx = stim_start_evIdx(iIdx);
            if isfield(EEG.event(evIdx), 'protocol_num')
                txt = sprintf('P%d', EEG.event(evIdx).protocol_num);
                text((EEG.event(evIdx).latency / EEG.srate) / 3600, 0, txt, ...
                    'VerticalAlignment', 'bottom', 'HorizontalAlignment', 'left', ...
                    'Color', 'k', 'FontWeight', 'bold', 'FontSize', 8);
            end
        end
    end

    % Plot stim end events as red stars
    if ~isempty(stim_end_times)
        plot(stim_end_times / 3600, zeros(size(stim_end_times)), 'r*', 'MarkerSize', 8, 'DisplayName', 'Stim End');
        % Annotate with protocol numbers if available
        for iIdx = 1:length(stim_end_evIdx)
            evIdx = stim_end_evIdx(iIdx);
            if isfield(EEG.event(evIdx), 'protocol_num')
                txt = sprintf('P%d', EEG.event(evIdx).protocol_num);
                text((EEG.event(evIdx).latency / EEG.srate) / 3600, 0, txt, ...
                    'VerticalAlignment', 'top', 'HorizontalAlignment', 'left', ...
                    'Color', 'k', 'FontWeight', 'bold', 'FontSize', 8);
            end
        end
    end

    % Configure plot aesthetics
    ylim([-5 2]);
    yticks([-5:1:2]);
    xlim([0 ceil(max(ss_latencies) / 3600)]);
    xlabel('Time (hours)', 'FontSize', 12);
    ylabel('Sleep Stage', 'FontSize', 12);
    yticklabels({'', 'REM', 'NREM3', 'NREM2', 'NREM1', 'WAKE', ''});
    title(sprintf('Subject %s Session %s Struct %s', whichSubj, whichSess, inputname(1)), 'FontSize', 16);

    legend('Location', 'northeast'); 
    grid on;

    % Include EEG structure name in the saved figure name
    eeg_struct_name = inputname(1); % Gets the variable name of EEG structure
    savestr = sprintf('Stim_Events_%s_%s_%s.png', whichSubj, whichSess, eeg_struct_name);
    fprintf('Saving figure as %s\n', fullfile(savepath, savestr));
    saveas(gcf, fullfile(savepath, savestr));

    % Close the figure
    close;

end %function
