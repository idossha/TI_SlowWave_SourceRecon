% timing_figs_with_nan.m
% Creates a figure with sleep stages, stim events, and highlights NaN segments in EEG data.

function timing_figs_with_nan(EEG, whichSubj, whichSess, fid, NaNSegments, desired_proto_type)
    % timing_figs_with_nan - Generates a hypnogram with stim events and highlights NaN segments.
    %
    % Syntax: timing_figs_with_nan(EEG, whichSubj, whichSess, fid, NaNSegments)
    %
    % Inputs:
    %   EEG         - EEG structure containing data, events, sampling rate, and filepath.
    %   whichSubj   - Subject identifier (string).
    %   whichSess   - Session identifier (string).
    %   fid         - File identifier for logging (opened with fopen).
    %   NaNSegments - (Optional) Nx2 matrix where each row represents [startIdx, endIdx] of NaN segments.
    %
    % Outputs:
    %   None (figure is saved to disk).

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

    % Grab all stim start and stim end events with desired_proto_type
    stim_start_times = [];
    stim_end_times = [];
    for iEv = 1:length(EEG.event)
        if (strcmp(EEG.event(iEv).type, 'stim start') || strcmp(EEG.event(iEv).type, 'stim end')) && ...
           isfield(EEG.event(iEv), 'proto_type') && EEG.event(iEv).proto_type == desired_proto_type
            if strcmp(EEG.event(iEv).type, 'stim start')
                stim_start_times = [stim_start_times (EEG.event(iEv).latency / EEG.srate)];
            elseif strcmp(EEG.event(iEv).type, 'stim end')
                stim_end_times = [stim_end_times (EEG.event(iEv).latency / EEG.srate)];
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
            % Convert sample indices to time in hours
            start_time_hr = NaNSegments(i, 1) / EEG.srate / 3600;
            end_time_hr = NaNSegments(i, 2) / EEG.srate / 3600;

            % Define y-limits for the shaded area
            y_lower = -5;
            y_upper = 2;

            % Create a patch (shaded area) for the NaN segment
            patch_handle = patch([start_time_hr end_time_hr end_time_hr start_time_hr], ...
                                 [y_lower y_lower y_upper y_upper], ...
                                 [0.5 0 0.5], ... % RGB for purple
                                 'FaceAlpha', 0.3, ... % Transparency
                                 'EdgeColor', 'none', ...
                                 'HandleVisibility', 'off'); % Hide from legend
        end
        % Create a single legend entry for NaN Segments
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
    end

    % Plot stim end events as red stars
    if ~isempty(stim_end_times)
        plot_handle_stim_end = plot(stim_end_times / 3600, zeros(size(stim_end_times)), ...
                                    'r*', 'MarkerSize', 8, 'DisplayName', 'Stim End');
    end



    % Determine x-axis limits based on sleep stage latencies and NaN segments
    if ~isempty(NaNSegments)
        % Convert end indices of NaN segments to time in seconds
        nan_end_times_sec = NaNSegments(:,2) / EEG.srate;
        % Maximum time from sleep stages and NaN segments
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
        if ~isempty(stim_start_times)
            legend_entries(end+1) = plot_handle_stim_start;
            legend_labels{end+1} = 'Stim Start';
        end
        if ~isempty(stim_end_times)
            legend_entries(end+1) = plot_handle_stim_end;
            legend_labels{end+1} = 'Stim End';
        end
        legend_entries(end+1) = nan_patch;
        legend_labels{end+1} = 'NaN Segment';
        legend(legend_entries, legend_labels, 'Location', 'best');
    else
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

    % Configure plot aesthetics
    ylim([-5 2]);
    yticks([-5:1:2]);
    yticklabels({'', 'REM', 'NREM3', 'NREM2', 'NREM1', 'WAKE', ''});
    xlabel('Time (hours)', 'FontSize', 12);
    ylabel('Sleep Stage', 'FontSize', 12);
    legend('Location' , 'northeast')
    title(sprintf('Subject %s Session %s Struct  %s', whichSubj, whichSess, inputname(1)), 'FontSize', 16);
    grid on;

    % Include EEG structure name in the saved figure name with '_with_NaNs'
    eeg_struct_name = inputname(1); % Gets the variable name of EEG structure
    savestr = sprintf('Stim_Events_%s_%s_%s_with_NaNs.png', whichSubj, whichSess, eeg_struct_name);
    fprintf('Saving figure as %s\n', fullfile(savepath, savestr));
    saveas(fig, fullfile(savepath, savestr));

    % Close the figure
    close(fig);
end