
function protocolTopo = protocol_topo_1Hz(EEG)
% protocol_topo_1Hz - Computes and plots topographic maps of 1 Hz power for each stimulation protocol.
%
% Syntax:
%   protocolTopo = protocol_topo_1Hz(EEG)
%
% For each stimulation protocol (data between a "stim start" and "stim end" event),
% this function computes the 1 Hz power for each channel using pwelch, and then plots
% a scalp topography using EEGLAB's topoplot.
%
% Output:
%   protocolTopo - A structure array with one element per protocol containing:
%       .protocol      - Protocol number (starting at 1)
%       .power1Hz      - Vector (nChans x 1) of power at ~1 Hz for each channel
%       .startLatency  - Sample index of stim start
%       .endLatency    - Sample index of stim end
%
% Note: This function assumes that EEG.event contains paired "stim start" and "stim end" events,
% and that EEG.chanlocs is correctly defined.

    % Ensure events are sorted by latency.
    [~, sortIdx] = sort([EEG.event.latency]);
    EEG.event = EEG.event(sortIdx);
    
    protocolTopo = [];
    protocolCount = 0;
    nEvents = length(EEG.event);
    k = 1;
    
    % Loop through events to identify protocol pairs.
    while k < nEvents
        if strcmpi(EEG.event(k).type, 'stim start') && (k+1 <= nEvents) && strcmpi(EEG.event(k+1).type, 'stim end')
            protocolCount = protocolCount + 1;
            startLatency = EEG.event(k).latency;
            endLatency   = EEG.event(k+1).latency;
            
            % For each channel, compute the power at ~1 Hz within the protocol segment.
            nChans = EEG.nbchan;
            power1Hz = zeros(nChans, 1);
            segmentLength = endLatency - startLatency + 1;
            
            % Use a window size for pwelch; if the segment is too short, use its length.
            win = min(256, segmentLength);
            overlap = round(win/2);
            nfft = win;
            
            for ch = 1:nChans
                segment = double(EEG.data(ch, startLatency:endLatency));
                [P, f] = pwelch(segment, win, overlap, nfft, EEG.srate);
                % Find the frequency bin closest to 1 Hz.
                [~, idx] = min(abs(f - 1));
                power1Hz(ch) = P(idx);
            end
            
            protocolTopo(protocolCount).protocol = protocolCount;
            protocolTopo(protocolCount).power1Hz = power1Hz;
            protocolTopo(protocolCount).startLatency = startLatency;
            protocolTopo(protocolCount).endLatency = endLatency;
        end
        k = k + 1;
    end
    
    % Plot a topographic map for each protocol.
    if ~isempty(protocolTopo)
        nProt = length(protocolTopo);
        figure('Name','Topographic Maps of 1 Hz Power for Each Protocol');
        nRows = ceil(sqrt(nProt));
        nCols = ceil(nProt / nRows);
        for i = 1:nProt
            subplot(nRows, nCols, i);
            topoplot(protocolTopo(i).power1Hz, EEG.chanlocs, 'electrodes','on');
            title(sprintf('Protocol %d', protocolTopo(i).protocol));
            colorbar;
        end
        sgtitle('Topographic Maps of 1 Hz Power for Each Protocol');
    else
        warning('No valid protocols found for topographic analysis.');
    end
end
