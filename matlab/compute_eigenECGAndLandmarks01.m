function [eigenLandmarks_ms_ECGs, t_ms_ECGs, eigen_nopad_ECGs] = compute_eigenECGAndLandmarks01(tensor_ecg_beats,ECGs_detectedLandmarks,fs,figuredebug)
% compute_eigenECGAndLandmarksXX 
% Input
%    tensor_ecg_beats resulted by func_allinea_picchi_XX
%         cell, ntrials x 1, the k-th trial is a double nbeats x nsamples 
%    ECGs_detectedLandmarks resulted by func_allinea_picchi_XX
%         cell, ntrials x 1, the k-th trial is a struct with fields
%                               .pOnset
%                               .idxQ
%                               .idxR
%                               .idxS
%                               .tOffset
%         Each ECGs_detectedLandmarks{k,1}.(fieldname) is a row vector 1 x nbeats
% Output
%    eigenLandmarks_ms_ECGs - stores the ntrials structs, each struct has
%    all landmarks as fields, 
%    i.e. pOnset, pPeak, qrsOnset, rPeak, qrsOffset, tOnset, tPeak, tOffset
%    the values refer to milliseconds
%    t_ms_ECGs - stores the ntrials vector times in milliseconds
%    eigen_nopad_ECGs - stores the ntrials no padded eigenbeat 
% Description
%    - l1pca.m function returns eigenECG, it contains padding since each
%    beat contains padding
%    - compute the averaged value of the available landmarks, these values
%    refer to indexes
%    - return the value of the undetected landmarks, these values are in
%    milliseconds (ms) and are computed on eigenECG no padding
if figuredebug % select signals' idx to visualize them steps
    num_exs_toplot = 1; % no signals
    rng(5) % reproducibility 
    K = numel(tensor_ecg_beats);
    idx_exs = randsample(K, num_exs_toplot); % int random number
    TF = ismember(1:K, idx_exs) ; % logical, true if index in idx_exs
    TF = num2cell(TF'); % convert to cell
else 
    TF = zeros( size(tensor_ecg_beats));
    TF = num2cell(TF); %  convert to cell
end
% l1pca, restituisce un eigen ribaltato motivo per cui ho il - davanti
eigen_ECGs = cellfun(@(matrix_ecgbeats) -l1pca(matrix_ecgbeats',1),tensor_ecg_beats,'UniformOutput',false);
ECGs_eigenLandmarks = compute_avgLandmarks(ECGs_detectedLandmarks);
[eigenLandmarks_ms_ECGs, t_ms_ECGs, eigen_nopad_ECGs]  = cellfun(@(eigenECG,eigenLandmarks,tf) compute_nopadLandmarks_ms(eigenECG,fs,eigenLandmarks,tf), ...
    eigen_ECGs,ECGs_eigenLandmarks,TF,'UniformOutput',false);
   
end % main function
%%%%%%%%%%% Nested
function eigenECGlandmarks = compute_avgLandmarks(ECGs_detectedLandmarks)
% Output:
%   eigenECGlandmarks:
%        Cell ntrials x 1, the k-th trial is a struct containing the
%        averaged (eigen) landmarks:
%                               .pOnset
%                               .qrsOnset
%                               .rPeak
%                               .qrsOffset
%                               .tOffset
% Description:
%   This function computes the eigen ECG landmarks across multiple beats. 
%   For each landmark (P onset, QRS onset, R peak,  QRS offset, T offset), 
%   the function calculates the mean position
%   across all detected beats and rounds it to the nearest integer.
%   The output is a cell array of structures containing the averaged
%   landmark positions for each beat.
% available landmarks 
pOnsets = cellfun(@(ECGlandmarks) ECGlandmarks.pOnset,ECGs_detectedLandmarks,'UniformOutput',false);
idxQs = cellfun(@(ECGlandmarks) ECGlandmarks.idxQ,ECGs_detectedLandmarks,'UniformOutput',false);
idxRs = cellfun(@(ECGlandmarks) ECGlandmarks.idxR,ECGs_detectedLandmarks,'UniformOutput',false);
idxSs = cellfun(@(ECGlandmarks) ECGlandmarks.idxS,ECGs_detectedLandmarks,'UniformOutput',false);
tOffsets = cellfun(@(ECGlandmarks) ECGlandmarks.tOffset,ECGs_detectedLandmarks,'UniformOutput',false);
% compute average
eigens_pOnset = cellfun(@(vec_pOnset) ceil(mean(vec_pOnset)), pOnsets);
eigens_qrsOnset= cellfun(@(vec_idxQ) ceil(mean(vec_idxQ)), idxQs);
eigens_rPeak = cellfun(@(eigen_idxR) ceil(mean(eigen_idxR)), idxRs);
eigens_qrsOffset = cellfun(@(eigen_idxS) ceil(mean(eigen_idxS)), idxSs);
eigens_tOffset = cellfun(@(eigen_tOffset) ceil(mean(eigen_tOffset)), tOffsets);
eigenECGlandmarks = cell(size(ECGs_detectedLandmarks));
for i = 1:numel(eigenECGlandmarks)
    eigenECGlandmarks{i}.pOnset = eigens_pOnset(i);
    eigenECGlandmarks{i}.qrsOnset = eigens_qrsOnset(i);
    eigenECGlandmarks{i}.rPeak = eigens_rPeak(i);
    eigenECGlandmarks{i}.qrsOffset = eigens_qrsOffset(i);
    eigenECGlandmarks{i}.tOffset = eigens_tOffset(i);
end
end % compute_avgLandmarks
function [eigenECGlandmarks_completems, t_ms, eigen_ECG] = compute_nopadLandmarks_ms(eigen_ECG,fs,eigenECGlandmarks,displayfigure)
% Input
%     eigen_ECG - double 1 x padnsamples -> padnsamples > nsamples and 
%     padnsamples is used to align beats in func_allinea_picchi_XX
%
%     eigenECGlandmarks - returned by compute_avgLandmarks -> struct with 
%     uncompleted fields since some landmarks are not detected by 
%     func_allinea_picchi_XX, the values refer to indexes
%
%     fs - sampling rate
%     displayfigure - logical
% Output
%     eigenECGlandmarks_completems - struct with all landmarks as fiels, 
%     i.e. pOnset, pPeak, qrsOnset, rPeak, qrsOffset, tOnset, tPeak, tOffset
%     the values refer to milliseconds
%     
%     t_ms - vector time in milliseconds
%
%     eigen_ECG - no padded eigenbeat

idx_nozero = find(eigen_ECG); % rm pad
eigen_ECG = eigen_ECG(idx_nozero);
NTime = numel(eigen_ECG);
t = 0: 1/fs : (NTime- 1)/fs;
t_ms = t * 1000;
FIELDNAMES_landmarks = fieldnames(eigenECGlandmarks);
for i = 1:numel(FIELDNAMES_landmarks)
    % eigenECGlandmarks contiene gli indici dei landmarks, ma per
    % l'eigen in cui ho anche gli zeri, quindi trovo i landmarks nel
    % nuovo eigen senza zeri
    field = FIELDNAMES_landmarks{i,1};
    original_idx = eigenECGlandmarks.(field);
    new_idx = find(idx_nozero == original_idx);
    eigenECGlandmarks.(field) = new_idx;
end
% qrs
% qrs_nsamples = eigenECGlandmarks.qrsOffset - eigenECGlandmarks.qrsOnset;
% max_qrs_nsamples = round(0.12 * fs); % fisiologico
% min_qrs_nsamples = round(0.08 * fs); % fisiologico
% if qrs_nsamples < min_qrs_nsamples 
%     disp('Non fisiologico - qrs - durata <  80 ms');
%     disp(qrs_nsamples/fs * 1000)
%     display_figure = 1;
% elseif qrs_nsamples > max_qrs_nsamples
%     qrs_nsamples = max_qrs_nsamples;
%     disp('Non fisiologico - qrs - durata <  120 ms');
%     disp(qrs_nsamples/fs * 1000)
%     display_figure = 1;
% end
% pPeak
max_pq_nsamples = round(0.08 * fs); % physiologic
min_pq_nsamples = round(0.06 * fs); % physiologic
max_pwave_nsamples = round(0.12 * fs); % physiologic
min_pwave_nsamples = round(0.06 * fs); % physiologic
pq_nsamples = max_pq_nsamples; % try max 
if eigenECGlandmarks.qrsOnset - pq_nsamples <= eigenECGlandmarks.pOnset
    % not enough space, try min
    pq_nsamples = min_pq_nsamples;
end
pwave_nsamples = eigenECGlandmarks.qrsOnset - pq_nsamples - eigenECGlandmarks.pOnset;
% check if physiologic
if pwave_nsamples < min_pwave_nsamples %no physiologic: duration <  60 ms
    pwave_nsamples = round(0.05 * fs);
elseif pwave_nsamples > max_pwave_nsamples %no physiologic: duration > 120 ms
    pwave_nsamples = round(0.13 * fs);
    if eigenECGlandmarks.qrsOnset - pq_nsamples - pwave_nsamples >=1
        eigenECGlandmarks.pOnset = eigenECGlandmarks.qrsOnset - pq_nsamples - pwave_nsamples;
    else
        pwave_nsamples = max_pwave_nsamples;
    end
end
win_p = eigenECGlandmarks.pOnset:pwave_nsamples+eigenECGlandmarks.pOnset;
[~,pPeak_win] = max(eigen_ECG(win_p));
pPeak = win_p(pPeak_win);
eigenECGlandmarks.pPeak=pPeak;
% tOnset
min_st_nsamples = round(0.1 * fs); %min value: duration 100ms
max_st_nsamples = round(0.12 * fs); % max value 120ms
min_twave_nsamples = round(0.12 * fs); %min value: duration 120ms
max_twave_nsamples = round(0.16 * fs); % max value 160ms
st_nsamples = max_st_nsamples; % try max
if eigenECGlandmarks.tOffset - st_nsamples <= eigenECGlandmarks.qrsOffset
   % not enough space, try min
    st_nsamples = min_st_nsamples;
end
twave_nsamples = eigenECGlandmarks.tOffset - st_nsamples - eigenECGlandmarks.qrsOffset;
% check if physiologic
if twave_nsamples < min_twave_nsamples % <120ms
    twave_nsamples = round(0.100 * fs);
elseif twave_nsamples > max_twave_nsamples %> 160 ms
    twave_nsamples = round(0.200 * fs);
    eigenECGlandmarks.tOffset = eigenECGlandmarks.qrsOffset + st_nsamples + twave_nsamples;
end
tOnset = eigenECGlandmarks.tOffset - twave_nsamples ;
win_t = tOnset:eigenECGlandmarks.tOffset;
[~,tPeak_win] = max(eigen_ECG(win_t));
tPeak = win_t(tPeak_win);
eigenECGlandmarks.tOnset=tOnset;
if displayfigure
    figure('Name','compute_eigenECGAndLandmarks01__completenopadms')
    plot(eigen_ECG);
    hold on
    plot(eigenECGlandmarks.pOnset, eigen_ECG(eigenECGlandmarks.pOnset,1), 'kx', 'MarkerFaceColor', 'k', 'MarkerSize', 8);
    plot(eigenECGlandmarks.qrsOnset, eigen_ECG(eigenECGlandmarks.qrsOnset,1), 'bo', 'MarkerFaceColor', 'b', 'MarkerSize', 6);
    plot(eigenECGlandmarks.rPeak, eigen_ECG(eigenECGlandmarks.rPeak,1), 'rv', 'MarkerFaceColor', 'r', 'MarkerSize', 8);
    plot(eigenECGlandmarks.qrsOffset, eigen_ECG(eigenECGlandmarks.qrsOffset,1), 'go', 'MarkerFaceColor', 'g', 'MarkerSize', 6);
    plot(eigenECGlandmarks.tOffset, eigen_ECG(eigenECGlandmarks.tOffset,1), 'kx', 'MarkerFaceColor', 'k', 'MarkerSize', 8);
    %% Punti trovati
    plot(pPeak, eigen_ECG(pPeak,1),'ms', 'MarkerFaceColor', 'm', 'MarkerSize', 8)
    plot(tPeak, eigen_ECG(tPeak,1),'ms', 'MarkerFaceColor', 'm', 'MarkerSize', 8)
    plot(tOnset,eigen_ECG(tOnset,1),'cs', 'MarkerFaceColor', 'c', 'MarkerSize', 8)  
    hold off
    xlabel('$n$','Interpreter','latex')
    ylabel('Amplitude')
    set(gca,'FontSize',20,'FontName','Times New Roman')
end
eigenECGlandmarks_completems = structfun(@(landmark,t_tms) convert_SampleToTime(landmark,t_ms),eigenECGlandmarks,"UniformOutput",false);             
end % compute_nopadeigenECGAndLandmarks
function landmark_ms = convert_SampleToTime(landmark,t_ms)
landmark_ms = t_ms(landmark);
end % convert_SampleToTime