
By: Erin Schaeffer

This block of code allows you to quickly count the amount of stim_start+stim_end event in EEGLAB.

Usgeage: 
1. open MATLAB 
2. Lunch eeglab
3. Load your .set file
4. run the block of code
5. look at `n_proto`


``` MATLAB
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

```
