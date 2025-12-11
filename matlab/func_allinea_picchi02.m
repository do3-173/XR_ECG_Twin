function [ecg_beats,ecg_detectedLandmarks_xbeat,correct]=func_allinea_picchi02(ecg, Params,figuredebug)
% FUNC_ALLINEA_PICCHI - Detects QRS landmarks, segments ECG beats, aligns 
% each beats based on R peaks 
% Sintax:
%   [ecg_beats, wave_detect_data, correct] = func_allinea_picchi02(ecg, Params,figuredebug)
% Input:
%   ecg : double [nleads x nsamples] 
%   Params : struct
%       fs : sampling rate (in Hz)
%   figuredebug: plot results
%
% Output:
%   ecg_beats : double [noBeats x window x 1]
%       Matrix containing the aligned and windowed heartbeats
%
%   ecg_detectedLandmarks : struct
%       Indexes of QRS landmarks
%
%   correct : boolean
%       Indicates whether the processing was successful (1) or if the signal
%       is too noisy (0).
%
% Description:
%   The function segments and allign the beats of single lead ECG: 
%   - Based on sampling rate, some parameters related to beat are initialized 
%   - If nleads > 1 select the best lead to detect R-peaks from
%   - Detect and Sync of the R-peaks
%   - Verify the number of detected peaks according to heart's physiology
%   - Under some conditions, it may update the initialized parameters
%   - Windowing 
%
% Nested function: LeadSelectionFcn, RsyncFcn, HBresizeFcn, apWindowingFcn
arguments
    ecg 
    Params 
    figuredebug 
end

[nleads, nsamples] = size(ecg);
% Initialize parameters based on sampling frequency (fs)
Lover = 1 + (1.5 * Params.fs);
Params.S4QRS = ceil(0.12 * Params.fs); % Length of QRS interval
if mod(Params.S4QRS,2) == 0
    Params.S4QRS = Params.S4QRS + 1; % Ensure S4QRS is odd
end
Params.S4PQ = ceil(.15 * Params.fs); % Length of PQ interval
Params.S4ST = ceil(.32 * Params.fs); % Length of ST interval
Params.Lhb = Params.S4QRS + Params.S4PQ + Params.S4ST; % Total length of heartbeat

% Synchronize with R peaks (select best lead)
nleads_toselect = 1; % fix: should be a parameter
if nleads>1 
    if nleads_toselect>nleads 
        nleads_toselect = nleads;
    end
    ref_p = LeadSelectionFcn02(Params, ecg, nleads_toselect); % Select reference lead  
else 
    ref_p=1;  
end % Select reference lead 
[ecg_detectedLandmarks,ecg_out ] = RsyncFcn02(Params, ecg,ecg(ref_p,:),figuredebug); % Synchronize R peaks

% signals that did not correctly detect the R peaks must be discarded
% atrial fibrillation means having an irregular heartbeat, therefore
% both bradycardia and tachycardia may occur
durationsignal = nsamples/Params.fs; % seconds
% in casi estremi di bradicardia posso avere 30 bpm 
% (30 beats /60 seconds) = 0.5 beats per seconds
numbeats_min = floor(0.5 * durationsignal);  
% in casi estremi di tachicardia posso avere 300 bpm
% (300 beats /60 seconds) = 5 beats per seconds
numbeats_max = floor(5 * durationsignal);
numbeats_detected = length(ecg_detectedLandmarks.idxR);

if numbeats_detected < numbeats_min || numbeats_detected > numbeats_max 
    correct=0;
    noHB = length(ecg_detectedLandmarks.idxR); % Number of heartbeats
    ecg_beats = zeros(noHB, Lover,1); %
    ecg_detectedLandmarks_xbeat = NaN;
    % Noisy record
    % NoisyRec_train = [NoisyRec_train n]; % Mark as noisy record
    % StoreFeatures_train(n,1,:) = NaN; % Store NaN for noisy records
else
    correct=1;
    % Re-evaluate windows for P wave, QRS complex, and T wave
    [Params] = HBresizeFcn_02(Params, ecg_detectedLandmarks,figuredebug); % Resize heartbeat windows
    % Concatenate heartbeat data lead by lead 
    noHB = length(ecg_detectedLandmarks.idxR); % Number of heartbeats
    ecg_beats = zeros(noHB, Lover,1); % Initialize beats' matrix
    for d = 1:nleads%1 lead
        if sum(isnan(ecg(d,:))) == 0 % If no NaNs in the lead data
            [dMatrixHB, ecg_detectedLandmarks_xbeat] = apWindowingFcn_02(Params, ecg_out(d,:), ecg_detectedLandmarks,figuredebug); % Apply windowing function
            ecg_beats(:,:,d) = dMatrixHB'; % Store the windowed data
        end
    end
end
end %end_func_allinea_picchi

function [ref_lead] = LeadSelectionFcn02(Params, data, noLead,options)
% LEADSELECTIONFCN - Selects the best ECG lead to detect R peaks
% Syntax:
%   ref_lead = LeadSelectionFcn(Params, ecg, noLead)
%
% Input:
%   Params : struct, with fiels
%       fs   : sampling rate ( Hz )
%
%   data : double [nleads x nsamples]
%       ECG multi lead to analyze 
%
%   noLead : int
%       maximum number of lead to analyze:  noLead<=nleads
%
% Output:
%   ref_lead : int
%       Index of the selected ECG lead as reference lead to detect R peaks 
%
% Description: 
% For each lead, 
%   - verify polarity and check if there is any NaN.
%   - detect R-peaks based on signal's amplitude and shape 
%   - count the number of R-peaks and the minimum RR-interval
% If the lead satisfy some criteria, then it is the referenced lead 
% If no lead is valid, then the first lead is selected.

