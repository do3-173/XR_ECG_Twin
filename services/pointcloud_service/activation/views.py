"""
Views for pointcloud activation service.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import numpy as np
import time
import os
from pathlib import Path

from .models import PointCloudData, ECGData, ActivationAnalysis, ActivationVideo
from .serializers import (
    PointCloudDataSerializer, ECGDataSerializer,
    ActivationAnalysisSerializer, ActivationVideoSerializer,
    ComputeActivationSerializer, GenerateVideoSerializer
)
from .compute_activation_space import ActivationSpaceComputer
from .compute_activation_time import ActivationTimeComputer, ECGEvents
from .video_generator import ActivationVideoGenerator


class PointCloudDataViewSet(viewsets.ModelViewSet):
    """ViewSet for PointCloudData model."""
    
    queryset = PointCloudData.objects.all()
    serializer_class = PointCloudDataSerializer
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get statistics about the point cloud."""
        pointcloud = self.get_object()
        points = np.array(pointcloud.points_data)
        
        stats = {
            'n_points': pointcloud.n_points,
            'bounds': {
                'x_min': float(points[:, 0].min()),
                'x_max': float(points[:, 0].max()),
                'y_min': float(points[:, 1].min()),
                'y_max': float(points[:, 1].max()),
                'z_min': float(points[:, 2].min()),
                'z_max': float(points[:, 2].max()),
            },
            'centroid': {
                'x': float(points[:, 0].mean()),
                'y': float(points[:, 1].mean()),
                'z': float(points[:, 2].mean()),
            }
        }
        
        return Response(stats)


class ECGDataViewSet(viewsets.ModelViewSet):
    """ViewSet for ECGData model."""
    
    queryset = ECGData.objects.all()
    serializer_class = ECGDataSerializer
    
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        """Get ECG events/landmarks."""
        ecg = self.get_object()
        
        events = {
            'p_wave': {
                'onset': ecg.p_onset,
                'peak': ecg.p_peak,
                'offset': ecg.p_offset,
            },
            'qrs_complex': {
                'onset': ecg.qrs_onset,
                'r_peak': ecg.r_peak,
                'offset': ecg.qrs_offset,
            },
            't_wave': {
                'onset': ecg.t_onset,
                'offset': ecg.t_offset,
            }
        }
        
        return Response(events)


class ActivationAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet for ActivationAnalysis model."""
    
    queryset = ActivationAnalysis.objects.all()
    serializer_class = ActivationAnalysisSerializer
    
    @action(detail=False, methods=['post'])
    def compute(self, request):
        """
        Compute activation space and time for given pointcloud and ECG data.
        
        POST /api/activation-analysis/compute/
        Body: {
            "pointcloud_id": 1,
            "ecg_data_id": 1,
            "name": "Analysis 1",
            "description": "Optional description"
        }
        """
        serializer = ComputeActivationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Get objects
        pointcloud = get_object_or_404(PointCloudData, id=data['pointcloud_id'])
        ecg_data = get_object_or_404(ECGData, id=data['ecg_data_id'])
        
        # Create analysis record
        analysis = ActivationAnalysis.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            pointcloud=pointcloud,
            ecg_data=ecg_data,
            status='processing'
        )
        
        try:
            start_time = time.time()
            
            # Convert data to numpy arrays
            points = np.array(pointcloud.points_data, dtype=np.float64)
            t_ms = np.array(ecg_data.time_data, dtype=np.float64)
            signal = np.array(ecg_data.signal_data, dtype=np.float64)
            
            # Compute Activation Space
            space_computer = ActivationSpaceComputer(points)
            activation_space = space_computer.compute(display_figures=False)
            
            # Compute Activation Time
            ecg_events = ECGEvents(
                p_onset=ecg_data.p_onset,
                p_peak=ecg_data.p_peak,
                p_offset=ecg_data.p_offset,
                qrs_onset=ecg_data.qrs_onset,
                r_peak=ecg_data.r_peak,
                qrs_offset=ecg_data.qrs_offset,
                t_onset=ecg_data.t_onset,
                t_offset=ecg_data.t_offset
            )
            time_computer = ActivationTimeComputer(t_ms, ecg_events)
            activation_time = time_computer.compute(display_figure=False)
            
            # Combine activation_space and activation_time to create signal_on_pc
            # signal_on_pc[i, j] = activation_time[region, j] if point i belongs to region
            signal_on_pc = np.zeros((points.shape[0], t_ms.shape[0]), dtype=np.uint8)
            activation_space_int = activation_space.astype(int)
            activation_time_int = activation_time.astype(np.uint8)
            for region_idx in range(8):
                point_mask = activation_space_int[:, region_idx] == 1
                signal_on_pc[point_mask, :] = activation_time_int[region_idx, :]
            
            processing_time = time.time() - start_time
            
            # Update analysis record
            analysis.activation_space = activation_space.tolist()
            analysis.activation_time = activation_time.tolist()
            analysis.status = 'completed'
            analysis.processing_time = processing_time
            analysis.save()
            
            response_serializer = ActivationAnalysisSerializer(analysis)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.save()
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def region_info(self, request, pk=None):
        """Get information about activation regions."""
        analysis = self.get_object()
        
        if not analysis.activation_space:
            return Response(
                {'error': 'Activation space not computed yet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        activation_space = np.array(analysis.activation_space)
        
        region_names = [
            "SA Node", "Right Atrium", "Left Atrium", "AV Node",
            "His Bundle", "Bundle Branches", "Apex", "Purkinje Fibers"
        ]
        
        regions = []
        for i in range(8):
            n_points = np.sum(activation_space[:, i])
            regions.append({
                'index': i,
                'name': region_names[i],
                'n_points': int(n_points),
                'percentage': float(n_points / activation_space.shape[0] * 100)
            })
        
        return Response({'regions': regions})


class ActivationVideoViewSet(viewsets.ModelViewSet):
    """ViewSet for ActivationVideo model."""
    
    queryset = ActivationVideo.objects.all()
    serializer_class = ActivationVideoSerializer
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate activation video for an analysis.
        
        POST /api/activation-video/generate/
        Body: {
            "analysis_id": 1,
            "name": "Video 1",
            "video_type": "ideal",
            "frame_rate": 30,
            "description": "Optional description"
        }
        """
        serializer = GenerateVideoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Get analysis
        analysis = get_object_or_404(ActivationAnalysis, id=data['analysis_id'])
        
        if analysis.status != 'completed':
            return Response(
                {'error': 'Analysis not completed yet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create video record
        video = ActivationVideo.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            analysis=analysis,
            video_type=data['video_type'],
            frame_rate=data['frame_rate'],
            status='generating'
        )
        
        try:
            start_time = time.time()
            
            # Prepare data
            pointcloud = analysis.pointcloud
            ecg_data = analysis.ecg_data
            
            points = np.array(pointcloud.points_data, dtype=np.float64)
            t_ms = np.array(ecg_data.time_data, dtype=np.float64)
            signal = np.array(ecg_data.signal_data, dtype=np.float64)
            activation_space = np.array(analysis.activation_space, dtype=np.uint8)
            activation_time = np.array(analysis.activation_time, dtype=np.uint8)
            
            # Create signal_on_pc
            signal_on_pc = np.zeros((points.shape[0], t_ms.shape[0]), dtype=np.uint8)
            for region_idx in range(8):
                point_mask = activation_space[:, region_idx] == 1
                signal_on_pc[point_mask, :] = activation_time[region_idx, :]
            
            # Generate video
            video_generator = ActivationVideoGenerator(
                points=points,
                signal_on_pc=signal_on_pc,
                signal=signal,
                t_ms=t_ms,
                type_of_signal=data['video_type']
            )
            
            # Create output path
            media_dir = Path('/app/media/videos')
            media_dir.mkdir(parents=True, exist_ok=True)
            output_filename = f"activation_{video.id}_{int(time.time())}.mp4"
            output_path = str(media_dir / output_filename)
            
            # Generate video
            video_path = video_generator.generate_video(
                output_path=output_path,
                frame_rate=data['frame_rate']
            )
            
            generation_time = time.time() - start_time
            
            # Update video record - save relative path for media URL
            video.video_file = f"videos/{output_filename}"
            if os.path.exists(output_path):
                video.file_size = os.path.getsize(output_path)
                video.duration = len(t_ms) / data['frame_rate']
            video.status = 'completed'
            video.generation_time = generation_time
            video.save()
            
            response_serializer = ActivationVideoSerializer(video)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            video.status = 'failed'
            video.error_message = str(e)
            video.save()
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
