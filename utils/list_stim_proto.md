
```matlab
% By E.S 
% find starts, ends, types for each protocol
starts = []; ends = []; types = [];
for iEv = 1:size(EEG.event,2)
if strcmp(EEG.event(iEv).type, 'stim start') & EEG.event(iEv).proto_type ~= 0 & EEG.event(iEv).proto_type ~= 1
starts = [starts (EEG.event(iEv).latency / EEG.srate)];
types = [types EEG.event(iEv).proto_type];
end
if strcmp(EEG.event(iEv).type, 'stim end') & EEG.event(iEv).proto_type ~= 0 & EEG.event(iEv).proto_type ~= 1
ends = [ends (EEG.event(iEv).latency / EEG.srate)];
end
end
n_proto = length(starts);
proto_lst = [1:n_proto];

n_proto
starts
ends
```



% By E.S 
% find starts, ends, types for each protocol
starts = []; ends = []; types = [];
for iEv = 1:size(EEG_forICA.event,2)
if strcmp(EEG_forICA.event(iEv).type, 'stim start') & EEG.event(iEv).proto_type ~= 0 & EEG_forICA.event(iEv).proto_type ~= 1
starts = [starts (EEG.event(iEv).latency / EEG.srate)];
types = [types EEG.event(iEv).proto_type];
end
if strcmp(EEG_forICA.event(iEv).type, 'stim end') & EEG_forICA.event(iEv).proto_type ~= 0 & EEG_forICA.event(iEv).proto_type ~= 1
ends = [ends (EEG.event(iEv).latency / EEG.srate)];
end
end
n_proto = length(starts);
proto_lst = [1:n_proto];

n_proto
starts
ends