arguments
    Params 
    data 
    noLead 
    options.DisplayFigure = 0
end
[nleads, nsamples] = size(data);
if noLead > nleads
    noLead = nleads;
end
durationsignal = nsamples/Params.fs; % seconds
% in extreme cases of bradycardia I may have 30 bpm
% (30 beats / 60 seconds) = 0.5 beats per second
numbeats_min = floor(0.5 * durationsignal);
% in extreme cases of tachycardia I may have 300 bpm
% (300 beats / 60 seconds) = 5 beats per second
numbeats_max = floor(5 * durationsignal);
%%% Params 
fs = Params.fs;
sign_ref = [1 1 -1 -1];
ThrDiffR = .5 * fs;
ref_lead = 0;
ph_ref_lead = 0;
%%% Ref
phnoRmax = 0;
noRmax = 0;
AmpRmean = 0;
DiffRmin = 0;
for p = 1:noLead
    pdata = data(p,:);
    %  polarità positiva predominante e numericamente valido
    if max(pdata)>abs(min(pdata)) && sum(isnan(pdata))==0 % correct condition
        pMax = max(pdata);
        vR_p = find(pdata > .7 * pMax);
        % first peaks' detection                     
        d_dt = diff(pdata(vR_p));
        s_dt = sign(d_dt);
        % second peaks' detection
        idxR = strfind(s_dt,sign_ref);
        noR = numel(idxR);
        % RR-intervals
        posR = vR_p(idxR) + 2;
        diffPosR = diff(posR);
        minDiff = min(diffPosR);
        % Decision
        if noR > numbeats_min &&  noR < numbeats_max 
            if minDiff>ThrDiffR && minDiff>DiffRmin
                ref_lead = p;
                noRmax = noR;
                AmpRmean = mean(pdata(posR));
                DiffRmin = minDiff;
            end
        end
        % Fallback decision
        if ref_lead == 0
            phnoR = diffPosR;
            phnoR(phnoR<DiffRmin) = [];
            phnoR = numel(phnoR) + 1;
            if phnoR > phnoRmax
                ph_ref_lead = p;
                phnoRmax = phnoR;
            end     
        end
        if options.DisplayFigure
            samples = 1:1:numel(pdata);
            fig_LeadSelectionFcn02 = figure('Name',['LeadSelectionFcn02_' num2str(p)]);
            figure(fig_LeadSelectionFcn02)
            subplot(3,1,1)
            hold on
            plot(pdata,'DisplayName','pdata')
            yline(pMax,'DisplayName','pMax')
            scatter(samples(vR_p),pdata(vR_p),'DisplayName','vR_p')
            hold off
            legend('Location','northoutside')
            xlim([0 numel(pdata)])
            subplot(3,1,2)
            d_dt(end+1) = d_dt(end);
            plot(vR_p,d_dt,'DisplayName','d_dt')
            xlim([0 numel(pdata)])
            subplot(3,1,3)
            s_dt(end+1) = s_dt(end);
            plot(vR_p,s_dt)
            hold on
            scatter(vR_p(idxR),s_dt(idxR))
            xlim([0 numel(pdata)])
        end           
    end
end
if ref_lead == 0
    if ph_ref_lead == 0
        % keyboard,   
        ref_lead = 1;
    else
        ref_lead = ph_ref_lead;
    end
end
end %LeadSelectionFcn02
function [ecg_detectedLandmarks,ecg_out ] = RsyncFcn02(Params, ecg, ecg_xqrsdetect,sDebug )
% RsyncFcn02 - detect and sync R peaks of an ECG single lead
%
% Sintax:
%   [ecg_detectedLandmarks,ecg_out ] = RsyncFcn02(Params, ecg, ecg_xqrsdetect,sDebug)
%
% Input:
%   Params : strct
%       - fs   : sampling rate ( Hz)
%       - Lhb  : total length of heart beat
%
%   ecg : double [noLeads x nsamples]
%       ECG multi lead
%
%   ecg_xqrsdetect: double [ 1 x nsamples]
%       selected ECG single lead to detect QRS landmarks
%
% Output:
%   ecg_detectedLandmarks: struct, with fields
%       idxR : row vector, [1 x noBeats ] 
%          Indexes of R-peaks
%       idxQ : row vector, [1 x noBeats ]
%          Indexes of Q points
%       idxS : row vectore, [1 x noBeats ]
%          Indexes of S points
%   ecg_out  : corrected ecg signal
%
%
% Description:
%   - The signal is divided into windows of 1000 samples for robust detection.
%   - R peaks and Q and S points are detected with `qrs_detect3_02`,
%     then filtered to remove those too close to the edges.
%   - The average polarity of the peaks is evaluated to correct possible
%     phase inversions.
%   - Each peak is locally centered to ensure alignment.
%   - "Uncertain" peaks (too high or too low compared to the average)
%     are removed.
%   - A check is performed to eliminate peaks that are too close to
%     each other.
%
% see: qrs_detect3
arguments
    Params 
    ecg 
    ecg_xqrsdetect = ecg(1,:)
    sDebug = 0
