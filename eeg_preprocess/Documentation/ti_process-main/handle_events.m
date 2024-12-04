% handle_events.m
% v.0.0.0 - initial commit
% last ()
% use - functions to do event handling

classdef handle_events
    methods(Static)
        % incorporate sleep stage information as events
        function EEG = add_sleep_stage(EEG)
            % find .mat file with sleep stage data
            ss_filepath = fullfile(EEG.filepath, 'staging', '*mat');
            fprintf('Looking for sleep stage data in \n')
            fprintf('%s \n', ss_filepath)

            ss_filename = dir(fullfile(EEG.filepath, 'staging', '*mat'));
            if isempty(ss_filename)
                error('No .mat file found in directory %s \n', ss_filepath) 
            elseif size(ss_filename,1) > 1
                error('More than 1 .mat file found; choose correct file')
            else
                fprintf('Loading %s \n', fullfile(ss_filename(1).folder, ss_filename(1).name))
                load(fullfile(ss_filename(1).folder, ss_filename(1).name))
            end 

            % add sleep stage data to existing events structure
            fprintf('Adding sleep stage data to EEG events and struct \n')

            count = size(EEG.event,2);
            for iSS = 1:size(stageData.stages,2)
                count = count + 1;
                EEG.event(count).latency = stageData.onsets(iSS);
                EEG.event(count).code = stageData.stages(iSS);
                EEG.event(count).type = 'Sleep Stage';
            end

            % add the stageData itself to the EEG struct 
            EEG.stageData = stageData;

            fprintf('Sleep stage data added \n')

        end %function

        % incorporate stim timings from metadata as events
        function EEG = add_stim_timings(EEG, ind_proto_metadata)
            % if _we.set file exists, load that file and don't overwrite
            new_fileName = split(EEG.filename, '.set');
            new_fileName = strcat(new_fileName{1}, '_we.set');

            if ~exist(fullfile(EEG.filepath, new_fileName))

                starts = []; ends = []; proto_types = [];
                for iProto = 1:size(ind_proto_metadata,2)
                    starts = [starts ind_proto_metadata(iProto).timing.stim_start_final];
                    ends = [ends ind_proto_metadata(iProto).timing.stim_end_final];
                    proto_types = [proto_types ind_proto_metadata(iProto).proto_type];

                    % add field for channels; need this to diff sham nrem
                    % and rem
                end
                
                % add stim start timings + protocol type to EEG events
                % add to end of event structure so as to not overwrite events
                count = size(EEG.event,2);
                for iTp = 1:length(starts)
                    count = count + 1;
                    % latency must be in samples
                    EEG.event(count).latency = starts(iTp);
                    EEG.event(count).code = 'ti';
                    EEG.event(count).type = 'stim start';
                    EEG.event(count).proto_ind = iTp;
                    EEG.event(count).proto_type = proto_types(iTp);
                end

                % add stim end timings + protocol type to EEG events
                count = size(EEG.event,2);
                for iTp = 1:length(ends)
                    count = count + 1;
                    % latency must be in samples
                    EEG.event(count).latency = ends(iTp);
                    EEG.event(count).code = 'ti';
                    EEG.event(count).type = 'stim end';
                    EEG.event(count).proto_ind = iTp;
                    EEG.event(count).proto_type = proto_types(iTp);
                end

                % check that the events were added properly and in the intended
                % protocol order
                starts = []; ends = []; types = [];
                for iEv = 1:size(EEG.event,2)
                    if strcmp(EEG.event(iEv).type, 'stim start')
                        starts = [starts (EEG.event(iEv).latency / EEG.srate)];
                        types = [types EEG.event(iEv).proto_type];
                    end
                
                    if strcmp(EEG.event(iEv).type, 'stim end')
                        ends = [ends (EEG.event(iEv).latency / EEG.srate)];
                    end
                end
                t_protos = [starts' ends' types']
                fprintf('Stim Start and Stim End data added \n')

                % rename set
                EEG.filename = new_fileName;
                EEG.setname = new_fileName;

                % save data
                fprintf('Saving data with events %s \n', new_fileName);
                pop_saveset(EEG, fullfile(EEG.filepath, new_fileName));
            else
                fprintf('%s exists, loading .set file \n', new_fileName);
                EEG = pop_loadset(fullfile(EEG.filepath, new_fileName))
            end

        end %function
        
    end %methods
end %classdef
