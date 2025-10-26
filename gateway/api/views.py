from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import httpx


class StatusView(APIView):
    """Gateway status endpoint"""
    
    def get(self, request):
        return Response({
            'gateway': 'online',
            'services': {
                'ecg_service': settings.ECG_SERVICE_URL,
                'iot_service': settings.IOT_SERVICE_URL,
            }
        })


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
