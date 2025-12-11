"""
Convert MATLAB binarymatrices.mat to JSON format for frontend use.

This creates a single JSON file with all the data needed for visualization:
- Point cloud from pcheart.ply
- IVT1, EVT1, ActivationSpaceSP, ActivationTimeSP1, t_ms, eigenbeat from .mat file
"""
import numpy as np
import json
from pathlib import Path

try:
    import h5py
    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False

try:
    import scipy.io as sio
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

MATLAB_DIR = Path(__file__).parent
OUTPUT_DIR = MATLAB_DIR.parent / 'frontend-vr' / 'public' / 'matlab_data'

def load_ply(filepath):
    """Load PLY point cloud file (handles both ASCII and binary)."""
    print(f"[INFO] Loading PLY from {filepath}")

    with open(filepath, 'rb') as f:
        header = []
        while True:
            line = f.readline()
            if b'end_header' in line:
                break
            header.append(line.decode('ascii', errors='ignore'))

        # Parse header
        n_vertices = 0
        is_binary = False
        for line in header:
            if 'element vertex' in line:
                n_vertices = int(line.split()[-1])
            if 'format binary' in line:
                is_binary = True

        print(f"[INFO] Format: {'binary' if is_binary else 'ascii'}, vertices: {n_vertices}")

        # Read vertex data
        if is_binary:
            # Binary format: read as float32
            vertex_data = np.frombuffer(f.read(), dtype=np.float32)
            # Reshape to (n_vertices, 3) - assuming x,y,z per vertex
            n_coords = len(vertex_data) // n_vertices
            points = vertex_data.reshape(n_vertices, n_coords)[:, :3]  # Take first 3 coords
        else:
            # ASCII format
            points = []
            for _ in range(n_vertices):
                line = f.readline().decode('ascii')
                parts = line.strip().split()
                x, y, z = float(parts[0]), float(parts[1]), float(parts[2])
                points.append([x, y, z])
            points = np.array(points)

    print(f"[OK] Loaded {points.shape[0]} points")
    return points


def convert_matlab_to_json():
    """Convert MATLAB files to JSON."""
    print("=" * 60)
    print("Converting MATLAB Data to JSON")
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

    print(f"[INFO] Loading MATLAB matrices from {mat_path}")

    # Try h5py first (for MATLAB v7.3), then scipy
    data = {}
    if HAS_H5PY:
        try:
            print("[INFO] Trying h5py reader (MATLAB v7.3)...")
            with h5py.File(mat_path, 'r') as f:
                for key in f.keys():
                    if not key.startswith('#'):
                        data[key] = np.array(f[key]).T  # Transpose for MATLAB compatibility
            print("[OK] Loaded with h5py")
        except Exception as e:
            print(f"[WARNING] h5py failed: {e}")
            data = None

    if not data and HAS_SCIPY:
        try:
            print("[INFO] Trying scipy reader...")
            data = sio.loadmat(mat_path)
            print("[OK] Loaded with scipy")
        except Exception as e:
            print(f"[ERROR] scipy failed: {e}")
            return

    if not data:
        print("[ERROR] Could not load .mat file. Install h5py: pip install h5py")
        return

    # Extract matrices
    activation_space = data.get('ActivationSpaceSP')
    activation_time = data.get('ActivationTimeSP1')
    ivt1 = data.get('IVT1')
    evt1 = data.get('EVT1')
    t_ms = data.get('t_ms')
    eigenbeat = data.get('eigenbeat')

    print(f"[OK] Loaded ActivationSpaceSP: {activation_space.shape}")
    print(f"[OK] Loaded ActivationTimeSP1: {activation_time.shape}")
    print(f"[OK] Loaded IVT1: {ivt1.shape}")
    print(f"[OK] Loaded EVT1: {evt1.shape}")
    print(f"[OK] Loaded t_ms: {t_ms.shape}")
    print(f"[OK] Loaded eigenbeat: {eigenbeat.shape}")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Convert to JSON-serializable format
    output_data = {
        'pointcloud': {
            'points': points.tolist(),
            'n_points': int(points.shape[0])
        },
        'activation_space': activation_space.tolist(),  # N x 8
        'activation_time': activation_time.tolist(),  # 8 x T
        'ivt1': ivt1.tolist(),  # N x T (0=off, 1=trigger, 2=depol, 3=repol)
        'evt1': evt1.tolist(),  # N x T (eigenbeat amplitudes)
        't_ms': t_ms.flatten().tolist(),  # Time vector in ms
        'eigenbeat': eigenbeat.flatten().tolist(),  # Eigenbeat signal
        'metadata': {
            'n_points': int(points.shape[0]),
            'n_samples': int(t_ms.shape[1]),
            'n_regions': 8,
            'region_names': [
                'SA Node',
                'Right Atrium',
                'Left Atrium',
                'AV Node',
                'His Bundle',
                'Bundle Branches',
                'Apex',
                'Purkinje Fibers'
            ],
            'state_names': [
                'Inactive',
                'Trigger',
                'Depolarization',
                'Repolarization'
            ],
            'state_colors': [
                '#808080',  # Gray
                '#00ff00',  # Green
                '#ff0000',  # Red
                '#0000ff'   # Blue
            ]
        }
    }

    # Save to JSON
    output_file = OUTPUT_DIR / 'activation_data.json'
    print(f"[INFO] Saving to {output_file}")

    with open(output_file, 'w') as f:
        json.dump(output_data, f)

    # Get file size
    file_size = output_file.stat().st_size / (1024 * 1024)  # MB
    print(f"[OK] Saved {file_size:.2f} MB to {output_file}")

    # Create a smaller version with reduced time samples for faster loading
    print("[INFO] Creating reduced version...")
    reduced_data = output_data.copy()

    # Take every 5th time sample
    step = 5
    reduced_data['ivt1'] = [row[::step] for row in ivt1.tolist()]
    reduced_data['evt1'] = [row[::step] for row in evt1.tolist()]
    reduced_data['t_ms'] = t_ms.flatten()[::step].tolist()
    reduced_data['eigenbeat'] = eigenbeat.flatten()[::step].tolist()
    reduced_data['activation_time'] = [row[::step] for row in activation_time.tolist()]
    reduced_data['metadata']['n_samples'] = len(reduced_data['t_ms'])

    reduced_file = OUTPUT_DIR / 'activation_data_reduced.json'
    with open(reduced_file, 'w') as f:
        json.dump(reduced_data, f)

    file_size = reduced_file.stat().st_size / (1024 * 1024)
    print(f"[OK] Saved reduced version: {file_size:.2f} MB to {reduced_file}")

    print("=" * 60)
    print("[OK] Conversion complete!")
    print("=" * 60)
    print(f"Full data: {OUTPUT_DIR / 'activation_data.json'}")
    print(f"Reduced data: {OUTPUT_DIR / 'activation_data_reduced.json'}")


if __name__ == '__main__':
    convert_matlab_to_json()
