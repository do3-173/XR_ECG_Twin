"""
URL configuration for activation app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PointCloudDataViewSet,
    ECGDataViewSet,
    ActivationAnalysisViewSet,
    ActivationVideoViewSet
)

router = DefaultRouter()
router.register(r'pointclouds', PointCloudDataViewSet, basename='pointcloud')
router.register(r'ecg-data', ECGDataViewSet, basename='ecg-data')
router.register(r'activation-analysis', ActivationAnalysisViewSet, basename='activation-analysis')
router.register(r'activation-video', ActivationVideoViewSet, basename='activation-video')

urlpatterns = [
    path('', include(router.urls)),
]
