"""
Django models for pointcloud activation service.
"""
from django.db import models
from django.contrib.postgres.fields import ArrayField
import json


class PointCloudData(models.Model):
    """Store point cloud data and metadata."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Point cloud data (stored as JSON)
    points_data = models.JSONField(help_text="Point cloud coordinates (Nx3)")
    n_points = models.IntegerField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # File reference if uploaded
    source_file = models.CharField(max_length=500, blank=True)
    
    class Meta:
        db_table = 'pointcloud_data'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.n_points} points)"


class ECGData(models.Model):
    """Store ECG signal data and events."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Signal data
    signal_data = models.JSONField(help_text="ECG signal amplitudes")
    time_data = models.JSONField(help_text="Time vector in milliseconds")
    n_samples = models.IntegerField()
    
    # ECG Events/Landmarks
    p_onset = models.FloatField(help_text="P wave onset (ms)")
    p_peak = models.FloatField(help_text="P wave peak (ms)")
    p_offset = models.FloatField(help_text="P wave offset (ms)")
    qrs_onset = models.FloatField(help_text="QRS complex onset (ms)")
    r_peak = models.FloatField(help_text="R peak (ms)")
    qrs_offset = models.FloatField(help_text="QRS complex offset (ms)")
    t_onset = models.FloatField(help_text="T wave onset (ms)")
    t_offset = models.FloatField(help_text="T wave offset (ms)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ecg_data'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.n_samples} samples)"


class ActivationAnalysis(models.Model):
    """Store computed activation analysis results."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # References
    pointcloud = models.ForeignKey(
        PointCloudData, 
        on_delete=models.CASCADE,
        related_name='analyses'
    )
    ecg_data = models.ForeignKey(
        ECGData,
        on_delete=models.CASCADE,
        related_name='analyses'
    )
    
    # Computed results
    activation_space = models.JSONField(
        help_text="Activation space matrix (NxT)",
        null=True,
        blank=True
    )
    activation_time = models.JSONField(
        help_text="Activation time matrix (8xT)",
        null=True,
        blank=True
    )
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")
    
    class Meta:
        db_table = 'activation_analysis'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.status}"


class ActivationVideo(models.Model):
    """Store generated activation videos."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Reference to analysis
    analysis = models.ForeignKey(
        ActivationAnalysis,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    
    # Video settings
    video_type = models.CharField(
        max_length=20,
        choices=[('ideal', 'Ideal'), ('eigen', 'Eigen')],
        default='ideal'
    )
    frame_rate = models.IntegerField(default=30)
    
    # File path
    video_file = models.CharField(max_length=500)
    file_size = models.BigIntegerField(null=True, blank=True, help_text="File size in bytes")
    duration = models.FloatField(null=True, blank=True, help_text="Duration in seconds")
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generation_time = models.FloatField(null=True, blank=True, help_text="Generation time in seconds")
    
    class Meta:
        db_table = 'activation_video'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.status}"
