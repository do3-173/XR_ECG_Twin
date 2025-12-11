function ActivationSpaceSP = compute_ActivationSpace_01(pc,options)
% compute_ActivationSpace  Identifica regioni anatomiche cardiache in una
% heart point cloud 
%
%   ActivationSpace = compute_ActivationSpace(pc, options)
%
%   Questa funzione segmenta una point cloud 3D del cuore in 8 regioni
%   anatomiche rilevanti per la propagazione del potenziale d'azione.
%   Restituisce una matrice binaria (uint8) di dimensione [nPoints × 8],
%   dove ogni colonna rappresenta una regione e ogni riga un punto.
%
%   Input:
%     pc                  - Oggetto pointCloud 
%     options.DisplayFigures - Booleano: se true, mostra figure di verifica
%   Output:
%     ActivationSpace     - Matrice uint8 [nPoints × 8], con 1 per i punti
%                           appartenenti a ciascuna regione anatomica:
%                           1 → Nodo SA
%                           2 → Atrio destro
%                           3 → Atrio sinistro
%                           4 → Nodo AV
%                           5 → His bundle
%                           6 → Bundle branches
%                           7 → Inizio fibre Purkinje (apice del cuore)
%                           8 → Estensione fibre Purkinje
%
%   Visualizzazione:
%     Se options.DisplayFigures è true, vengono generate due figure:
%       • Nodo SA, Atrio destro e sinistro
%       • Nodo AV, His bundle, Branches, Purkinje
%
%   Vedi anche: findNearestNeighbors, findNeighborsInRadius,
%   findPointsInObliqueCylinder -> è nested function
arguments
    pc 
    options.DisplayFigures 
end
nPoints = pc.Count;
ActivationSpace = zeros(nPoints,8);
%% Nodo seno atriale 
% Giunzione tra vena cava superiore e atrio destro
c_nodoSA = [1.3 5 -11.2];
[idx_nodoSA, ~] = findNearestNeighbors(pc,c_nodoSA,10);
ActivationSpace(idx_nodoSA,1) = 1;
nodoSA = select(pc, idx_nodoSA);
%% Atrio Destro
c_AtrioDestro = [1.3 4.2 -11.2];
r_AtrioDestro = 1;
[idx_AtrioDestro, ~] = findNeighborsInRadius(pc, c_AtrioDestro, r_AtrioDestro);
ActivationSpace(idx_AtrioDestro,2) = 1;
AtrioDestro = select(pc, idx_AtrioDestro);
%% Atrio Sinistro
c_AtrioSinistro = [3 4.5 -12];
r_AtrioSinistro = 0.7;
[idx_AtrioSinistro, ~] = findNeighborsInRadius(pc, c_AtrioSinistro, r_AtrioSinistro);
ActivationSpace(idx_AtrioSinistro,3) = 1;
AtrioSinistro = select(pc, idx_AtrioSinistro);
%% Nodo atrio ventricolare
c_nodoAV = [1.5 3.8 -11.2];
[idx_nodoAV, ~] = findNearestNeighbors(pc,c_nodoAV,10);
ActivationSpace(idx_nodoAV,4) = 1;
nodoAV = select(pc, idx_nodoAV);
%% His bundle - Bundle branches
c_startPurkinje = [4.5 1.0 -9];
endHisBundle = (c_nodoAV + c_startPurkinje) / 2;
startBundleBranches = endHisBundle;
endBundleBranches =  [4 1.7 -9];
radius = 0.7;
[HisBundle, idx_HisBundle] = findPointsInObliqueCylinder(pc, ...
    c_nodoAV, endHisBundle, radius);
[BundleBranches, idx_BundleBranches] = findPointsInObliqueCylinder(pc, ...
    startBundleBranches, endBundleBranches, radius);
