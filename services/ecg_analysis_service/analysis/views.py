from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from .models import AnalysisJob, AnalysisResult
from .serializers import (
    AnalysisJobSerializer,
    AnalysisResultSerializer,
    ProcessECGRequestSerializer
)
from .algorithms import (
    compute_full_autocorr_analysis,
    compute_full_wavelet_analysis,
    compute_full_graph_analysis
)
import numpy as np
import uuid
import time
import traceback
import requests


@api_view(['POST'])
def process_ecg(request):
    """
    POST /api/analysis/process/
    
    Process ECG signal and extract features.
    
    Request body:
    {
        "ecg_samples": [0.1, 0.2, ...],
        "sampling_frequency": 128.0,
        "device_id": "device001",
        "participant_id": 1,
        "session_id": 1,
        "wavelet_type": "sym4",
        "wavelet_level": null
    }
    
    Response:
    {
        "job_id": "abc123...",
        "status": "completed",
        "result": { ... }
    }
    """
    
    # Validate request
    serializer = ProcessECGRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    data = serializer.validated_data
    
    # Create analysis job
    job_id = str(uuid.uuid4())
    job = AnalysisJob.objects.create(
        job_id=job_id,
        status='processing',
        device_id=data.get('device_id'),
        participant_id=data.get('participant_id'),
        session_id=data.get('session_id'),
        sampling_frequency=data['sampling_frequency'],
        wavelet_type=data['wavelet_type'],
        wavelet_level=data.get('wavelet_level')
    )
    
    try:
        start_time = time.time()
        
        # Convert ECG samples to numpy array
        ecg_signal = np.array(data['ecg_samples'])
        fs = data['sampling_frequency']
        wavelet = data['wavelet_type']
        level = data.get('wavelet_level')
        
        # Step 1: Autocorrelation analysis
        autocorr_result = compute_full_autocorr_analysis(ecg_signal, fs=fs)
        
        # Step 2: Wavelet analysis
        wavelet_result = compute_full_wavelet_analysis(
            ecg_signal,
            wavelet=wavelet,
            level=level,
            fs=fs
        )
        
        # Step 3: Graph analysis (from wavelet correlation matrix)
        corr_matrix = np.array(wavelet_result['corr_matrix'])
        graph_result = compute_full_graph_analysis(
            corr_matrix,
            threshold_method='none',  # Match MATLAB: show all edges
            threshold_value=0.0
        )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Update job status
        job.status = 'completed'
        job.processing_time_ms = processing_time_ms
        job.save()
        
        # Create result object
        result = AnalysisResult.objects.create(
            job=job,
            # Autocorrelation features
            autocorr_first_min_lag=autocorr_result['features'].get('first_min_lag'),
            autocorr_first_min_value=autocorr_result['features'].get('first_min_value'),
            autocorr_first_peak_lag=autocorr_result['features'].get('first_peak_lag'),
            autocorr_first_peak_value=autocorr_result['features'].get('first_peak_value'),
            autocorr_decay_rate=autocorr_result['features'].get('decay_rate'),
            autocorr_periodicity_strength=autocorr_result['features'].get('periodicity_strength'),
            autocorr_data=autocorr_result,
            # Wavelet features
            wavelet_name=wavelet_result['wavelet'],
            wavelet_level=wavelet_result['level'],
            wavelet_total_energy=wavelet_result['features'].get('total_energy'),
            wavelet_energy_entropy=wavelet_result['features'].get('energy_entropy'),
            wavelet_xcorr_mean=wavelet_result['features'].get('xcorr_mean'),
            wavelet_xcorr_std=wavelet_result['features'].get('xcorr_std'),
            wavelet_xcorr_max=wavelet_result['features'].get('xcorr_max'),
            wavelet_xcorr_min=wavelet_result['features'].get('xcorr_min'),
            wavelet_data=wavelet_result,
            # Graph features
            graph_n_nodes=graph_result['features'].get('n_nodes'),
            graph_n_edges=graph_result['features'].get('n_edges'),
            graph_density=graph_result['features'].get('density'),
            graph_avg_degree=graph_result['features'].get('avg_degree'),
            graph_avg_clustering=graph_result['features'].get('avg_clustering'),
            graph_n_components=graph_result['features'].get('n_components'),
            graph_is_connected=graph_result['features'].get('is_connected'),
            graph_diameter=graph_result['features'].get('diameter'),
            graph_max_degree_centrality=graph_result['features'].get('max_degree_centrality'),
            graph_avg_degree_centrality=graph_result['features'].get('avg_degree_centrality'),
            graph_data=graph_result
        )
        
        # Cache result for quick access
        cache.set(f'analysis_result_{job_id}', result.get_summary(), timeout=3600)
        
        # Return response
        result_serializer = AnalysisResultSerializer(result)
        return Response({
            'job_id': job_id,
            'status': 'completed',
            'processing_time_ms': processing_time_ms,
            'result': result_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        # Handle errors
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        job.status = 'failed'
        job.error_message = error_msg
        job.save()
        
        return Response({
            'job_id': job_id,
            'status': 'failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_result(request, job_id):
    """
    GET /api/analysis/result/<job_id>/
    
    Retrieve analysis result by job ID.
    """
    
    # Check cache first
    cached_result = cache.get(f'analysis_result_{job_id}')
    if cached_result:
        return Response(cached_result, status=status.HTTP_200_OK)
    
    # Query database
    try:
        job = AnalysisJob.objects.get(job_id=job_id)
        
        if job.status == 'pending' or job.status == 'processing':
            return Response({
                'job_id': job_id,
                'status': job.status,
                'message': 'Analysis still in progress'
            }, status=status.HTTP_202_ACCEPTED)
        
        elif job.status == 'failed':
            return Response({
                'job_id': job_id,
                'status': 'failed',
                'error': job.error_message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        elif job.status == 'completed':
            result = AnalysisResult.objects.get(job=job)
            serializer = AnalysisResultSerializer(result)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
    except AnalysisJob.DoesNotExist:
        return Response({
            'error': f'Job {job_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except AnalysisResult.DoesNotExist:
        return Response({
            'error': f'Result for job {job_id} not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_latest_result(request):
    """
    GET /api/analysis/latest/
    
    Get the most recent completed analysis result.
    Query parameters:
    - device_id: Filter by device
    - participant_id: Filter by participant
    """
    
    device_id = request.query_params.get('device_id')
    participant_id = request.query_params.get('participant_id')
    
    # Build query
    query = AnalysisJob.objects.filter(status='completed')
    
    if device_id:
        query = query.filter(device_id=device_id)
    if participant_id:
        query = query.filter(participant_id=participant_id)
    
    # Get latest
    job = query.order_by('-created_at').first()
    
    if not job:
        return Response({
            'error': 'No completed analysis found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        result = AnalysisResult.objects.get(job=job)
        serializer = AnalysisResultSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except AnalysisResult.DoesNotExist:
        return Response({
            'error': 'Result not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def list_jobs(request):
    """
    GET /api/analysis/jobs/
    
    List all analysis jobs.
    Query parameters:
    - status: Filter by status
    - device_id: Filter by device
    - limit: Limit number of results (default: 50)
    """
    
    status_filter = request.query_params.get('status')
    device_id = request.query_params.get('device_id')
    limit = int(request.query_params.get('limit', 50))
    
    # Build query
    query = AnalysisJob.objects.all()
    
    if status_filter:
        query = query.filter(status=status_filter)
    if device_id:
        query = query.filter(device_id=device_id)
    
    # Apply limit
    jobs = query[:limit]
    
    serializer = AnalysisJobSerializer(jobs, many=True)
    return Response({
        'count': len(jobs),
        'jobs': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def health_check(request):
    """
    GET /api/analysis/health/
    
    Health check endpoint.
    """
    return Response({
        'status': 'healthy',
        'service': 'ecg-analysis-service',
        'version': '1.0.0'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def generate_plots(request):
    """
    POST /api/analysis/plots/
    
    Generate visualization plots for analysis result.
    """
    job_id = request.data.get('job_id')
    
    if not job_id:
        return Response({'error': 'job_id is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from .visualization import ECGVisualizer
        
        job = AnalysisJob.objects.get(job_id=job_id)
        
        if job.status != 'completed':
            return Response({'error': f'Job status is {job.status}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to fetch heart rate from the main API
        heart_rate = None
        try:
            response = requests.get('http://gateway:8000/api/heartrate/', timeout=2)
            if response.status_code == 200:
                api_data = response.json()
                heart_rate = api_data.get('heart_rate')
        except:
            pass  # If API fails, will calculate from autocorr
        
        result = job.result
        result_data = {
            'autocorr_data': result.autocorr_data,
            'wavelet_data': result.wavelet_data,
            'graph_data': result.graph_data,
            'autocorr_first_min_lag': result.autocorr_first_min_lag,
            'autocorr_first_min_value': result.autocorr_first_min_value,
            'autocorr_first_peak_lag': result.autocorr_first_peak_lag,
            'autocorr_first_peak_value': result.autocorr_first_peak_value,
            'autocorr_periodicity_strength': result.autocorr_periodicity_strength,
            'autocorr_decay_rate': result.autocorr_decay_rate,
            'wavelet_name': result.wavelet_name,
            'graph_n_nodes': result.graph_n_nodes,
            'graph_n_edges': result.graph_n_edges,
            'graph_density': result.graph_density,
            'graph_avg_degree': result.graph_avg_degree,
            'graph_avg_clustering': result.graph_avg_clustering,
            'graph_n_components': result.graph_n_components,
            'graph_is_connected': result.graph_is_connected,
            'graph_diameter': result.graph_diameter,
            'fs': job.sampling_frequency,
            'heart_rate': heart_rate,  # Pass heart rate from API
        }
        
        visualizer = ECGVisualizer()
        plots = visualizer.create_analysis_dashboard(result_data)
        
        return Response({'job_id': job_id, 'plots': plots})
        
    except AnalysisJob.DoesNotExist:
        return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def generate_video(request):
    """
    POST /api/analysis/video/
    
    Generate real-time video animation from ECG samples.
    """
    from .video_generator import ECGVideoGenerator
    
    ecg_samples = request.data.get('ecg_samples')
    fs = request.data.get('sampling_frequency', 128.0)
    duration = request.data.get('duration_seconds', 30)
    
    if not ecg_samples:
        return Response({'error': 'ecg_samples is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        signal = np.array(ecg_samples)
        video_gen = ECGVideoGenerator()
        video_path = video_gen.create_realtime_video(signal, fs=fs, duration_seconds=duration)
        
        video_filename = video_path.split('/')[-1]
        video_url = f"/api/analysis/video/{video_filename}"
        
        return Response({
            'video_path': video_path,
            'video_url': video_url,
            'duration_seconds': duration,
            'fps': 10
        })
        
    except Exception as e:
        return Response({'error': str(e), 'traceback': traceback.format_exc()}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def serve_video(request, filename):
    """
    GET /api/analysis/video/<filename>
    
    Serve generated video file.
    """
    import os
    from django.http import FileResponse
    
    video_path = os.path.join('videos', filename)
    
    if not os.path.exists(video_path):
        return Response({'error': 'Video not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return FileResponse(open(video_path, 'rb'), content_type='video/mp4')