end
[nleads, nsamples] = size(ecg);
%%% QRS detection   
SzWdw = 1000;
noWdw = floor(nsamples / SzWdw);
SzWdw_seconds = nsamples/Params.fs; % seconds
% avoid bradycardia, i.e. 30 bpm 
% (30 beats /60 seconds) = 0.5 beats per seconds
noBeats_min = floor(0.5 * SzWdw_seconds);  
% avoid tachycardia, i.e 300 bpm
% (300 beats /60 seconds) = 5 beats per seconds
noBeats_max = floor(5 * SzWdw_seconds);
idxR = [];
idxQ = [];
idxS = [];

for i = 1:noWdw
    iecg = ecg_xqrsdetect(1+(i-1)*SzWdw:i*SzWdw);
    %0.25,0.6,Params.fs
    [iidxR,~,~,~,iidxQ,iidxS] = qrs_detect3_03(iecg,"fs",Params.fs,"debug",sDebug);
    idxR = [idxR iidxR+(i-1)*SzWdw];
    idxQ = [idxQ iidxQ+(i-1)*SzWdw];
    idxS = [idxS iidxS+(i-1)*SzWdw];
end
valid = idxR<Params.Lhb;
idxR(valid) = []; idxQ(valid) = []; idxS(valid) = [];
valid = idxR>length(ecg)-Params.Lhb;
idxR(valid) = []; idxQ(valid) = []; idxS(valid) = [];

%%% Valutazione fase (anche se dovrebbe essere sempre quella giusta)
ecg_out = ecg;
if ~isempty(idxR)
    vAmp = ecg(idxR);
    if mean(vAmp)<0 && median(vAmp)<0
        ecg_out = -1 * ecg;
        idxDel = find(vAmp > 0);
    else            
        idxDel = find(vAmp < 0);
    end        
    idxR(idxDel) = []; idxQ(idxDel) = []; idxS(idxDel) = [];
end
% Centratura picchi R
sz_w = 15;
for r = 1:numel(idxR)
    w = ecg_out(idxR(r)-sz_w:idxR(r)+sz_w);
    idxmax = find(w == max(w));
    idxmax = idxmax(1);
    if idxmax ~= (sz_w + 1)%%%Non è già centrato
        shift = idxmax - (sz_w + 1);
        idxR(r) = idxR(r) + shift;
        idxQ(r) = idxQ(r) + shift;
        idxS(r) = idxS(r) + shift;
    end
end
%%% Cancellazione picchi R "dubbi"
vAmp = ecg_out(idxR);
avAmp = mean(vAmp);
medAmp = median(vAmp);
ref = min(avAmp,medAmp);
sEXIT = false;
while ~sEXIT            
    del1 = find(vAmp > 1.5*ref);
    del2 = find(vAmp < .5*ref);
    del = [del1 del2];
    if isempty(del)
        sEXIT = true;
    else
        idxR(del) = []; idxQ(del) = []; idxS(del) = [];
        vAmp = ecg_out(idxR);
        avAmp = mean(vAmp);
        medAmp = median(vAmp);
        ref = min(avAmp,medAmp);
    end
end

%%% Check su duplicati o picchi troppo vicini
sCHECK = false;
while ~sCHECK  
    Dr = diff(idxR);
    idxD = find(Dr <= .5*Params.Lhb);
    if isempty(idxD)
        sCHECK = true;
    else        
        idxD = idxD(1);
        c_r = idxR(idxD:idxD+1);
        if ecg_out(c_r(1)) >= ecg_out(c_r(2))
            idxR(idxD+1) = []; idxQ(idxD+1) = []; idxS(idxD+1) = [];
        else
            idxR(idxD) = []; idxQ(idxD) = []; idxS(idxD) = [];
        end
    end
end
clear sCHECK Dr idxD c_r

ecg_detectedLandmarks.idxR=idxR;
ecg_detectedLandmarks.idxQ = idxQ;
ecg_detectedLandmarks.idxS = idxS;
% wave_detect_data.ecg_out=ecg_out;
if sDebug
    valR = ecg_out(idxR);
    valQ = ecg_out(idxQ);
    valS = ecg_out(idxS);
    FONTSIZE = 20;
    FONTNAME = 'Times New Roman';
    fig_qrscorrect = figure('Name','RsyncFcn02');
    figure(fig_qrscorrect)
    plot(ecg_out);
    hold on; 
    plot(idxR, valR, 'rv', 'MarkerFaceColor', 'r', 'MarkerSize', 8);
    plot(idxQ, valQ, 'go', 'MarkerFaceColor', 'g', 'MarkerSize', 6);
    plot(idxS, valS, 'bo', 'MarkerFaceColor', 'b', 'MarkerSize', 6);
    fig_qrscorrect.CurrentAxes.FontName = FONTNAME; 
    fig_qrscorrect.CurrentAxes.FontSize = FONTSIZE;
    grid on; grid minor;
    xlabel('n'); ylabel('Amplitude [mV]');
    hold off;
    
    clear valR valQ valS;
end

if numel(idxR) > 3
    DeltaRmin = min(diff(idxR));
    DeltaRmean = mean(diff(idxR));
    if ((DeltaRmean-DeltaRmin)/DeltaRmean)>0.5 && ~sDebug

    end
end

