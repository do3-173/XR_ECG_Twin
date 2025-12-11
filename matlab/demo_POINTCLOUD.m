%% Dataset YAADbothseg5meanblr - 03/12/2025 

clearvars;close all;clc;
load('.\Data\YAADbothseg5meanblr.mat') % segnali ecg
pcname = 'heart2k'; %heart2k heart18k heart92k
figuredebug = 1;
Nhigh = 10; Nlow = 30;
VTFtype = 'GFT_eigen';
numutenti = numel(dataECG_pp);
numseg_xutente = cellfun(@(segsignal) size(segsignal,1), dataECG_pp);
min_numseg = min(numseg_xutente);
features_vertex_time_overseg = cell(1,min_numseg);
correct_overseg = cell(1,min_numseg);
for idx_seg=1:min_numseg
    extractfeatfrom = cellfun(@(segsignals) segsignals(idx_seg,:),dataECG_pp,'UniformOutput',false);
    [features_vertex_time_overseg{1,idx_seg},correct_overseg{1,idx_seg}] = ECG_XR_04(extractfeatfrom,256, ...
        "figuredebug",figuredebug,"Nhigh",Nhigh,"Nlow",Nlow,"pcname",pcname,"VTFtype",VTFtype);
end
%save('..\features\YAADbothseg5meanblr_VERTEXTIME92k.mat',"correct_overseg","features_vertex_time_overseg")
