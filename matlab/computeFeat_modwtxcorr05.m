function varargout = computeFeat_modwtxcorr05(signal,fs,wname,options)
% computeFeat_modwtxcorr05 - the function compute a wavelet analysis based
% on MODWT
%
% Syntax:
%   signal_modwtxcorr = computeFeat_modwtxcorr05(signal, fs, ...
%        wname, options)
%   [xcorr, selectedscale, croppedscale] = computeFeat_modwtxcorr05(signal, ...
%        fs, wname, options) 
%
% Description:
%   This function computes the autocorrelation between wavelet coefficients 
%   obtained via MODWT (Maximum Overlap Discrete Wavelet Transform) 
%   of a single-channel signal. 
%
% Inputs:
%   signal      - Row vector (1 x N) containing the signal to analyze 
%                 (single channel only)
%   fs          - Sampling frequency of the signal
%   wname       - Name of the orthogonal wavelet (e.g., 'sym4', 'db6')
%   options     - Structure with the following fields:
%       .win                - segment size around the peak of the
%       autocorrelation at selected scale (default: index_center/4) 
%       .midlevels          - If true, selects only MODWT scales
%       corresponding to 0.5–130 Hz 
%       .ReadDatastoreOutput - If true, returns a single cell array with 3
%       elements; otherwise returns 3 separate outputs 
%       .myvisual           - If true (only valid when ReadDatastoreOutput
%       = false), enables visualization of MODWT and autocorrelation 
%
% Outputs:
%  If options.ReadDatastoreOutput == 0 (default):
%       xcorr         - Cell array of autocorrelations for each scale
%       selectedscale - Vector of the  selected scale
%        WF: segment of the selected scale around the central peak
%   If options.ReadDatastoreOutput == 1:
%       signal_modwtxcorr - 1x3 cell array containing:
%           {1} - xcorr: cell array of autocorrelations for each scale
%           {2} - selectedscale: vector of the selected scale
%           {3} - WF: segment of the selected scale around the central peak
%

%
% Notes:
%   - The function uses modwt and modwtxcorr_stf to decompose the signal
%   and compute cross-correlations. 
%   - If options.midlevels is enabled, only physiologically relevant scales
%   are retained. 
%   - Visualization is available only when ReadDatastoreOutput is disabled.
%
% See also:
%   modwt, modwtxcorr_stf, wfilters, findpeaks
% Nested functions: plotMODWT, plotMODWTXCORRkandWF

arguments
    signal double {mustBeRow} % 1 x nsamples -> un solo canale !
    fs double % sampling frequency
    wname {mustBeText} % Orthogonal wavelet
    options.win double {mustBeScalarOrEmpty} = [] % windows used to consider only some samples around the max peak if [] win=ceil(index_center/4); 
    options.midlevels {mustBeNumericOrLogical} = 0
    options.ReadDatastoreOutput {mustBeNumericOrLogical} = 0 % per gestire K segnali
    options.myvisual {mustBeNumericOrLogical} = 0 % può essere 1 solo se ReadDatastoreOutput = 0
end


w1 = modwt(signal, wname);
[num_computed_levels, N] = size(w1); % number of scales, number of samples 
Nwav = length(wfilters(wname));  % length of wavelet filter
Jmax_nonboundary = min(num_computed_levels,floor(log2(N / (Nwav - 1) + 1))); %num max livelli con coefficienti non-boundary
if options.midlevels
    low_cut = 0.5;
    high_cut = 130;
    num_levels=size(w1,1);
    for j = 1:(num_levels-1)
        if fs/( 2^(j+1) ) > low_cut && fs/( 2^(j) )< high_cut && ~isequal(Jmax_nonboundary,j)
            if ~exist("sel_wavcoef_scale","var")
                sel_wavcoef_scale = j;
            else
                sel_wavcoef_scale = vertcat(sel_wavcoef_scale,j);
            end
        end
    end
    w1_new = w1(sel_wavcoef_scale,:);
    % aggiungere un plot che paragona w1 con w1_new
    if isequal(options.ReadDatastoreOutput,0) && isequal(options.myvisual,1)
        plotMODWT(w1,'old')
        plotMODWT(w1_new,'new')
    end
    w1 = w1_new;
else
    if isequal(options.ReadDatastoreOutput,0) && isequal(options.myvisual,1)
        plotMODWT(w1)
    end    
end

[xcorr, xcorri, lag] = modwtxcorr_stf(w1, w1, wname); %0.95 è di default per CI
% da valutare anche TimeAlign=true, di default è false

scale = ceil(size(xcorr,1)/2 + 1);
selectedscale = xcorr{scale,1}';
[pks,locs] = findpeaks(selectedscale);
[maxpks,idx] = max(pks);
index_center=locs(idx);
if isempty(options.win)
    options.win=ceil(index_center/4); 
end
% Evita out-of-bounds 
min_index = max(1, index_center - options.win);
max_index = min(index_center + options.win, numel(selectedscale));

% Plots
if isequal(options.ReadDatastoreOutput,0) && isequal(options.myvisual,1)
     plotMODWTXCORRkandWF(xcorr,lag,scale,min_index, max_index)
end

% Output
if options.ReadDatastoreOutput
    signal_modwtxcorr = cell(1, 3 ); % Preallocazione 
    signal_modwtxcorr{1, 1} = xcorr;
    signal_modwtxcorr{1, 2} = selectedscale;
    signal_modwtxcorr{1, 3} = selectedscale(1,min_index:max_index);
    varargout{1} = signal_modwtxcorr;
else
    varargout{1} = xcorr; % xcorr di w
    varargout{2} = selectedscale; % selected scale of xcorr di w
    varargout{3} = selectedscale(1,min_index:max_index); % peak-segmented selected scale of xcorr di w
end % if ReadDatastoreOutput
end

function plotMODWT(w,options)
arguments
    w 
    options.figuredescription = []
end
N = size(w,2);
figure('Name',['plotMODWT' options.figuredescription]);
tiledlayout
for j = 1:(size(w,1)-1)
    nexttile
    plot(w(j,:),'LineWidth',1.5)
    set(gca,'FontSize',20,'FontName','Times New Roman')
    title('$ \mathbf{\hat{s}}_k^{(l)} $','Interpreter','latex','FontSize',30)
    xlim([0 N])
end
nexttile
plot(w(end,:))
set(gca,'FontSize',20,'FontName','Times New Roman')
title('Final-level scaling coefficients','Interpreter','latex','FontSize',20)
xlim([0 N])
end

function plotMODWTXCORRkandWF(xcorr,lag,scale,min_index, max_index,options)
arguments
    xcorr 
    lag 
    scale 
    min_index 
    max_index 
    options.figuredescription = [] 
end
Jmax = size(xcorr,1);
figure('Name',['plotMODWTXCORRkandWFk' options.figuredescription]);
tiledlayout
for j = 1:Jmax
    nexttile
    if j == scale
        plot(lag{j,1},xcorr{j,1},'LineWidth',1.5)
        hold on
        % xline(min_index)
        % xline(max_index)
        plot(lag{j,1}(min_index:max_index),xcorr{j,1}(min_index:max_index,1),'LineWidth',1.5)
    else
        plot(lag{j,1},xcorr{j,1},'LineWidth',1.5)
    end
    set(gca,'FontSize',20,'FontName','Times New Roman')
    title('$ \mathbf{r}_{k}^{(l)} $' ,'Interpreter','latex',FontSize=30)
end
end
