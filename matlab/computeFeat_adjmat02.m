function varargout =computeFeat_adjmat02(xcorr_w1, xcorr_w2, options)
% Computes adjacency matrices from wavelet autocorrelation estimates and
% the proposed graph wavelet features (GWF)
%
% Syntax:
%   adjmatrix = computeFeat_adjmat02(xcorr_w1)
%   adjmatrix = computeFeat_adjmat02(xcorr_w1, xcorr_w2)
%   [A1, GWF1, A2, GWF2, A_cross, GWF_cross] = computeFeat_adjmat02(xcorr_w1, ...
%        xcorr_w2, "ReadDatastoreOutput",0)
%
% Description:
%   This function computes weighted adjacency matrices based on the wavelet
%   autocorrelation estimates from one or two signals. Each wavelet
%   autocorrelation estimates is a cell array of wavelet autocorrelation 
%   coefficients across multiple scales. If xcorr_w2 is provided, 
%   the function also computes a cross-adjacency matrix
%
% Inputs:
%   xcorr_w1 - Cell array (nLevels x 1), wavelet autocorrelation
%   coefficients of signal 1. 
%   xcorr_w2 - (Optional) Cell array (nLevels x 1), wavelet autocorrelation
%   coefficients of signal 2. If empty or omitted, only signal 1 is
%   processed. 
%   options.figuredebug - Logical scalar (default: false).
%              If true, returns 3 plots: A_k, GWF_k, graph_k.
%   options.ReadDatastoreOutput - Logical scalar (default: false).
%              If true, returns a cell array containing all adjacency matrices.
%              If false, returns each matrix as a separate output argument.
%
% Outputs:
%   If options.ReadDatastoreOutput == false (default): 
%     A1       - Adjacency matrix of signal 1
%     GWF1       - Vectorized adjacency matrix of signal 1
%     A2       - Adjacency matrix of signal 2 (if provided)
%     GWF2       - Vectorized adjacency matrix of signal 2 (if provided)
%     A_cross  - Combined adjacency matrix (multigraph) of both signals
%     GWF_cross  - Vectorized combined adjacency matrix
%   If options.ReadDatastoreOutput == true:
%     adjmatrix{1,1} - Adjacency matrix of signal 1
%     adjmatrix{1,2} - Vectorized adjacency matrix of signal 1
%     adjmatrix{1,3} - Adjacency matrix of signal 2 (if provided)
%     adjmatrix{1,4} - Vectorized adjacency matrix of signal 2 (if provided)
%     adjmatrix{1,5} - Combined adjacency matrix (multigraph) of both signals
%     adjmatrix{1,6} - Vectorized combined adjacency matrix
%
% Notes:
%   - The adjacency matrices are symmetric and have zero diagonal.
%   - The function uses Pearson correlation between interpolated wavelet autocorrelation
%     vectors to compute edge weights.
%   - The number of output arguments must match the calling context when
%     options.ReadDatastoreOutput is false.
%
% See also: corrcoef, interp1
% nested functions: elementary_corr
arguments
    xcorr_w1 cell % num of scale x 1 
    xcorr_w2 {mustBeCellorEmpty} = []
    options.figuredebug {mustBeNumericOrLogical} = 0
    options.ReadDatastoreOutput {mustBeNumericOrLogical} = 0 
end


nLevels = numel(xcorr_w1);
[A_signal1,A_vect_signal1]=elementary_corr(xcorr_w1, ...
    xcorr_w1,nLevels);
% A è pesata e la diagonale è tutta 0

adjmatrix{1,1} = A_signal1; % A of graph signal 1
adjmatrix{1,2} = A_vect_signal1; % vectorized A of graph of signal 1;

