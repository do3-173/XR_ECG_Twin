function heart_twin_struct= vertextime_analysis_02(pc,ECGs_eigenECGlandmarks_ms,ECGs_t_ms,ECGs_eigenbeat,display_figure,display_video)
% vertextime_analysis_XX
% Input
% pc - point cloud
% ECGs_eigenECGlandmarks_ms - stores the ntrials structs, each struct has
%    all landmarks as fields, i.e. pOnset, pPeak, qrsOnset, rPeak, 
%    qrsOffset, tOnset, tPeak, tOffset - the values are in milliseconds
%    - computed by compute_eigenECGAndLandmarksXX
% ECGs_t_ms - stores the ntrials vector times in milliseconds - computed by
%    compute_eigenECGAndLandmarksXX 
% ECGs_eigenbeat - stores the ntrials no padded eigenbeat - computed by
%    compute_eigenECGAndLandmarksXX 
% Output
% heart_twin_struct - struct with fields ECGs_IdealSignalOnPC and
% ECGs_EigenSignalOnPC 
arguments
    pc 
    ECGs_eigenECGlandmarks_ms
    ECGs_t_ms
    ECGs_eigenbeat
    display_figure = 0
    display_video = 0
end
if display_figure || display_video % select signals' idx to visualize them steps
    num_exs_toplot = 1; % no signals
    rng(5) % reproducibility 
    K = numel(ECGs_eigenECGlandmarks_ms);
    idx_exs = randsample(K, num_exs_toplot); % int random number
    TF = ismember(1:K, idx_exs) ; % logical, true if index in idx_exs
    TF = num2cell(TF'); % convert to cell
else 
    TF = zeros( size(ECGsignals));
    TF = num2cell(TF); %  convert to cell
end
%% Compute Signal On PC
% ActivationSpace=Matrice [nPoints × numRegions], con 1 per i punti
% appartenenti a ciascuna regione anatomica, numRegions=8;

ActivationSpaceSP = compute_ActivationSpace_01(pc,"DisplayFigures",display_figure);
% ActivationTime=Matrice  [numRegions × NTime], 
% dove ogni riga rappresenta un distretto cardiaco e ogni colonna un istante temporale. 
% I valori codificano: % 0 - non attivo,1 - trigger , 2 - depolarizzazione ,3 - ripolarizzazione
[ECGs_ActivationTimeSP, ECGs_ActivationTimetrueSP] = cellfun( @(eigenECGlandmarks_ms,t_ms,eigenbeat,tf) compute_ActivationTime_01(t_ms,eigenECGlandmarks_ms, ...
"DisplayFigure",tf,"Signal",eigenbeat),ECGs_eigenECGlandmarks_ms, ECGs_t_ms,ECGs_eigenbeat,TF,'UniformOutput',false);
% nPoints x NTime: per ogni punto un vettore riga, quando e come si attiva
% For each k, compute matrix product between the k-th ActivationSpaceSP and the k-th ActivationTimeSP
ECGs_IdealSignalOnPC = cellfun( @(ActivationTimeSP)  ActivationSpaceSP*ActivationTimeSP, ...
    ECGs_ActivationTimeSP,'UniformOutput',false);
% nPoints x NTime: per ogni punto un vettore riga, quanto vale eigenECG quando il punto si attiva 
% For each k, compute the k-th diageigen (diagonal matrix, where the
% diagonal store the k-theigenbeat)
ECGs_diageigen = cellfun(@(eigenbeat) spdiags(eigenbeat(:), 0, numel(eigenbeat), numel(eigenbeat)), ...
    ECGs_eigenbeat,'UniformOutput',false );
% NTime = numel(eigenbeat)
% For each k, compute the k-th EigenSignalOnPC (diagonal matrix, where the
% diagonal store the k-theigenbeat)
ECGs_EigenSignalOnPC = cellfun(@(ActivationTimetrueSP,diageigen) ActivationSpaceSP*(ActivationTimetrueSP)*diageigen, ...
    ECGs_ActivationTimetrueSP,ECGs_diageigen,'UniformOutput',false);
% output
heart_twin_struct.ECGs_IdealSignalOnPC = ECGs_IdealSignalOnPC;
heart_twin_struct.ECGs_EigenSignalOnPC = ECGs_EigenSignalOnPC;

if display_video
    idx = idx_exs(1);
    EigenSignalOnPC = full(ECGs_EigenSignalOnPC{idx,1});
    eigen_ECG = ECGs_eigenbeat{idx,1};
    t_ms = ECGs_t_ms{idx,1};
    video_Activation(pc,EigenSignalOnPC,eigen_ECG,t_ms,'Eigen','SaveVideo', true,'FrameRate',30)
end

end
