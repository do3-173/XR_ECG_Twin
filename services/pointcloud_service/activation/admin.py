from django.contrib import admin
from .models import PointCloudData, ECGData, ActivationAnalysis, ActivationVideo


@admin.register(PointCloudData)
class PointCloudDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'n_points', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']


@admin.register(ECGData)
class ECGDataAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'n_samples', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['created_at']


@admin.register(ActivationAnalysis)
class ActivationAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'status', 'pointcloud', 'ecg_data', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['status', 'created_at']


@admin.register(ActivationVideo)
class ActivationVideoAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'status', 'video_type', 'frame_rate', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['status', 'video_type', 'created_at']
