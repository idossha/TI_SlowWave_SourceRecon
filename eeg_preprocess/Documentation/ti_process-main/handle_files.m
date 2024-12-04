% handle_files.m
% v.0.0.0 - initial commit 
% last ()
% use - functions to handle files during EEG processing

classdef handle_files
    methods(Static)
        function EEG = convert_mff_to_set(path, old_filename, new_filename)
            fprintf('Loading mff file %s \n', old_filename)
            EEG = pop_mffimport({fullfile(path, old_filename)}, {'code'}, 0, 0);

            fprintf('Extracting time info \n')

            % find recording date and start time based off
            % of filename; this is correct so long as EGI
            % computer clock is correct
            str_split = split(old_filename, '_');
            recdate = sprintf('%c%c%c%c-%c%c-%c%c', str_split{4});
            recstart = split(str_split{5}, '.mff');
            recstart = sprintf('%c%c:%c%c:%c%c', recstart{1});
            
            % check to see if in 24 hour time, if not then
            % convert
            start_hr = str2num(recstart(1:2));
            % assume times < 13 need to be converted
            % note this doesn't work well for midnight (00) start times
            % will need eventual fix
            if start_hr < 13
                fprintf('Converting start time of %s to 24 hr time \n', recstart)
                start_hr = start_hr + 12;
                recstart(1:2) = num2str(start_hr);
            end
            
            fprintf('Recording started at %s \n', recstart)

            fprintf('Initializing timing info and saving as .set \n')
            % init timing info in EEG.etc
            EEG.etc.startTime = datetime(recstart, 'Format', 'HH:mm:ss');
            EEG.etc.timeIndices = 1:EEG.pnts;
            samplingInterval = seconds(1 / EEG.srate);
            EEG.etc.actualTimes = EEG.etc.startTime + [0:EEG.pnts-1] * samplingInterval;
            EEG.etc.startDate = recdate;
            EEG.etc.rejRegions = [];
            EEG.etc.saveNaN = 0;
            
            EEG.setname = new_filename;
            EEG.filename = new_filename;
            EEG.filepath = path;

            % save .mff file as .set
            pop_saveset(EEG, fullfile(path, new_filename))
        end

        % given processing directory, rm non-essential files to reduce
        % space being occupied
        function remove_processing_files(filepath)
            files = dir(filepath);
            filenames_to_keep = {};
            
            % find the last filename, assumes it ends in NREM
            last_filenames = {};
            for iFile = 1:size(files,1)
                if contains(files(iFile).name, '.set')
                    if contains(files(iFile).name, 'NREM')
                        last_filenames = [last_filenames files(iFile).name];
                    end
                end
            end
            
            if isempty(last_filenames)
                error('Automatic file deletion depends on having the last step (_NREM.set) in the directory \n')
            end
            
            start_str = split(last_filenames{1}, '_NREM.set');
            filenames_to_keep{1} = strcat(start_str{1}, '.set');
            filenames_to_keep{2} = strcat(start_str{1}, '.fdt');
            
            pre_start_str = split(start_str{1}, '_rm');
            filenames_to_keep{3} = strcat(pre_start_str{1}, '.set');
            filenames_to_keep{4} = strcat(pre_start_str{1}, '.fdt');
            
            fprintf('Files to be DELETED from %s \n', filepath)
            for iFile = 1:size(files,1)
                if contains(files(iFile).name, '.set') || contains(files(iFile).name, '.fdt')
                    if ~contains(filenames_to_keep, files(iFile).name)
                        fprintf('%s \n', files(iFile).name)
                    end
                elseif contains(files(iFile).name, '.mff')
                    fprintf('%s \n', files(iFile).name)
                end
            end
            
            resp = input('OK to proceed? (y/n) : ', 's');
            if resp == 'y'
                for iFile = 1:size(files,1)
                    if contains(files(iFile).name, '.set') || contains(files(iFile).name, '.fdt')
                        if ~contains(filenames_to_keep, files(iFile).name)
                            delete(fullfile(filepath, files(iFile).name))
                        end
                    elseif contains(files(iFile).name, '.mff')
                        delete(fullfile(filepath, strcat(files(iFile).name, '\Contents\*')))
                        rmdir(fullfile(filepath, strcat(files(iFile).name, '\Contents')))
                        delete(fullfile(filepath, strcat(files(iFile).name, '\*')))
                        rmdir(fullfile(filepath, strcat(files(iFile).name)))
                    end
                end
                fprintf('DELETING files automatically \n')
            else
                fprintf('NOT DELETING automatically \n')
                fprintf('Please remove non-essential files manually \n')
            end

            fprintf('DONE! \n')
        end
       
    end %methods
end %classdef