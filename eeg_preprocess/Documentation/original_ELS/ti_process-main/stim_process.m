% stim_process.m
% v.0.0.0 - initial commit
% last ()
% use - functions to process stimulation data

classdef stim_process
    methods(Static)
        % identify indices corresponding to stimulation pulses
        function ind_proto_metadata   = find_and_align_protos(EEG)
            %% find and load stimulator metadata file (.mat from .p file)
            dirs    = [dir(fullfile(EEG.filepath, 'stim'))];
            dir_ind = find(contains({dirs(:).name}, 'ind_proto_metadata.mat'));
            if isempty(dir_ind)
                error('ind_proto_metadata.mat file not found')
            end

            load(fullfile(EEG.filepath, 'stim', dirs(dir_ind).name))

            durations = round([ind_proto_metadata(:).duration_backend])';
            types = [ind_proto_metadata(:).proto_type]';
            inds = [ind_proto_metadata(:).proto_ind]';

            %% find and load stimulator metadata file (.txt) with stim clock
            dirs    = [dir(fullfile(EEG.filepath, 'stim'))];
            dir_ind = find(contains({dirs(:).name}, 'metadata.txt'));
            if isempty(dir_ind)
                error('metadata.txt file not found')
            end

            % load stim clock if metadata.txt file found (TI computer)
            fileID  = fopen(fullfile(EEG.filepath, 'stim', dirs(dir_ind).name), 'r');
            lines   = textscan(fileID, '%s', 'Delimiter', '\n'); % Read each line of the entire txt file into a cell array
            lines   = lines{1};  % Extract the data from the cell array; now lines{i} is the i-th line of the file
            fclose(fileID); % Close the file
            
            % Create a table variable for metadata information
            stim_clocks = table('Size', [1 7],...
                'VariableTypes', {'duration', 'double',       'double',        'string',        'double',          'double',           'double'},...
                'VariableNames', {'Time',     'protocol_ind', 'protocol_type', 'protocol_name', 'DurationMax',     'RampUpDur',        'RampDownDur'});
            
            % Parse each line
            iProtocol   = 1;
            for i       = 1:length(lines)
                columns = regexp(lines{i}, '[ :]', 'split'); % Use regexp to split each line, assuming the delimiter can be a space or a colon
                 if strcmp(columns{1,1}, 'Time')
                    stim_clocks.Time(iProtocol) = duration([columns{1,4} ':' columns{1,5} ':' columns{1,6}]);
                    columns = regexp(lines{i+1}, '[ :]', 'split'); stim_clocks.protocol_ind(iProtocol)  = str2double(columns{1,3});
                    columns = regexp(lines{i+2}, '[ :]', 'split'); stim_clocks.protocol_type(iProtocol) = str2double(columns{1,3});
                    columns = regexp(lines{i+3}, '[ ]' , 'split'); stim_clocks.protocol_name(iProtocol) = string(columns{1,1});
                    j = 0;
                    columns_tmp  = regexp(lines{i+4+j}, '[ :]', 'split');     
                    while contains(columns_tmp{1, 1} , 'Chan')
                        columns = regexp(lines{i+4+j}, '[ :]', 'split'); stim_clocks.(columns{1, 1})(iProtocol) = string([columns{1,3:end}])';
                        j = j+1;
                        columns_tmp  = regexp(lines{i+4+j}, '[ :]', 'split');     
                    end

                    columns = regexp(lines{i+4+j}, '[ :]', 'split'); stim_clocks.DurationMax(iProtocol)   = str2double(columns{1,5});
                    columns = regexp(lines{i+5+j}, '[ :]', 'split'); stim_clocks.RampUpDur(iProtocol)     = str2double(columns{1,5});
                    columns = regexp(lines{i+6+j}, '[ :]', 'split'); stim_clocks.RampDownDur(iProtocol)   = str2double(columns{1,5});
                    
                    iProtocol   = iProtocol+1;
                end
            end
            stim_clocks = stim_clocks(find(stim_clocks.protocol_ind == inds(1)):end, :); % align with the metadata file

            % find .mff folder in dir and search for log file within that dir
            dirs        = [dir(EEG.filepath)];
            mff_dir_ind = contains({dirs(:).name}, '.mff');
            mff_dir     = dirs(mff_dir_ind).name;
            dirs        = [dir(fullfile(EEG.filepath, mff_dir))];

            dir_ind     = find(contains({dirs(:).name}, 'log_'));
            if isempty(dir_ind)
                error('log_ .txt file not found')
            end

            % Time_EGI        = duration([dirs(dir_ind).name(end-9:end-8) ':' dirs(dir_ind).name(end-7:end-6) ':' dirs(dir_ind).name(end-5:end-4)]); % EEG data saved time (from its name)
            Time_EGI = duration(string(EEG.etc.startTime));
            if Time_EGI    >= duration('2:00:00') && Time_EGI < duration('12:00:00') % to make the time (e.g., 2~11:59:59 pm) to be 24 hour format
                Time_EGI    = Time_EGI + duration("12:00:00"); % to be 24 hour format
                stim_clocks_latency = stim_clocks.Time-Time_EGI; 
                stim_clocks_latency(stim_clocks_latency < duration("-12:00:00")) = stim_clocks_latency(stim_clocks_latency < duration("-12:00:00")) + duration("24:00:00");
            elseif Time_EGI>= duration('12:00:00') % (12~23:59:59) it is already 24 hour format
                stim_clocks_latency = stim_clocks.Time-Time_EGI; 
                stim_clocks_latency(stim_clocks_latency < duration("-12:00:00")) = stim_clocks_latency(stim_clocks_latency < duration("-12:00:00")) + duration("24:00:00");
            elseif Time_EGI < duration('2:00:00') % after 12 am (0~1:59:59 am)
                stim_clocks_latency	= stim_clocks.Time-Time_EGI; 
                stim_clocks_latency(stim_clocks_latency > duration("12:00:00")) = stim_clocks_latency(stim_clocks_latency > duration("12:00:00")) - duration("24:00:00");
            end

            %% Correct durations, and latency
            stim_clocks.plannedDur      = stim_clocks.DurationMax + stim_clocks.RampUpDur + stim_clocks.RampDownDur;
            index_correctedDur          = find(durations < stim_clocks.DurationMax(1:length(durations))); % determine if planned duration was fully done (if < DurationMax, not), if not, use recorded duration in metadata_short.mat file instead
            stim_clocks.correctedDur    = stim_clocks.plannedDur; % creat another variable to save corrected duration
            stim_clocks.correctedDur(index_correctedDur) = durations(index_correctedDur); % use recorded duration in metadata_short.mat file instead
            stim_clocks.correctedDur(stim_clocks.correctedDur < 15) = 15; % duration should be at least a ramp up/down as 15s or so
            stim_clocks.latency_end     = seconds(stim_clocks_latency); 
            stim_clocks.latency_start   = stim_clocks.latency_end - stim_clocks.correctedDur; % calculate start from end by subtracting the stim duration

            %% find first stim protocol fully applied after lights out (not sure how best to do this,
            % right now assuming it is the first 4, NREM)
            max_proto_ex    = 1; % usually protocol 0,1 should be excluded
            ind_afterSleep  = find(stim_clocks.latency_start > 0, 1, "first"); % after EEG recording onset
            ind_formalStim  = find((types > max_proto_ex) & (durations >= max(stim_clocks.DurationMax))); % excluding procotol type 0 & 1, select stim duration >= planned one (in metadata.txt)
            first_sleep_ind = ind_formalStim(find(ind_formalStim >= ind_afterSleep, 1, "first")); % after EEG recording onset, type > 1, duration > plannedDur
        
            %% threshold and window over which to look for stim end index, very important to adjust to your exp
            threshold       = 10000; % uv
            win             = (stim_clocks.plannedDur + stim_clocks.correctedDur)/2 * 0.2; % seconds
            win(win<10)     = 10; % at least 10s
            win_samp        = win * EEG.srate;
            diff_start_TRIG_Vs_ENV = -5; % by observation, the difference of stim start between TRIG and ENV is around 5

            %% take indices including and after first sleep protocol
            inds = inds(first_sleep_ind:end);
            types = types(first_sleep_ind:end);
            
            %% Find first stim protos based on ENV & TRIG channels for correction of time between TI and EGI computer
            % find env trigger channel
            env_chan_ind    = find(contains({EEG.chanlocs(:).labels}, 'SI-ENV'));
            env_data        = EEG.data(env_chan_ind,:);
            env_hi_inds     = find(abs(env_data) > threshold); % find where env signal goes high

            % find TRIG trigger channel
            trig_chan_ind   = find(contains({EEG.chanlocs(:).labels}, 'TRIG'));
            trig_data       = EEG.data(trig_chan_ind,:);
            trig_hi_inds    = find(abs(trig_data) > threshold*100); % find where TRIG signal goes high

            % Find first stim protos based on either ENV or TRIG, or both channels   
            fflag_ENV       = 0; fflag_TRIG  = 0;
            n_proto         = length(inds);
            for iProto      = 1: n_proto
                env_end_lower   = stim_clocks.latency_end(iProto+first_sleep_ind-1) * EEG.srate - win_samp(iProto+first_sleep_ind-1);
                env_end_upper   = stim_clocks.latency_end(iProto+first_sleep_ind-1) * EEG.srate + win_samp(iProto+first_sleep_ind-1);
                trig_end_lower  = stim_clocks.latency_end(iProto+first_sleep_ind-1) * EEG.srate - win_samp(iProto+first_sleep_ind-1);
                trig_end_upper  = stim_clocks.latency_end(iProto+first_sleep_ind-1) * EEG.srate + win_samp(iProto+first_sleep_ind-1);
                if iProto < n_proto
                    inter_proto_upper   = (stim_clocks.latency_end(iProto+first_sleep_ind-1) + (stim_clocks.latency_start(iProto+first_sleep_ind)-stim_clocks.latency_end(iProto+first_sleep_ind-1))/2 ...
                        /(stim_clocks.protocol_ind(iProto+first_sleep_ind)-stim_clocks.protocol_ind(iProto+first_sleep_ind-1))^2) * EEG.srate; % between present end and next start (1/4/(number of time points between twe indexes) because the interval is too short...
                    if env_end_upper   >= inter_proto_upper && env_end_lower < inter_proto_upper % to prevent the window overlaps with the next protocol
                        env_end_upper   = inter_proto_upper;
                    end

                    if trig_end_upper  >= inter_proto_upper && trig_end_lower < inter_proto_upper
                        trig_end_upper  = inter_proto_upper;
                    end
                end

                if ~isempty(find(env_hi_inds >= env_end_lower & env_hi_inds <= env_end_upper, 1, "last")) % if any ENV triggers are found
                    env_end_ind = env_hi_inds(find(env_hi_inds >= env_end_lower & env_hi_inds <= env_end_upper, 1, "last"));
                    if fflag_ENV == 0 % find out first ENV trigger
                        env_end_1st                 = env_end_ind;
                        lantency_correction_ENVEnd  = env_end_1st/EEG.srate - stim_clocks.latency_end(iProto+first_sleep_ind-1);
                    end 
                    fflag_ENV                       = iProto; % keep searching ENV trigger for next protocol until finding a TRIG trigger for the same protocol
                end

                if ~isempty(find(trig_hi_inds >= trig_end_lower & trig_hi_inds <= trig_end_upper, 1, "last")) % if any TRIG triggers are found
                    trig_end_ind = trig_hi_inds(find(trig_hi_inds >= trig_end_lower & trig_hi_inds <= trig_end_upper, 1, "last"));
                    if fflag_TRIG == 0 % find out first TRIG trigger
                        trig_end_1st                = trig_end_ind;
                        lantency_correction_TRIGEnd = trig_end_1st/EEG.srate - stim_clocks.latency_end(iProto+first_sleep_ind-1);                  
                    end 
                    fflag_TRIG                      = iProto;
                    trig_end_1st_com                = trig_end_ind; % keep searching TRIG trigger for next protocol until finding a ENV trigger for the same protocol
                    lantency_correction_TRIGEnd_com = trig_end_1st_com/EEG.srate - stim_clocks.latency_end(iProto+first_sleep_ind-1);
                end

                if fflag_ENV == fflag_TRIG % quit after detecting both ENV & TRIG triggers from a same protocol
                    break
                end
            end
            
            %% From the manual event markers, roughly deduce the trigger time, and then use it to correct stim time in metadata file
            manu_start_ind = []; manu_end_ind = [];
            if ~isempty(EEG.event)
                for i = 1: length({EEG.event.label})
                    if strcmp(EEG.event(i).label, 'Stim Start') | strcmp(EEG.event(i).label, 'StimStart')
                        manu_start_ind = [manu_start_ind i];
                    end
    
                    if strcmp(EEG.event(i).label, 'Stim End') | strcmp(EEG.event(i).label, 'StimEnd')
                        manu_end_ind = [manu_end_ind i];
                    end
                end
                manu_start  = [EEG.event.latency]; manu_start = manu_start(manu_start_ind)'; % stim time by manual tagging 
                manu_end    = [EEG.event.latency]; manu_end = manu_end(manu_end_ind)';
                meta_start  = stim_clocks.latency_start(first_sleep_ind:end); meta_start = meta_start(types > max_proto_ex) * EEG.srate; % stim time in metadata.txt
                meta_end    = stim_clocks.latency_end(first_sleep_ind:end); meta_end = meta_end(types > max_proto_ex) * EEG.srate;
                manu_start_corr = []; % correspond manual stim start and metadata stim start
                for i = 1:length(meta_start)
                    if find(min(abs(manu_start - meta_start(i))) / EEG.srate < 60) % difference less than 1min (arbitrary determined)
                        manu_start_corr(i, 1) = manu_start(abs(manu_start - meta_start(i)) == min(abs(manu_start - meta_start(i))));
                    else
                        manu_start_corr(i, 1) = NaN;
                    end
                end
                manu_end_corr = [];  % correspond manual stim end and metadata stim end
                for i = 1:length(meta_end)
                    if find(min(abs(manu_end - meta_end(i))) / EEG.srate < 60)
                        manu_end_corr(i, 1) = manu_end(abs(manu_end - meta_end(i)) == min(abs(manu_end - meta_end(i))));
                    else
                        manu_end_corr(i, 1) = NaN;
                    end
                end
                diff_start  = (manu_start_corr - (meta_start + (diff_start_TRIG_Vs_ENV - 1)*EEG.srate)) / EEG.srate; % difference between manual stim start and the inferred TRIG start, plus 1s more
                lantency_correction_manu = nanmedian(diff_start); % use nanmedian to avoid NaNs, and extreme numbers
                if isnan(lantency_correction_manu) % if no manual event markers
                    lantency_correction_manu = 0;
                end
            else % if no manual event markers
                lantency_correction_manu = 0;
            end
            
            if fflag_ENV == 0 && fflag_TRIG == 0 % no triggers were found, then use manual stim time for time correction
                lantency_correction = lantency_correction_manu;

            elseif fflag_ENV ~= 0 && fflag_TRIG == 0 % only ENV trigger
                lantency_correction = lantency_correction_ENVEnd;
            elseif fflag_ENV == 0 && fflag_TRIG ~= 0 % only TRIG trigger
                lantency_correction = lantency_correction_TRIGEnd;
            else
                lantency_correction = lantency_correction_TRIGEnd_com; % both ENV and TRIG triggers from same protocol, but here use TRIG's 
                if abs(lantency_correction_ENVEnd-lantency_correction_TRIGEnd_com) >= 6 % check - if the time difference calculated in two ways is consistent (<= 5s)
                    error('The time difference calculated in two ways (ENV and TRIG) is not consistent(>1s, !) \n')
                end
            end

            stim_clocks.latency_start_corrected = stim_clocks.latency_start + lantency_correction; % correct the latency and use it for actual trigger detection
            stim_clocks.latency_end_corrected = stim_clocks.latency_end + lantency_correction; 
             
            %% Find stim protos based on SI-ENV trigger 
            % based on latency ENV start and ENV end times for each protocol, look within win
            % for stim start and end time, then move to the next stim start; repeat
            % until all times identified
            env_starts = []; env_ends = []; env_missing_starts = []; env_missing_ends = []; env_missing_starts_iProto = []; env_missing_ends_iProto = [];
            for iProto = 1: n_proto
                env_start_lower = stim_clocks.latency_start_corrected(iProto+first_sleep_ind-1) * EEG.srate - win_samp(iProto+first_sleep_ind-1);
                env_start_upper = stim_clocks.latency_start_corrected(iProto+first_sleep_ind-1) * EEG.srate + win_samp(iProto+first_sleep_ind-1);
                if iProto > 1 || first_sleep_ind > 1
                    inter_proto_lower   = (stim_clocks.latency_end_corrected(iProto+first_sleep_ind-2) + ...
                        (stim_clocks.latency_start_corrected(iProto+first_sleep_ind-1) - stim_clocks.latency_end_corrected(iProto+first_sleep_ind-2))/2 ...
                        /(stim_clocks.protocol_ind(iProto+first_sleep_ind-1) - stim_clocks.protocol_ind(iProto+first_sleep_ind-2))^2) * EEG.srate; % between present start and previous end (1/2/(number of time points between twe indexes) because the interval is too short...
                    if env_start_lower <= inter_proto_lower && env_start_upper > inter_proto_lower % to prevent the window overlaping with the previous protocol
                        env_start_lower = inter_proto_lower;
                    end
                end
                if isempty(find(env_hi_inds >= env_start_lower & env_hi_inds <= env_start_upper, 1, "first")) % if trigger not found, which is meant missing
                    env_start_ind               = stim_clocks.latency_start_corrected(iProto+first_sleep_ind-1) * EEG.srate; % if any trigggers are missing, use stim time (s) in metadata.txt instead; 
                    env_missing_starts          = [env_missing_starts env_start_ind]; % index
                    env_missing_starts_iProto   = [env_missing_starts_iProto iProto]; % protocol index
                else
                    env_start_ind               = env_hi_inds(find(env_hi_inds >= env_start_lower & env_hi_inds <= env_start_upper, 1, "first"));
                end

                env_end_lower   = stim_clocks.latency_end_corrected(iProto+first_sleep_ind-1) * EEG.srate - win_samp(iProto+first_sleep_ind-1); 
                env_end_upper   = stim_clocks.latency_end_corrected(iProto+first_sleep_ind-1) * EEG.srate + win_samp(iProto+first_sleep_ind-1);
                if iProto < n_proto
                    inter_proto_upper   = (stim_clocks.latency_end_corrected(iProto+first_sleep_ind-1) + ...
                        (stim_clocks.latency_start_corrected(iProto+first_sleep_ind) - stim_clocks.latency_end_corrected(iProto+first_sleep_ind-1))/2 ...
                        /(stim_clocks.protocol_ind(iProto+first_sleep_ind) - stim_clocks.protocol_ind(iProto+first_sleep_ind-1))^2) * EEG.srate; % between present end and next start (1/2/(number of time points between twe indexes) because the interval is too short...
                    if env_end_upper   >= inter_proto_upper && env_end_lower < inter_proto_upper % to prevent the window overlaps with the next protocol
                        env_end_upper   = inter_proto_upper;
                    end
                end
                if isempty(find(env_hi_inds >= env_end_lower & env_hi_inds <= env_end_upper, 1, "last")) % if trigger not found, which is meant missing
                    env_end_ind                 = (stim_clocks.latency_end_corrected(iProto+first_sleep_ind-1) + 1)* EEG.srate; % if any trigggers are missing, use stim time (s) in metadata.txt instead;
                    env_missing_ends            = [env_missing_ends env_end_ind];
                    env_missing_ends_iProto     = [env_missing_ends_iProto iProto];
                else
                    env_end_ind                 = env_hi_inds(find(env_hi_inds >= env_end_lower & env_hi_inds <= env_end_upper, 1, "last"));
                end
                
                env_starts  = [env_starts env_start_ind];
                env_ends    = [env_ends env_end_ind];
            end

            % check - every stim start should have a stim end
            if length(env_starts) ~= length(env_ends)
                error('number of ENV stim starts does not match number of stim ends(!) \n')
            end

            %% Find stim protos based on TRIG trigger
            % based on latency TRIG start and ENV end times for each protocol, look within win
            % for stim start and end time, then move to the next stim start; repeat
            % until all times identified
            trig_starts = []; trig_ends = []; trig_missing_starts = []; trig_missing_ends = []; trig_missing_starts_iProto = []; trig_missing_ends_iProto = [];
            fflag       = 0;
            for iProto  = 1: n_proto
                trig_start_lower                = (stim_clocks.latency_start_corrected(iProto+first_sleep_ind-1) + diff_start_TRIG_Vs_ENV) * EEG.srate - win_samp(iProto+first_sleep_ind-1); % plus diff_start_TRIG_Vs_ENV to calculate TRIG start 
                trig_start_upper                = (stim_clocks.latency_start_corrected(iProto+first_sleep_ind-1) + diff_start_TRIG_Vs_ENV) * EEG.srate + win_samp(iProto+first_sleep_ind-1);
                env_start_lower                 = stim_clocks.latency_start_corrected(iProto+first_sleep_ind-1) * EEG.srate - win_samp(iProto+first_sleep_ind-1);
                env_start_upper                 = stim_clocks.latency_start_corrected(iProto+first_sleep_ind-1) * EEG.srate + win_samp(iProto+first_sleep_ind-1);
                if iProto > 1 || first_sleep_ind > 1
                    inter_proto_lower           = (stim_clocks.latency_end_corrected(iProto+first_sleep_ind-2) + ...
                                (stim_clocks.latency_start_corrected(iProto+first_sleep_ind-1) - stim_clocks.latency_end_corrected(iProto+first_sleep_ind-2))/2 ...
                                /(stim_clocks.protocol_ind(iProto+first_sleep_ind-1) - stim_clocks.protocol_ind(iProto+first_sleep_ind-2))^2 + diff_start_TRIG_Vs_ENV) * EEG.srate; % between present start and previous end (1/2/(number of time points between twe indexes) because the interval is too short...
                    if trig_start_lower        <= inter_proto_lower && trig_start_upper > inter_proto_lower 
                        trig_start_lower        = inter_proto_lower;
                    end

                    inter_proto_lower           = (stim_clocks.latency_end_corrected(iProto+first_sleep_ind-2) + ...
                                (stim_clocks.latency_start_corrected(iProto+first_sleep_ind-1) - stim_clocks.latency_end_corrected(iProto+first_sleep_ind-2))/2 ...
                                /(stim_clocks.protocol_ind(iProto+first_sleep_ind-1) - stim_clocks.protocol_ind(iProto+first_sleep_ind-2))^2) * EEG.srate; % between present start and previous end (1/2/(number of time points between twe indexes) because the interval is too short...
                    if env_start_lower         <= inter_proto_lower && env_start_upper > inter_proto_lower 
                        env_start_lower         = inter_proto_lower;
                    end
                end
                if isempty(find(trig_hi_inds    >= trig_start_lower & trig_hi_inds <= trig_start_upper, 1, "first")) % if triggers not found, which means triggers missing
                    trig_start_ind              = env_starts(iProto); % if any trigggers are missing, use stim clock/ENV stim start
                    trig_missing_starts         = [trig_missing_starts trig_start_ind];
                    trig_missing_starts_iProto  = [trig_missing_starts_iProto iProto];
                else
                    trig_start_ind              = trig_hi_inds(find(trig_hi_inds >= trig_start_lower & trig_hi_inds <= trig_start_upper, 1, "first"));
                    if ~isempty(env_hi_inds(find(env_hi_inds >= env_start_lower & env_hi_inds <= env_start_upper, 1, "first"))) & fflag == 0
                        trig_start_1st          = trig_start_ind;
                        fflag                   = 1;
                        env_start_with_trig     = env_hi_inds(find(env_hi_inds >= env_start_lower & env_hi_inds <= env_start_upper, 1, "first"));
                    end
                end
                
                trig_end_lower                  = stim_clocks.latency_end_corrected(iProto+first_sleep_ind-1) * EEG.srate - win_samp(iProto+first_sleep_ind-1);
                trig_end_upper                  = stim_clocks.latency_end_corrected(iProto+first_sleep_ind-1) * EEG.srate + win_samp(iProto+first_sleep_ind-1);
                if iProto < n_proto
                    inter_proto_upper   = (stim_clocks.latency_end_corrected(iProto+first_sleep_ind-1) + ...
                        (stim_clocks.latency_start_corrected(iProto+first_sleep_ind) - stim_clocks.latency_end_corrected(iProto+first_sleep_ind-1))/2 ...
                        /(stim_clocks.protocol_ind(iProto+first_sleep_ind) - stim_clocks.protocol_ind(iProto+first_sleep_ind-1))^2) * EEG.srate; % between present end and next start (1/2/(number of time points between twe indexes) because the interval is too short...
                    if trig_end_upper          >= inter_proto_upper && trig_end_lower < inter_proto_upper
                        trig_end_upper          = inter_proto_upper;
                    end
                end

                if isempty(find(trig_hi_inds    >= trig_end_lower & trig_hi_inds <= trig_end_upper, 1, "last")) % if triggers not found, which means triggers missing
                    trig_end_ind                = env_ends(iProto); % (stim_clocks.latency_end_corrected(iProto+first_sleep_ind-1) + 2) * EEG.srate; % if any trigggers are missing, use env stim time (s) determined above instead, plus 2s for small correction;
                    trig_missing_ends           = [trig_missing_ends trig_end_ind];
                    trig_missing_ends_iProto    = [trig_missing_ends_iProto iProto];
                else
                    trig_end_ind                = trig_hi_inds(find(trig_hi_inds >= trig_end_lower & trig_hi_inds <= trig_end_upper, 1, "last"));
                end
           
                trig_starts                     = [trig_starts trig_start_ind];
                trig_ends                       = [trig_ends trig_end_ind];
            end

            if fflag == 0 % no TRIG triggers were found
                env_start_with_trig             = stim_clocks.latency_start_corrected(first_sleep_ind) * EEG.srate;
                trig_start_1st                  = env_start_with_trig + EEG.srate * diff_start_TRIG_Vs_ENV;
            end

            % check - every stim start should have a stim end
            if length(trig_starts)             ~= length(trig_ends)
                error('number of TRIG stim starts does not match number of stim ends(!) \n')
            end
            
            %% Infer the stim start of missing TRIG triggers
            lantency_correction_TRIGStart       = trig_start_1st/EEG.srate - env_start_with_trig/EEG.srate;
            correction_included                 = ~ismember(trig_missing_starts_iProto, find((env_starts'/EEG.srate - stim_clocks.latency_start_corrected(first_sleep_ind:length(env_starts)+first_sleep_ind-1)) <= diff_start_TRIG_Vs_ENV * 0.9));
            trig_starts(trig_missing_starts_iProto(correction_included))    = trig_starts(trig_missing_starts_iProto(correction_included)) + lantency_correction_TRIGStart * EEG.srate; % trig_starts(trig_missing_starts_iProto)   + lantency_correction_ENVEnd * EEG.srate    + lantency_correction_TRIGStart * EEG.srate; % use it to calculate all TRIG starts

            %% Check detection          
            savepath = fullfile(EEG.filepath, 'processing', 'find_stim');
            if ~exist(savepath)
                mkdir(savepath)
            end

            % cross-reference between SI-ENV and TRIG
            figure; clf
            set(gcf, 'Position', [6 500 1870 242], 'Visible', 'on')
            hold on

            plot(trig_starts(1), 50000, '>', 'Color', 'r')
            plot(env_starts(1), -50000, '>', 'Color', 'g')

            plot(trig_data)
            plot(env_data)

            plot(trig_missing_starts, ones(length(trig_missing_starts)) * 50000 * 2, 'x', 'Color', 'k')
            plot(trig_missing_ends, ones(length(trig_missing_ends)) * 50000 * 2, 'x', 'Color', 'k')
            plot(env_missing_starts, ones(length(env_missing_starts)) * -50000 * 2, 'x', 'Color', 'k')
            plot(env_missing_ends, ones(length(env_missing_ends)) * -50000 * 2, 'x', 'Color', 'k')

            plot(trig_starts, ones(length(trig_starts)) * 50000, '>', 'Color', 'r')
            plot(trig_ends, ones(length(trig_ends)) * 50000, '<', 'Color', 'r')
            plot(env_starts, ones(length(env_starts)) * -50000, '>', 'Color', 'g')
            plot(env_ends, ones(length(env_ends)) * -50000, '<', 'Color', 'g')

            legend('TRIG', 'ENV', '', '', 'Not detected' , 'Location', 'bestoutside')

            % Below section is for any manual adjustments if needed
            % when figuring this out ask yourself; what (if any) protocols
            % show up in SI-ENV but not in TRIG
            % include the indexes of these protocols on top of TRIG indexes
            inds_from_env = []; % HERE(!) 
            inds_from_trig = [1:length(trig_starts)];
            starts = round(sort([env_starts(inds_from_env) trig_starts(inds_from_trig)]));
            ends = round(sort([env_ends(inds_from_env) trig_ends(inds_from_trig)]));

            % figure out what protocol timings cannot be identified in data
            % exclude the index corresponding to the METADATA(!)
            exclude = []; % HERE(!) 
            inds = inds(~ismember(inds,exclude));

            title(sprintf('Stim Timings - BOTH %g Protocols Detected', length(starts)))
            ylim([-250000 250000])
            fontsize(gcf, 14, 'points')

            fprintf('saving %s \n', fullfile(savepath, 'stim_timing_both.png, .fig'))
            saveas(gcf, fullfile(savepath, 'stim_timing_both.png'))
            saveas(gcf, fullfile(savepath, 'stim_timing_both.fig'))

            % auto check step; if # of protocols in metadata does not match
            % # of protocols detected, then throw error
            if length(inds) ~= length(starts)
                error('Number of protocols in metadata=%g does not match number of protocols detected=%g, manual adjustment needed \n', length(inds), length(starts))
            else
                fprintf('Number of protocols in metadata=%g matches number of protocols detected=%g \n', length(inds), length(starts))
            end

            fprintf('PLEASE CHECK Stim Timings Figure to make sure starts and ends are aligned \n')

            %% final output; keep timings in sample space for easy adding
            % events
            ind_proto_metadata = ind_proto_metadata(inds);
            stim_starts_meta = (stim_clocks.latency_start(first_sleep_ind:end) + lantency_correction_manu + diff_start_TRIG_Vs_ENV) * EEG.srate;
            stim_ends_meta = (stim_clocks.latency_end(first_sleep_ind:end) + lantency_correction_manu + 1) * EEG.srate;
            for iProto = 1:length(inds)
                ind_proto_metadata(iProto).timing.duration_backend = ind_proto_metadata(iProto).duration_backend;
                rmfield(ind_proto_metadata(iProto), 'duration_backend');
                ind_proto_metadata(iProto).timing.stim_start_final = starts(iProto);
                ind_proto_metadata(iProto).timing.stim_end_final = ends(iProto);
                ind_proto_metadata(iProto).timing.stim_start_env = env_starts(iProto);
                ind_proto_metadata(iProto).timing.stim_end_env = env_ends(iProto);
                ind_proto_metadata(iProto).timing.stim_start_meta = stim_starts_meta(iProto);
                ind_proto_metadata(iProto).timing.stim_end_meta = stim_ends_meta(iProto);
            end

            if length(types) ~= length(starts)
                error('number of protocols in metadata does not match number of starts or ends')
            end

            fprintf('Protocols Identified: \n')
            % provide duration information in text output to user
            delta_t = (ends - starts) / EEG.srate;
            info = [delta_t' types [1:length(types)]']
            nrem_dur = sum(delta_t(types == 4));
            rem_dur = sum(delta_t(types == 5));

            fprintf('NREM # Protocols = %g \n', length(delta_t(types == 4)))
            fprintf('NREM Stim Duration = %g min \n', nrem_dur / 60)
            
            fprintf('REM # Protocols = %g \n', length(delta_t(types == 5)))
            fprintf('REM Stim Duration = %g min \n', rem_dur / 60)

            nrem_dur = nrem_dur / 60;
            rem_dur = rem_dur / 60;

            fprintf('saving %s \n', fullfile(savepath, 'stim_metadata.mat'))
            save(fullfile(savepath, 'stim_metadata.mat'), 'ind_proto_metadata')

            fprintf('Generating figures for individual protocols... \n')
            Protocol_Identified = [starts' ends' types];
            j = 1;
            for i = 1:length(Protocol_Identified) % ploting the Protocol_Identified for confirmation
                figure; clf
                set(gcf, 'Position', [12 422 1828 450], 'Visible', 'off')
                hold on

                Protocol_start  = Protocol_Identified(i,1) - EEG.srate*20;
                Protocol_end    = Protocol_Identified(i,2) + EEG.srate*20;
                plot(env_data(Protocol_start : Protocol_end))%, 'b')
                plot(trig_data(Protocol_start : Protocol_end))%, 'm')
                plot(Protocol_Identified(i,1) - Protocol_start + 1, 0, '>', 'Color', 'r', 'MarkerSize', 30, 'LineWidth', 2)
                plot(env_starts(i) - Protocol_start + 1, 0, 'V', 'Color', 'g', 'MarkerSize', 10, 'LineWidth', 2)
                plot(stim_starts_meta(i)- Protocol_start + 1, 0, '|', 'Color', 'k', 'MarkerSize', 20, 'LineWidth', 2)
                if Protocol_Identified(i,3) > max_proto_ex
                    if ~isempty(EEG.event)
                        if ~(isempty(manu_start_corr) & isempty(manu_end_corr))
                            if ~isempty(manu_start_corr)
                                plot(manu_start_corr(j,1)- Protocol_start + 1, 0*manu_start_corr(j,1), 'o', 'Color', 'k', 'MarkerSize', 10, 'LineWidth', 2)
                            end
                            if ~isempty(manu_end_corr)
                                plot(manu_end_corr(j,1)  - Protocol_start + 1, 0*manu_end_corr(j,1), 'o', 'Color', 'k', 'MarkerSize', 10, 'LineWidth', 2)
                            end
                            j = j + 1;
                        end
                    end
                end
                plot(Protocol_Identified(i,2) - Protocol_start + 1, 0, '<', 'Color', 'r', 'MarkerSize', 30, 'LineWidth', 2)
                plot(env_ends(i)   - Protocol_start + 1, 0, '^', 'Color', 'g', 'MarkerSize', 10, 'LineWidth', 2)
                plot(stim_ends_meta(i)  - Protocol_start + 1, 0, '|', 'Color', 'k', 'MarkerSize', 20, 'LineWidth', 2)

                if Protocol_Identified(i,3) > max_proto_ex
                    if ~isempty(EEG.event)
                        if ~(isempty(manu_start_corr) & isempty(manu_end_corr))
                            legend('', '', 'TRIG (chosen)', 'ENV', 'Metadata (corrected)', 'Manual Marker')
                        end
                    else
                        legend('', '', 'TRIG (chosen)', 'ENV', 'Metadata (corrected)')
                    end
                else
                    legend('', '', 'TRIG (chosen)', 'ENV', 'Metadata (corrected)')
                end
                
                title(['Protocol Identified - Ind' num2str(i) ' - Type' num2str(Protocol_Identified(i,3))])
                ylim([-150000 150000])
                xlim([-20 * EEG.srate (Protocol_Identified(i,2)-Protocol_Identified(i,1)) + 60 * EEG.srate])
                fontsize(gcf, 14, 'points')
                hold off

                saveas(gcf, fullfile(savepath, ['Protocol_Identified_Ind' num2str(i) '_Type' num2str(Protocol_Identified(i,3)) '.png']))
                close
            end
            fprintf('Done! \n')
            fprintf('Please review individual protocol stim timings figures \n')
            fprintf('Located in: %s \n', fullfile(savepath))

        end %function

        % given EEG data, search for z check protocols and replace
        % their data with NaN
        function EEG = remove_z_checks(EEG)
            starts = []; ends = [];
            for iEv = 1:size(EEG.event,2)
                if strcmp(EEG.event(iEv).type, 'stim start')
                    if EEG.event(iEv).proto_type == 0 | EEG.event(iEv).proto_type == 1
                        starts = [starts EEG.event(iEv).latency];
                    end
                end
            
                if strcmp(EEG.event(iEv).type, 'stim end')
                    if EEG.event(iEv).proto_type == 0 | EEG.event(iEv).proto_type == 1
                        ends = [ends EEG.event(iEv).latency];
                    end
                end
            end

            rej_inds = [starts' ends'];

            % perform NaN replacement
            cd = clean_data;
            EEG = cd.replace_region_wnan(EEG, rej_inds, '_noZ')
        end

        % make summary figures of current, impedance across a set of
        % protocols
        function stim_summary_figs(EEG, dataOut, fieldname)
            % savepath
            savepath = fullfile(EEG.filepath, 'analysis', 'stim', fieldname);
            if ~exist(savepath)
                mkdir(savepath)
            end

            close all

            % plot each individual protocol 
            n_protos = size(dataOut.(fieldname).proto,2);
            for iProto = 1:n_protos
                fprintf('Generating current and impedance figures for protocol %g / %g \n', iProto, n_protos)
                figure(1); clf; hold on
                set(gcf, 'Position', [20 400 600 420], 'Visible', 'off')
                leg_strs = {};
                for iChan = 1:size(dataOut.(fieldname).proto(iProto).stim.stim_data.chan_data,2)
                    plot(dataOut.(fieldname).proto(iProto).stim.stim_data.chan_data(iChan).data_amp, 'linewidth', 2)
                    leg_strs = [leg_strs sprintf('Chan %g, %g mA', dataOut.(fieldname).proto(iProto).stim.stim_data.chan_data(iChan).num, round(dataOut.(fieldname).proto(iProto).stim.stim_data.chan_data(iChan).data_amp_est,2))];
                end
                xlim([0 length(dataOut.(fieldname).proto(iProto).stim.stim_data.chan_data(1).data_amp)])
                tmp = gca;
                ylim([tmp.YLim(1) tmp.YLim(2) + 1])
                ylabel('Current (mA)')
                xlabel('Samples')
                dur = round((dataOut.(fieldname).proto(iProto).stim.stim_data.timing.stim_end_final - dataOut.(fieldname).proto(iProto).stim.stim_data.timing.stim_start_final) / EEG.srate);
                title(sprintf('Protocol Ind: #Run: %g, #Detected: %g, Type: %g, Duration: %g sec', dataOut.(fieldname).proto(iProto).stim.stim_data.proto_ind, dataOut.(fieldname).proto(iProto).abs_proto_n, dataOut.(fieldname).proto(iProto).stim.stim_data.proto_type, dur));
                legend(leg_strs)
                fontsize(gcf, 14, 'points')
                savestr = sprintf('01_protocol_%g_current.png', iProto);
                saveas(gcf, fullfile(savepath, savestr))
                close

                figure(2); clf; hold on
                set(gcf, 'Position', [20 400 600 420], 'Visible', 'off')
                leg_strs = {};
                for iChan = 1:size(dataOut.(fieldname).proto(iProto).stim.stim_data.chan_data,2)
                    plot(dataOut.(fieldname).proto(iProto).stim.stim_data.chan_data(iChan).data_imp, 'linewidth', 2)
                    leg_strs = [leg_strs sprintf('Chan %g, %g Ohm', dataOut.(fieldname).proto(iProto).stim.stim_data.chan_data(iChan).num, round(dataOut.(fieldname).proto(iProto).stim.stim_data.chan_data(iChan).data_imp_est,2))];
                end
                xlim([0 length(dataOut.(fieldname).proto(iProto).stim.stim_data.chan_data(1).data_imp)])
                tmp = gca;
                ylim([tmp.YLim(1) tmp.YLim(2) + 30])
                ylabel('Impedance (Ohm)')
                xlabel('Samples')
                title(sprintf('Protocol Ind: #Run: %g, #Detected: %g, Type: %g, Duration: %g sec', dataOut.(fieldname).proto(iProto).stim.stim_data.proto_ind, dataOut.(fieldname).proto(iProto).abs_proto_n, dataOut.(fieldname).proto(iProto).stim.stim_data.proto_type, dur));
                legend(leg_strs)
                fontsize(gcf, 14, 'points')
                savestr = sprintf('01_protocol_%g_impedance.png', iProto);
                saveas(gcf, fullfile(savepath, savestr))
                close
            end

            % plot across protocols that were included in group-level
            % analysis
            n_protos = size(dataOut.(fieldname).all_protos.stim.stim_data,2);
            n_chans = size(dataOut.(fieldname).all_protos.stim.stim_data(1).chan_data,2);
            times = [];
            i = nan(n_protos, n_chans); z = nan(n_protos, n_chans);
            for iProto = 1:n_protos
                % times = [times EEG.etc.actualTimes(dataOut.(fieldname).proto(iProto).stim.stim_data.timing.stim_start_final)];
                times = [times EEG.etc.actualTimes(round(dataOut.(fieldname).proto(iProto).stim.stim_data.timing.stim_start_final))]; % ~~byFrancis20240903, round to make the index right format, or else error
                for iChan = 1:n_chans
                    i(iProto,iChan) = dataOut.(fieldname).all_protos.stim.stim_data(iProto).chan_data(iChan).data_amp_est;
                    z(iProto,iChan) = dataOut.(fieldname).all_protos.stim.stim_data(iProto).chan_data(iChan).data_imp_est;
                end
            end

            fprintf('Generating current and impedance figures for group-level protocols \n')
            figure(1); clf; hold on
            set(gcf, 'Position', [20 400 600 420], 'Visible', 'off')

            plot(times, i(:,1), '-o', 'MarkerSize', 8, 'MarkerEdgeColor', "#0072BD", 'MarkerFaceColor', "#0072BD")
            plot(times, i(:,2), '-o', 'MarkerSize', 8, 'MarkerEdgeColor', "#D95319", 'MarkerFaceColor', "#D95319")
            yline(mean(i(:,1)), '--', 'color', "#0072BD")
            yline(mean(i(:,2)), '--', 'color', "#D95319")
            legend({'Chan1', 'Chan2', '', ''})

            title(sprintf('%s Protocols N=%g, t=%g min \n', upper(fieldname), n_protos, round(dataOut.(fieldname).all_protos.stim.t_total / 60, 1)))
            xlabel('Time of Night')
            ylabel('Current (mA)')

            tmp = gca;
            ylim([tmp.YLim(1) - 0.1 tmp.YLim(2) + 0.1])

            fontsize(gcf, 14, 'points')
            savestr = '02_group_protocol_current.png';
            saveas(gcf, fullfile(savepath, savestr))
            close

            figure(2); clf; hold on
            set(gcf, 'Position', [20 400 600 420], 'Visible', 'off')

            plot(times, z(:,1), '-o', 'MarkerSize', 8, 'MarkerEdgeColor', "#0072BD", 'MarkerFaceColor', "#0072BD")
            plot(times, z(:,2), '-o', 'MarkerSize', 8, 'MarkerEdgeColor', "#D95319", 'MarkerFaceColor', "#D95319")
            yline(mean(z(:,1)), '--', 'color', "#0072BD")
            yline(mean(z(:,2)), '--', 'color', "#D95319")
            legend({'Chan1', 'Chan2', '', ''})

            title(sprintf('%s Protocols N=%g, t=%g min \n', upper(fieldname), n_protos, round(dataOut.(fieldname).all_protos.stim.t_total / 60, 1)))
            xlabel('Time of Night')
            ylabel('Impedance (Ohm)')

            tmp = gca;
            ylim([tmp.YLim(1) - 20 tmp.YLim(2) + 20])
            fontsize(gcf, 14, 'points')
            savestr = '02_group_protocol_impedance.png';
            saveas(gcf, fullfile(savepath, savestr))
            close
        end

        function parse_stim_pkl_metadata(subj_sess_filepath)
            savepath = fullfile(subj_sess_filepath, 'stim');
            if ~exist(savepath)
                error('stim folder not found \n')
            end

            dirItems = dir(savepath);
            dir_ind = find(contains({dirItems(:).name}, 'ind_proto_metadata.mat'));
            if ~isempty(dir_ind)
                fprintf('ind_proto_metadata.mat file found in stim folder \n')
            else
                fprintf('ind_proto_metadata.mat file not found in stim folder, parsing now \n')
                path_to_ind_protos = fullfile(subj_sess_filepath, 'stim', 'ind_protos');
                dirItems = dir(path_to_ind_protos);
                % main loop, load .mat files output from python script for 
                % each protocol and put into struct
                ind_proto_metadata = struct();
                count = 0;
                for iFile = 1:size(dirItems,1)
                    if contains(dirItems(iFile).name, '.mat')
                        count = count + 1;
                
                        load(fullfile(dirItems(iFile).folder, dirItems(iFile).name))
                
                        ind_proto_metadata(proto_ind).proto_ind = proto_ind;
                        ind_proto_metadata(proto_ind).proto_name = proto_name;
                        ind_proto_metadata(proto_ind).max_dur = max_dur;
                        ind_proto_metadata(proto_ind).ramp_up_dur = ramp_up_dur;
                        ind_proto_metadata(proto_ind).ramp_down_dur = ramp_down_dur;
                
                        ind_proto_metadata(proto_ind).timing.start_time_backend = start_time;
                        ind_proto_metadata(proto_ind).timing.end_time_backend = end_time;
                        ind_proto_metadata(proto_ind).duration_backend = proto_duration;

                        % hacky fix to break up SHAM (type 2) trials into
                        % NREM and REM based on which channels were stim
                        if contains(proto_name, 'SHAM')
                            if num == 1 || num == 2
                                proto_type = 4;
                            elseif num == 3 || num == 4
                                proto_type = 5;
                            else
                                error('Channel Number %g not recognized for SHAM protocols \n', num)
                            end
                        end

                        ind_proto_metadata(proto_ind).proto_type = proto_type;
                
                        chan_ind = split(dirItems(iFile).name, 'chan_');
                        chan_ind = split(chan_ind{2}, '_metadata.mat');
                        chan_ind = str2num(chan_ind{1}) + 1;
                
                        ind_proto_metadata(proto_ind).chan_data(chan_ind).num = num;
                        ind_proto_metadata(proto_ind).chan_data(chan_ind).amp = amp;
                        ind_proto_metadata(proto_ind).chan_data(chan_ind).freq = freq;
                        ind_proto_metadata(proto_ind).chan_data(chan_ind).data_amp = data_amp;
                        ind_proto_metadata(proto_ind).chan_data(chan_ind).data_imp = data_imp;
                        ind_proto_metadata(proto_ind).chan_data(chan_ind).data_ts_plt = data_ts_plt;
                
                        % find single estimate of max current and impedance for each channel
                        % find maximum current value
                        v = max(data_amp);
                        % find indices that correspond to a range around this max
                        inds = find(data_amp >= v - 0.1 & data_amp <= v + 0.1);
                        ind_proto_metadata(proto_ind).chan_data(chan_ind).data_amp_est_inds = inds;
                        ind_proto_metadata(proto_ind).chan_data(chan_ind).data_amp_est = mean(data_amp(inds), 'omitnan');
                        ind_proto_metadata(proto_ind).chan_data(chan_ind).data_imp_est = mean(data_imp(inds), 'omitnan');
                
                    end
                end

                if count == 0
                    error('.mat files for individual protocols are missing, run Python script to parse pkl')
                end

                close all

                % plot the current and impedance for each electrode for each protocol
                for iProto = 1:size(ind_proto_metadata,2)
                    if ~isempty(ind_proto_metadata(iProto).proto_ind)
                        fprintf('Generating current and impedance figures for protocol %g / %g \n', iProto, size(ind_proto_metadata,2))
                        figure(1); clf; hold on
                        set(gcf, 'Position', [20 400 560 420], 'Visible', 'off')
                        leg_strs = {};
                        for iChan = 1:size(ind_proto_metadata(iProto).chan_data,2)
                            plot(ind_proto_metadata(iProto).chan_data(iChan).data_amp, 'linewidth', 2)
                            leg_strs = [leg_strs sprintf('Chan %g, %g mA', ind_proto_metadata(iProto).chan_data(iChan).num, round(ind_proto_metadata(iProto).chan_data(iChan).data_amp_est,2))];
                        end
                        xlim([0 length(ind_proto_metadata(iProto).chan_data(1).data_amp)])
                        tmp = gca;
                        ylim([tmp.YLim(1) tmp.YLim(2) + 1])
                        ylabel('Current (mA)')
                        xlabel('Samples')
                        title(sprintf('Protocol Ind: %g, Type: %g, Duration: %g sec', ind_proto_metadata(iProto).proto_ind, ind_proto_metadata(iProto).proto_type, ind_proto_metadata(iProto).duration_backend))
                        legend(leg_strs)
                        fontsize(gcf, 16, 'points')
                        savestr = sprintf('protocol_%g_current.png', iProto);
                        saveas(gcf, fullfile(path_to_ind_protos, savestr))
                        close

                        figure(2); clf; hold on
                        set(gcf, 'Position', [20 400 560 420], 'Visible', 'off')
                        leg_strs = {};
                        for iChan = 1:size(ind_proto_metadata(iProto).chan_data,2)
                            plot(ind_proto_metadata(iProto).chan_data(iChan).data_imp, 'linewidth', 2)
                            leg_strs = [leg_strs sprintf('Chan %g, %g Ohm', ind_proto_metadata(iProto).chan_data(iChan).num, round(ind_proto_metadata(iProto).chan_data(iChan).data_imp_est,2))];
                        end
                        xlim([0 length(ind_proto_metadata(iProto).chan_data(1).data_imp)])
                        tmp = gca;
                        ylim([tmp.YLim(1) tmp.YLim(2) + 30])
                        ylabel('Impedance (Ohm)')
                        xlabel('Samples')
                        title(sprintf('Protocol Ind: %g, Type: %g, Duration: %g sec', ind_proto_metadata(iProto).proto_ind, ind_proto_metadata(iProto).proto_type, ind_proto_metadata(iProto).duration_backend))
                        legend(leg_strs)
                        fontsize(gcf, 14, 'points')
                        savestr = sprintf('protocol_%g_impedance.png', iProto);
                        saveas(gcf, fullfile(path_to_ind_protos, savestr))
                        close
                    end
                end
                
                % save data from individual protocols in a struct
                dirItems_tmp = dir(savepath);
                dir_ind = find(contains({dirItems_tmp(:).name}, '_metadata.p'));
                str = split(dirItems_tmp(dir_ind).name, '_metadata');
                fprintf('Saving individual protocol data %s \n', fullfile(savepath, sprintf('%s_ind_proto_metadata.mat', str{1})))
                save(fullfile(savepath, sprintf('%s_ind_proto_metadata.mat', str{1})), 'ind_proto_metadata')
                
                % delete all those pesky individual protocol mat files
                resp = input('OK to delete individual protocol .mat files? (y/n): ', 's');
                if resp == 'y'
                    % delete .mat files after info has been extracted
                    for iFile = 1:size(dirItems,1)
                        if contains(dirItems(iFile).name, '.mat')
                            delete(fullfile(dirItems(iFile).folder, dirItems(iFile).name))
                        end
                    end
                    fprintf('individual protocol .mat files deleted \n')
                else
                    fprintf('individual protocol .mat files NOT deleted \n')
                end
            end
        end

    end %methods
end %classdef
