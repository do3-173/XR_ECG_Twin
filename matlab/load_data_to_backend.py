"""
Load MATLAB point cloud and binary matrices into the backend service.

This script:
1. Loads pcheart.ply point cloud
2. Loads binarymatrices.mat (ActivationSpace, ActivationTime, etc.)
3. Uploads them to the pointcloud service backend
"""
import numpy as np
import scipy.io as sio
import requests
import json
from pathlib import Path

# Configuration
MATLAB_DIR = Path(__file__).parent
BACKEND_URL = 'http://localhost:8004/api'

def load_ply(filepath):
    """Load PLY point cloud file."""
    print(f"[INFO] Loading PLY from {filepath}")

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # Parse header
    header_end = 0
    n_vertices = 0
    for i, line in enumerate(lines):
        if 'element vertex' in line:
            n_vertices = int(line.split()[-1])
        if 'end_header' in line:
            header_end = i + 1
            break

    # Parse vertices (x, y, z)
    points = []
    for i in range(header_end, header_end + n_vertices):
        parts = lines[i].strip().split()
        x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
        points.append([x, y, z])

    points = np.array(points)
    print(f"[OK] Loaded {points.shape[0]} points")
    return points


def load_matlab_matrices(filepath):
    """Load MATLAB .mat file with binary matrices."""
    print(f"[INFO] Loading MATLAB matrices from {filepath}")

    data = sio.loadmat(filepath)

    # Extract matrices
    result = {}
    for key in ['ActivationSpaceSP', 'ActivationTimeSP1', 'IVT1', 'EVT1', 't_ms', 'eigenbeat']:
        if key in data:
            result[key] = data[key]
            print(f"[OK] Loaded {key}: {data[key].shape}")
        else:
            print(f"[WARNING] {key} not found in mat file")

    return result


def upload_pointcloud(points):
    """Upload point cloud to backend."""
    print(f"[INFO] Uploading point cloud ({points.shape[0]} points) to backend")

    payload = {
        'name': 'Heart Model (MATLAB pcheart.ply)',
        'description': f'Loaded from matlab/pcheart.ply - {points.shape[0]} points',
        'points_data': points.tolist()
    }

    response = requests.post(f'{BACKEND_URL}/pointclouds/', json=payload)

    if response.status_code in [200, 201]:
        pc_data = response.json()
        print(f"[OK] Point cloud uploaded successfully (ID: {pc_data['id']})")
        return pc_data
    else:
        print(f"[ERROR] Failed to upload point cloud: {response.status_code}")
        print(response.text)
        return None


def upload_ecg_data(t_ms, eigenbeat, sampling_frequency=128):
    """Upload ECG data to backend with automatic landmark detection."""
    print(f"[INFO] Uploading ECG data ({len(eigenbeat)} samples)")

    # Simple landmark detection for eigenbeat
    # Find R peak (max value)
    r_peak_idx = np.argmax(eigenbeat)
    r_peak_time = t_ms[r_peak_idx] if len(t_ms.shape) > 1 else t_ms[0, r_peak_idx]

    # Estimate other landmarks based on typical ECG timing
    payload = {
        'name': 'ECG Eigenbeat (MATLAB)',
        'description': 'Eigenbeat from binarymatrices.mat',
        'signal_data': eigenbeat.flatten().tolist(),
        'time_data': t_ms.flatten().tolist(),
        'p_onset': max(0, float(r_peak_time - 150)),
        'p_peak': max(0, float(r_peak_time - 100)),
        'p_offset': max(0, float(r_peak_time - 50)),
        'qrs_onset': max(0, float(r_peak_time - 40)),
        'r_peak': float(r_peak_time),
        'qrs_offset': min(float(t_ms.flatten()[-1]), float(r_peak_time + 40)),
        't_onset': min(float(t_ms.flatten()[-1]), float(r_peak_time + 100)),
        't_offset': min(float(t_ms.flatten()[-1]), float(r_peak_time + 200))
    }

    response = requests.post(f'{BACKEND_URL}/ecg-data/', json=payload)

    if response.status_code in [200, 201]:
        ecg_data = response.json()
        print(f"[OK] ECG data uploaded successfully (ID: {ecg_data['id']})")
        return ecg_data
    else:
        print(f"[ERROR] Failed to upload ECG data: {response.status_code}")
        print(response.text)
        return None


