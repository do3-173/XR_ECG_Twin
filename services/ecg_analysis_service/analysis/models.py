from django.db import models
from django.contrib.postgres.fields import ArrayField
import json


class AnalysisJob(models.Model):
    """
    Represents an ECG analysis job request.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Job metadata
    job_id = models.CharField(max_length=64, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Input parameters
    device_id = models.CharField(max_length=100, null=True, blank=True)
    participant_id = models.IntegerField(null=True, blank=True)
    session_id = models.IntegerField(null=True, blank=True)
    
    # ECG data reference (could be from iot_sensordata table)
    sensor_data_id = models.IntegerField(null=True, blank=True)
    
    # Analysis parameters
    sampling_frequency = models.FloatField(default=128.0)
    wavelet_type = models.CharField(max_length=20, default='sym4')
    wavelet_level = models.IntegerField(null=True, blank=True)
    
    # Execution info
    processing_time_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'analysis_job'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['device_id', '-created_at']),
        ]
    
    def __str__(self):
        return f"AnalysisJob {self.job_id} - {self.status}"


class AnalysisResult(models.Model):
    """
    Stores results of ECG analysis including autocorrelation, wavelet, and graph features.
    """
    
    # Link to job
    job = models.OneToOneField(
        AnalysisJob,
        on_delete=models.CASCADE,
        related_name='result',
        primary_key=True
    )
    
    # Timestamps
    completed_at = models.DateTimeField(auto_now_add=True)
    
    # === Autocorrelation Features ===
    autocorr_first_min_lag = models.IntegerField(null=True, blank=True)
    autocorr_first_min_value = models.FloatField(null=True, blank=True)
    autocorr_first_peak_lag = models.IntegerField(null=True, blank=True)
    autocorr_first_peak_value = models.FloatField(null=True, blank=True)
    autocorr_decay_rate = models.FloatField(null=True, blank=True)
    autocorr_periodicity_strength = models.FloatField(null=True, blank=True)
    
    # Full autocorrelation data (stored as JSON)
    autocorr_data = models.JSONField(null=True, blank=True)
    
    # === Wavelet Features ===
    wavelet_name = models.CharField(max_length=20, default='sym4')
    wavelet_level = models.IntegerField(default=5)
    wavelet_total_energy = models.FloatField(null=True, blank=True)
    wavelet_energy_entropy = models.FloatField(null=True, blank=True)
    wavelet_xcorr_mean = models.FloatField(null=True, blank=True)
    wavelet_xcorr_std = models.FloatField(null=True, blank=True)
    wavelet_xcorr_max = models.FloatField(null=True, blank=True)
    wavelet_xcorr_min = models.FloatField(null=True, blank=True)
    
    # Full wavelet data (stored as JSON)
    wavelet_data = models.JSONField(null=True, blank=True)
    
    # === Graph Features ===
    graph_n_nodes = models.IntegerField(null=True, blank=True)
    graph_n_edges = models.IntegerField(null=True, blank=True)
    graph_density = models.FloatField(null=True, blank=True)
    graph_avg_degree = models.FloatField(null=True, blank=True)
    graph_avg_clustering = models.FloatField(null=True, blank=True)
    graph_n_components = models.IntegerField(null=True, blank=True)
    graph_is_connected = models.BooleanField(null=True, blank=True)
    graph_diameter = models.IntegerField(null=True, blank=True)
    graph_max_degree_centrality = models.FloatField(null=True, blank=True)
    graph_avg_degree_centrality = models.FloatField(null=True, blank=True)
    
    # Full graph data (stored as JSON)
    graph_data = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'analysis_result'
    
    def __str__(self):
        return f"AnalysisResult for {self.job.job_id}"
    
    def get_summary(self):
        """
        Get a summary of the analysis results.
        """
        return {
            'job_id': self.job.job_id,
            'completed_at': self.completed_at.isoformat(),
            'autocorrelation': {
                'first_min_lag': self.autocorr_first_min_lag,
                'first_peak_lag': self.autocorr_first_peak_lag,
                'periodicity_strength': self.autocorr_periodicity_strength,
                'decay_rate': self.autocorr_decay_rate,
            },
            'wavelet': {
                'name': self.wavelet_name,
                'level': self.wavelet_level,
                'total_energy': self.wavelet_total_energy,
                'energy_entropy': self.wavelet_energy_entropy,
                'xcorr_mean': self.wavelet_xcorr_mean,
            },
            'graph': {
                'n_nodes': self.graph_n_nodes,
                'n_edges': self.graph_n_edges,
                'density': self.graph_density,
                'avg_degree': self.graph_avg_degree,
                'is_connected': self.graph_is_connected,
            }
        }
