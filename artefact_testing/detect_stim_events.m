
function [EEG, trigData, newEvents] = detect_stim_events(EEG, trigIdx)
% detect_stim_events - Detect stimulation events using the TRIG channel.
%
% Syntax:
%   [EEG, trigData, newEvents] = detect_stim_events(EEG, trigIdx)
%
% Inputs:
%   EEG     - The EEG structure.
%   trigIdx - Index of the TRIG channel.
%
% Outputs:
%   EEG       - Updated EEG structure.
%   trigData  - The TRIG channel data.
%   newEvents - Structure array of new events (stim start/end).
%
% Parameters
pulseThreshold = 50000;    % in µV
bufferSamples  = 500;      % 1 sec at 500 Hz

% Extract TRIG channel data.
trigData = EEG.data(trigIdx, :);

% Create a logical vector (true when above threshold).
aboveThreshold = trigData > pulseThreshold;

% Detect rising edges (transition from below to above threshold).
rawRisingEdges = find(diff(aboveThreshold) == 1) + 1;  % +1 for diff offset

% Apply buffer to avoid multiple detections of the same pulse.
filteredRisingEdges = [];
if ~isempty(rawRisingEdges)
    filteredRisingEdges = rawRisingEdges(1);
    for k = 2:length(rawRisingEdges)
        if rawRisingEdges(k) - filteredRisingEdges(end) > bufferSamples
            filteredRisingEdges(end+1) = rawRisingEdges(k);  %#ok<AGROW>
        end
    end
end

% Check for an even number of pulses.
if mod(length(filteredRisingEdges), 2) ~= 0
    warning('Odd number of pulses detected. Ignoring the last unmatched pulse.');
    filteredRisingEdges = filteredRisingEdges(1:end-1);
end

% Create new events: first pulse = 'stim start', second pulse = 'stim end'.
newEvents = struct('type', {}, 'latency', {});
for i = 1:2:length(filteredRisingEdges)
    evtStart.type    = 'stim start';
    evtStart.latency = filteredRisingEdges(i);
    
    evtEnd.type      = 'stim end';
    evtEnd.latency   = filteredRisingEdges(i+1);
    
    newEvents(end+1) = evtStart; %#ok<AGROW>
    newEvents(end+1) = evtEnd;   %#ok<AGROW>
end
end
