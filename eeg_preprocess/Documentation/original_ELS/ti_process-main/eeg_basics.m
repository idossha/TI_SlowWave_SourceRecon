% eeg_basics.m
% v.0.0.0 - initial commit
% last ()
% use - functions to do basic eeg pre-processing steps

classdef eeg_basics
    methods(Static)
        % given EEG data, perform band pass filter
        function EEG = apply_filters(EEG)
            % if _filt.set file exists, load that file and don't overwrite
            new_fileName = split(EEG.filename, '.set');
            new_fileName = strcat(new_fileName{1}, '_filt.set');

            if ~exist(fullfile(EEG.filepath, new_fileName))

                fprintf('Applying Band-Pass filter to %s \n', EEG.filename);

                % Band pass filter 0.5 to 40
                EEG = pop_eegfiltnew(EEG, 0.5, 40, [], 0, [], 0);

                % rename set
                EEG.filename = new_fileName;
                EEG.setname = new_fileName;

                % save data
                fprintf('Saving filtered data %s \n', new_fileName);
                pop_saveset(EEG, fullfile(EEG.filepath, new_fileName));
            else
                fprintf('%s exists, loading .set file \n', new_fileName);
                EEG = pop_loadset(fullfile(EEG.filepath, new_fileName))
            end
        end %function

        % given EEG data, perform resampling
        function EEG = resamp(EEG)
            % if _ds.set file exists, load that file and don't overwrite
            new_fileName = split(EEG.filename, '.set');
            new_fileName = strcat(new_fileName{1}, '_ds.set');

            if ~exist(fullfile(EEG.filepath, new_fileName))

                fprintf('Resampling %s \n', EEG.filename);

                % Use eeglab resamp function
                EEG = pop_resample(EEG, 250);

                % rename set
                EEG.filename = new_fileName;
                EEG.setname = new_fileName;

                % save data
                fprintf('Saving downsampled data %s \n', new_fileName);
                pop_saveset(EEG, fullfile(EEG.filepath, new_fileName));
            else
                fprintf('%s exists, loading .set file \n', new_fileName);
                EEG = pop_loadset(fullfile(EEG.filepath, new_fileName))
            end
        end %function

    end %methods
end %classdef
