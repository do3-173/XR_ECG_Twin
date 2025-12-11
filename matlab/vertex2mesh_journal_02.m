function [vertices,faces,normals, c_normals, av_m_normals]=vertex2mesh_journal_02(PC_GT)
% Edo!!!! only the fist two inputs are usefull for us -> line 3 and 5 
vertices=double(PC_GT.Location);
% faces crust
faces=MyCrustOpen(vertices); 

if size(PC_GT.Normal,1)
     f_normals=PC_GT.Normal;
else
    f_normals=[];
end
% normal mesh
mymesh = surfaceMesh(vertices,faces);
computeNormals(mymesh);
normals=mymesh.VertexNormals;

% normal crust
c_normals=compute_normal( vertices, faces)';

% normal matlab
myPC=pointCloud(vertices);
m_normals=pcnormals(myPC);

%smoothing
for i=1:size(m_normals,1)
 nn_indexes= findNearestNeighbors(myPC,vertices(i,:),20);
 av_normals(i,:)=median(normals(nn_indexes,:),1);
 av_c_normals(i,:)=median(c_normals(nn_indexes,:),1);
 av_m_normals(i,:)=median(m_normals(nn_indexes,:),1);
end


% view normals on a point subset
point_subset=1:10:size(vertices,1);

myvisual=0;
if myvisual
% view mesh
myfig = uifigure(Name="Point Cloud GT: mesh");
myg = uigridlayout(myfig,[1 1],Padding=[0 0 0 0]);
myviewer = viewer3d(myfig);
surfaceMeshShow(vertices,double(faces),Parent=myviewer,WireFrame=true,ColorMap="autumn")


% view mesh normals
figure('Name','mesh normals (denoised)');
scatter3(vertices(:,1),vertices(:,2),vertices(:,3), 18);
colormap gray
hold on;
quiver3(vertices(point_subset,1),vertices(point_subset,2),vertices(point_subset,3), ...
        av_normals(point_subset,1),av_normals(point_subset,2),av_normals(point_subset,3), ...
        3.5, 'r'); % 0.5 is the scale factor for normals, 'r' is the color
% view crust normals
figure('Name','crust normals (denoised)');
scatter3(vertices(:,1),vertices(:,2),vertices(:,3), 18);
colormap gray
hold on;
quiver3(vertices(point_subset,1),vertices(point_subset,2),vertices(point_subset,3), ...
        av_c_normals(point_subset,1),av_c_normals(point_subset,2),av_c_normals(point_subset,3), ...
        3.5, 'g'); 

% view matlab normals
figure('Name','matlab normals (denoised)');
scatter3(vertices(:,1),vertices(:,2),vertices(:,3), 18);
colormap gray
hold on;
quiver3(vertices(point_subset,1),vertices(point_subset,2),vertices(point_subset,3), ...
        av_m_normals(point_subset,1),av_m_normals(point_subset,2),av_m_normals(point_subset,3), ...
        3.5, 'b'); % 0.5 is the scale factor for normals, 'r' is the color
end


end