function timing_figs_with_nan(EEG, whichSubj, whichSess, fid, NaNSegments, desired_proto_type)
    % TIMING_FIGS_WITH_NAN Generates a hypnogram with stim events and highlights NaN segments.
    %
    % Parameters:
    %   EEG                 - EEGLAB EEG structure
    %   whichSubj           - Subject ID (string)
    %   whichSess           - Session/Night ID (string)
    %   fid                 - File identifier for logging (opened with fopen)
    %   NaNSegments         - Nx2 matrix where each row represents [startIdx, endIdx] of NaN segments
    %   desired_proto_type  - The proto_type(s) of stim events to highlight

    % If NaNSegments is not provided, identify them
    if nargin < 5 || isempty(NaNSegments)
        [NaNSegments, ~, ~, ~] = identify_nan_segs(EEG, fid);
    end

    % Create savepath for figures
    savepath = fullfile(EEG.filepath, 'analysis', 'sleep');
    if ~exist(savepath, 'dir')
        mkdir(savepath);
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

    % Grab stim events with desired_proto_type
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
    fig = figure;
    set(fig, 'Position', [100 100 1200 600], 'Visible', 'off');
    hold on;

    % Plot NaN segments as shaded purple regions
    if ~isempty(NaNSegments)
        for i = 1:size(NaNSegments, 1)
            start_time_hr = NaNSegments(i, 1) / EEG.srate / 3600;
            end_time_hr = NaNSegments(i, 2) / EEG.srate / 3600;

            y_lower = -5;
            y_upper = 2;
            patch([start_time_hr end_time_hr end_time_hr start_time_hr], ...
                  [y_lower y_lower y_upper y_upper], ...
                  [0.5 0 0.5], ... % purple
                  'FaceAlpha', 0.3, ...
                  'EdgeColor', 'none', ...
                  'HandleVisibility', 'off');
        end
        nan_patch = patch([0 0 0 0], [0 0 0 0], [0.5 0 0.5], ...
                          'FaceAlpha', 0.3, 'EdgeColor', 'none', ...
                          'DisplayName', 'NaN Segment');
    end

    % Plot sleep stages
    plot_handle_ss = plot(ss_latencies / 3600, -all_ss, 'k', 'LineWidth', 1.5, 'DisplayName', 'Sleep Stage');

    % Plot stim start events as green stars
    if ~isempty(stim_start_times)
        plot_handle_stim_start = plot(stim_start_times / 3600, zeros(size(stim_start_times)), ...
                                      'g*', 'MarkerSize', 8, 'DisplayName', 'Stim Start');
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
        plot_handle_stim_end = plot(stim_end_times / 3600, zeros(size(stim_end_times)), ...
                                    'r*', 'MarkerSize', 8, 'DisplayName', 'Stim End');
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

    % Determine x-axis limits based on sleep stage latencies and NaN segments
    if ~isempty(NaNSegments)
        nan_end_times_sec = NaNSegments(:,2) / EEG.srate;
        max_time_sec = max([max(ss_latencies), max(nan_end_times_sec)]);
    else
        max_time_sec = max(ss_latencies);
    end
    max_time_hr = ceil(max_time_sec / 3600);
    xlim([0 max_time_hr]);

    % Create a single legend
    if ~isempty(NaNSegments)
        legend_entries = [plot_handle_ss];
        legend_labels = {'Sleep Stage'};
        if exist('plot_handle_stim_start', 'var')
            legend_entries(end+1) = plot_handle_stim_start;
            legend_labels{end+1} = 'Stim Start';
        end
        if exist('plot_handle_stim_end', 'var')
            legend_entries(end+1) = plot_handle_stim_end;
            legend_labels{end+1} = 'Stim End';
        end
        legend_entries(end+1) = nan_patch;
        legend_labels{end+1} = 'NaN Segment';
        legend(legend_entries, legend_labels, 'Location', 'best');
    else
        % Handle legend in case no NaN segments
        if ~isempty(stim_start_times) && ~isempty(stim_end_times)
            legend({'Sleep Stage', 'Stim Start', 'Stim End'}, 'Location', 'best');
        elseif ~isempty(stim_start_times)
            legend({'Sleep Stage', 'Stim Start'}, 'Location', 'best');
        elseif ~isempty(stim_end_times)
            legend({'Sleep Stage', 'Stim End'}, 'Location', 'best');
        else
            legend({'Sleep Stage'}, 'Location', 'best');
        end
    end

    ylim([-5 2]);
    yticks([-5:1:2]);
    yticklabels({'', 'REM', 'NREM3', 'NREM2', 'NREM1', 'WAKE', ''});
    xlabel('Time (hours)', 'FontSize', 12);
    ylabel('Sleep Stage', 'FontSize', 12);
    title(sprintf('Subject %s Session %s Struct %s', whichSubj, whichSess, inputname(1)), 'FontSize', 16);
    grid on;

    % Include EEG structure name in the saved figure name
    eeg_struct_name = inputname(1); % Gets the variable name of EEG structure
    savestr = sprintf('Stim_Events_%s_%s_%s.png', whichSubj, whichSess, eeg_struct_name);
    fprintf('Saving figure as %s\n', fullfile(savepath, savestr));
    saveas(gcf, fullfile(savepath, savestr));

    % Close the figure
    close;

end %function