def compute_activation(pointcloud_id, ecg_data_id):
    """Compute activation analysis."""
    print(f"[INFO] Computing activation analysis")

    payload = {
        'pointcloud_id': pointcloud_id,
        'ecg_data_id': ecg_data_id,
        'name': 'Heart Activation Analysis (MATLAB)',
        'description': 'Computed from MATLAB pcheart.ply and binarymatrices.mat'
    }

    response = requests.post(f'{BACKEND_URL}/activation-analysis/compute/', json=payload)

    if response.status_code in [200, 201]:
        analysis_data = response.json()
        print(f"[OK] Activation analysis computed (ID: {analysis_data['id']})")
        return analysis_data
    else:
        print(f"[ERROR] Failed to compute activation: {response.status_code}")
        print(response.text)
        return None


def generate_video(analysis_id, video_type='ideal', frame_rate=30):
    """Generate activation video."""
    print(f"[INFO] Generating video (type: {video_type}, fps: {frame_rate})")

    payload = {
        'analysis_id': analysis_id,
        'name': f'Heart Activation Video ({video_type})',
        'video_type': video_type,
        'frame_rate': frame_rate,
        'description': f'Generated from MATLAB data at {frame_rate}fps'
    }

    response = requests.post(f'{BACKEND_URL}/activation-video/generate/', json=payload)

    if response.status_code in [200, 201]:
        video_data = response.json()
        print(f"[OK] Video generated successfully (ID: {video_data['id']})")
        return video_data
    else:
        print(f"[ERROR] Failed to generate video: {response.status_code}")
        print(response.text)
        return None


def main():
    """Main loading workflow."""
    print("=" * 60)
    print("Loading MATLAB Data to Backend Service")
    print("=" * 60)

    # Load point cloud
    ply_path = MATLAB_DIR / 'pcheart.ply'
    if not ply_path.exists():
        print(f"[ERROR] PLY file not found: {ply_path}")
        return

    points = load_ply(ply_path)

    # Load MATLAB matrices
    mat_path = MATLAB_DIR / 'binarymatrices.mat'
    if not mat_path.exists():
        print(f"[ERROR] MAT file not found: {mat_path}")
        return

    matrices = load_matlab_matrices(mat_path)

    # Upload to backend
    pc_data = upload_pointcloud(points)
    if not pc_data:
        return

    # Upload ECG data
    if 't_ms' in matrices and 'eigenbeat' in matrices:
        ecg_data = upload_ecg_data(matrices['t_ms'], matrices['eigenbeat'])
        if not ecg_data:
            return

        # Compute activation analysis
        analysis_data = compute_activation(pc_data['id'], ecg_data['id'])
        if not analysis_data:
            return

        # Generate videos
        print("\n[INFO] Generating videos...")
        video_ideal = generate_video(analysis_data['id'], video_type='ideal', frame_rate=30)
        video_eigen = generate_video(analysis_data['id'], video_type='eigen', frame_rate=30)

        print("\n" + "=" * 60)
        print("Summary:")
        print("=" * 60)
        print(f"Point Cloud ID: {pc_data['id']}")
        print(f"ECG Data ID: {ecg_data['id']}")
        print(f"Analysis ID: {analysis_data['id']}")
        if video_ideal:
            print(f"Video (Ideal) ID: {video_ideal['id']}")
        if video_eigen:
            print(f"Video (Eigen) ID: {video_eigen['id']}")
        print("=" * 60)
        print("[OK] All data loaded successfully!")
    else:
        print("[ERROR] Missing required matrices in MAT file")


if __name__ == '__main__':
    main()
