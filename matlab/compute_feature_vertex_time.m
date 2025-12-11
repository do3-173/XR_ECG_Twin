function [feature_vertex_time, matrix_vertex_time]= compute_feature_vertex_time(U0_selected,vertex_time)
% Input
% U0_selected - matrix Npoints x Neigenvalues, where Npoints is the number
%    of points in the heart point cloud. Each col is one eigenvector 
% vertex_time - matrix Npoints x NTimes - can be or IdealSignalOnPC or
%    EigenSignalOnPC, Ideal is informative for depolarization and
%    re-polarization events and Eigen show the eigenbeat amplitude on PC
% Output
% feature_vertex_time - row vector, Vectorization of matrix_vertex_time
% matrix_vertex_time - matrix Neigenvalues x NTimes is the graph fourier
%    transform of the signal on graph vertex_time 
% 
arguments
    U0_selected 
    vertex_time 
end
[Npoints_u,Neigenvalues] = size(U0_selected);
[Npoints_vt, NTimes] = size(vertex_time);
if Npoints_u == Npoints_vt
    % Per ogni istante di tempo campionato (i), considero il segnale 
    % sul grafo al tempo (i) e lo proietto sulla base
    % Per ogni istante di tempo campionato (i), il segnale 
    % sul grafo al tempo (i) è combinazione lineare degli elementi della
    % base, ovvero gli autovettori del laplaciano
    matrix_vertex_time= U0_selected' * vertex_time;
end
feature_vertex_time = matrix_vertex_time(:)';
end