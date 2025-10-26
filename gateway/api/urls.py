from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.StatusView.as_view(), name='status'),
    path('ecg/', views.ECGProxyView.as_view(), name='ecg-proxy'),
    path('devices/', views.DeviceProxyView.as_view(), name='device-proxy'),
]
