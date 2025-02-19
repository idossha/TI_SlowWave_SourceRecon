
function protocolTF = protocol_timefreq_single(EEG, protocolNumber)
% protocol_timefreq_single - Computes and plots the time-frequency analysis
% for a single stimulation protocol by first averaging the EEG signal across
% all channels and then running the wavelet analysis.
%
% Syntax:
%   protocolTF = protocol_timefreq_single(EEG, protocolNumber)
%
% Inputs:
%   EEG           - An EEGLAB EEG structure (preprocessed and containing
%                   'stim start' and 'stim end' events).
%   protocolNumber- The protocol number (starting at 1) to analyze.
%                   Default is 1.
%
% Outputs:
%   protocolTF    - A structure containing:
%                     .protocol    - Protocol number
%                     .ersp        - ERSP (power) from the averaged signal
%                     .itc         - Inter-trial coherence (if computed)
%                     .times       - Time axis (s, relative to epoch start)
%                     .freqs       - Frequency axis (Hz)
%                     .t0          - Time (s) of stim start relative to the epoch
%                     .t1          - Time (s) of stim end relative to the epoch
%                     .epochRange  - [start end] sample indices of the extracted epoch
%
% Definition:
%   - Protocol: the data segment from a 'stim start' to its corresponding 'stim end'.
%   - Epoch: extends one protocol-duration before the stim start and one protocol-duration
%            after the stim end.
%
% The function averages the EEG data across channels, then uses newtimef with
% frequency limits [1 15] Hz, a high cycle count (8), and a fine frequency grid (nfreqs=100)
% to maximize frequency resolution. The resulting plot shows time (s) on the x axis,
% frequency (Hz) on the y axis, with vertical dashed lines indicating the stim start
% (black) and stim end (red).

    if nargin < 2
        protocolNumber = 1;
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
    
    % Define the epoch: one protocol-duration before stimStart to one protocol-duration after stimEnd.
    epochStart = stimStart - protocolDuration;
    epochEnd   = stimEnd + protocolDuration;
    if epochStart < 1, epochStart = 1; end
    if epochEnd > size(EEG.data,2), epochEnd = size(EEG.data,2); end

    % Extract data segment from all channels and average across channels.
    segment_all = double(EEG.data(:, epochStart:epochEnd));  % [nChans x frames]
    averaged_signal = mean(segment_all, 1);                    % [1 x frames]
    frames = length(averaged_signal);

    % Compute time offsets (in ms):
    % t0: time of stim start relative to epoch start.
    % t1: time of stim end relative to epoch start.
    t0 = ((stimStart - epochStart) / EEG.srate) * 1000; 
    t1 = t0 + ((protocolDuration / EEG.srate) * 1000);

    % Convert times to seconds for plotting.
    t0_sec = t0 / 1000;
    t1_sec = t1 / 1000;

    % Define the time range for newtimef (in ms relative to epoch start).
    totalDuration_sec = frames / EEG.srate;
    timerange = [0 totalDuration_sec*1000];

    % Run time-frequency analysis using newtimef on the averaged signal.
    [ersp, itc, ~, times, freqs, ~, ~] = newtimef(averaged_signal, frames, timerange, EEG.srate, ...
                                                     'cycles', 8, 'nfreqs', 100, ...
                                                     'plotitc', 'off', 'plotersp', 'off', 'verbose', 'off', ...
                                                     'freqs', [1 15]);
    
    % Convert newtimef time axis from ms to seconds.
    times_sec = times / 1000;

    % Plot the averaged ERSP.
    figure;
    imagesc(times_sec, freqs, ersp);
    axis xy;
    xlabel('Time (s)');
    ylabel('Frequency (Hz)');
    title(sprintf('Time-Frequency Analysis for Protocol %d (Averaged Across Channels)', protocolNumber));
    colorbar;
    hold on;
    % Draw vertical dashed lines at stim start (black) and stim end (red)
    plot([t0_sec t0_sec], [min(freqs) max(freqs)], 'k--', 'LineWidth', 2);
    plot([t1_sec t1_sec], [min(freqs) max(freqs)], 'r--', 'LineWidth', 2);
    hold off;

    % Save results in output structure.
    protocolTF.protocol    = protocolNumber;
    protocolTF.ersp        = ersp;
    protocolTF.itc         = itc;
    protocolTF.times       = times_sec; % time in seconds
    protocolTF.freqs       = freqs;
    protocolTF.t0          = t0_sec;
    protocolTF.t1          = t1_sec;
    protocolTF.epochRange  = [epochStart, epochEnd];
end

