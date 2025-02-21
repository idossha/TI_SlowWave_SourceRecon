% MATLAB script to process EEGLAB .set files, count waves per electrode,
% normalize counts using z-scoring, and generate topoplots with fixed color scale

% Clear workspace and command window
clear; clc;

% Add EEGLAB to the MATLAB path
% Update the path to where EEGLAB is installed on your system
addpath('/users/idohaber/documents/matlab/eeglab2024.0'); % replace with your EEGLAB path
eeglab nogui; % Initialize EEGLAB without the GUI

% Define the list of .set files with 'N1' instead of 'n1'
files = {
    '/volumes/csc-ido/analyze/101/N1/strength_101_N1_forsw.set',
    '/volumes/csc-ido/analyze/102/N1/strength_102_N1_forsw.set',
    '/volumes/csc-ido/analyze/107/N1/strength_107_N1_forsw.set',
    '/volumes/csc-ido/analyze/108/N1/strength_108_N1_forsw.set',
    '/volumes/csc-ido/analyze/109/N1/strength_109_N1_forsw.set',
    '/volumes/csc-ido/analyze/110/N1/strength_110_N1_forsw.set',
    '/volumes/csc-ido/analyze/111/N1/strength_111_N1_forsw.set',
    '/volumes/csc-ido/analyze/112/N1/strength_112_N1_forsw.set',
    '/volumes/csc-ido/analyze/114/N1/strength_114_N1_forsw.set',
    '/volumes/csc-ido/analyze/115/N1/strength_115_N1_forsw.set',
    '/volumes/csc-ido/analyze/116/N1/strength_116_N1_forsw.set',
    '/volumes/csc-ido/analyze/117/N1/strength_117_N1_forsw.set',
    '/volumes/csc-ido/analyze/119/N1/strength_119_N1_forsw.set',
    '/volumes/csc-ido/analyze/120/N1/strength_120_N1_forsw.set',
    '/volumes/csc-ido/analyze/121/N1/strength_121_N1_forsw.set',
    '/volumes/csc-ido/analyze/122/N1/strength_122_N1_forsw.set',
    '/volumes/csc-ido/analyze/127/N1/strength_127_N1_forsw.set',
    '/volumes/csc-ido/analyze/132/N1/strength_132_N1_forsw.set'
};

% Define the output directory
output_dir = '/users/idohaber/desktop/Jan_23_Topoplots/first_wave/';
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

% Define fixed color scale limits for z-scored topoplots
fixed_z_limit = 3; % You can adjust this value as needed

