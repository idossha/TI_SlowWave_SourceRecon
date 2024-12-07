% identify_nan_segments.m
% Identifies segments in EEG.data that contain NaNs and logs the process.

function [NaNSegments, nanIndices, totalTimeSeconds, totalTimeMinutes] = identify_nan_segs(EEG, fid)
    % Logical array where any channel is NaN
    nanData = any(isnan(EEG.data), 1);

    % Find start and end indices of NaN segments
    d = diff([0 nanData 0]);
    startIdx = find(d == 1);
    endIdx = find(d == -1) - 1;

    NaNSegments = [startIdx; endIdx]';
    nanIndices = nanData;

    totalTimeSeconds = 0; % Initialize total time in seconds

    if isempty(NaNSegments)
        log_message(fid, 'No NaN segments identified.');
        fprintf('No NaN segments identified.\n'); % Print to console
    else
        for i = 1:size(NaNSegments, 1)
            % Calculate the length of the NaN segment in seconds
            segmentLength = (NaNSegments(i, 2) - NaNSegments(i, 1)) / EEG.srate;
            
            % Accumulate total time
            totalTimeSeconds = totalTimeSeconds + segmentLength;
            
            % Prepare the detailed message
            detailedMessage = sprintf('Identified NaN segment #%d from sample %d to %d, with length (%.2f seconds).', ...
                i, NaNSegments(i, 1), NaNSegments(i, 2), segmentLength);
            
            % Log the message to the file
            log_message(fid, '%s', detailedMessage);
            
            % Print the message to the console
            fprintf('%s\n', detailedMessage);
        end
        
        % Convert total time to minutes
        totalTimeMinutes = totalTimeSeconds / 60;
        
        % Prepare the summary message with total time
        summaryMessage = sprintf('Found %d NaN segments with a total length of %.2f seconds (%.2f minutes).', ...
            size(NaNSegments, 1), totalTimeSeconds, totalTimeMinutes);
        
        % Log the summary message to the file
        log_message(fid, '%s', summaryMessage);
        
        % Print the summary message to the console
        fprintf('%s\n', summaryMessage);
    end
end

% Example implementation of log_message (if not already defined)
function log_message(fid, varargin)
    if nargin < 2
        return; % Nothing to log
    end
    fprintf(fid, varargin{:});
    fprintf(fid, '\n'); % Add a newline character at the end
end
