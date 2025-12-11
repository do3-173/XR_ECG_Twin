function [ECGs_VTF,correct] = ECG_XR_04(ECGsignals,fs,options)
% ECG_XR_04 - main function to extract ECG vertex time features
%
% Syntax:
%   ECGs_VTF = ECG_XR_04(ECGsignals,fs)
%
% Description:
%   For each k-th signal, segment the beats and align them.
%   For each i-th beat, identify the Q, R, and S points of the QRS complex.
%   If the operation is successful, it returns true.
%   If true, for the k-th signal we have noBeats, and the L1-principal
%   component analysis returns the k-th eigenbeat and its respective Q, R, and S points.
%   Missing landmarks related to the P wave and T wave are identified.
%   In the heart point cloud, 8 anatomical regions are identified.
%   Two signals are constructed on the graph (heart point cloud): the first
%   contains only the information about depolarization and
%   repolarization of the 8 regions, the second associates each region
%   with the amplitude of the eigenbeat.
%
% Input:
%   ECGsignals - cell, K x 1. K is the total number of signals. The k-th
%   signal is a row vector of dimensions 1 x nsamples.
%   fs         - Sampling frequency of the ECG signal (Hz).
%   pcname     - str, heart point cloud: heart2k heart18k heart92k
%
% Output:
%   ECGs_VTF  - Kc x M_times_bin, Kc < K, number of signals from
%   which it was possible to extract the features
%   correct - logical vector K x 1, contains 1 only if the features
%   were successfully extracted
%
% Dipendenze:
%   - toolbox_graph
%   - MyCrustOpen070909
%   - crea_tensore02
%   - l1pca
%   - funzione_vertextime_analysis
%   - vertex2mesh_journal_02
%   - compute_mesh_laplacian
arguments
    ECGsignals 
    fs 
    options.figuredebug = 0
    options.pcname {mustBeMember(options.pcname,{'heart2k','heart18k','heart92k'})} = 'heart2k'
    options.Nlow {mustBeLessThanOrEqual(options.Nlow,50)} = 10
    options.Nhigh {mustBeLessThanOrEqual(options.Nhigh,50)} = 10
    options.VTFtype {mustBeMember(options.VTFtype,{'GFT_ideal','GFT_eigen'})} = 'GFT_eigen'
end
if options.figuredebug % select signals' idx to visualize them steps
    num_exs_toplot = 1; % no signals
    rng(5) % reproducibility 
    K = numel(ECGsignals);
    idx_exs = randsample(K, num_exs_toplot); % int random number
    TF = ismember(1:K, idx_exs) ; % logical, true if index in idx_exs
    TF = num2cell(TF'); % convert to cell
else 
    TF = zeros( size(ECGsignals));
    TF = num2cell(TF); %  convert to cell
end


ref_folder='.\';%stf
%addpath(genpath([[ref_folder 'iso2mesh-master']]))
addpath(genpath([ [ref_folder 'toolbox_graph']]))
addpath(genpath([ [ref_folder 'MyCrustOpen070909']]))

Params.fs=fs;% check for each database
%% ECG signals processing
[tensor_ecgbeats, ECGs_detectedLandmarks, correct]=crea_tensore02(ECGsignals,Params,options.figuredebug);
[ECGs_eigenLandmarks_ms, ECGs_t_ms, ECGs_eigenbeat] = compute_eigenECGAndLandmarks01(tensor_ecgbeats,ECGs_detectedLandmarks,fs,options.figuredebug);
%% Heart point cloud processing
% load point cloud and build signal on point cloud
basePath = fullfile('.', 'Data');
matFile = fullfile(basePath, options.pcname + ".mat");
plyFile = fullfile(basePath, options.pcname + ".ply");
switch true
    case isfile(matFile)
        pc = importdata(matFile);
    case isfile(plyFile)
        pc = pcread(plyFile);
    otherwise
        error('File "%s" non trovato in formato .mat o .ply.', pcname);
end
pc_loc_clean = unique(pc.Location, 'rows');
if size(pc_loc_clean,1) ~= size(pc.Location,1)
    pc = pointCloud(pc_loc_clean);
end
heart_twin_struct= vertextime_analysis_02(pc,ECGs_eigenLandmarks_ms,ECGs_t_ms,ECGs_eigenbeat,options.figuredebug);
%% ECG signals on heart graph processing
switch options.VTFtype
    case 'GFT_ideal'
        ECGs_VT = heart_twin_struct.ECGs_IdealSignalOnPC;
    case 'GFT_eigen'
        ECGs_VT = heart_twin_struct.ECGs_EigenSignalOnPC;
end
[ ~, M_time_bins] = cellfun(@size,ECGs_VT);
M_time_bins_vectorvalues = unique(M_time_bins);
if length(M_time_bins_vectorvalues)>2
    max_M_time_bins = max(M_time_bins_vectorvalues);
    idxs_max = M_time_bins == max_M_time_bins;
    M_time_bins = M_time_bins_vectorvalues(idxs_max);
    correct = correct(idxs_max);
    ECGs_VT = ECGs_VT(idxs_max);
    n_rimossi = numel(idxs_max) - sum(idxs_max);
    fprintf('Numero dei rimossi per M_times_bin insufficiente: %d\n', n_rimossi);
else
    M_time_bins = M_time_bins_vectorvalues; % singolo valore
end

% eigen-analysis point cloud
[vertex_GT,face_GT,~, ~,~]=vertex2mesh_journal_02(pc);
options.symmetrize=1;
options.normalize=1;
L_GT_conf = compute_mesh_laplacian(vertex_GT, face_GT', 'conformal', options);
% gli autovalori codificano la frequenza spaziale dell'oggetto
% il numero degli autovalori e degli autovettori è uguale al numero dei
% punti della point cloud. 
[U_low, ~] = eigs(L_GT_conf, options.Nlow, 'smallestabs'); % variazioni lente 
[U_high, ~] = eigs(L_GT_conf, options.Nhigh, 'largestabs'); % dettagli rapidi
U0_selected = [U_low, U_high]; %Npoints x Neigenvalues, each col is one eigenvector
[ECGs_VTF, ~]= cellfun(@(vt) compute_feature_vertex_time(U0_selected,vt),ECGs_VT,'UniformOutput',false  );
ECGs_VTF = cell2mat(ECGs_VTF);

end