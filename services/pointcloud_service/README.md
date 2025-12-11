# PointCloud Activation Service

This service implements heart point cloud activation analysis and visualization, translating the MATLAB algorithms from the XR ECG Twin project to Python.

## Overview

The service computes and visualizes cardiac electrical activation patterns on 3D heart point clouds, synchronized with ECG signals. It implements:

1. **Activation Space**: Identifies 8 anatomical cardiac regions in a heart point cloud
2. **Activation Time**: Generates temporal activation maps based on ECG landmarks
3. **Video Generation**: Creates synchronized visualizations of activation patterns and ECG signals

## Architecture

### Core Components

- **compute_activation_space.py**: Identifies anatomical heart regions (SA node, atria, AV node, His bundle, bundle branches, Purkinje fibers)
- **compute_activation_time.py**: Computes temporal activation states (inactive, trigger, depolarization, repolarization)
- **video_generator.py**: Creates MP4 videos showing activation patterns over time

### Data Models

1. **PointCloudData**: Stores 3D heart point clouds
2. **ECGData**: Stores ECG signals with landmark events (P wave, QRS complex, T wave)
3. **ActivationAnalysis**: Stores computed activation space and time matrices
4. **ActivationVideo**: Stores generated visualization videos

## API Endpoints

### Point Cloud Management

```bash
# List all point clouds
GET /api/pointclouds/

# Create new point cloud
POST /api/pointclouds/
{
  "name": "Heart Model 1",
  "description": "18k points heart model",
  "points_data": [[x1, y1, z1], [x2, y2, z2], ...]
}

# Get point cloud statistics
GET /api/pointclouds/{id}/stats/
```

### ECG Data Management

```bash
# List all ECG data
GET /api/ecg-data/

# Create new ECG data
POST /api/ecg-data/
{
  "name": "ECG Beat 1",
  "signal_data": [0.1, 0.15, ...],
  "time_data": [0, 1, 2, ...],
  "p_onset": 50,
  "p_peak": 70,
  "p_offset": 90,
  "qrs_onset": 120,
  "r_peak": 150,
  "qrs_offset": 180,
  "t_onset": 250,
  "t_offset": 350
}

# Get ECG events
GET /api/ecg-data/{id}/events/
```

### Activation Analysis

```bash
# Compute activation space and time
POST /api/activation-analysis/compute/
{
  "pointcloud_id": 1,
  "ecg_data_id": 1,
  "name": "Analysis 1",
  "description": "First analysis"
}

# Get region information
GET /api/activation-analysis/{id}/region_info/

# List all analyses
GET /api/activation-analysis/
```

### Video Generation

```bash
# Generate activation video
POST /api/activation-video/generate/
{
  "analysis_id": 1,
  "name": "Activation Video 1",
  "video_type": "ideal",  # or "eigen"
  "frame_rate": 30,
  "description": "Visualization of cardiac activation"
}

# List all videos
GET /api/activation-video/
```

## Anatomical Regions

The service identifies 8 cardiac regions:

1. **SA Node**: Sinoatrial node (pacemaker)
2. **Right Atrium**: Right atrial tissue
3. **Left Atrium**: Left atrial tissue
4. **AV Node**: Atrioventricular node
5. **His Bundle**: Bundle of His
6. **Bundle Branches**: Left and right bundle branches
7. **Apex**: Ventricular apex (Purkinje start)
8. **Purkinje Fibers**: Extended Purkinje network

## Activation States

Each region transitions through 4 states:

- **0 - Inactive**: No electrical activity (gray)
- **1 - Trigger**: Action potential initiated (green)
- **2 - Depolarization**: Cell depolarizing (red)
- **3 - Repolarization**: Cell repolarizing (blue)

## ECG Correlation

The service correlates anatomical activation with ECG features:

- **P Wave**: Atrial depolarization
  - SA node fires → Right atrium → Left atrium
- **PQ Segment**: AV node delay (isoelectric)
- **QRS Complex**: Ventricular depolarization
  - AV node → His bundle → Bundle branches → Apex → Purkinje
- **T Wave**: Ventricular repolarization
  - All ventricular regions repolarize

## Usage Example

```python
import requests
import numpy as np

# 1. Upload point cloud
points = np.loadtxt('heart_pointcloud.txt')  # Nx3 array
response = requests.post('http://localhost:8004/api/pointclouds/', json={
    'name': 'Heart 18k',
    'points_data': points.tolist()
})
pointcloud_id = response.json()['id']

# 2. Upload ECG data
signal = np.loadtxt('ecg_signal.txt')
time = np.arange(len(signal))
response = requests.post('http://localhost:8004/api/ecg-data/', json={
    'name': 'ECG Beat 1',
    'signal_data': signal.tolist(),
    'time_data': time.tolist(),
    'p_onset': 50, 'p_peak': 70, 'p_offset': 90,
    'qrs_onset': 120, 'r_peak': 150, 'qrs_offset': 180,
    't_onset': 250, 't_offset': 350
})
ecg_id = response.json()['id']

# 3. Compute activation
response = requests.post('http://localhost:8004/api/activation-analysis/compute/', json={
    'pointcloud_id': pointcloud_id,
    'ecg_data_id': ecg_id,
    'name': 'Analysis 1'
})
analysis_id = response.json()['id']

# 4. Generate video
response = requests.post('http://localhost:8004/api/activation-video/generate/', json={
    'analysis_id': analysis_id,
    'name': 'Activation Video',
    'video_type': 'ideal',
    'frame_rate': 30
})
video_path = response.json()['video_file']
```

## MATLAB Correspondence

This service is a Python translation of:

- `compute_ActivationSpace_01.m` → `compute_activation_space.py`
- `compute_ActivationTime_01.m` → `compute_activation_time.py`
- `video_Activation.m` → `video_generator.py`

Key differences:
- Uses Open3D/NumPy instead of MATLAB point cloud functions
- Uses matplotlib/FFmpeg for video generation instead of MATLAB VideoWriter
- REST API interface for easy integration with web frontends
- PostgreSQL database for persistent storage

## Dependencies

- Django + Django REST Framework
- NumPy, SciPy
- matplotlib (for visualization)
- FFmpeg (for video encoding)
- Open3D (for point cloud processing)
- PostgreSQL (for data storage)

## Development

```bash
# Build and start service
docker-compose up pointcloud-service

# Run migrations
docker-compose exec pointcloud-service python manage.py migrate

# Create superuser
docker-compose exec pointcloud-service python manage.py createsuperuser

# Access admin interface
http://localhost:8004/admin/

# Access API
http://localhost:8004/api/
```

## Integration with Frontend

The service can be integrated with the React frontends (standard and VR):

```javascript
// Fetch activation analysis
const response = await fetch('http://localhost:8004/api/activation-analysis/1/');
const analysis = await response.json();

// Use activation_space and activation_time matrices for visualization
const activationSpace = analysis.activation_space;  // NxT matrix
const activationTime = analysis.activation_time;    // 8xT matrix
```

