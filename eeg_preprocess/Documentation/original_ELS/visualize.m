% Plot the first processed EEG file for verification
figure; pop_timtopo(EEG, 1, [0 EEG.xmax*1000], 'EEG Data');
hold on;

% Plot rejection regions (Red patches)
for i = 1:size(EEG.etc.rejRegions, 1)
    x_start = EEG.etc.rejRegions(i, 1) / EEG.srate * 1000; % Convert to ms
    x_end = EEG.etc.rejRegions(i, 2) / EEG.srate * 1000;
    patch([x_start x_end x_end x_start], [0 0 1 1], 'r', 'FaceAlpha', 0.3, 'EdgeColor', 'none');
end

% Highlight critical events (Stim Start in Green, Stim End in Blue)
for i = 1:length(EEG.event)
    if strcmp(EEG.event(i).type, 'stim start')
        x = EEG.event(i).latency / EEG.srate * 1000; % Convert to ms
        line([x x], ylim, 'Color', 'g', 'LineStyle', '--', 'LineWidth', 1);
    elseif strcmp(EEG.event(i).type, 'stim end')
        x = EEG.event(i).latency / EEG.srate * 1000; % Convert to ms
        line([x x], ylim, 'Color', 'b', 'LineStyle', '--', 'LineWidth', 1);
    end
end

legend('EEG Data', 'Rejection Regions (NaNs)', 'Stim Start', 'Stim End');
title('EEG Data with Rejection Regions and Critical Events');
hold off;