end %end_rsync
function [qrs_pos,sign,en_thres,bpfecg,q_pos,s_pos] = qrs_detect3_03(ecg,options)
% QRS detector based on the P&T method. This is an offline implementation
% of the detector.
%
% inputs
%   ecg:            one ecg channel on which to run the detector (required)
%                   in [mV]
%   optional inputs
%       
%       REF_PERIOD: refractory period in sec between two R-peaks (default: 0.250)
%                   in [ms]
%       THRES:      energy threshold of the detector (default: 0.6) 
%                   [arbitrary units]
%       fs:         sampling frequency (default: 1KHz) [Hz]
%       fid_vec:    if some subsegments should not be used for finding the
%                   optimal threshold of the P&Tthen input the indices of
%                   the corresponding points here
%       SIGN_FORCE: force sign of peaks (positive value/negative value).
%                   Particularly usefull if we do window by window detection and want to
%                   unsure the sign of the peaks to be the same accross
%                   windows (which is necessary to build an FECG template)
%       debug:      1: plot to bebug, 0: do not plot
%
% outputs
%   qrs_pos:        indexes of detected peaks (in samples)
%   sign:           sign of the peaks (a pos or neg number)
%   en_thres:       energy threshold used
%
% Physionet Challenge 2014, version 1.0
% Released under the GNU General Public License
%
% Copyright (C) 2014  Joachim Behar
% Oxford university, Intelligent Patient Monitoring Group
% joachim.behar@eng.ox.ac.uk
%
% Last updated : 24-11-2014
% - bug on refrac period fixed
% - sombrero hat for prefiltering added
% - code a bit more tidy
% - condition added on flatline detection for overall segment (if flatline 
% then returns empty matrices rather than some random stuff)
%
% This program is free software; you can redistribute it and/or modify it
% under the terms of the GNU General Public License as published by the
% Free Software Foundation; either version 2 of the License, or (at your
% option) any later version.
% This program is distributed in the hope that it will be useful, but
% WITHOUT ANY WARRANTY; without even the implied warranty of
% MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
% Public License for more details.
arguments
    ecg 
    options.REF_PERIOD = 0.250  
    options.THRES = 0.6; 
    options.fs = 1000; 
    options.fid_vec = [];
    options.SIGN_FORCE = [];
    options.debug = 0;
    options.WIN_SAMP_SZ = 7;
    options.SEARCH_BACK = 1; 
    options.MAX_FORCE = []; % if you want to force the energy threshold value
end
% == managing inputs
qrs_pos = [];
R_t = [];
R_amp = [];
hrv = [];
sign = [];
en_thres = [];

if isrow(ecg) 
    ecg = ecg';
end
NB_SAMP = length(ecg); % number of input samples
tm = 0:1/options.fs:(NB_SAMP/options.fs -1/options.fs); % old tm = 1/fs:1/fs:ceil(NB_SAMP/fs);

% == constants
MED_SMOOTH_NB_COEFF = round(options.fs/100);% number of coefficients of the median smoothing filter
INT_NB_COEFF = round(options.WIN_SAMP_SZ*options.fs/256); % length is 30 for fs=256Hz  
% number of coefficients for integration (moving average)
MIN_AMP = 0.05;
% if the median of the filtered ECG is inferior to MINAMP then it is likely 
% to be a flatline note the importance of the units here for the ECG (mV) 

