function video_Activation(pc, SignalOnPC, signal, t_ms, typeOfSignalOnPC,varargin)
% ActivationVideo - Visualizza un video sincronizzato tra la point cloud
% dell'attivazione e il segnale ECG nel tempo.
%
% USO:
%   video_Activation(pc, SignalOnPC, signal, t_ms, typeOfSignalOnPC)
%   video_Activation(..., 'SaveVideo', true, 'FileName', 'MyVideo.avi', 'FrameRate', 20)
%
% INPUT:
%   pc           - PointCloud object (es. pc = pcread(...))
%   SignalOnPC   - Matrice NxT degli stati nel tempo (0-3)
%   signal       - Vettore ECG (1xT) o (Tx1)
%   t_ms         - Vettore dei tempi corrispondenti (1xT) in millisecondi
%   typeOfSignalOnPC - 'Ideal' or 'Eigen'
%
% PARAMETRI OPZIONALI:
%   'SaveVideo'  - true/false, salva il video se true (default: false)
%   'FileName'   - nome del file video (default: 'ActivationVideo.avi')
%   'FrameRate'  - frame rate video (default: 20)
%

% === Parser parametri opzionali ===
p = inputParser;
addParameter(p, 'SaveVideo', false, @islogical);
addParameter(p, 'FileName', 'ActivationVideo.avi', @ischar);
addParameter(p, 'FrameRate', 20, @isnumeric);
parse(p, varargin{:});

saveVideo = p.Results.SaveVideo;
videoName = p.Results.FileName;
frameRate = p.Results.FrameRate;

% === Validazione input ===
assert(size(SignalOnPC,2) == numel(signal) && numel(signal) == numel(t_ms), ...
    'SignalOnPC, signal e t_ms devono avere la stessa dimensione temporale.');