% Loop through each file
for i = 1:length(files)
    fname = files{i};
    fprintf('Processing file: %s\n', fname);
    
    % Extract subject and night from the file path
    path_parts = split(fname, filesep);
    subject = path_parts{end-2}; % e.g., '101'
    night = path_parts{end-1};   % e.g., 'N1'
    
    % Construct the path to the corresponding CSV file
    csv_path = sprintf('/volumes/csc-ido/analyze/%s/%s/output/strength_%s_%s_forsw/filtered_epochs_500ms_first.csv', ...
                       subject, night, subject, night);
    
    % Check if the CSV file exists
    if ~exist(csv_path, 'file')
        fprintf('CSV file not found for %s. Skipping...\n', fname);
        continue;
    end
    
    % Load the raw EEG data using EEGLAB
    try
        eeg = pop_loadset('filename', fname);
    catch ME
        fprintf('Error loading .set file for %s: %s\n', fname, ME.message);
        continue;
    end
    
    % Ensure channel locations are available
    if isempty(eeg.chanlocs)
        fprintf('No channel locations found for %s! Skipping...\n', fname);
        continue;
    end
    
    % Load the corresponding CSV file
    try
        df = readtable(csv_path);
    catch ME
        fprintf('Error reading CSV file for %s: %s\n', fname, ME.message);
        continue;
    end
    
    % Check if required columns exist
    required_cols = {'Channel', 'Region_Classification', 'Classification'};
    if ~all(ismember(required_cols, df.Properties.VariableNames))
        fprintf('CSV file for %s is missing required columns. Skipping...\n', fname);
        continue;
    end
    
    % Exclude rows with 'Region_Classification' == 'unclassified'
    df = df(~strcmpi(df.Region_Classification, 'unclassified'), :);
    
    % Count the number of waves per channel
    channel_names = {eeg.chanlocs.labels};
    num_channels = length(channel_names);
    wave_counts = zeros(num_channels, 1);
    
    % Initialize counts for pre-stim, stim, and post-stim
    pre_stim_counts = zeros(num_channels, 1);
    stim_counts = zeros(num_channels, 1);
    post_stim_counts = zeros(num_channels, 1);
    
    % Ensure that the 'Channel' entries match EEG channel labels
    for c = 1:num_channels
        current_channel = channel_names{c};
        wave_counts(c) = sum(strcmpi(df.Channel, current_channel));
        pre_stim_counts(c) = sum(strcmpi(df.Channel, current_channel) & strcmpi(df.Classification, 'pre-stim'));
        stim_counts(c) = sum(strcmpi(df.Channel, current_channel) & strcmpi(df.Classification, 'stim'));
        post_stim_counts(c) = sum(strcmpi(df.Channel, current_channel) & strcmpi(df.Classification, 'post-stim'));
    end
    
    % Create a table for the counts
    counts_table = table(channel_names', wave_counts, pre_stim_counts, stim_counts, post_stim_counts, ...
                        'VariableNames', {'Channel', 'wave_count', 'pre_stim_count', 'stim_count', 'post_stim_count'});
    
    % Define the output CSV file name
    output_csv = fullfile(output_dir, sprintf('wave_counts_%s_%s.csv', subject, night));
    
    % Save the counts to a CSV file
    try
        writetable(counts_table, output_csv);
        fprintf('Wave counts saved to %s\n', output_csv);
    catch ME
        fprintf('Error saving counts for %s: %s\n', fname, ME.message);
    end
    
    %% Normalization by z-scoring with fixed color scale
    
    % Perform z-score normalization for each count type
    z_wave_counts = zscore_fixed(wave_counts);
    z_pre_stim_counts = zscore_fixed(pre_stim_counts);
    z_stim_counts = zscore_fixed(stim_counts);
    z_post_stim_counts = zscore_fixed(post_stim_counts);
    
    % Calculate differences
    stim_minus_pre = stim_counts - pre_stim_counts;
    post_minus_pre = post_stim_counts - pre_stim_counts;
    
    % Z-score normalize the differences
    z_stim_minus_pre = zscore_fixed(stim_minus_pre);
    z_post_minus_pre = zscore_fixed(post_minus_pre);
    
    % Update counts_table with normalized counts and differences
    counts_table.z_wave_count = z_wave_counts;
    counts_table.z_pre_stim_count = z_pre_stim_counts;
    counts_table.z_stim_count = z_stim_counts;
    counts_table.z_post_stim_count = z_post_stim_counts;
    counts_table.z_stim_minus_pre = z_stim_minus_pre;
    counts_table.z_post_minus_pre = z_post_minus_pre;
    
    %% Prepare for Topoplot Generation
    
    % Check if channel locations have valid positions
    if all(~isnan([eeg.chanlocs.X])) && all(~isnan([eeg.chanlocs.Y])) && all(~isnan([eeg.chanlocs.Z]))
        % Channel locations are present
        chanlocs = eeg.chanlocs;
    else
        % If channel locations are missing, apply a standard montage
        fprintf('Channel locations incomplete for %s. Applying standard 10-20 montage.\n', fname);
        try
            eeg = pop_chanedit(eeg, 'lookup','standard-1020.elc'); % Ensure the path to standard montage is correct
            chanlocs = eeg.chanlocs;
        catch ME
            fprintf('Error applying standard montage for %s: %s\n', fname, ME.message);
            continue;
        end
    end
    
    % Function to order data according to channel locations
    order_data = @(data_table_field) arrayfun(@(ch) ...
        data_table_field(strcmpi(counts_table.Channel, ch.labels)), chanlocs, 'UniformOutput', true);
    
    % Extract ordered data
    z_wave_counts_ordered = order_data(counts_table.z_wave_count);
    z_pre_stim_counts_ordered = order_data(counts_table.z_pre_stim_count);
    z_stim_counts_ordered = order_data(counts_table.z_stim_count);
    z_post_stim_counts_ordered = order_data(counts_table.z_post_stim_count);
    z_stim_minus_pre_ordered = order_data(counts_table.z_stim_minus_pre);
    z_post_minus_pre_ordered = order_data(counts_table.z_post_minus_pre);
    
    % Define fixed color scale limits
    fixed_z_limits = [-fixed_z_limit, fixed_z_limit]; % e.g., [-3, 3]
    
    %% Exclude Channels with Zero Waves from Topoplots
    
    % Create a mask for channels with at least one wave
    valid_channels = counts_table.wave_count >= 1;
    valid_channels_ordered = order_data(valid_channels);
    
    % Set data to NaN for channels with zero waves
    z_wave_counts_ordered(~valid_channels_ordered) = NaN;
    z_pre_stim_counts_ordered(~valid_channels_ordered) = NaN;
    z_stim_counts_ordered(~valid_channels_ordered) = NaN;
    z_post_stim_counts_ordered(~valid_channels_ordered) = NaN;
    z_stim_minus_pre_ordered(~valid_channels_ordered) = NaN;
    z_post_minus_pre_ordered(~valid_channels_ordered) = NaN;
    
    %% Generate and Save Topoplots for Counts
    
    % Define titles and output filenames for counts
    counts_info = {
        z_wave_counts_ordered, sprintf('Z-Scored Overall Wave Counts - Subject %s %s', subject, night), ...
            fullfile(output_dir, sprintf('z_wave_counts_topoplot_%s_%s.png', subject, night));
        z_pre_stim_counts_ordered, sprintf('Z-Scored Pre-Stim Wave Counts - Subject %s %s', subject, night), ...
            fullfile(output_dir, sprintf('z_pre_stim_counts_topoplot_%s_%s.png', subject, night));
        z_stim_counts_ordered, sprintf('Z-Scored Stim Wave Counts - Subject %s %s', subject, night), ...
            fullfile(output_dir, sprintf('z_stim_counts_topoplot_%s_%s.png', subject, night));
        z_post_stim_counts_ordered, sprintf('Z-Scored Post-Stim Wave Counts - Subject %s %s', subject, night), ...
            fullfile(output_dir, sprintf('z_post_stim_counts_topoplot_%s_%s.png', subject, night));
    };
    
    % Generate topoplots for each count
    for c = 1:size(counts_info, 1)
        data = counts_info{c,1};
        title_str = counts_info{c,2};
        filename = counts_info{c,3};
        generate_topoplot(data, chanlocs, title_str, filename, fixed_z_limits);
    end
    
    %% Generate and Save Topoplots for Differences
    
    % Define titles and output filenames for differences
    differences_info = {
        z_stim_minus_pre_ordered, sprintf('Z-Scored Stim minus Pre-Stim Wave Counts - Subject %s %s', subject, night), ...
            fullfile(output_dir, sprintf('z_stim_minus_pre_topoplot_%s_%s.png', subject, night));
        z_post_minus_pre_ordered, sprintf('Z-Scored Post-Stim minus Pre-Stim Wave Counts - Subject %s %s', subject, night), ...
            fullfile(output_dir, sprintf('z_post_minus_pre_topoplot_%s_%s.png', subject, night));
    };
    
    % Generate topoplots for each difference
    for d = 1:size(differences_info, 1)
        data = differences_info{d,1};
        title_str = differences_info{d,2};
        filename = differences_info{d,3};
        generate_topoplot(data, chanlocs, title_str, filename, fixed_z_limits);
    end
    
end

fprintf('Processing complete.\n');

%% Helper Functions

% Define the z-score normalization function
function z = zscore_fixed(x)
    % Z-score normalization with omission of NaN values
    z = (x - mean(x, 'omitnan')) / std(x, 'omitnan');
end

% Define the topoplot generation function
function generate_topoplot(data, chanlocs, title_str, output_filename, fixed_z_limits)
    % Function to generate and save a topoplot
    try
        figure('visible', 'off'); % Create a new figure without displaying it
        topoplot(data, chanlocs, 'style', 'map', 'electrodes', 'on', ...
                 'maplimits', fixed_z_limits);
        colorbar;
        caxis(fixed_z_limits); % Ensure colorbar matches the fixed limits
        title(title_str, 'Interpreter', 'none');
        
        % Save the plot as a PNG file
        saveas(gcf, output_filename);
        fprintf('Topoplot saved to %s\n', output_filename);
        close(gcf); % Close the figure
    catch ME
        fprintf('Error generating topoplot: %s\n', ME.message);
        if exist('gcf', 'var')
            close(gcf);
        end
    end
end
