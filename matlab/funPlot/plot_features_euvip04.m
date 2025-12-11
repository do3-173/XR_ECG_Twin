function plot_features_euvip04(dataname,wname,featname, featvalue,options)

arguments
    dataname {mustBeText} 
    wname {mustBeText} 
end
arguments (Repeating)
    featname {mustBeMember(featname,["Wavelet feature", "Graph feature"])} 
    featvalue cell
end
arguments
    options.save_figure_flag = 0
    options.selObs = 1
end
if options.save_figure_flag
    fig_mainfolderName = '.\features\figure\plot_features_euvip04\' ;
    if ~exist(fig_mainfolderName,'dir')
        disp(['Creating ' fig_mainfolderName])
        mkdir(fig_mainfolderName);
    else
        disp(['Already exist' fig_mainfolderName] )
    end
end

cellfun(@(name,value) plot_feature(name,value,dataname,wname,options.save_figure_flag,options.selObs),featname,featvalue)

function plot_feature(featname,featvalue,dataname,wname,save_figure_flag,selObs)
    dataname = [dataname '_' wname '_' num2str(selObs) 'Obs' ];
    switch featname
        case 'Wavelet feature'
            selChannel = 1;
            % cross-correlation of wavelet coefficients obtained using 
            % modwtxcorr_stf(w1, w1, wname, 0.95), where
            % w1 = modwt(signal_oneChannel, wname);
            xcorr_ww = featvalue(:,1:3:end); % cell, numObsx1
            % scala selezionata
            selected_xcorr_ww = featvalue(:,2:3:end); %numOs x 1
            % scala selezionata finestrata
            winselected_xcorr_ww = featvalue(:,3:3:end); %numOs x 1
    
            xcorr_ww_ex = xcorr_ww{selObs,selChannel}; % cell num of scale x 1    
            selected_xcorr_ww_ex = selected_xcorr_ww{selObs,selChannel};            
            winselected_xcorr_ww_ex = winselected_xcorr_ww{selObs,selChannel};
                     
            num_levels = numel(xcorr_ww_ex);
            fig_rww = figure('Name',[dataname '_rww'] );
            figure(fig_rww)
            for lev=1:num_levels
                subplot(num_levels,1,lev)
                plot(xcorr_ww_ex{lev,1})
                set(gca,'FontSize',20,'FontName','Times New Roman')
                ylabel("Scale "+num2str(lev-1))
            end
            if save_figure_flag
                savefig(fullfile(fig_mainfolderName,[fig_rww.Name '.fig'] ))
            end

            fig_selected_rww = figure('Name',[dataname '_SegSelrww']);
            figure(fig_selected_rww)
            tiledlayout
            nexttile
            plot(selected_xcorr_ww_ex)
            title("Selected scale")
            ylim([-2 2])
            set(gca,'FontSize',20,'FontName','Times New Roman')
            nexttile
            plot(winselected_xcorr_ww_ex,LineWidth=3)
            title("Around the center peak")
            ylim([-2 2])
            set(gca,'FontSize',20,'FontName','Times New Roman')

            if save_figure_flag
                savefig(fullfile(fig_mainfolderName,[fig_selected_rww.Name '.fig'] ))
            end
            % Se ho più di un canale
                % for ch = 1: numel(winselected_ECGdxtautocorr(1,:))
                %     winselected_ECGdxtautocorr_selectedCh = winselected_ECGdxtautocorr(:,ch);
                %     emptyCells = cellfun(@isempty,winselected_ECGdxtautocorr_selectedCh);
                %     numEmpty = sum(emptyCells);
                %     noemptyCells = winselected_ECGdxtautocorr_selectedCh(~emptyCells);
                %     if numEmpty>0
                %         winselected_ECGdxtautocorr_selectedCh(emptyCells) = {ones(size(noemptyCells{1,1}))};
                %     end
                %     winselected_ECGdxtautocorr_selectedCh_mat =cell2mat(winselected_ECGdxtautocorr_selectedCh);
                %     nexttile
                %     imagesc(winselected_ECGdxtautocorr_selectedCh_mat)
                % end 
    
        case 'Graph feature'
            selChannel = 1;
            Adj = featvalue(:, 1:2:end);
            vectAdj = featvalue(:,2:2:end);
            
            graph_ex1 = graph( Adj{selObs, selChannel});
            weights = graph_ex1.Edges.Weight;
            minWidth = 0.5;  % Larghezza minima dello spessore dell'arco
            maxWidth = 2.5;   % Larghezza massima
            normalizedWidths = minWidth + (maxWidth - minWidth) * (weights - min(weights)) / (max(weights) - min(weights));
            fig_graph = figure('Name', [dataname '_Graphrww']);
            p = plot(graph_ex1,'LineWidth', normalizedWidths, 'EdgeCData', graph_ex1.Edges.Weight);%', 'NodeCData',U(:,2));%'EdgeLabel', G.Edges.Weight,
            p.MarkerSize = 20;          % dimensione nodi
            p.NodeFontSize = 30;        % dimensione font label nodi
            p.NodeFontName = 'Times New Roman';
            
            % Etichette nodi da 0 a N-1
            nNodes = numnodes(graph_ex1);
            p.NodeLabel = string(0:nNodes-1);
            
            title('$ \mathcal{G}_k = (\mathcal{V}_k,\mathcal{E}_k)$','Interpreter','latex','FontSize',30)
            colormap turbo;colorbar;
            clim(gca,[0,0.25])
            set(gca,'FontSize',20,'FontName','Times New Roman')
            if save_figure_flag
                savefig(fullfile(fig_mainfolderName,[fig_graph.Name '.fig'] ))
            end

            fig_adj = figure('Name', [dataname '_adj']);
            adj_mat = Adj{selObs, selChannel};
            figure(fig_adj)
            imagesc(adj_mat)
            n = size(adj_mat,1);   % numero di righe/colonne
            xticks(1:n)      % tick sulle posizioni interne della matrice
            yticks(1:n)
            xticklabels(0:n-1)   % label da 0 a n-1
            yticklabels(0:n-1)
            
            colormap turbo; colorbar;
            clim(gca,[0,0.25])
            set(gca,'FontSize',20,'FontName','Times New Roman')
            xlabel('$j$','Interpreter','latex','FontSize',30)
            ylabel('$i$','Interpreter','latex','FontSize',30)
            title('$ \mathbf{A}_k, a_{ij} = \frac{ < \mathbf{r}_{k}^{(i)} ,\mathbf{r}_{k}^{(j)} >}{ |\mathbf{r}_{k}^{(i)}||\mathbf{r}_{k}^{(j)}|}  $', ...
                'Interpreter','latex','FontSize',30)
            if save_figure_flag
                savefig(fullfile(fig_mainfolderName,[fig_adj.Name '.fig'] ))
            end


        case 'Multilayer graph'
            % G_Multi_example=graph(A_all_mat_Multi{num_example}-diag(diag(A_all_mat_Multi{num_example})));
            % figure(Name='Graphs subplot')
            % tiledlayout(1,3)
            % nexttile, p=plot(G_ECG_example),title('ECG'), p.NodeColor = 'r',p.LineWidth=12*G_ECG_example.Edges.Weight;
            % nexttile, p=plot(G_GSR_example),title('GSR'), p.NodeColor = 'r',p.LineWidth=12*G_GSR_example.Edges.Weight;
            % x_coords = p.XData;
            % y_coords = p.YData;
            % nexttile, p=plot(G_Multi_example),title('Multi'), p.NodeColor = 'r',p.LineWidth=12*G_Multi_example.Edges.Weight;
            % drawnow
            
    end % switch
  
    end
end