switch typeOfSignalOnPC
    case 'Ideal' 
        % === Colori per stati ===
        colors = [ ...
            0.5 0.5 0.5;  % 0: inattivo → grigio
            0   1   0;    % 1: trigger → verde
            1   0   0;    % 2: depolarizzazione → rosso
            0   0   1];   % 3: ripolarizzazione → blu
        
        % === Setup video (se richiesto) ===
        if saveVideo
            v = VideoWriter(videoName);
            v.FrameRate = frameRate;
            open(v);
        end
        
        % === Figura con layout ===
        fig = figure('Color','w', 'Name', 'Activation Video', 'NumberTitle','off');
        tiledlayout(fig, 1, 2, 'TileSpacing', 'tight', 'Padding', 'compact');
        
        % === --- (1) SEGNALe ECG --- ===
        nexttile(1);
        plot(t_ms, signal, 'k', 'LineWidth', 1.2);
        hold on
        yl = ylim;
        ecgMarker = plot(t_ms(1), signal(1), 'ko', 'MarkerFaceColor', 'k', 'MarkerSize', 6);
        ylabel('Segnale ECG');
        title('Segnale ECG');
        grid on
        xlim([t_ms(1) t_ms(end)]);
        
        % === --- (2) POINT CLOUD --- ===
        nexttile(2);
        ax3d = gca;
        axis(ax3d, 'equal');
        axis(ax3d, 'vis3d');
        grid(ax3d, 'on');
        xlabel(ax3d, 'X'), ylabel(ax3d, 'Y'), zlabel(ax3d, 'Z');
        view(2);
        xlim(ax3d, [min(pc.Location(:,1)) max(pc.Location(:,1))]);
        ylim(ax3d, [min(pc.Location(:,2)) max(pc.Location(:,2))]);
        zlim(ax3d, [min(pc.Location(:,3)) max(pc.Location(:,3))]);
        
        N = size(SignalOnPC,1);
        T = size(SignalOnPC,2);
        
        scatterHandles = gobjects(4,1);
        hold(ax3d, 'on');
        for s = 0:3
            scatterHandles(s+1) = scatter3(ax3d, nan, nan, nan, 3, colors(s+1,:), 'filled');
        end
        
        % === LOOP TEMPORALE ===
        for t = 1:T
            % Aggiorna marker ECG
            set(ecgMarker, 'XData', t_ms(t), 'YData', signal(t));
        
            % Aggiorna stati nella point cloud
            state = SignalOnPC(:,t);
            for s = 0:3
                idx = (state == s);
                set(scatterHandles(s+1), ...
                    'XData', pc.Location(idx,1), ...
                    'YData', pc.Location(idx,2), ...
                    'ZData', pc.Location(idx,3));
            end
        
            title(ax3d, sprintf('Tempo: %.1f ms', t_ms(t)));
            drawnow limitrate
        
            % Scrittura su video
            if saveVideo
                frame = getframe(fig);
                writeVideo(v, frame);
            end
        
        end
        
        % === Chiusura video ===
        if saveVideo
            close(v);
            disp([' Video salvato come: ', videoName])
        end
    case 'Eigen'
        % === Colori ===
        % I punti inattivi (NaN o 0) saranno grigi chiaro, quelli attivi colorati secondo ampiezza ECG
        cmap = parula(256);   % oppure 'jet', 'turbo', ecc.
        inactiveColor = [0.7 0.7 0.7];
        
        % === Setup video (se richiesto) ===
        if saveVideo
            v = VideoWriter(videoName);
            v.FrameRate = frameRate;
            open(v);
        end
        
        % === Figura con layout ===
        fig = figure('Color','w', 'Name', 'Activation Video', 'NumberTitle','off');
        tiledlayout(fig, 1, 2, 'TileSpacing', 'tight', 'Padding', 'compact');
        
        % === --- (1) SEGNALe ECG --- ===
        nexttile(1);
        plot(t_ms, signal, 'k', 'LineWidth', 1.2);
        hold on
        yl = ylim;
        ecgMarker = plot(t_ms(1), signal(1), 'ko', 'MarkerFaceColor', 'k', 'MarkerSize', 6);
        ylabel('Segnale ECG');
        title('Segnale ECG');
        grid on
        xlim([t_ms(1) t_ms(end)]);
        
        % === --- (2) POINT CLOUD --- ===
        nexttile(2);
        ax3d = gca;
        axis(ax3d, 'equal');
        axis(ax3d, 'vis3d');
        grid(ax3d, 'on');
        xlabel(ax3d, 'X'), ylabel(ax3d, 'Y'), zlabel(ax3d, 'Z');
        view(2);
        
        xlim(ax3d, [min(pc.Location(:,1)) max(pc.Location(:,1))]);
        ylim(ax3d, [min(pc.Location(:,2)) max(pc.Location(:,2))]);
        zlim(ax3d, [min(pc.Location(:,3)) max(pc.Location(:,3))]);
        
        N = size(SignalOnPC,1);
        T = size(SignalOnPC,2);
        
        % === Scatter iniziale ===
        scatterHandle = scatter3(ax3d, ...
            pc.Location(:,1), pc.Location(:,2), pc.Location(:,3), ...
            6, inactiveColor, 'filled');
        
        colormap(ax3d, cmap);
        cb = colorbar(ax3d);
        cb.Label.String = 'Ampiezza ECG';
        title(ax3d, 'Mappa ampiezza ECG');
        
        % Limiti colori (usa range globale)
        ampMin = min(SignalOnPC(:));
        ampMax = max(SignalOnPC(:));
        cb.Limits = [ampMin ampMax];
        
        % === LOOP TEMPORALE ===
        for t = 1:T
            % Aggiorna marker ECG
            set(ecgMarker, 'XData', t_ms(t), 'YData', signal(t));
        
            % Valori ECG correnti sui punti
            amp = SignalOnPC(:,t);
        
            % Identifica punti attivi e inattivi
            activeIdx = ~isnan(amp) & amp ~= 0;
            inactiveIdx = ~activeIdx;
        
            % Colora secondo ampiezza
            colorsAmp = interp1(linspace(ampMin, ampMax, 256), cmap, amp, 'linear', 'extrap');
        
            % Applica grigio ai punti inattivi
            colorsAmp(inactiveIdx,:) = repmat(inactiveColor, sum(inactiveIdx), 1);
        
            % Aggiorna scatter
            set(scatterHandle, 'CData', colorsAmp);
        
            title(ax3d, sprintf('Tempo: %.1f ms', t_ms(t)));
            drawnow limitrate
            view(2);
        
            % Scrittura su video
            if saveVideo
                frame = getframe(fig);
                writeVideo(v, frame);
            end
        end
        
        % === Chiusura video ===
        if saveVideo
            close(v);
            disp([' Video salvato come: ', videoName])
        end


end

end



