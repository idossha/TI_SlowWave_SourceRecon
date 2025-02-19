
function plot_channels(EEG, trigData, siEnvIdx)
% plot_channels - Plot TRIG and SI-ENV channels with event markers.
%
% Syntax:
%   plot_channels(EEG, trigData, siEnvIdx)
%
% Inputs:
%   EEG      - The EEG structure containing .srate and .event.
%   trigData - The TRIG channel data (used for plotting and markers).
%   siEnvIdx - Index of the SI-ENV channel (from original EEG.chanlocs).
%
% Note:
%   This function uses EEG.extra_chans to extract the SI-ENV data.

    % Create a time vector.
    timeVec = (0:size(trigData, 2)-1) / EEG.srate;

    % Extract event latencies.
    stimStartIndices = [];
    stimEndIndices   = [];
    for k = 1:length(EEG.event)
        if strcmpi(EEG.event(k).type, 'stim start')
            stimStartIndices(end+1) = EEG.event(k).latency; %#ok<AGROW>
        elseif strcmpi(EEG.event(k).type, 'stim end')
            stimEndIndices(end+1) = EEG.event(k).latency;     %#ok<AGROW>
        end
    end
    timeStart = (stimStartIndices - 1) / EEG.srate;
    timeEnd   = (stimEndIndices - 1) / EEG.srate;

    % Attempt to extract SI-ENV data from EEG.extra_chans.
    siEnvData = [];
    if ~isempty(siEnvIdx) && isfield(EEG, 'extra_chans')
        extraLabels = {EEG.extra_chans.chanlocs.labels};
        siEnvExtraIdx = find(strcmpi(extraLabels, 'SI-ENV'));
        if ~isempty(siEnvExtraIdx)
            siEnvData = EEG.extra_chans.data(siEnvExtraIdx, :);
        end
    end

    % Create the plot.
    figure;
    hold on;
    % Plot TRIG channel.
    plot(timeVec, trigData, 'k', 'DisplayName', 'TRIG Channel');
    % Plot SI-ENV channel (if available).
    if ~isempty(siEnvData)
        plot(timeVec, siEnvData, 'b', 'DisplayName', 'SI-ENV Channel');
    end
    % Overlay event markers.
    plot(timeStart, trigData(stimStartIndices), 'g*', 'MarkerSize', 10, 'DisplayName', 'Stim Start');
    plot(timeEnd, trigData(stimEndIndices), 'r*', 'MarkerSize', 10, 'DisplayName', 'Stim End');
    xlabel('Time (s)');
    ylabel('Amplitude (µV)');
    title('TRIG & SI-ENV Channels with Stimulation Markers');
    legend('show');
    hold off;
end
