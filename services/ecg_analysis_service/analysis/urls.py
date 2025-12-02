from django.urls import path
from . import views

urlpatterns = [
    # Main endpoints
    path('process/', views.process_ecg, name='process_ecg'),
    path('result/<str:job_id>/', views.get_result, name='get_result'),
    path('latest/', views.get_latest_result, name='get_latest_result'),
    path('jobs/', views.list_jobs, name='list_jobs'),
    path('health/', views.health_check, name='health_check'),
    # Visualization endpoints
    path('plots/', views.generate_plots, name='generate_plots'),
    path('video/', views.generate_video, name='generate_video'),
    path('video/<str:filename>', views.serve_video, name='serve_video'),
]