ActivationSpace(idx_HisBundle,5) = 1;
ActivationSpace(idx_BundleBranches,6) = 1;
%% Apex - Purkinje Fibers
% Purkinje sfera -> apex
c_startPurkinje = [4.5 1.0 -9];
r_startPurkinje = 1;
[idx_startPurkinje, ~] = findNeighborsInRadius(pc, c_startPurkinje, r_startPurkinje);
ActivationSpace(idx_startPurkinje,7) = 1;
startPurkinje = select(pc, idx_startPurkinje);

% Purkinje SX - DX 
p1_Purkinje_sx = [3.3 4.2 -13];
p2_Purkinje_sx = [4.5 1.0 -9]; %[5.5 1.0 -8.0];
c_Purkinje_sx = (p1_Purkinje_sx + p2_Purkinje_sx) / 2;
p1_Purkinje_dx = [1.5 6 -8];
p2_Purkinje_dx =[4.5 1.0 -9];% [4.5 1.0 -9];
c_Purkinje_dx = (p1_Purkinje_dx + p2_Purkinje_dx) / 2;
% Purkinje cono
Purkinje_cono_base_c = (c_Purkinje_sx + c_Purkinje_dx) / 2;
Purkinje_cono_base_raggio = norm(c_Purkinje_dx - Purkinje_cono_base_c)/2;
% Purkinje_cono_theta = linspace(0, 2*pi, 100);
Purkinje_cono_normal = Purkinje_cono_base_c - p2_Purkinje_sx;
Purkinje_cono_normal = Purkinje_cono_normal/norm(Purkinje_cono_normal);
% x_axis = (c_Purkinje_dx - c_Purkinje_sx);
% x_axis = x_axis / norm(x_axis);
% y_axis = cross(Purkinje_cono_normal, x_axis);
% y_axis = y_axis / norm(y_axis);
% theta = linspace(0, 2*pi, 100);
% circle_points = Purkinje_cono_base_c' + 2*Purkinje_cono_base_raggio * (x_axis'*cos(theta) + y_axis'*sin(theta));
% Lateral Purkinje
points = pc.Location;
maxHeight = 1.5;
v = points - c_startPurkinje; % Vettori dal centro base a tutti i punti
h = v * Purkinje_cono_normal';  % (pcCount x 1) % Proiezione lungo la normale del cono
axisPoints = c_startPurkinje + h .* Purkinje_cono_normal;  % Punti sull'asse del cono
r = (h / maxHeight) * (2 * Purkinje_cono_base_raggio);  % (pcCount x 1) % Raggio teorico a ogni altezza
% Distanza laterale da ogni punto all'asse
lateralDistance = NaN(nPoints,1);
for i = 1:nPoints
    lateralDistance(i, 1) = norm(points(i, :) - axisPoints(i, :));
    if abs(lateralDistance(i, 1) - r(i, 1)) <= 0.7 && points(i,3) > -11.2
        ActivationSpace(i,8) = 1;
    end
end
% Condizione di appartenenza alla superficie laterale
idx_LateralPurkinje = find(ActivationSpace(:,8));
LateralPurkinje = select(pc, idx_LateralPurkinje);

