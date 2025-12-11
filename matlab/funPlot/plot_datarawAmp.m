function [fig_dataAmp_byclass, fig_dataAmp_byclass_samefig ]=plot_datarawAmp(datamat,datatype,datasetname, labels, options)
arguments
    datamat 
    datatype {mustBeMember(datatype,["signals","GWF","WF"])} 
    datasetname {mustBeMember(datasetname,["synth","YAAD","VREED","CPSC2018"])}  
    labels 
    options.save_figure_flag {mustBeNumericOrLogical} = 0
    options.titlename = [datasetname datatype]
end

if options.save_figure_flag
    fig_mainfolderName = '.\figure\plot_datarawAmp02\' ;
    if ~exist(fig_mainfolderName,'dir')
        disp(['Creating ' fig_mainfolderName])
        mkdir(fig_mainfolderName);
    else
        disp(['Already exist' fig_mainfolderName] )
    end
end
switch datatype
    case "signals"
        ylab = '$k$';
        xlab = '$n$';
        titlefeat = '';
    case "GWF"
        ylab = '$k$';
        xlab = '$a_{ij}$';
        titlefeat = '$\mathcal{F}^{(GWF)}$';
        loc_colorbar = 'eastoutside';
        if datasetname == "synth"
        amp_lim = [0 0.2]; % da 0 a 0.3
        end
    case "WF"
        ylab = '$k$';
        xlab = '$n$';
        titlefeat = '$\mathcal{F}^{(WF)}$';
        loc_colorbar = 'eastoutside';
        if datasetname == "synth"
        amp_lim = [-0.7 0.7]; % da -0.7 a 0.7
        end
end


classes = unique(labels); % classes{idx_class,1}
fig_dataAmp_byclass = figure('Name',[options.titlename 'DataAmp_sepClasses']);
figure(fig_dataAmp_byclass)
tiledlayout
databyclasses_org = cell(size(classes));
for idx_class = 1:numel(classes)
    classname = classes{idx_class,1};
    true_classname = strcmp(labels, classname);
    databyclasses_org{idx_class,1} = datamat(true_classname,:);
    
    nexttile
    imagesc(datamat(true_classname,:))
    if exist('amp_lim','var')
        clim(gca, amp_lim) % imposta i limiti di ampiezza
    end
    set(gca,'FontSize',20,'FontName','Times New Roman')
    xlabel(xlab,'Interpreter','latex','FontSize',30)
    ylabel(ylab,'Interpreter','latex','FontSize',30)
    colormap(jet)
    colorbar(loc_colorbar)
    if ~isempty(titlefeat)
        title(titlefeat,'Interpreter','latex','FontSize',30)
        subtitle(classname,'FontSize',20)
    else
        title(classname,'FontSize',20)
    end

end % for over classes
if options.save_figure_flag
    savefig(fullfile(fig_mainfolderName,[fig_dataAmp_byclass.Name '.fig'] ))
    disp(fullfile(fig_mainfolderName,[fig_dataAmp_byclass.Name '.fig'] ))
end
fig_dataAmp_byclass_samefig = figure('Name',[options.titlename 'DataAmp_sepClasses_same']);
figure(fig_dataAmp_byclass_samefig)
imagesc(cell2mat(databyclasses_org))
if exist('amp_lim','var')
    clim(gca, amp_lim) % imposta i limiti di ampiezza
end
set(gca,'FontSize',20,'FontName','Times New Roman')
xlabel(xlab,'Interpreter','latex','FontSize',30)
ylabel(ylab,'Interpreter','latex','FontSize',30)
if ~isempty(titlefeat)
    title(titlefeat,'Interpreter','latex','FontSize',30)
end
colormap(jet)
colorbar(loc_colorbar)
if options.save_figure_flag
    savefig(fullfile(fig_mainfolderName,[fig_dataAmp_byclass_samefig.Name '.fig'] ))
    disp(fullfile(fig_mainfolderName,[fig_dataAmp_byclass_samefig.Name '.fig'] ))
end

end