try
    % == Bandpass filtering for ECG signal
    % this sombrero hat has shown to give slightly better results than a
    % standard band-pass filter. Plot the frequency response to convince
    % yourself of what it does
    b1 = [-7.757327341237223e-05  -2.357742589814283e-04 -6.689305101192819e-04 -0.001770119249103 ...
         -0.004364327211358 -0.010013251577232 -0.021344241245400 -0.042182820580118 -0.077080889653194...
         -0.129740392318591 -0.200064921294891 -0.280328573340852 -0.352139052257134 -0.386867664739069 ...
         -0.351974030208595 -0.223363323458050 0 0.286427448595213 0.574058766243311 ...
         0.788100265785590 0.867325070584078 0.788100265785590 0.574058766243311 0.286427448595213 0 ...
         -0.223363323458050 -0.351974030208595 -0.386867664739069 -0.352139052257134...
         -0.280328573340852 -0.200064921294891 -0.129740392318591 -0.077080889653194 -0.042182820580118 ...
         -0.021344241245400 -0.010013251577232 -0.004364327211358 -0.001770119249103 -6.689305101192819e-04...
         -2.357742589814283e-04 -7.757327341237223e-05];
    b1_res = resample(b1,options.fs,250); % ricampiono da 250 Hz a fs
    % filtfilt: applico filtro digitale in avanti ed indietro eliminando lo
    % sfasamento (zero-phase filering); FIR -> a=1, i coefficienti a 
    % sono al denominatore; le dimensioni di ecg sono uguali a quelle di 
    % bpfecg = vettori colonna
    bpfecg = filtfilt(b1,1,ecg)'; % band pass filtered ecg, diventa riga
    
    if mean(abs(ecg-median(ecg))>MIN_AMP)<0.2
        % if 20% of the samples have an absolute amplitude which is higher
        % than MIN_AMP then we are good to go, else return
        plot_flatlinecheck(ecg,MIN_AMP)
        qrs_pos = [];             R_t = [];
        R_amp = [];             hr = [];             sign = [];
        en_thres = [];             q_pos = [];             s_pos = [];
        return
    end        
    % == P&T operations
    dffecg = diff(bpfecg);  % (4) differentiate (one datum shorter)
    % evidenziare i rapidi cambiamenti -  QRS ha slope molto ripide 
    sqrecg = dffecg.^2; % (5) square ecg
    % rendere tutti i valori positivi e amplificare i picchi - trasformare 
    % la derivata in una misura di energia istantanea.
    intecg = filter(ones(1,INT_NB_COEFF),1,sqrecg); % (6) integrate
    % calcolare l’energia media in una finestra temporale.
    mdfint = medfilt1(intecg,MED_SMOOTH_NB_COEFF);  % (7) smooth
    delay  = ceil(INT_NB_COEFF/2); 
    mdfint = circshift(mdfint,-delay); % remove filter delay for scanning back through ECG

    % look for some measure of signal quality with signal fid_vec? (FIXME)
    if isempty(options.fid_vec); mdfintFidel = mdfint; else mdfintFidel(options.fid_vec>2) = 0; end;

    % == P&T threshold
    if NB_SAMP/options.fs>90; xs=sort(mdfintFidel(options.fs:options.fs*90)); else xs = sort(mdfintFidel(options.fs:end)); end;

    if isempty(options.MAX_FORCE)
       if NB_SAMP/options.fs>10
            ind_xs = ceil(98/100*length(xs)); 
            en_thres = xs(ind_xs); % if more than ten seconds of ecg then 98% CI
        else
            ind_xs = ceil(99/100*length(xs)); 
            en_thres = xs(ind_xs); % else 99% CI  
        end 
    else
       en_thres = options.MAX_FORCE;
    end

        % build an array of segments to look into
        poss_reg = mdfint>(options.THRES*en_thres); 

        % in case empty because force threshold and crap in the signal
        if isempty(poss_reg); poss_reg(10) = 1; end;

        % == P&T QRS detection & search back
        if  options.SEARCH_BACK
            indAboveThreshold = find(poss_reg); % ind of samples above threshold
            RRv = diff(tm(indAboveThreshold));  % compute RRv
            medRRv = median(RRv(RRv>0.01));
            indMissedBeat = find(RRv>1.5*medRRv); % missed a peak?
            % find interval onto which a beat might have been missed
            indStart = indAboveThreshold(indMissedBeat);
            indEnd = indAboveThreshold(indMissedBeat+1);

            for i=1:length(indStart)
                % look for a peak on this interval by lowering the energy threshold
                poss_reg(indStart(i):indEnd(i)) = mdfint(indStart(i):indEnd(i))>(0.5*options.THRES*en_thres);
            end
        end

        % find indices into boudaries of each segment
        % poss_reg deve essere colonna -> uso poss_reg(:) invece di
        % poss_reg'
        left  = find(diff([0 poss_reg])==1);  % remember to zero pad at start
        right = find(diff([poss_reg 0])==-1); % remember to zero pad at end
        if ~isequal(size(left),size(right)); error('isequal(size(left),size(right)) = 0'); end

        % looking for max/min?
        if options.SIGN_FORCE 
            sign = options.SIGN_FORCE;
        else
            nb_s = length(left<30*options.fs);
            loc  = zeros(1,nb_s);
            for j=1:nb_s
                [~,loc(j)] = max(abs(bpfecg(left(j):right(j))));
                loc(j) = loc(j)-1+left(j);
            end
            sign = mean(ecg(loc));  % FIXME: change to median?  
        end

        % loop through all possibilities  
        compt=1;
        NB_PEAKS = length(left);
        maxval = zeros(1,NB_PEAKS);
        maxloc = zeros(1,NB_PEAKS);
        % disp([num2str(NB_PEAKS) mat2str(right) mat2str(left)])
        keep_idx = true(1,NB_PEAKS);
        for i=1:NB_PEAKS
            % disp([num2str(right(i)) ' ' num2str(left(i))])
            if sign>0
                % if sign is positive then look for positive peaks
                [maxval(compt), maxloc(compt)] = max(ecg(left(i):right(i)));
            else
                % if sign is negative then look for negative peaks
                [maxval(compt), maxloc(compt)] = min(ecg(left(i):right(i)));
            end
            maxloc(compt) = maxloc(compt)-1+left(i); % add offset of present location

            % refractory period - has proved to improve results
            if compt>1
                if maxloc(compt)-maxloc(compt-1)<options.fs*options.REF_PERIOD && abs(maxval(compt))<abs(maxval(compt-1))
                    %maxloc(compt)=[]; maxval(compt)=[]; left(compt)=[]; right(compt)=[];
                    keep_idx(compt) = false;
                elseif maxloc(compt)-maxloc(compt-1)<options.fs*options.REF_PERIOD && abs(maxval(compt))>=abs(maxval(compt-1))
                    %maxloc(compt-1)=[]; maxval(compt-1)=[];left(compt)=[]; right(compt)=[];
                    keep_idx(compt) = false;
                elseif maxloc(compt)<=left(compt) || right(compt)<=maxloc(compt)
                    %maxloc(compt)=[]; maxval(compt)=[]; left(compt)=[]; right(compt)=[];
                    keep_idx(compt) = false;
                else
                    compt=compt+1;
                end
            else
                % if first peak then increment
                compt=compt+1;
            end
        end % for peaks
        idx_zero = ~maxloc; % trova gli zeri
        keep_idx(idx_zero) = false;
        maxloc = maxloc(keep_idx); left = left(keep_idx);
        right = right(keep_idx); maxval = maxval(keep_idx);
        % disp([num2str(NB_PEAKS) mat2str(maxloc) mat2str(right) mat2str(left)])
        if isequal(size(qrs_pos), size(left)) || ...
           isequal(size(qrs_pos), size(right)) || ...
           isequal(size(left), size(right)) 
            % disp(mat2str(maxloc))

            qrs_pos = maxloc; % datapoints QRS positions 
            R_t = tm(maxloc); % timestamps QRS positions
            R_amp = maxval; % amplitude at QRS positions
            hr = 60./diff(R_t); % heart rate istantanea
            q_pos = left;
            s_pos = right;
      
        else
            % this is a flat line
            qrs_pos = [];
            R_t = [];
            R_amp = [];
            hr = [];
            sign = [];
            en_thres = [];
            q_pos = [];
            s_pos = [];
        end
    
