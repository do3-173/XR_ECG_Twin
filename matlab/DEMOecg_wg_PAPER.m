%% Dataset  YAADbothseg5meanblr
clearvars; close all; clc
load('.\Data\YAADbothseg5meanblr.mat')
load('.\Data\YAADboth_labels.mat')
datasetname ='YAAD';
labelECG = labelECG.Valence_HL;
wname =  {'sym4'} %,'fk14','han4.5','db4'};
numutenti = numel(dataECG_pp);
numseg_xutente = cellfun(@(segsignal) size(segsignal,1), dataECG_pp);
min_numseg = min(numseg_xutente);
features_waveletgraph_overseg = cell(1,min_numseg);
results_WGanalysis_overseg = cell(1,min_numseg);
for idx_seg=1:min_numseg
    extractfeatfrom = cellfun(@(segsignals) segsignals(idx_seg,:),dataECG_pp,'UniformOutput',false);
    results_WGanalysis = WG_analysis03(extractfeatfrom,labelECG,256,wname,"display_figure_flag",1,"datacellname",datasetname);
end