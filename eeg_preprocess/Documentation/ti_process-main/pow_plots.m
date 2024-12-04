% pow_plots.m
% v.0.0.0 - initial commit
% last ()
% use - generate figures for power analyses

classdef pow_plots
    methods(Static)
        % plot different figures to show power analysis results
        function pow_results(dataOut, fieldname, whichProtos)
            % create savepath for figures
            savepath = fullfile(dataOut.savepath, fieldname, whichProtos);
            if ~exist(savepath)
                mkdir(savepath)
            end

            % analysis window names
            analyze_interval_names = {'pre', 'stim', 'post'};

            % init info
            n_chans = dataOut.chanInfo.n_chans;
            n_bands = size(dataOut.freqInfo,2);

            if strcmp(whichProtos, 'individual')
                n_protos = size(dataOut.(fieldname).proto,2);
            elseif strcmp(whichProtos, 'group')
                n_protos = 1;
            else
                error('Choose individual or group for whichProtos to plot \n')
            end

            for iProto = 1:n_protos
                analyze_interval_topo_data = {}; analyze_interval_psd_data = {}; topo_cax_lims = nan(n_bands,2);
                for iAnName = 1:numel(analyze_interval_names)
                    analyze_interval_name = analyze_interval_names{iAnName};

                    fprintf('\n')
                    fprintf('Generating figs for %s protocol %g %s \n', whichProtos, iProto, analyze_interval_name)
                    
                    if strcmp(whichProtos, 'individual')
                        proto_txt = iProto;
                        t_total = round(dataOut.(fieldname).proto(iProto).(analyze_interval_name).t_total / 60,1);
                        ss = num2str(unique(dataOut.(fieldname).proto(iProto).(analyze_interval_name).sleep_stages));
                        
                        f_ax = dataOut.(fieldname).proto(iProto).(analyze_interval_name).f_ax;
                        t_ax = dataOut.(fieldname).proto(iProto).(analyze_interval_name).t_ax;
                        t_ax = t_ax - t_ax(1);

                        psd = dataOut.(fieldname).proto(iProto).(analyze_interval_name).psd;
                        pow = dataOut.(fieldname).proto(iProto).(analyze_interval_name).pow;
                        banded_pow = dataOut.(fieldname).proto(iProto).(analyze_interval_name).banded_pow;
                        banded_psd = dataOut.(fieldname).proto(iProto).(analyze_interval_name).banded_psd;

                    else
                        proto_txt = length(dataOut.(fieldname).all_protos.(analyze_interval_name).protos_include);
                        t_total = round(dataOut.(fieldname).all_protos.(analyze_interval_name).t_total / 60,1);
                        ss = num2str(dataOut.(fieldname).all_protos.(analyze_interval_name).sleep_stages);

                        f_ax = dataOut.(fieldname).all_protos.(analyze_interval_name).f_ax;
                        t_ax = dataOut.(fieldname).all_protos.(analyze_interval_name).t_ax;

                        % take mean xproto
                        psd = squeeze(mean(dataOut.(fieldname).all_protos.(analyze_interval_name).psd,1,'omitnan'));
                        pow = squeeze(mean(dataOut.(fieldname).all_protos.(analyze_interval_name).pow,1,'omitnan'));
                        banded_psd = squeeze(mean(dataOut.(fieldname).all_protos.(analyze_interval_name).banded_psd,1,'omitnan'));
                        banded_pow = squeeze(mean(dataOut.(fieldname).all_protos.(analyze_interval_name).banded_pow,1,'omitnan'));
                    end

                    analyze_interval_topo_data = [analyze_interval_topo_data banded_psd];
                    analyze_interval_psd_data = [analyze_interval_psd_data psd];

                    % FIGURE 1 - pow v. freq
                    figure(2); clf
                    hold on
                    set(gcf, 'Position', [25 505 724 620], 'Visible', 'off')
                    for iChan = 1:n_chans
                        p = psd(iChan,:);
                        plot(f_ax, p, 'linewidth', 1)
                    end

                    % mean xchan
                    mu = squeeze(mean(psd,1,'omitnan'));

                    plot(f_ax, mu, 'linewidth', 2, 'color', 'k')
                    xlim([0 25])
                    ylim([-20 30])
                    xlabel('Freq (Hz)')
                    ylabel('Power Spectral Density (dB / Hz)')
                    fontsize(gcf, 16, 'points')
                    sgtitle(sprintf('%s %s Proto: %g, Chans: %g, Time: %g min, Stages: %s', upper(fieldname), upper(analyze_interval_name), proto_txt, n_chans, t_total, ss))
                    savestr = sprintf('%02d_1_pow_v_freq_%g%s.png', iProto, iAnName, analyze_interval_name);
                    fprintf('saving %s \n', fullfile(savepath, savestr))
                    saveas(gcf, fullfile(savepath, savestr))
                    close

                    % FIGURE 2 - spec v. time
                    figure(3); clf
                    set(gcf, 'Visible', 'off', 'Position', [6 600 1700 600])

                    tf = squeeze(mean(pow(:,:, f_ax <= 25), 1, 'omitnan'));

                    imagesc(t_ax, f_ax(f_ax <= 25), flipud(tf'))

                    colormap(brewermap([], '*RdYlBu'))
                    cb = colorbar();
                    clim([35 85])
                    ylabel(cb, 'Decibels (dB)')

                    yticklabels(fliplr([0:5:25]))
                    xlabel('Time (sec)')
                    ylabel('Freq (Hz)')

                    sgtitle(sprintf('%s %s Proto: %g, Chans: %g, Time: %g min, Stages: %s', upper(fieldname), upper(analyze_interval_name), proto_txt, n_chans, t_total, ss))
                    fontsize(gcf, 16, 'points')
                    savestr = sprintf('%02d_2_spec_v_time_%g%s.png', iProto, iAnName, analyze_interval_name);
                    fprintf('saving %s \n', fullfile(savepath, savestr))
                    saveas(gcf, fullfile(savepath, savestr))
                    close

                    % FIGURE 3 - banded spec v. time
                    figure(4); clf
                    set(gcf, 'Visible', 'off', 'Position', [6 600 1700 400])

                    % mean xchan
                    tf = squeeze(mean(banded_pow,1,'omitnan'));

                    imagesc(t_ax, [1:n_bands], flipud(tf'))

                    yticks([1:n_bands])
                    yticklabels(fliplr({dataOut.freqInfo.name}))
                    xlabel('Time (sec)')

                    colormap(brewermap([], '*RdYlBu'))
                    cb = colorbar();
                    clim([35 75])
                    ylabel(cb, 'Decibels (dB)')

                    sgtitle(sprintf('%s %s Proto: %g, Chans: %g, Time: %g min, Stages: %s', upper(fieldname), upper(analyze_interval_name), proto_txt, n_chans, t_total, ss))
                    fontsize(gcf, 16, 'points')
                    savestr = sprintf('%02d_3_banded_spec_v_time_%g%s.png', iProto, iAnName, analyze_interval_name);
                    fprintf('saving %s \n', fullfile(savepath, savestr))
                    saveas(gcf, fullfile(savepath, savestr))
                    close

                    % FIGURE 4 - banded pow v. time
                    figure(5); clf
                    set(gcf, 'Visible', 'off', 'Position', [6 600 1700 1500])

                    % mean xchan
                    tf = squeeze(mean(banded_pow,1,'omitnan'));

                    for iBand = 1:n_bands
                        subplot(n_bands, 1, iBand)
                        hold on
                        plot(t_ax, tf(:,iBand), '-o', 'color', [0.5 0.5 0.5], 'linewidth', 1.5)
                        yline(mean(tf(:,iBand), 'omitnan'), 'color', 'r', 'linewidth', 1, 'linestyle', '--')

                        if iBand == n_bands
                            ylabel('Decibels (dB)')
                            xlabel('Time (min)')
                        end

                        title(dataOut.freqInfo(iBand).name)
                        xlim([t_ax(1) t_ax(end)])
                    end

                    fontsize(gcf, 16, 'points')
                    sgtitle(sprintf('%s %s Proto: %g, Chans: %g, Time: %g min, Stages: %s', upper(fieldname), upper(analyze_interval_name), proto_txt, n_chans, t_total, ss))
                    savestr = sprintf('%02d_4_banded_pow_v_time_%g%s.png', iProto, iAnName, analyze_interval_name);
                    fprintf('saving %s \n', fullfile(savepath, savestr))
                    saveas(gcf, fullfile(savepath, savestr))
                    close

                    % FIGURE 5 - banded psd topoplot 2 ways - Z-scored and
                    % min/max
                    for i = 1:2
                        figure(6); clf
                        set(gcf, 'Position', [14 650 2000 400], 'Visible', 'off')
                        for iBand = 1:n_bands
                            subplot_tight(1, n_bands, iBand, 0.01);
    
                            if ~isempty(find(~isnan(banded_psd)))
                                if i == 1
                                    % Z-score topoplot data
                                    topodata = (banded_psd(:,iBand) - mean(banded_psd(:,iBand),'omitnan')) / std(banded_psd(:,iBand),'omitnan');
                                    topoplot(topodata, dataOut.chanInfo.chanlocs, 'electrodes', 'on', 'style', 'both', 'maplimits', [-3 3]);
                                    if iBand == 1
                                       cb = colorbar();
                                       ylabel(cb, 'Z-Score')
                                    end
                                else
                                    % min/max topoplot data 
                                    % pull cax values from first min/max topo
                                    % and apply to all other topos for a
                                    % given protocol
                                    if iAnName == 1
                                        topoplot(banded_psd(:,iBand), dataOut.chanInfo.chanlocs, 'electrodes', 'on', 'style', 'both', 'maplimits', 'minmax');
                                        cb = colorbar();
                                        topo_cax_lims(iBand,1) = cb.Limits(1);
                                        topo_cax_lims(iBand,2) = cb.Limits(2);
                                        topoplot(banded_psd(:,iBand), dataOut.chanInfo.chanlocs, 'electrodes', 'on', 'style', 'both', 'maplimits', [topo_cax_lims(iBand,1) topo_cax_lims(iBand,2)]);
                                        cb = colorbar();
                                    else
                                        % if no data from first min/max
                                        % topo just use min/max
                                        if isnan(topo_cax_lims(1,1))
                                            topoplot(banded_psd(:,iBand), dataOut.chanInfo.chanlocs, 'electrodes', 'on', 'style', 'both', 'maplimits', 'minmax');
                                        else
                                            topoplot(banded_psd(:,iBand), dataOut.chanInfo.chanlocs, 'electrodes', 'on', 'style', 'both', 'maplimits', [topo_cax_lims(iBand,1) topo_cax_lims(iBand,2)]);
                                        end
                                        cb = colorbar();
                                    end
                                    if iBand == 1
                                       ylabel(cb, 'PSD (dB / Hz)')
                                    end
                                end

                                title(dataOut.freqInfo(iBand).name)
                                colormap(brewermap([], '*RdYlBu'))
                            end
                        end
                        fontsize(gcf, 16, 'points')
                        sgtitle(sprintf('%s %s Proto: %g, Chans: %g, Time: %g min, Stages: %s', upper(fieldname), upper(analyze_interval_name), proto_txt, n_chans, t_total, ss))
                        savestr = sprintf('%02d_%g_banded_pow_topo_%g%s.png', iProto, 4+i, iAnName, analyze_interval_name);
                        fprintf('saving %s \n', fullfile(savepath, savestr))
                        saveas(gcf, fullfile(savepath, savestr))
                        close
                    end
                end

                % calculate difference in psd for each condition
                % check that condition order is as expected
                check = strcmp(analyze_interval_names{1}, 'pre') & strcmp(analyze_interval_names{2}, 'stim') & strcmp(analyze_interval_names{3}, 'post');
                if ~check
                    error('analyze_interval_names order must be pre, stim, post to run difference plots')
                end

                fprintf('\n')
                fprintf('Generating diff figs for %s protocol %g \n', whichProtos, iProto)

                % define which diff to take [a b] is a-b
                diffs = {[2 1], [2 3], [3 1]}; 
                for iDiff = 1:numel(diffs)
                    d_name1 = analyze_interval_names{diffs{iDiff}(1)};
                    d_name2 = analyze_interval_names{diffs{iDiff}(2)};
                    title_str = sprintf('%s-%s', upper(d_name1), upper(d_name2));

                    d1 = analyze_interval_topo_data{diffs{iDiff}(1)};
                    d2 = analyze_interval_topo_data{diffs{iDiff}(2)};

                    % FIGURE 6 - banded psd topoplot differences
                    for i = 1:2
                        figure(7); clf
                        set(gcf, 'Position', [14 650 2000 400], 'Visible', 'off')
                        for iBand = 1:n_bands
                            subplot_tight(1, n_bands, iBand, 0.01);
    
                            % Z-score psd data
                            d1_z = (d1(:,iBand) - mean(d1(:,iBand),'omitnan')) / std(d1(:,iBand),'omitnan');
                            d2_z = (d2(:,iBand) - mean(d2(:,iBand),'omitnan')) / std(d2(:,iBand),'omitnan');
    
                            if ~isempty(find(~isnan(d1_z))) && ~isempty(find(~isnan(d2_z)))
                                if i == 1
                                    diff = d1_z - d2_z;
                                    topoplot(diff, dataOut.chanInfo.chanlocs, 'electrodes', 'on', 'style', 'both', 'maplimits', [-0.3 0.3]);
                                    if iBand == 1
                                        cb = colorbar();
                                        ylabel(cb, 'Z-Score Diff')
                                    end
                                else
                                    topoplot(d1(:,iBand) - d2(:,iBand), dataOut.chanInfo.chanlocs, 'electrodes', 'on', 'style', 'both', 'maplimits', [-1 1]);
                                    if iBand == 1
                                       cb = colorbar();
                                       ylabel(cb, 'PSD Diff (dB / Hz)')
                                    end
                                end
    
                                title(dataOut.freqInfo(iBand).name)
                                colormap(brewermap([], '*RdYlBu'))
                            end
                        end
                        sgtitle(title_str)
                        fontsize(gcf, 16, 'points')
                        savestr = sprintf('%02d_%g_banded_pow_topo_%g%s.png', iProto, 6+i, iDiff, title_str);
                        fprintf('saving %s \n', fullfile(savepath, savestr))
                        saveas(gcf, fullfile(savepath, savestr))
                        close
                    end

                    % FIGURE 7 - pow v. freq differences
                    d1 = analyze_interval_psd_data{diffs{iDiff}(1)};
                    d2 = analyze_interval_psd_data{diffs{iDiff}(2)};

                    diff = d1 - d2;

                    figure(8); clf
                    hold on
                    set(gcf, 'Position', [25 505 724 620], 'Visible', 'off')
                    for iChan = 1:n_chans
                        p = diff(iChan,:);
                        plot(f_ax, p, 'linewidth', 1, 'color', [0.7 0.7 0.7])
                    end

                    % mean xchan
                    mu = squeeze(mean(diff,1,'omitnan'));
                    sd = squeeze(std(diff,0,1,'omitnan'));
                    ub = mu + sd;
                    lb = mu - sd;

                    plot(f_ax, mu, 'color', 'k', 'linewidth', 1.5)
                    plot(f_ax, ub, 'color', 'k', 'linewidth', 1, 'linestyle', '--')
                    plot(f_ax, lb, 'color', 'k', 'linewidth', 1, 'linestyle', '--')
                    yline(0, 'color', 'r', 'linewidth', 0.5, 'linestyle', '--')

                    xlim([0 25])
                    ylim([-4 4])
                    xlabel('Freq (Hz)')
                    ylabel('Power Spectral Density Diff (dB / Hz)')
                    fontsize(gcf, 16, 'points')
                    sgtitle(title_str)
                    savestr = sprintf('%02d_9_pow_v_freq_%g%s.png', iProto, iDiff, title_str);
                    fprintf('saving %s \n', fullfile(savepath, savestr))
                    saveas(gcf, fullfile(savepath, savestr))
                    close
                end
            end
        end %function
        
    end %methods
end %classdef