catch ME
    rethrow(ME);
    for enb=1:length(ME.stack); disp(ME.stack(enb)); end;
    qrs_pos = [1 10 20]; sign = 1; en_thres = 0.5; 
end

% == plots
if options.debug
    ecg = ecg';
    FONTSIZE = 20;
    FONTNAME = 'Times New Roman';
    fig_fir = figure('Name','qrs_detect3_02_FIR');
    figure(fig_fir)
    plot(tm,ecg,'DisplayName','raw ECG'); 
    hold on; plot(tm,bpfecg,'DisplayName','zero-phase FIR filtered ECG'); 
    hold off;
    title('ECG filtering');ylabel('Amplitude [mV]'); xlabel('Time [s]')
    legend('Location','southoutside','Orientation','horizontal')
    xlim([0 tm(end)]); 
    fig_fir.CurrentAxes.FontName = FONTNAME; 
    fig_fir.CurrentAxes.FontSize = FONTSIZE;
    
    fig_int = figure('Name','qrs_detect3_02_Int');
    figure(fig_int)
    plot(tm(1:length(mdfint)),mdfint);
    hold on; plot(tm,max(mdfint)*bpfecg/(2*max(bpfecg)), ...
        tm(left),mdfint(left),'o', ...
        tm(right),mdfint(right),'o','LineWidth',1); hold off
    title('Integrated ecg with scan boundaries over scaled ECG');
    ylabel('Int ECG'); xlim([0 tm(end)]); 
    fig_int.CurrentAxes.FontName = FONTNAME; 
    fig_int.CurrentAxes.FontSize = FONTSIZE;
    
    fig_qrs = figure('Name','qrs_detect3_02_qrs');
    figure(fig_qrs)
    plot(tm,ecg,'DisplayName','raw ECG');
    hold on; plot(R_t,R_amp,'vr','MarkerFaceColor', 'r','LineWidth',2,'DisplayName','R');
    plot(tm(q_pos),ecg(q_pos),'og','MarkerFaceColor', 'g','LineWidth',2,'DisplayName','Q');
    plot(tm(s_pos),ecg(s_pos),'ob','MarkerFaceColor', 'b','LineWidth',2,'DisplayName','S');  
    hold off;
    fig_qrs.CurrentAxes.FontName = FONTNAME; fig_qrs.CurrentAxes.FontSize = FONTSIZE;
    ylabel('Amplitude [mV]'); xlabel('Time [s]'); xlim([0 tm(end)]);
    legend('Location','southoutside','Orientation','horizontal')
    
    if ~isempty(hr)
        fig_hr = figure('Name','hr');
        figure(fig_hr)
        plot(R_t(1:length(hr)),hr,'r+','LineWidth',2)
        fig_hr.CurrentAxes.FontName = FONTNAME; fig_hr.CurrentAxes.FontSize = FONTSIZE;
        title('HR'); ylabel('RR (s)'); xlabel('Time [s]'); 
        xlim([0 tm(end)]);
    end
    
    %linkaxes(ax,'x');

end


% NOTES
%   Finding the P&T energy threshold: in order to avoid crash due to local 
%   huge bumps, threshold is choosen at 98-99% of amplitude distribution. 
%   first sec removed for choosing the thres because of filter init lag.
%   
%   Search back: look for missed peaks by lowering the threshold in area
%   where the  RR interval variability (RRv) is higher than 1.5*medianRRv
% 
%   Sign of the QRS (signForce): look for the mean sign of the R-peak over
%   the first 30sec when looking for max of abs value. Then look for the
%   R-peaks over the whole record that have this given sign. This allows to
%   not alternate between positive and negative detections which might
%   happen in some occasion depending on the ECG morphology. It is also
%   better than forcing to look for a max or min systematically.


end

function plot_flatlinecheck(ecg,MIN_AMP)
figure('Name','qrs_detect3_03\plot_flatlinecheck')
tiledlayout(1,2)
nexttile
plot(ecg,'b');
hold on;
yline(median(ecg),'r--','Mediana');
yline(median(ecg)+MIN_AMP,'k--','+MIN\_AMP');
yline(median(ecg)-MIN_AMP,'k--','-MIN\_AMP');
xlabel('Samples'); ylabel('Amplitude [mV]');
legend('ECG','Median','Thresholds');
% Plot distribuzione deviazioni
nexttile
deviations = abs(ecg - median(ecg));
histogram(deviations,50);
hold on;
xline(MIN_AMP,'r--','MIN\_AMP');
xlabel('|ecg - median| [mV]'); ylabel('count samples');

sgtitle('Not satisfy flatline check');
end %plot_flatlinecheck

function [Params_new] = HBresizeFcn_02(Params, ecg_detectedLandmarks,sDebug)
% HBresizeFcn_02 - Resizes heart beat based on R peaks 
%
% Sintassi:
%   Params_new = HBresizeFcn_02(Params, idxR, idxQ, idxS)
%
% Input:
%   Params - struct, with fields
%       .Lhb     - length of heart beat
%       .S4PQ    - segment for PQ
%       .S4QRS   - segment for QRS
%       .S4ST    - segment for ST
%   ecg_detectedLandmarks - Struct
%       .idxR   - indexes of detected R peaks
%   ecg sing lead
%
% Output:
%   Params_new - Updated struct
%
% Description:
%   The function computes the new heartbeat length (Lhb) based on
%   the variability of RR intervals. If the new Lhb is
%   significantly shorter than the previous one, it updates
%   Lhb and the durations of the PQ, QRS, and ST segments proportionally.
%   In addition, it calculates the left and right portions of the beat
%   for alignment.
   
