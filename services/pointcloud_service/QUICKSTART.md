# Quick Start Guide - PointCloud Activation Service

## Prerequisites
- Docker and Docker Compose installed
- XR_ECG_Twin project cloned

## 1. Build and Start the Service

```bash
# From project root
cd /home/edo/Sapienza/XR_ECG_Twin

# Build and start all services (or just pointcloud service)
docker-compose up -d pointcloud-service

# Check service is running
docker-compose ps pointcloud-service

# View logs
docker-compose logs -f pointcloud-service
```

## 2. Initialize Database

```bash
# Run migrations to create database tables
docker-compose exec pointcloud-service python manage.py makemigrations
docker-compose exec pointcloud-service python manage.py migrate

# Create superuser for admin access
docker-compose exec pointcloud-service python manage.py createsuperuser
# Follow prompts to set username/password
```

## 3. Verify Installation

```bash
# Run test suite
docker-compose exec pointcloud-service python test_service.py

# Access API documentation
curl http://localhost:8004/api/

# Access admin interface
# Browser: http://localhost:8004/admin/
# Login with superuser credentials
```

## 4. Example Usage with cURL

### Upload Point Cloud Data

```bash
# Prepare sample data (you'll need actual point cloud data)
cat > pointcloud_sample.json << 'EOF'
{
  "name": "Heart Model 18k",
  "description": "18000 point heart model",
  "points_data": [
    [1.0, 2.0, -10.0],
    [1.1, 2.1, -10.1],
    [1.2, 2.2, -10.2]
  ]
}
EOF

# Upload point cloud
curl -X POST http://localhost:8004/api/pointclouds/ \
  -H "Content-Type: application/json" \
  -d @pointcloud_sample.json
```

### Upload ECG Data

```bash
cat > ecg_sample.json << 'EOF'
{
  "name": "ECG Beat Sample",
  "description": "Single heartbeat",
  "signal_data": [0.0, 0.1, 0.15, 0.2, 0.5, 1.0, 0.7, 0.3, 0.1, 0.0],
  "time_data": [0, 50, 100, 150, 200, 250, 300, 350, 400, 450],
  "p_onset": 50,
  "p_peak": 100,
  "p_offset": 150,
  "qrs_onset": 200,
  "r_peak": 250,
  "qrs_offset": 300,
  "t_onset": 350,
  "t_offset": 450
}
EOF

curl -X POST http://localhost:8004/api/ecg-data/ \
  -H "Content-Type: application/json" \
  -d @ecg_sample.json
```

### Compute Activation Analysis

```bash
curl -X POST http://localhost:8004/api/activation-analysis/compute/ \
  -H "Content-Type: application/json" \
  -d '{
    "pointcloud_id": 1,
    "ecg_data_id": 1,
    "name": "First Analysis",
    "description": "Testing activation computation"
  }'

# Save the returned analysis ID
ANALYSIS_ID=1
```

### Generate Video

```bash
curl -X POST http://localhost:8004/api/activation-video/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": 1,
    "name": "Activation Video 1",
    "video_type": "ideal",
    "frame_rate": 30,
    "description": "First activation video"
  }'
```

## 5. Using with Python

```python
import requests
import numpy as np

BASE_URL = "http://localhost:8004/api"

# Load MATLAB data (if you have .mat files)
from scipy.io import loadmat

# Load point cloud from MATLAB
data = loadmat('matlab/Data/heart18k.mat')
points = data['vertices']  # Assuming this structure

# Upload point cloud
response = requests.post(f"{BASE_URL}/pointclouds/", json={
    "name": "Heart 18k from MATLAB",
    "points_data": points.tolist()
})
pointcloud_id = response.json()['id']
print(f"Point cloud uploaded: ID={pointcloud_id}")

# Upload ECG (you'll need to extract from your data)
# Assuming you have time vector and signal
response = requests.post(f"{BASE_URL}/ecg-data/", json={
    "name": "ECG from MATLAB",
    "signal_data": signal.tolist(),
    "time_data": t_ms.tolist(),
    "p_onset": 50,
    "p_peak": 70,
    "p_offset": 90,
    "qrs_onset": 120,
    "r_peak": 150,
    "qrs_offset": 180,
    "t_onset": 250,
    "t_offset": 350
})
ecg_id = response.json()['id']
print(f"ECG uploaded: ID={ecg_id}")

# Compute activation
response = requests.post(f"{BASE_URL}/activation-analysis/compute/", json={
    "pointcloud_id": pointcloud_id,
    "ecg_data_id": ecg_id,
    "name": "MATLAB Data Analysis"
})
analysis = response.json()
print(f"Analysis completed: {analysis['status']}")
print(f"Processing time: {analysis['processing_time']:.2f}s")

# Generate video
response = requests.post(f"{BASE_URL}/activation-video/generate/", json={
    "analysis_id": analysis['id'],
    "name": "MATLAB Visualization",
    "video_type": "ideal",
    "frame_rate": 30
})
video = response.json()
print(f"Video generated: {video['video_file']}")
```

