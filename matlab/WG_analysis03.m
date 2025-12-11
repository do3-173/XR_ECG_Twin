function results_WGanalysis = WG_analysis03(datacell, labels,fs,wname_cell, options)
% WG_analysis03 - Extracts wavelet and graph-based features from labeled
% signals 
%
% Syntax:
%   results_WGanalysis = WG_analysis03(datacell, labels, fs, datasetname, wname_cell)
%   results_WGanalysis = WG_analysis03(datacell, labels, fs,datasetname, wname_cell, options)
%
% Description:
%   This function performs Wavelet Graph (WG) analysis on a set of K
%   labeled signals. 
%   Each signal is processed using one or more wavelet functions specified
%   in wname_cell. 
%   The analysis extracts two types of features:
%     - Wavelet Features (WF): obtained via peak-segmented autocorrelation
%     of wavelet coefficients at selected level
%     - Graph Wavelet Features (GWF): derived from adjacency matrices
%     computed from wavelet autocorrelation estimates
%
%   The function internally calls:
%     - computeFeat_modwtxcorr05.m to compute WF
%     - computeFeat_adjmat02.m to compute GWF
%
%   The output is a struct variable results_WGanalysis, where each field corresponds
%   to a wavelet function used. Each field contains the following subfields:
%     - rww : wavelet autocorrelation estimates (cell array)
%     - WF  : extracted wavelet features (cell array)
%     - A   : adjacency matrices (cell array)
%     - GWF : extracted graph wavelet features (cell array)
%
% Inputs:
%   datacell       - Cell array containing K raw signals
%   labels         - Cell array of class labels for K signals
%   fs             - Sampling frequency (scalar)
%   datasetname    - Dataset name
%   wname_cell     - Cell array of wavelet function names (e.g., {'db4','sym5'})
%
% Optional Name-Value Pair Arguments (inside 'options' struct):
%   win                - Scalar, number of samples retained after peak segmentation (default: [])
%   midlevels          - Logical flag to select only mid-level wavelet coefficients (default: 0)
%   display_figure_flag- Logical flag to enable plotting of features and graphs (default: 0)
%   datacellname       - String used for figure titles and saving (default: "")
%   save_figure_flag   - Logical flag to save generated figures (default: 0)
%
% Outputs:
%   results_WGanalysis - Struct with one field per wavelet function used.
%                        Each field contains subfields: rww, WF, A, GWF
%
% Notes:
%   - WF extraction can be customized via the 'options' struct.
%
% See also: computeFeat_modwtxcorr05, computeFeat_adjmat02, 
% plot_features_euvip04, plot_datarawAmp

arguments
    datacell cell % contains K signals -> raw data
    labels % contains K labels
    fs (1,1) double % 
    wname_cell cell 
    options.win double {mustBeScalarOrEmpty}  = []
    options.midlevels {mustBeNumericOrLogical} = 0
    options.display_figure_flag {mustBeNumericOrLogical} = 0
    options.datacellname {mustBeText} = ''
    options.save_figure_flag = 0
end
if options.display_figure_flag
    num_exs_toplot = 3; % numero di segnali di cui voglio visualizzare gli steps
    rng(5) % per riproducibilità
    K = numel(datacell);
    idx_exs = randsample(K, num_exs_toplot);
    % Indici degli esempi da plottare, devono essere numeri interi 
    % random compresi tra 1 e il numero totale dei segnali
    TF = ismember(1:K, idx_exs) ; % vettore logico, true se l'indice è contenuto in idx_exs
    TF = num2cell(TF'); % trasformo in cell, poiché uso cellfun per gli steps
else 
    TF = zeros( size(datacell));
    TF = num2cell(TF); % trasformo in cell, poiché uso cellfun per gli steps
end

wname_xsave = cellfun(@(wname) strrep(wname,'.','point'),wname_cell,'UniformOutput',false);
for idx_wname = 1:numel(wname_cell)
    wname = wname_cell{idx_wname};
    [rww,selscale_rww,WF] = cellfun(@(signal,myvisual) computeFeat_modwtxcorr05(signal, ...
        fs,wname,"win",options.win,"midlevels",options.midlevels,"myvisual",myvisual), ...
        datacell,TF,'UniformOutput',false );
    % rww -> cell, numObs x numChannel, numChannel = 1
    % Proposed wavelet features (WF) = peak-segmented selected scale of rww 
    %cell, numObs x numChannels
    [A,GWF] = cellfun(@(rww_k,myvisual) computeFeat_adjmat02(rww_k,[],"figuredebug",myvisual), ...
        rww,TF,'UniformOutput',false);
    % Proposed graph wavelet features (GWF) = vectorized version of A 
    results_WGanalysis.(wname_xsave{idx_wname}).rww = rww;
    results_WGanalysis.(wname_xsave{idx_wname}).A = A;
    features_waveletgraph = table(cell2mat(WF),cell2mat(GWF));
    features_waveletgraph.Properties.VariableNames = {'WF','GWF'};
    results_WGanalysis.(wname_xsave{idx_wname}).features_waveletgraph = features_waveletgraph;
    
    if options.display_figure_flag && ~isempty('options.datacellname')
        addpath(".\funPlot\")
        classes = unique(labels);
        for idx_class = 1:length(classes)
            classname = classes{idx_class,1};
            true_classname = strcmp(labels, classname);
            idx_true = find(true_classname);
            plot_features_euvip04(options.datacellname, wname_xsave{idx_wname}, ...
                "Wavelet feature",[rww,selscale_rww,WF], ...
                "Graph feature",[A,GWF], ...
                "save_figure_flag",options.save_figure_flag, ...
                "selObs",idx_true(1));
        end
        WF_mat = cell2mat(WF);
        titlename = [options.datacellname wname_xsave{idx_wname} 'SegSelScalerww_AllObs'];
        plot_datarawAmp(WF_mat, "WF",options.datacellname, labels,'titlename',titlename);
        GWF_mat = cell2mat(GWF);
        titlename = [options.datacellname wname_xsave{idx_wname} 'vectA_AllObs'];
        plot_datarawAmp(GWF_mat, "GWF",options.datacellname, labels,'titlename',titlename);          
    end
end %for - wname
