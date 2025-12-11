"""
Serializers for pointcloud activation service.
"""
from rest_framework import serializers
from .models import PointCloudData, ECGData, ActivationAnalysis, ActivationVideo


class PointCloudDataSerializer(serializers.ModelSerializer):
    """Serializer for PointCloudData model."""
    
    class Meta:
        model = PointCloudData
        fields = [
            'id', 'name', 'description', 'points_data', 'n_points',
            'source_file', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'n_points']
    
    def validate_points_data(self, value):
        """Validate point cloud data format."""
        if not isinstance(value, list):
            raise serializers.ValidationError("points_data must be a list")
        
        if len(value) == 0:
            raise serializers.ValidationError("points_data cannot be empty")
        
        # Check first point has 3 coordinates
        if not isinstance(value[0], list) or len(value[0]) != 3:
            raise serializers.ValidationError("Each point must have 3 coordinates [x, y, z]")
        
        return value
    
    def create(self, validated_data):
        """Override create to set n_points."""
        validated_data['n_points'] = len(validated_data['points_data'])
        return super().create(validated_data)


class ECGDataSerializer(serializers.ModelSerializer):
    """Serializer for ECGData model."""
    
    class Meta:
        model = ECGData
        fields = [
            'id', 'name', 'description', 'signal_data', 'time_data', 'n_samples',
            'p_onset', 'p_peak', 'p_offset', 'qrs_onset', 'r_peak', 'qrs_offset',
            't_onset', 't_offset', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'n_samples']
    
    def validate(self, data):
        """Validate ECG data."""
        signal_data = data.get('signal_data')
        time_data = data.get('time_data')
        
        if not isinstance(signal_data, list) or not isinstance(time_data, list):
            raise serializers.ValidationError("signal_data and time_data must be lists")
        
        if len(signal_data) != len(time_data):
            raise serializers.ValidationError("signal_data and time_data must have same length")
        
        if len(signal_data) == 0:
            raise serializers.ValidationError("signal_data cannot be empty")
        
        return data
    
    def create(self, validated_data):
        """Override create to set n_samples."""
        validated_data['n_samples'] = len(validated_data['signal_data'])
        return super().create(validated_data)


class ActivationAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for ActivationAnalysis model."""
    
    pointcloud_name = serializers.CharField(source='pointcloud.name', read_only=True)
    ecg_data_name = serializers.CharField(source='ecg_data.name', read_only=True)
    
    class Meta:
        model = ActivationAnalysis
        fields = [
            'id', 'name', 'description', 'pointcloud', 'pointcloud_name',
            'ecg_data', 'ecg_data_name', 'activation_space', 'activation_time',
            'status', 'error_message', 'processing_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'activation_space', 'activation_time', 'status',
            'error_message', 'processing_time', 'created_at', 'updated_at'
        ]


class ActivationVideoSerializer(serializers.ModelSerializer):
    """Serializer for ActivationVideo model."""
    
    analysis_name = serializers.CharField(source='analysis.name', read_only=True)
    video_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivationVideo
        fields = [
            'id', 'name', 'description', 'analysis', 'analysis_name',
            'video_type', 'frame_rate', 'video_file', 'video_url', 'file_size', 'duration',
            'status', 'error_message', 'generation_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'video_file', 'video_url', 'file_size', 'duration', 'status',
            'error_message', 'generation_time', 'created_at', 'updated_at'
        ]
    
    def get_video_url(self, obj):
        """Return full URL to video file."""
        if obj.video_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/media/{obj.video_file}')
            return f'http://localhost:8004/media/{obj.video_file}'
        return None


class ComputeActivationSerializer(serializers.Serializer):
    """Serializer for compute activation request."""
    
    pointcloud_id = serializers.IntegerField()
    ecg_data_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)


class GenerateVideoSerializer(serializers.Serializer):
    """Serializer for generate video request."""
    
    analysis_id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    video_type = serializers.ChoiceField(choices=['ideal', 'eigen'], default='ideal')
    frame_rate = serializers.IntegerField(default=30, min_value=1, max_value=120)
    description = serializers.CharField(required=False, allow_blank=True)
