
function [trigIdx, siEnvIdx] = identify_channels(EEG)
% identify_channels - Locate TRIG and SI-ENV channels by label.
%
% Syntax:
%   [trigIdx, siEnvIdx] = identify_channels(EEG)
%
% Inputs:
%   EEG - The EEG structure with fields .chanlocs and .data.
%
% Outputs:
%   trigIdx - Index (or indices) for the TRIG channel.
%   siEnvIdx - Index (or indices) for the SI-ENV channel.

    chanLabels = {EEG.chanlocs.labels};
    trigIdx = find(strcmpi(chanLabels, 'TRIG'));
    siEnvIdx = find(strcmpi(chanLabels, 'SI-ENV'));

    if isempty(trigIdx)
        error('TRIG channel not found in EEG.chanlocs.');
    end
    if isempty(siEnvIdx)
        warning('SI-ENV channel not found in EEG.chanlocs. Only the TRIG channel will be plotted.');
    end
end