if iscell(xcorr_w2)
    [A_signal2,A_vect_signal2]=elementary_corr(xcorr_w2, ...
        xcorr_w2,nLevels);
    [A_cross,~]=elementary_corr(xcorr_w1,xcorr_w2);
    A_cross = [A_signal1, A_cross; A_cross, A_signal2];
    A_vect_cross = A_cross(:)'; 
    adjmatrix{1,3} = A_signal2; % A of graph of signal 2
    adjmatrix{1,4} = A_vect_signal2; % vectorized A of graph of signal 2
    adjmatrix{1,5} = A_cross; % A of multigraph
    adjmatrix{1,6} = A_vect_cross; % vectorized A of multigraph
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% Figure debug
if options.figuredebug
    plotAkGWFkGraphk(A_signal1,A_vect_signal1,"name",'Signal 1')
    if iscell(xcorr_w2)
        plotAkGWFkGraphk(A_signal2,A_vect_signal2,"name",'Signal 2')
    end
end

if options.ReadDatastoreOutput
    varargout{1} = adjmatrix;
else
    varargout{1} = A_signal1;
    if nargout > 1
        varargout{2} = A_vect_signal1; 
    end
    if iscell(xcorr_w2)
        if nargout > 2, varargout{3} = A_signal2; end
        if nargout > 3, varargout{4} = A_vect_signal2; end
        if nargout > 4, varargout{5} = A_cross; end
        if nargout > 5, varargout{6} = A_vect_cross; end
    end
end

end %function computeFeat_adjmat02

%%%%%%%%%%%%%%%%%%%%%%%%%%% Nested function %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function [A, A_vect] = elementary_corr(xc_signal1,xc_signal2,nLevels)
% Input:
%    - allscale_modwtautocorr_signal1 and allscale_modwtautocorr_signal1ù
%    -> cell, num of scale modwtautocorr x 1

A = NaN(nLevels); % double, nlevels x nlevels
for w = 1:nLevels % for over levels
    for y = 1:1:nLevels
        d2 = interp1(1:numel(xc_signal2{y}),xc_signal2{y},linspace(1,numel(xc_signal2{y}),numel(xc_signal2{w})));
        A_matrix = corrcoef(xc_signal1{w}, d2);
        A(w,y) = A_matrix(1,2);
    end
end
A = (A+A')/2; %double
% Creare la matrice di adiacenza - gli elementi della diagonale sono 0
A = A - diag(diag(A));
A_vect = A(:)'; % double, 1 x nLevels^2 
end %elementary_corr
function mustBeCellorEmpty(input_variable)
assert(isempty(input_variable) | iscell(input_variable),'Variable must be cell or empty')
end % mustBeCellorEmpty
function plotAkGWFkGraphk(A,A_vect,options)
arguments
    A 
    A_vect 
    options.name =''
    options.label =''
end
fig_Ak = figure('Name',['plotAkGWFkGraphk_Ak' options.name options.label ]);
figure(fig_Ak)
imagesc(A) 
n = size(A,1);   % numero di righe/colonne
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

fig_GWFk = figure('Name',['plotAkGWFkGraphk_GWFk' options.name options.label ]);
figure(fig_GWFk)
if isrow(A_vect)
    GWF_k = A_vect';
end
imagesc(GWF_k); 
colormap turbo;
colorbar; clim(gca,[0,0.25])
set(gca,'FontSize',20,'FontName','Times New Roman')
xticklabels([])
ylabel('$a_{ij}$','Interpreter','latex','FontSize',30)
title('$ \mathbf{f}_k^{(GWF)}$','Interpreter','latex','FontSize',30)

fig_Graphk = figure('Name',['plotAkGWFkGraphk_Graphk' options.name options.label ]);
figure(fig_Graphk)
graph_ex1 = graph(A);
weights = graph_ex1.Edges.Weight;
minWidth = 0.5;  % Larghezza minima dello spessore dell'arco
maxWidth = 2.5;   % Larghezza massima
normalizedWidths = minWidth + (maxWidth - minWidth) * (weights - min(weights)) / (max(weights) - min(weights));
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

end % plotAkGWFkGraphk
function plotMultiGraphk(A,A_vect,options) % da completare
arguments
    A 
    A_vect 
    options.name =''
    options.label =''
end
end % plotMultiGraphk