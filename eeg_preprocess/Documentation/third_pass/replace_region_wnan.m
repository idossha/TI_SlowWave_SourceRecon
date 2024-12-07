% replace_region_wnan.m
% Replaces specified regions in EEG data with NaNs and logs the process.

function EEG = replace_region_wnan(EEG, rej_inds, savestr, fid)
    if nargin < 4
        error('Insufficient input arguments. Usage: EEG = replace_region_wnan(EEG, rej_inds, savestr, fid)');
    end

    if isempty(rej_inds)
        log_message(fid, 'No regions provided for replacement. Skipping replace_region_wnan.');
        return;
    end

    % Replace data with NaNs
    for i = 1:size(rej_inds,1)
        if rej_inds(i,1) < 1 || rej_inds(i,2) > EEG.pnts
            log_message(fid, 'Error: Rejection region [%d, %d] is out of bounds. Skipping this region.', rej_inds(i,1), rej_inds(i,2));
            continue;
        end
        EEG.data(:, rej_inds(i,1):rej_inds(i,2)) = NaN;
        log_message(fid, 'Replaced data from sample %d to %d with NaNs.', rej_inds(i,1), rej_inds(i,2));
    end

    % Track rejection regions
    if isfield(EEG.etc, 'rejRegions') && ~isempty(EEG.etc.rejRegions)
        EEG.etc.rejRegions = [EEG.etc.rejRegions; rej_inds];
    else
        EEG.etc.rejRegions = rej_inds;
    end
end