ActivationSpaceSP = sparse(ActivationSpace);
if options.DisplayFigures
    %% Nodi SA - Atrii 
    figure('Name','nodoSA_Atrii') 
    subplot(1,2,1)
    pcshow(pc.Location,[0.5 0.5 0.5],'ViewPlane','XY','BackgroundColor','w');
    hold on
    pcshow(nodoSA.Location,[0 0 1] ,'ViewPlane','XY','BackgroundColor','w','MarkerSize',150)
    pcshow(nodoAV.Location,[1 0 0] ,'ViewPlane','XY','BackgroundColor','w','MarkerSize',150)
    hold off
    l = legend('Points off','SA node','AV node');
    l.Box = "off"; l.Orientation = "horizontal"; l.Location ="southoutside";
    xlabel('$x$','Interpreter','latex')
    ylabel('$y$','Interpreter','latex')
    zlabel('$z$','Interpreter','latex')
    set(gca,'FontName','Times New Roman','FontSize',20)
    subplot(1,2,2)
    pcshow(pc.Location,[0.5 0.5 0.5],'ViewPlane','XY','BackgroundColor','w');
    hold on
    pcshow(AtrioDestro.Location,[0 0.6 0.6] ,'ViewPlane','XY','BackgroundColor','w','MarkerSize',150)
    pcshow(AtrioSinistro.Location,[0.3 0.65 0.75],'ViewPlane','XY','BackgroundColor','w','MarkerSize',150)
    l = legend('Points off','Right Atrium','Left Atrium');
    l.Box = "off"; l.Orientation = "horizontal"; l.Location ="southoutside";
    xlabel('$x$','Interpreter','latex')
    ylabel('$y$','Interpreter','latex')
    zlabel('$z$','Interpreter','latex')
    set(gca,'FontName','Times New Roman','FontSize',20)
    %% nodoAV - HisBundle - BundleBranches - Apex - Purkinje
    figure('Name','nodoAV_HisBundle_BundleBranches_Apex_Purkinje')
    subplot(1,2,1)
    pcshow(pc.Location,[0.5 0.5 0.5],'ViewPlane','XY','BackgroundColor','w');
    hold on
    pcshow(HisBundle.Location,[0.8 0.5 0.1],'ViewPlane','XY','BackgroundColor','w','MarkerSize',150)
    pcshow(BundleBranches.Location,[0.6 0.2 0.2],'ViewPlane','XY','BackgroundColor','w','MarkerSize',150)
    xlabel('$x$','Interpreter','latex')
    ylabel('$y$','Interpreter','latex')
    zlabel('$z$','Interpreter','latex')
    l = legend('Points off', 'His Bundle', 'Bundle Branches');
    l.Box = "off"; l.Orientation = "horizontal"; l.Location ="southoutside";
    hold off
    set(gca,'FontName','Times New Roman','FontSize',20)
    subplot(1,2,2)
    pcshow(pc.Location,[0.5 0.5 0.5],'ViewPlane','XY','BackgroundColor','w');
    hold on
    pcshow(LateralPurkinje.Location,[0.8 0.5 0.1],'ViewPlane','XY','BackgroundColor','w','MarkerSize',150)
    pcshow(startPurkinje.Location,[0.6 0.2 0.1],'ViewPlane','XY','BackgroundColor','w','MarkerSize',150)
    hold off
    xlabel('$x$','Interpreter','latex')
    ylabel('$y$','Interpreter','latex')
    zlabel('$z$','Interpreter','latex')
    l = legend('Points off','Apex','Purkinje Fibers');
    l.Box = "off"; l.Orientation = "horizontal"; l.Location ="southoutside";
    set(gca,'FontName','Times New Roman','FontSize',20)

end
end

function [selectedPoints, idx] = findPointsInObliqueCylinder(pc, P1, P2, radius)

    % Estrai i punti della point cloud
    points = pc.Location;

    % Vettore direzione del cilindro
    axisVec = P2 - P1;
    axisLen = norm(axisVec);
    axisDir = axisVec / axisLen;  % normalizzato

    % Vettore da P1 a ciascun punto
    vecToPoints = points - P1;

    % Proiezione scalare di ogni punto sull'asse
    t = dot(vecToPoints, repmat(axisDir, size(points,1), 1), 2);

    % Proiezione ortogonale del punto sull'asse
    projPoints = P1 + t .* axisDir;

    % Distanza ortogonale del punto dall'asse
    distOrth = sqrt(sum((points - projPoints).^2, 2));

    % Criteri: entro il cilindro (lunghezza + raggio)
    inside = (t >= 0) & (t <= axisLen) & (distOrth <= radius);

    % Indici e punti selezionati
    idx = find(inside);
    selectedPoints = select(pc, idx);
end

