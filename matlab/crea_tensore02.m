function [tensore_ecg_wrapped, ECGs_detectedLandmarks, correct]=crea_tensore02(ECGsignals,Params,figuredebug)
% CREA_TENSORE02 - processing of K ECG signals to build a tensor of align 
% ECG beats 
% Syntax:
%   [tensore_ecg_wrapped, cellarr_peaks_wrapped, flag_trial_ok] = 
%                            crea_tensore02(ECGsignals, Params, figuredebug)
%
% Input:
%   ECGsignals : cell [K x 1], K number of trials
%       the k-th element is a double, [nleads x nsamples]
%
%   Params : struct
%       fs : sampling rate (in Hz)
%   figuredebug: Display figures
%
% Output:
%   tensore_ecg_wrapped : cell [K1 x 1], K1<=K
%       The k-th element is a matrix nBeats x nsamples, i.e. stores
%       aligned beats. nBeats vary across K
%
%   cellarr_peaks_wrapped : cell [K1 x 1], K1<=K
%       The k-th elements is a struct with idxQ, idxR and idxS fields, each
%       key value is a row vector, and the number of columns is equal to 
%       nBeats 
%
%   flag_trial_ok : logical vector [K x 1]
%       True: The k-th computation has not issues
%
% Description:
%   The function computes `func_allinea_picchi02` for each signal in 
%   ECGsignals, removes both the k-th beats and landmarks with some issues 
%   during computations.   
%
% Nested function: func_allinea_picchi02
arguments
    ECGsignals 
    Params 
    figuredebug = 0
end

if figuredebug % select signals' idx to visualize them steps
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

[tensore_ecg_wrapped,ECGs_detectedLandmarks,correct] = cellfun(@(signal,myvisual) func_allinea_picchi02(signal,Params,myvisual),ECGsignals,TF,'UniformOutput',false);
correct = cellfun(@(value) value==1,correct); % convert to double
tensore_ecg_wrapped = tensore_ecg_wrapped(correct); % remove not valid k
ECGs_detectedLandmarks = ECGs_detectedLandmarks(correct); % remove not valid k


%save(['matrice_ecg_wrapped_' num2str(selected_row) '.mat'],"matrice_ecg_wrapped")

if figuredebug
    idx_ex = idx_exs(1);
    ex = tensore_ecg_wrapped{idx_ex,1};
    noHB = size(ex,1);
    figure('Name','crea_tensore02_randEx')
    for i=1:noHB
        hold on
        beat = ex(i,:);
        idx_pOnset = ECGs_detectedLandmarks{idx_ex, 1}.pOnset(1,i);
        idx_r = ECGs_detectedLandmarks{idx_ex, 1}.idxR(1,i);
        idx_q = ECGs_detectedLandmarks{idx_ex, 1}.idxQ(1,i);
        idx_s = ECGs_detectedLandmarks{idx_ex, 1}.idxS(1,i);
        idx_tOffset = ECGs_detectedLandmarks{idx_ex, 1}.tOffset(1,i);
        plot(beat); % Beat ECG
        % plot dei landmarks
        plot(idx_pOnset,beat(idx_pOnset), 'x', 'MarkerSize', 8,'Color', 'k');
        plot(idx_r, beat(idx_r), 'v', 'MarkerSize', 8, 'Color', 'r'); 
        plot(idx_q, beat(idx_q), 'o', 'MarkerSize', 8, 'Color', 'g');          
        plot(idx_s, beat(idx_s), 'o', 'MarkerSize', 8, 'Color', 'b');  
        plot(idx_tOffset, beat(idx_tOffset), 'x', 'MarkerSize', 8, 'Color', 'k'); % T offset
        grid on
        grid minor
    end
    hold off
    xlabel('n'); ylabel('Amplitude [mV]');
    set(gca,'FontName','Times New Roman','FontSize',20)

end

end
%scrittura tensore
%save(['tensore_ecg_wrapped.mat'],"tensore_ecg_wrapped")