## 6. Loading Existing MATLAB Data

If you have the binary matrices from SC's email:

```python
import scipy.io as sio
import requests

# Load MATLAB data
mat_data = sio.loadmat('matlab/binarymatrices.mat')

# Extract matrices (adjust keys based on your .mat file)
activation_space_sp = mat_data['ActivationSpaceSP']
activation_time_sp = mat_data['ActivationTimeSP1']
ivt1 = mat_data['IVT1']
evt1 = mat_data['EVT1']
t_ms = mat_data['t_ms']
eigenbeat = mat_data['eigenbeat']

# Convert sparse matrices to dense if needed
if hasattr(activation_space_sp, 'toarray'):
    activation_space_sp = activation_space_sp.toarray()

# Now you can use this data with the service
# Note: You'll still need the original point cloud coordinates
```

## 7. Integration with Frontend

In your React application:

```javascript
// Fetch activation analysis
async function loadActivationData(analysisId) {
  const response = await fetch(
    `http://localhost:8004/api/activation-analysis/${analysisId}/`
  );
  const data = await response.json();
  
  // Use activation matrices for visualization
  const activationSpace = data.activation_space;  // N×8 matrix
  const activationTime = data.activation_time;    // 8×T matrix
  
  // Render in Three.js or your VR framework
  renderHeartActivation(activationSpace, activationTime);
}

// Generate and monitor video creation
async function generateVideo(analysisId) {
  const response = await fetch(
    'http://localhost:8004/api/activation-video/generate/',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        analysis_id: analysisId,
        name: 'Frontend Generated Video',
        video_type: 'ideal',
        frame_rate: 30
      })
    }
  );
  
  const video = await response.json();
  
  // Poll for completion
  const checkStatus = setInterval(async () => {
    const statusRes = await fetch(
      `http://localhost:8004/api/activation-video/${video.id}/`
    );
    const status = await statusRes.json();
    
    if (status.status === 'completed') {
      clearInterval(checkStatus);
      console.log('Video ready:', status.video_file);
      // Download or display video
    }
  }, 2000);
}
```

## 8. Troubleshooting

### Service won't start
```bash
# Check logs
docker-compose logs pointcloud-service

# Rebuild if needed
docker-compose build pointcloud-service
docker-compose up -d pointcloud-service
```

### Database errors
```bash
# Reset database
docker-compose exec pointcloud-service python manage.py flush
docker-compose exec pointcloud-service python manage.py migrate
```

### FFmpeg not found
```bash
# Reinstall in container
docker-compose exec pointcloud-service apt-get update
docker-compose exec pointcloud-service apt-get install -y ffmpeg
```

### Out of memory during video generation
```bash
# Increase Docker memory limit or reduce:
# - Point cloud size (downsample points)
# - Video frame rate
# - Video duration
```

## 9. Development Tips

```bash
# Interactive shell
docker-compose exec pointcloud-service python manage.py shell

# Django shell for testing
>>> from activation.models import *
>>> PointCloudData.objects.all()
>>> from activation.compute_activation_space import ActivationSpaceComputer
>>> import numpy as np
>>> # Test directly in shell
```

## 10. API Documentation

Full API documentation available at:
- Browsable API: http://localhost:8004/api/
- Admin interface: http://localhost:8004/admin/
- README: `/services/pointcloud_service/README.md`

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f pointcloud-service`
2. Review README: `/services/pointcloud_service/README.md`
3. Check MATLAB correspondence in IMPLEMENTATION_SUMMARY.md
