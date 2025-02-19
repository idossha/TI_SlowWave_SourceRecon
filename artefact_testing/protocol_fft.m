
function protocolFFT = protocol_fft(EEG)
% protocol_fft - Computes the FFT for each stimulation protocol by averaging across all channels.
%
% Syntax:
%   protocolFFT = protocol_fft(EEG)
%
% Inputs:
%   EEG       - EEGLAB dataset (preprocessed and with stim events in EEG.event)
%
% Outputs:
%   protocolFFT - A structure array with one element per protocol containing:
%       .protocol      - Protocol number (starting at 1)
%       .f             - Frequency vector (Hz) from 0.5 to 30 Hz
%       .mag           - Magnitude spectrum corresponding to f (averaged across channels)
%       .startLatency  - Sample index of stim start
%       .endLatency    - Sample index of stim end
%
% Each protocol is defined as the data segment between a "stim start" event and
% its following "stim end" event.

    % Ensure events are sorted by latency
    [~, sortIdx] = sort([EEG.event.latency]);
    EEG.event = EEG.event(sortIdx);

    protocolFFT = [];
    protocolCount = 0;
    
    % Loop over events to find protocol pairs.
    % (Assumes events appear in pairs: stim start followed immediately by stim end)
    nEvents = length(EEG.event);
    k = 1;
    while k < nEvents
        if strcmpi(EEG.event(k).type, 'stim start') && ...
           (k+1 <= nEvents) && strcmpi(EEG.event(k+1).type, 'stim end')
       
            protocolCount = protocolCount + 1;
            startLatency = EEG.event(k).latency;
            endLatency   = EEG.event(k+1).latency;
            
            % Extract the segment for the protocol from all channels and average across channels.
            segment_all = double(EEG.data(:, startLatency:endLatency)); % size: [nChans x samples]
            segment = mean(segment_all, 1); % average across channels (1 x samples)
            N = length(segment);
            
            % Compute FFT and normalize.
            Y = fft(segment) / N;
            % Use only the first half (positive frequencies)
            Nhalf = floor(N/2) + 1;
            f = (0:Nhalf-1) * (EEG.srate / N);
            mag = abs(Y(1:Nhalf));
            
            % Restrict frequency axis to 0.5-30 Hz.
            idx = (f >= 0.5 & f <= 30);
            protocolFFT(protocolCount).protocol = protocolCount;
            protocolFFT(protocolCount).f = f(idx);
            protocolFFT(protocolCount).mag = mag(idx);
            protocolFFT(protocolCount).startLatency = startLatency;
            protocolFFT(protocolCount).endLatency = endLatency;
        end
        k = k + 1;
    end

    % Plot FFT for each protocol in separate subplots
    if ~isempty(protocolFFT)
        nProt = length(protocolFFT);
        figure('Name','FFT for each Stimulation Protocol (Averaged across Channels)');
        for i = 1:nProt
            subplot(ceil(nProt/2), 2, i);
            plot(protocolFFT(i).f, protocolFFT(i).mag, 'LineWidth', 1.5);
            xlabel('Frequency (Hz)');
            ylabel('Magnitude');
            title(sprintf('Protocol %d', protocolFFT(i).protocol));
            xlim([0.5 30]);
        end
        sgtitle('FFT of Each Stimulation Protocol (Averaged across Channels)');
    else
        warning('No valid stimulation protocols found for FFT computation.');
    end
end

