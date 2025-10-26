from django.db import models
from django.contrib.postgres.fields import ArrayField


class ECGReading(models.Model):
    """Store ECG readings from devices"""
    device_id = models.CharField(max_length=100, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    signal_data = ArrayField(models.FloatField(), help_text="ECG signal values")
    sampling_rate = models.IntegerField(default=128)
    duration_seconds = models.FloatField()
    
    # Processed features
    heart_rate = models.FloatField(null=True, blank=True)
    hrv_rmssd = models.FloatField(null=True, blank=True)
    hrv_sdnn = models.FloatField(null=True, blank=True)
    heart_rate_zone = models.IntegerField(null=True, blank=True)
    
    # Metadata
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device_id', '-timestamp']),
        ]
    
    def __str__(self):
        return f"ECG Reading {self.device_id} at {self.timestamp}"


class ECGFeatures(models.Model):
    """Store extracted features from ECG signals"""
    reading = models.OneToOneField(ECGReading, on_delete=models.CASCADE, related_name='features')
    
    # HRV Features
    mean_hr = models.FloatField(null=True)
    std_hr = models.FloatField(null=True)
    rmssd = models.FloatField(null=True)
    sdnn = models.FloatField(null=True)
    pnn50 = models.FloatField(null=True)
    
    # Wavelet Features (simplified - store as JSON for flexibility)
    wavelet_features = models.JSONField(default=dict)
    
    # Statistical Features
    signal_mean = models.FloatField(null=True)
    signal_std = models.FloatField(null=True)
    signal_min = models.FloatField(null=True)
    signal_max = models.FloatField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Features for {self.reading}"
