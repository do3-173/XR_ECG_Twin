from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.conf import settings
import httpx
import os
import logging

logger = logging.getLogger(__name__)
NODE_RED_URL = os.environ.get('NODE_RED_URL', 'http://nodered:1880')


class StatusView(APIView):
    """Gateway status endpoint"""
    
    def get(self, request):
        return Response({
            'gateway': 'online',
            'services': {
                'ecg_service': settings.ECG_SERVICE_URL,
                'iot_service': settings.IOT_SERVICE_URL,
                'node_red': NODE_RED_URL,
            }
        })


@api_view(['GET'])
def heartrate_api(request):
    """
    Proxy heart rate data from Node-RED
    GET /api/heartrate
    """
    try:
        with httpx.Client() as client:
            response = client.get(f'{NODE_RED_URL}/api/heartrate', timeout=5.0)
            response.raise_for_status()
            return Response(response.json())
    except Exception as e:
        logger.error(f"Error fetching heartrate from Node-RED: {e}")
        return Response({
            'error': 'Node-RED service unavailable',
            'details': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
def status_api(request):
    """
    Proxy system status from Node-RED
    GET /api/status
    """
    try:
        with httpx.Client() as client:
            response = client.get(f'{NODE_RED_URL}/api/status', timeout=5.0)
            response.raise_for_status()
            return Response(response.json())
    except Exception as e:
        logger.error(f"Error fetching status from Node-RED: {e}")
        return Response({
            'error': 'Node-RED service unavailable',
            'details': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
def ecg_latest(request):
    """
    Get latest ECG data (proxy from Node-RED heartrate endpoint)
    GET /api/ecg/latest
    """
    try:
        with httpx.Client() as client:
            response = client.get(f'{NODE_RED_URL}/api/heartrate', timeout=5.0)
            response.raise_for_status()
            data = response.json()
            
            # Transform to match frontend expectations
            return Response({
                'timestamp': data.get('timestamp'),
                'heartRate': data.get('heart_rate', data.get('heartRate')),
                'zone': data.get('zone'),
                'zoneText': data.get('zone_text', data.get('zoneText')),
                'samples': data.get('samples', data.get('ecg_samples', [])),
                'isConnected': True
            })
    except Exception as e:
        logger.error(f"Error fetching ECG data from Node-RED: {e}")
        return Response({
            'error': 'Node-RED service unavailable',
            'details': str(e),
            'isConnected': False
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class ECGProxyView(APIView):
    """Proxy requests to ECG service"""
    
    async def get(self, request):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.ECG_SERVICE_URL}/api/ecg/",
                    params=request.GET
                )
                return Response(response.json(), status=response.status_code)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
    
    async def post(self, request):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{settings.ECG_SERVICE_URL}/api/ecg/",
                    json=request.data
                )
                return Response(response.json(), status=response.status_code)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )


class DeviceProxyView(APIView):
    """Proxy requests to IoT service"""
    
    async def get(self, request):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.IOT_SERVICE_URL}/api/devices/",
                    params=request.GET
                )
                return Response(response.json(), status=response.status_code)
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
