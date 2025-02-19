
function protocolPSD = protocol_psd(EEG, chanForPSD)
% protocol_psd - Computes and plots the power spectral density (PSD) 
% for each stimulation protocol.
%
% Syntax:
%   protocolPSD = protocol_psd(EEG, chanForPSD)
%
% Inputs:
%   EEG        - An EEGLAB EEG structure (preprocessed and containing 
%                "stim start" and "stim end" events).
%   chanForPSD - (Optional) The channel index to use for PSD computation.
%                Default is 1.
%
% Output:
%   protocolPSD - A structure array with one element per protocol containing:
%       .protocol      - Protocol number (starting at 1)
%       .psd           - PSD values (in dB) computed for that protocol
%       .freqs         - Frequency vector (Hz)
%       .startLatency  - Sample index of stim start
%       .endLatency    - Sample index of stim end
%
% This function extracts the segment of data between each "stim start" and 
% "stim end" event, computes its PSD using spectopo (with frequency range 
% restricted to 0.5–30 Hz), and then plots each protocol’s PSD in a subplot.
%
% Note: This code assumes that EEG.event is sorted by latency and that the 
% events occur in pairs: "stim start" followed by "stim end".

    if nargin < 2
        chanForPSD = 1;
    end

    % Sort events by latency (if not already sorted)
    [~, sortIdx] = sort([EEG.event.latency]);
    EEG.event = EEG.event(sortIdx);
    
    protocolPSD = [];
    protocolCount = 0;
    nEvents = length(EEG.event);
    k = 1;
    
    while k < nEvents
        if strcmpi(EEG.event(k).type, 'stim start') && ...
           (k+1 <= nEvents) && strcmpi(EEG.event(k+1).type, 'stim end')
       
            protocolCount = protocolCount + 1;
            startLatency = EEG.event(k).latency;
            endLatency   = EEG.event(k+1).latency;
            
            % Extract the segment from the specified channel.
            segment = double(EEG.data(chanForPSD, startLatency:endLatency));
            
            % Compute PSD using spectopo.
            % The second argument "0" tells spectopo to use the entire segment.
            [psd, freqs] = spectopo(segment, 0, EEG.srate, 'freqrange', [0.5 30], 'plot', 'off');
            
            protocolPSD(protocolCount).protocol     = protocolCount;
            protocolPSD(protocolCount).psd          = psd;
            protocolPSD(protocolCount).freqs        = freqs;
            protocolPSD(protocolCount).startLatency = startLatency;
            protocolPSD(protocolCount).endLatency   = endLatency;
        end
        k = k + 1;
    end

    % Plot the PSD for each protocol.
    if ~isempty(protocolPSD)
        nProt = length(protocolPSD);
        figure('Name','PSD for Each Stimulation Protocol');
        nRows = ceil(sqrt(nProt));
        nCols = ceil(nProt/nRows);
        for i = 1:nProt
            subplot(nRows, nCols, i);
            plot(protocolPSD(i).freqs, protocolPSD(i).psd, 'LineWidth', 1.5);
            xlabel('Frequency (Hz)');
            ylabel('Power (dB)');
            title(sprintf('Protocol %d', protocolPSD(i).protocol));
            xlim([0.5 30]);
            grid on;
        end
        sgtitle('PSD for Each Stimulation Protocol');
    else
        warning('No stimulation protocols found for PSD computation.');
    end
end