old_Lhb = Params.Lhb; % lunghezza precedente
idxR = ecg_detectedLandmarks.idxR;
DeltaRmin = min(diff(idxR));
DeltaRmean = mean(diff(idxR));    
new_Lhb = DeltaRmean + (DeltaRmean - DeltaRmin); % nuova lunghezza

if new_Lhb < .8 * old_Lhb % se significativamente più corta, aggiorna
    disp('HBresizeFcn_02: resize length heart beat ')
    sDebug = 1;
    update = 1;
    new_Lhb = round(.99 * new_Lhb);
    if mod(new_Lhb,2) == 0
        new_Lhb = new_Lhb + 1;
    end

    Rp = Params.S4PQ / old_Lhb; 
    S4PQ = round(Rp * new_Lhb);

    Rr = Params.S4QRS / old_Lhb;
    S4QRS = round(Rr * new_Lhb);

    S4ST = new_Lhb - S4PQ - S4QRS;

    Params_new.Lhb = S4QRS + S4PQ + S4ST;
    Params_new.S4QRS = S4QRS;
    Params_new.S4PQ = S4PQ;
    Params_new.S4ST = S4ST;
else
    update = 0;
    Params_new = Params;
end % if
Params_new.Lhb_left = floor(.5*Params_new.S4QRS+Params_new.S4PQ);
Params_new.Lhb_right = floor(.5*Params_new.S4QRS+Params_new.S4ST);
if sDebug
    FONTSIZE = 20;
    FONTNAME = 'Times New Roman';
    fig_debug = figure('Name','HBresizeFcn_02');
    figure(fig_debug)
    segs = [Params.S4PQ Params.S4QRS Params.S4ST];
    labels1 = {'S4PQ','S4QRS','S4ST'};
    b1 = bar(1,segs,'stacked');
    xtips1 = b1(1).XEndPoints;
    for i=1:numel(b1)
        ytips1 = b1(i).YEndPoints - 10;
        text(xtips1,ytips1,labels1{i},'HorizontalAlignment','center',...
    'VerticalAlignment','bottom','FontName',FONTNAME)
    end
    hold on
    bar(2,Params.Lhb,'stacked')
    set(gca, 'XTick', [1 2],'XTickLabel', {'Segments', 'Lhb'});
    if update   
        segs = [Params_new.S4PQ Params_new.S4QRS Params_new.S4ST];
        labels1 = {'S4PQ','S4QRS','S4ST'};
        b1 = bar(3,segs,'stacked');
        xtips1 = b1(1).XEndPoints;
        for i=1:numel(b1)
            ytips1 = b1(i).YEndPoints - 10;
            text(xtips1,ytips1,labels1{i},'HorizontalAlignment','center',...
        'VerticalAlignment','bottom','FontName',FONTNAME)
        end
        bar(4,Params_new.Lhb,'stacked')
        set(gca, 'XTick', [1 2 3 4], ...
            'XTickLabel', {'Old Seg', 'Old Lhb', 'New Seg', 'New Lhb'});
    end
    hold off
    ylabel('n')
    fig_debug.CurrentAxes.FontName = FONTNAME; 
    fig_debug.CurrentAxes.FontSize = FONTSIZE;

end %plot
end % end_hbresize
function [mdLeadSig, ecg_detectedLandmarks_xbeat] = apWindowingFcn_02(Params, dLeadSig, ecg_detectedLandmarks,sdebug)
% apWindowingFcn_02 - Extracts ECG windows centered on R peaks for each
% heartbeat
%
% Syntax:
%   [mdLeadSig, idxR] = apWindowingFcn_02(Params, dLeadSig, ecg_detectedLandmarks,sdebug)
%
% Description:
%   This function performs a windowed extraction of the i-th ECG beat
%   centered on the detected R peaks. For each heartbeat, a symmetric
%   (or nearly symmetric) window is created around the R peak, with width
%   defined by the parameters `Lhb_left` and `Lhb_right`. The result is a
%   matrix in which each column represents an aligned heartbeat.
% Input:
%   Params   - struct containing ECG parameters:
%              .fs         - Sampling frequency (Hz)
%              .Lhb_left   - Number of samples to the left of the R peak
%              .Lhb_right  - Number of samples to the right of the R peak
%
%   dLeadSig - Single-lead ECG signal vector from which to extract
%              the windowed beats
%   ecg_detectedLandmarks - struct containing the fields:
%          .idxR
%          .idxQ
%          .idxS
% Output:
%   mdLeadSig - Matrix (Lover x noHB) containing ECG windows aligned
%               on each R peak. Each column is a heartbeat.
%   ecg_detectedLandmarks_xbeat - Structure with local landmarks:
%       .idxR - R indices relative to the window center
%       .idxQ - Q indices relative to the window center
%       .idxS - S indices relative to the window center


%%% Empirical Params
%%% Params
noHB = length(ecg_detectedLandmarks.idxR);%no. HeartBeat    

Lleft = Params.Lhb_left;
Lright = Params.Lhb_right;
Lover = 1 + (1.5 * Params.fs); 
center = ceil(.5 * Lover);

