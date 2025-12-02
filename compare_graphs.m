% Generate same test ECG data
rng(42);
fs = 128;
duration = 5;
samples = duration * fs;
t = (0:samples-1) / fs;
hr_freq = 95 / 60;

ecg = zeros(1, samples);
for i = 1:samples
    tt = (i-1) / fs;
    qrs = 0.8 * sin(2 * pi * hr_freq * tt);
    p_wave = 0.2 * sin(2 * pi * hr_freq * tt - 0.5);
    t_wave = 0.3 * sin(2 * pi * hr_freq * tt + 0.8);
    noise = (rand() - 0.5) * 0.05;
    ecg(i) = qrs + p_wave + t_wave + noise;
end

fprintf('Generated %d ECG samples at %d Hz\n', length(ecg), fs);

% Add path to software v2
addpath('/home/edo/Sapienza/SE/SE_Project/software v2');
addpath(genpath('/home/edo/Sapienza/SE/SE_Project/software v2'));

% Run MATLAB analysis
wname = 'sym4';
w1 = modwt(ecg, wname);
fprintf('MODWT: %dx%d (levels x samples)\n', size(w1, 1), size(w1, 2));

% Compute cross-correlation sequences
xcorr_seqs = modwtxcorr(w1, w1, wname);
fprintf('Cross-correlation sequences: %d levels\n', length(xcorr_seqs));

% Compute correlation matrix (returns cell array)
graphFeat_result = computeFeat_adjmat01(xcorr_seqs);
A_matlab = graphFeat_result{1,1};  % Extract the adjacency matrix
fprintf('Correlation matrix: %dx%d\n', size(A_matlab, 1), size(A_matlab, 2));

% Plot graph using MATLAB's graph function
G = graph(A_matlab);
weights = G.Edges.Weight;
minWidth = 0.5;
maxWidth = 2.5;
normalizedWidths = minWidth + (maxWidth - minWidth) * (weights - min(weights)) / (max(weights) - min(weights));

figure('Name', 'MATLAB Graph', 'Position', [100 100 800 700]);
h = plot(G, 'LineWidth', normalizedWidths, 'EdgeCData', G.Edges.Weight);
colormap jet;
cb = colorbar;
cb.Label.String = 'Edge Weight';
clim([0, 0.7]);
title(sprintf('Graph Features (sym4) - HR: 95.0 bpm - MATLAB'));

% Save plot
saveas(gcf, 'matlab_graph_output.png');
fprintf('✓ Saved: matlab_graph_output.png\n');

% Also save the adjacency matrix for comparison
csvwrite('matlab_adj_matrix_comparison.csv', A_matlab);
fprintf('✓ Saved: matlab_adj_matrix_comparison.csv\n');
fprintf('Adjacency matrix stats: min=%.4f, max=%.4f, mean=%.4f\n', min(A_matlab(:)), max(A_matlab(:)), mean(A_matlab(:)));
fprintf('First 3x3:\n');
disp(A_matlab(1:3, 1:3));
