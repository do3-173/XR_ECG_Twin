from django.db import models

class Device(models.Model):
    device_id = models.CharField(max_length=100, unique=True)
    device_type = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'devices'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.device_id})"


class SensorData(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='sensor_data')
    heart_rate = models.IntegerField(null=True, blank=True)
    zone = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField()
    ecg_samples = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sensor_data'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['device', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.device_id} - HR: {self.heart_rate} at {self.timestamp}"
