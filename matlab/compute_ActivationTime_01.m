function [ActivationTimeSP, ActivationTimetrueSP] = compute_ActivationTime_01(t_ms, ECGEvents,  options)
% Questa funzione genera una mappa temporale di attivazione cardiaca 
% suddivisa in 8 distretti anatomici, basata sui landmark temporali 
% dell'ECG. Ogni distretto viene codificato nel tempo con valori discreti 
% che rappresentano gli stati: inattivo, trigger, depolarizzazione 
% o ripolarizzazione. Distretti anatomici mappati: Nodo SA - Atrio destro
% - Atrio sinistro - Nodo AV - His bundle - Bundle branches - Apex - Fibre 
% Purkinje

% Output
% - ActivationTime: matrice uint8 di dimensione [8 × nTime], 
% dove ogni riga rappresenta un distretto cardiaco e ogni colonna 
% un istante temporale. I valori codificano:
% - 0: non attivo
% - 1: trigger (inizio potenziale d'azione)
% - 2: depolarizzazione
% - 3: ripolarizzazione

% Input
% - t_ms: vettore temporale in millisecondi
% - Landmark ECG:
%     pOnset, ppeak, pOffset: inizio, picco e fine dell’onda P
%     qrsOnset, rpeak, qrsOffset: inizio, picco R e fine del QRS
%     tOnset, tOffset: inizio e fine dell’onda T
% - options: struttura con campi opzionali
%     DisplayFigure (default: 0): se true, visualizza la mappa di 
%     attivazione e, se disponibile, il segnale ECG in 3D
%     Signal: vettore ECG (es. derivazione II) da usare per la 
%     visualizzazione 3D

arguments
    t_ms
   ECGEvents
    options.DisplayFigure = 0
    options.Signal = []
end

pOnset=ECGEvents.pOnset;
pPeak=ECGEvents.pPeak;
%pOffset=ECGEvents.pOffset;
qrsOnset=ECGEvents.qrsOnset;
rPeak=ECGEvents.rPeak;
%qrsOffset=ECGEvents.qrsOffset;
tOnset=ECGEvents.tOnset;
tOffset=ECGEvents.tOffset;
%% Descrizione ciclo cardiaco
% nodo SA spara
% P wave: l'attività elettrica si propaga negli atrii, contrazione
%  -> ampiezza 0.1-0.2 mV e durata 60-80 ms
% PQ segment: la propagazione subisce un ritardo nel nodo atrio
% ventricolare-> ho un segmento isoelettrico di 60-80 ms
% nodo AV spara
% QRS: depolarizzazione dei ventricoli, contrazione, sistole
% onda bifasica o trifasica di 1mV con durata 80 ms
% His bundle - bundle branches - apex - Purkinje fibers
% ST segment: isoelettrica, poiché ho il plateau del potenziale d'azione.
% Durata di 100-120 ms  
% T wave: ripolarizzazione dei ventricoli, ampiezza di 0.1-0.3 mV e durata
% di 120-160 ms
% da T a P: isoelettrica, diastole

%% nodi che danno origine al potenziale d'azione

nodoSA_TFtime = t_ms >= pOnset - 10 & t_ms < pOnset;
nodoAV_TFtime = t_ms >= qrsOnset - 10 & t_ms < qrsOnset; 
%% Atrii - Depolarizzazione e Ripolarizzazione
AtrioDestro_dep_TFtime   = t_ms >= pOnset  & t_ms < qrsOnset;
AtrioSinistro_dep_TFtime = t_ms >= pPeak   & t_ms < qrsOnset;
AtrioDestro_rip_TFtime   = t_ms >= qrsOnset & t_ms < rPeak;
AtrioSinistro_rip_TFtime = t_ms >= qrsOnset & t_ms < rPeak;

%% Ventricoli - Depolarizzazione e Ripolarizzazione
HisBundle_dep_TFtime       = t_ms >= qrsOnset       & t_ms < tOnset;
BundleBranches_dep_TFtime  = t_ms >= qrsOnset + 20  & t_ms < tOnset;
Apex_dep_TFtime            = t_ms >= qrsOnset + 40  & t_ms < tOnset;
Purkinje_dep_TFtime        = t_ms >= rPeak          & t_ms < tOnset;

HisBundle_rip_TFtime       = t_ms >= tOnset & t_ms < tOffset;
BundleBranches_rip_TFtime  = t_ms >= tOnset & t_ms < tOffset;
Apex_rip_TFtime            = t_ms >= tOnset & t_ms < tOffset;
Purkinje_rip_TFtime        = t_ms >= tOnset & t_ms < tOffset;

%% Create and Save variable
nTime = numel(t_ms);
ActivationTime = zeros(8,nTime);
ActivationTime(1,nodoSA_TFtime) = 1; 
ActivationTime(2,AtrioDestro_dep_TFtime)=2; 
ActivationTime(3,AtrioSinistro_dep_TFtime)=2; 
ActivationTime(2,AtrioDestro_rip_TFtime)=3; 
ActivationTime(3,AtrioSinistro_rip_TFtime)=3;
ActivationTime(4,nodoAV_TFtime) = 1; 
ActivationTime(5,HisBundle_dep_TFtime) = 2;
ActivationTime(6,BundleBranches_dep_TFtime) = 2;
ActivationTime(7,Apex_dep_TFtime) = 2;
ActivationTime(8,Purkinje_dep_TFtime)=2;
ActivationTime(5,HisBundle_rip_TFtime) = 3;
ActivationTime(6,BundleBranches_rip_TFtime) = 3;
ActivationTime(7,Apex_rip_TFtime) = 3;
ActivationTime(8,Purkinje_rip_TFtime)=3;

ActivationTimeSP = sparse(ActivationTime);
ActivationTimetrueSP = sparse(ActivationTime~=0);

if options.DisplayFigure
%     figure('Name','ActivationTime')
% imagesc(ActivationTime);
    if ~isempty(options.Signal)
        % Colormap discreta personalizzata
        customMap = [
            0.6 0.6 0.6;   % 0 - non attivo 
            0.0 1 0.0;   % 1 - trigger 
            1.0 0.0 0.0;   % 2 - depolarizzazione 
            0.0 0.0 1    % 3 - ripolarizzazione
        ];
        figure('Name','ActivationTime')
        hold on;
        for i = 1:8 % Distretti Anatomici
            act = ActivationTime(i,:);
            for colorvalue = 0:3
                idx_all = find(act == colorvalue);
                if isempty(idx_all)
                    continue;
                end
                % Trova segmenti 
                d = [true, diff(idx_all) > 1, true]; 
                start_idx = find(d(1:end-1));
                end_idx   = find(d(2:end)) - 1;
                color = customMap(colorvalue+1, :); % Colore corrispondente
                for k = 1:numel(start_idx) % plot di ogni segmento
                    seg = idx_all(start_idx(k):end_idx(k));
                    plot3(t_ms(seg), i*ones(size(seg)), options.Signal(seg), ...
                          'Color', color, 'LineWidth', 1.5);               
                end     
            end
        end
        set(gca,'FontName','Times New Roman','FontSize',20)
        yticks(1:8);
        yticklabels({'SA Node', 'Right Atrium', 'Left Atrium', 'AV Node', ...
                     'His Bundle', 'Bundle Branches', 'Apex', 'Purkinje fibers'});
        cb = colorbar;
        cb.Ticks = [0.375, 1.125, 1.875, 2.625]; % Centri delle bande discrete
        % Depolarization and Re-polarization
        cb.TickLabels = {'Non attivo', 'Trigger', 'Depolarization', 'Re-polarization'};
        colormap(customMap);
        caxis([0 3]);
        xlabel('Time [ms]');
        zlabel('Amplitude');
        title('ECG 3D continuo con segmenti colorati per ActivationTime');
        view(3);
        grid on;
    end

    % AtrioDestro_TFtime = AtrioDestro_dep_TFtime | AtrioDestro_rip_TFtime; 
    % AtrioSinistro_TFtime = AtrioSinistro_dep_TFtime | AtrioSinistro_rip_TFtime;
    % checkplot = [AtrioDestro_dep_TFtime;
    %     AtrioDestro_rip_TFtime;
    %     AtrioDestro_TFtime;
    %     AtrioSinistro_dep_TFtime;
    %     AtrioSinistro_rip_TFtime;
    %     AtrioSinistro_TFtime];
    % imagesc(checkplot)
    % HisBundle_TFtime =  HisBundle_rip_TFtime | HisBundle_dep_TFtime;
    % BundleBranches_TFtime = BundleBranches_dep_TFtime | BundleBranches_rip_TFtime;
    % Apex_TFtime = Apex_dep_TFtime | Apex_rip_TFtime;
    % Purkinje_TFtime = Purkinje_rip_TFtime | Purkinje_dep_TFtime;
    % checkplot = [
    %     HisBundle_dep_TFtime;
    %     HisBundle_rip_TFtime;
    %     HisBundle_TFtime;
    %     BundleBranches_dep_TFtime;
    %     BundleBranches_rip_TFtime;
    %     BundleBranches_TFtime;
    %     Apex_dep_TFtime;
    %     Apex_rip_TFtime;
    %     Apex_TFtime;
    %     Purkinje_dep_TFtime;
    %     Purkinje_rip_TFtime;
    %     Purkinje_TFtime];
    % imagesc(checkplot)
    
end