from rest_framework import serializers
from .models import AnalysisJob, AnalysisResult


class AnalysisJobSerializer(serializers.ModelSerializer):
    """
    Serializer for AnalysisJob model.
    """
    class Meta:
        model = AnalysisJob
        fields = [
            'job_id', 'status', 'created_at', 'updated_at',
            'device_id', 'participant_id', 'session_id',
            'sensor_data_id', 'sampling_frequency',
            'wavelet_type', 'wavelet_level',
            'processing_time_ms', 'error_message'
        ]
        read_only_fields = ['job_id', 'created_at', 'updated_at', 'status']


class AnalysisResultSerializer(serializers.ModelSerializer):
    """
    Serializer for AnalysisResult model.
    """
    job = AnalysisJobSerializer(read_only=True)
    summary = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalysisResult
        fields = '__all__'
    
    def get_summary(self, obj):
        return obj.get_summary()


class ProcessECGRequestSerializer(serializers.Serializer):
    """
    Serializer for ECG processing request.
    """
    ecg_samples = serializers.ListField(
        child=serializers.FloatField(),
        help_text="Array of ECG signal samples"
    )
    sampling_frequency = serializers.FloatField(
        default=128.0,
        help_text="Sampling frequency in Hz"
    )
    device_id = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Device identifier"
    )
    participant_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Participant ID"
    )
    session_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Session ID"
    )
    wavelet_type = serializers.CharField(
        default='sym4',
        help_text="Wavelet type (sym4, db4, coif1, etc.)"
    )
    wavelet_level = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Wavelet decomposition level (auto if None)"
    )
    
    def validate_ecg_samples(self, value):
        """Validate ECG samples array."""
        if len(value) < 128:  # At least 1 second of data at 128 Hz
            raise serializers.ValidationError(
                "ECG samples must contain at least 128 samples (1 second at 128 Hz)"
            )
        if len(value) > 100000:  # Max ~13 minutes at 128 Hz
            raise serializers.ValidationError(
                "ECG samples array too large (max 100,000 samples)"
            )
        return value
    
    def validate_sampling_frequency(self, value):
        """Validate sampling frequency."""
        if value < 50 or value > 1000:
            raise serializers.ValidationError(
                "Sampling frequency must be between 50 and 1000 Hz"
            )
        return value
