
function [EEG, extraIdx] = separate_extra_channels(EEG, trigIdx, siEnvIdx)
% separate_extra_channels - Move TRIG and SI-ENV channels to EEG.extra_chans.
%
% Syntax:
%   [EEG, extraIdx] = separate_extra_channels(EEG, trigIdx, siEnvIdx)
%
% Inputs:
%   EEG     - The EEG structure.
%   trigIdx - Index of the TRIG channel.
%   siEnvIdx- Index of the SI-ENV channel.
%
% Outputs:
%   EEG      - Updated EEG structure with extra channels removed.
%   extraIdx - Indices of the extra channels that were separated.

    % Combine TRIG and SI-ENV indices.
    extraIdx = unique([trigIdx, siEnvIdx]);

    % Save the extra channels.
    EEG.extra_chans.data     = EEG.data(extraIdx, :);
    EEG.extra_chans.chanlocs = EEG.chanlocs(extraIdx);

    % Remove extra channels from the main EEG data.
    keepIdx = setdiff(1:size(EEG.data, 1), extraIdx);
    EEG.data     = EEG.data(keepIdx, :);
    EEG.chanlocs = EEG.chanlocs(keepIdx);
    EEG.nbchan   = size(EEG.data, 1);
end
