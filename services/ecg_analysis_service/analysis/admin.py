from django.contrib import admin
from .models import AnalysisJob, AnalysisResult


@admin.register(AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    list_display = ['job_id', 'status', 'device_id', 'participant_id', 'created_at', 'processing_time_ms']
    list_filter = ['status', 'created_at']
    search_fields = ['job_id', 'device_id']
    readonly_fields = ['job_id', 'created_at', 'updated_at']


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ['job', 'completed_at', 'wavelet_name', 'graph_n_nodes']
    readonly_fields = ['completed_at']
