
function protocolTF = protocol_timefreq_single(EEG, protocolNumber, chanForTF)
% protocol_timefreq_single - Computes and plots the time-frequency analysis for a single stimulation protocol.
%
% Syntax:
%   protocolTF = protocol_timefreq_single(EEG, protocolNumber, chanForTF)
%
% Inputs:
%   EEG           - An EEGLAB EEG structure (preprocessed and containing 'stim start' and 'stim end' events).
%   protocolNumber- The protocol number (starting at 1) to analyze. Default is 1.
%   chanForTF     - (Optional) Channel index to use for the analysis. Default is 1.
%
% Outputs:
%   protocolTF    - A structure containing:
%                     .protocol    - Protocol number
%                     .ersp        - Event-related spectral perturbation (ERSP)
%                     .itc         - Inter-trial coherence (ITC)
%                     .times       - Time axis (ms, relative to epoch start)
%                     .freqs       - Frequency axis (Hz)
%                     .t0          - Time (ms) of stim start relative to the epoch
%                     .t1          - Time (ms) of stim end relative to the epoch
%                     .epochRange  - [start end] sample indices of the extracted epoch
%
% Definition:
%   - Protocol: from 'stim start' to 'stim end'
%   - Epoch: extends one protocol-duration before the 'stim start' and one
%            protocol-duration after the 'stim end'.
%
% The function computes a wavelet-based time-frequency analysis using newtimef,
% and then plots the ERSP with vertical dashed lines indicating the stim start
% (black) and stim end (red).

    if nargin < 2
        protocolNumber = 1;
    end
    if nargin < 3
        chanForTF = 1;
    end

    % Ensure events are sorted by latency.
    [~, sortIdx] = sort([EEG.event.latency]);
    EEG.event = EEG.event(sortIdx);

    % Find the requested protocol.
    count = 0;
    found = false;
    nEvents = length(EEG.event);
    for k = 1:(nEvents-1)
        if strcmpi(EEG.event(k).type, 'stim start') && strcmpi(EEG.event(k+1).type, 'stim end')
            count = count + 1;
            if count == protocolNumber
                found = true;
                stimStart = EEG.event(k).latency;
                stimEnd   = EEG.event(k+1).latency;
                break;
            end
        end
    end
    if ~found
        error('Protocol number %d not found.', protocolNumber);
    end

    % Protocol duration in samples.
    protocolDuration = stimEnd - stimStart;
    
    % Define the epoch boundaries:
    % Epoch spans one protocol-duration before stimStart to one protocol-duration after stimEnd.
    epochStart = stimStart - protocolDuration;
    epochEnd   = stimEnd + protocolDuration;
    if epochStart < 1, epochStart = 1; end
    if epochEnd > size(EEG.data,2), epochEnd = size(EEG.data,2); end

    % Extract data segment from the specified channel.
    segment = double(EEG.data(chanForTF, epochStart:epochEnd));
    frames = length(segment);

    % Compute time offsets in ms:
    % t0: stim start relative to epoch start.
    % t1: stim end relative to epoch start.
    t0 = ((stimStart - epochStart) / EEG.srate) * 1000; 
    t1 = t0 + ((protocolDuration / EEG.srate) * 1000);

    % Define the time range for newtimef (in ms) relative to epoch start.
    totalDuration_sec = frames / EEG.srate;
    timerange = [0 totalDuration_sec*1000];

    % Run the time-frequency analysis using newtimef.
    % 'cycles' parameter is set to 3 (adjust as needed).
    [ersp, itc, ~, times, freqs, ~, ~] = newtimef(segment, frames, timerange, EEG.srate, ...
                                                     'cycles', 3, 'plotitc', 'off', 'plotersp', 'off', 'verbose', 'off');

    % Plot the ERSP.
    figure;
    imagesc(times, freqs, ersp);
    axis xy;
    xlabel('Time (ms)');
    ylabel('Frequency (Hz)');
    title(sprintf('Time-Frequency Analysis for Protocol %d', protocolNumber));
    colorbar;
    hold on;
    % Draw vertical dashed line at stim start (black) and stim end (red)
    plot([t0 t0], ylim, 'k--', 'LineWidth', 2);
    plot([t1 t1], ylim, 'r--', 'LineWidth', 2);
    hold off;

    % Save results in output structure.
    protocolTF.protocol    = protocolNumber;
    protocolTF.ersp        = ersp;
    protocolTF.itc         = itc;
    protocolTF.times       = times;
    protocolTF.freqs       = freqs;
    protocolTF.t0          = t0;
    protocolTF.t1          = t1;
    protocolTF.epochRange  = [epochStart, epochEnd];
end

