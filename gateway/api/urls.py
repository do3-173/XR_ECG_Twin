from django.urls import path
from . import views

urlpatterns = [
    path('status/', views.StatusView.as_view(), name='status'),
    path('heartrate/', views.heartrate_api, name='heartrate'),
    path('ecg/latest/', views.ecg_latest, name='ecg-latest'),
    path('ecg/', views.ECGProxyView.as_view(), name='ecg-proxy'),
    path('devices/', views.DeviceProxyView.as_view(), name='device-proxy'),
]
