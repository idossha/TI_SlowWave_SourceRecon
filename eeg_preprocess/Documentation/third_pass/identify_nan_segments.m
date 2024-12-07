% identify_nan_segments.m
% Identifies segments in EEG.data that contain NaNs and logs the process.

function [NaNSegments, nanIndices] = identify_nan_segments(EEG, fid)
    % Logical array where any channel is NaN
    nanData = any(isnan(EEG.data), 1);

    % Find start and end indices of NaN segments
    d = diff([0 nanData 0]);
    startIdx = find(d == 1);
    endIdx = find(d == -1) - 1;

    NaNSegments = [startIdx; endIdx]';
    nanIndices = nanData;

    if isempty(NaNSegments)
        log_message(fid, 'No NaN segments identified.');
    else
        for i = 1:size(NaNSegments,1)
            log_message(fid, 'Identified NaN segment from sample %d to %d.', NaNSegments(i,1), NaNSegments(i,2));
        end
    end
end