if Lleft >= center
    Lleft = center - 1;
end
if Lright >= center
    Lright = center - 1;
end

mdLeadSig = zeros(Lover,noHB);
ecg_detectedLandmarks_xbeat.pOnset = [];
ecg_detectedLandmarks_xbeat.idxR = [];
ecg_detectedLandmarks_xbeat.idxQ = [];
ecg_detectedLandmarks_xbeat.idxS = [];
ecg_detectedLandmarks_xbeat.tOffset = [];

for i = 1:noHB
    iR = ecg_detectedLandmarks.idxR(i);
    iQ = ecg_detectedLandmarks.idxQ(i);
    iS = ecg_detectedLandmarks.idxS(i);
    deltaQR = iR-iQ;
    deltaSR = iS-iR;

    iStart = iR - Lleft;
    iEnd = iR + Lright; 

    if iEnd<=numel(dLeadSig) && iStart>=1
        iSig = dLeadSig(iStart:iEnd);
        mdLeadSig(center-Lleft:center+Lright,i) = iSig;
    end 
    ecg_detectedLandmarks_xbeat.pOnset(end+1) = center-Lleft;
    ecg_detectedLandmarks_xbeat.idxR(end+1) = center;
    ecg_detectedLandmarks_xbeat.idxQ(end+1) = center - deltaQR ;
    ecg_detectedLandmarks_xbeat.idxS(end+1) = center + deltaSR;
    ecg_detectedLandmarks_xbeat.tOffset(end+1) = center+Lright;
end   
if sdebug
    FONTSIZE = 20;
    FONTNAME = 'Times New Roman';
    fig_debug = figure('Name','apWindowingFcn_02_ecglandmarks');
    figure(fig_debug)
    hold on
    % plot della finestra utilizzando un patch
    ylimVals = [min(dLeadSig) max(dLeadSig)];
    for i = 1:noHB
        iR = ecg_detectedLandmarks.idxR(i);
        iStart = iR - Lleft;
        iEnd = iR + Lright;
        if iEnd <= numel(dLeadSig) && iStart >= 1
            xPatch = [iStart iEnd iEnd iStart];
            yPatch = [ylimVals(1) ylimVals(1) ylimVals(2) ylimVals(2)];
            patch(xPatch, yPatch, [0.8 0.8 1], 'FaceAlpha', 0.5, 'EdgeColor', 'none');
        end
    end
    plot(dLeadSig) % plot dell'intero ecg
    % plot dei landmarks dell'ecg, per ogni battito ne ho 3
    plot(ecg_detectedLandmarks.idxR, dLeadSig(ecg_detectedLandmarks.idxR), ...
        'rv', 'MarkerFaceColor', 'r', 'DisplayName', 'R');
    plot(ecg_detectedLandmarks.idxQ, dLeadSig(ecg_detectedLandmarks.idxQ), ...
        'go', 'MarkerFaceColor', 'g', 'DisplayName', 'Q');
    plot(ecg_detectedLandmarks.idxS, dLeadSig(ecg_detectedLandmarks.idxS), ...
        'bo', 'MarkerFaceColor', 'b', 'DisplayName', 'S');
    hold off
    fig_debug.CurrentAxes.FontName = FONTNAME; 
    fig_debug.CurrentAxes.FontSize = FONTSIZE;
    xlabel('n'); ylabel('Amplitude [mV]');
    grid on; grid minor;
    
    fig_debug = figure('Name','apWindowingFcn_02_ecgsegs_allign');
    figure(fig_debug)
    hold on
    for i = 1:noHB
        plot(mdLeadSig(:,i),'DisplayName',['noHB' num2str(i)])
        % Plot dei punti pOnset, idxQ, idxR, idxS e tOffset perl'i-th beat
        plot(ecg_detectedLandmarks_xbeat.idxQ(i), mdLeadSig(ecg_detectedLandmarks_xbeat.idxQ(i),i), ...
            'go', 'MarkerFaceColor', 'g', 'DisplayName', ['Q' num2str(i)]);
        plot(ecg_detectedLandmarks_xbeat.idxR(i), mdLeadSig(ecg_detectedLandmarks_xbeat.idxR(i),i), ...
            'rv', 'MarkerFaceColor', 'r', 'DisplayName', ['R' num2str(i)]);
        plot(ecg_detectedLandmarks_xbeat.idxS(i), mdLeadSig(ecg_detectedLandmarks_xbeat.idxS(i),i), ...
            'bo', 'MarkerFaceColor', 'b', 'DisplayName', ['S' num2str(i)]);
        plot(ecg_detectedLandmarks_xbeat.pOnset(i), mdLeadSig(ecg_detectedLandmarks_xbeat.pOnset(i),i), ...
            'kx', 'MarkerFaceColor', 'k', 'DisplayName', ['pOnset' num2str(i)]);
        plot(ecg_detectedLandmarks_xbeat.tOffset(i), mdLeadSig(ecg_detectedLandmarks_xbeat.tOffset(i),i), ...
            'kx', 'MarkerFaceColor', 'k', 'DisplayName', ['tOffset' num2str(i)]);

    end
    hold off
    fig_debug.CurrentAxes.FontName = FONTNAME; 
    fig_debug.CurrentAxes.FontSize = FONTSIZE;
    xlabel('n'); ylabel('Amplitude [mV]');
    % legend('Location','southoutside','Orientation','horizontal')
    grid on; grid minor;
end
end
