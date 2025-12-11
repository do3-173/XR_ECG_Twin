"""
Test script for PointCloud Activation Service
"""
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from activation.compute_activation_space import ActivationSpaceComputer
from activation.compute_activation_time import ActivationTimeComputer, ECGEvents


def test_activation_space():
    """Test ActivationSpace computation with synthetic data."""
    print("Testing ActivationSpace computation...")
    
    # Create synthetic heart point cloud (simplified)
    # In reality, this would be loaded from a .mat or .ply file
    n_points = 1000
    
    # Generate random points in a heart-like region
    np.random.seed(42)
    points = np.random.randn(n_points, 3)
    points[:, 0] = points[:, 0] * 2 + 2.5  # x: 0-5
    points[:, 1] = points[:, 1] * 2 + 3.0  # y: 0-6
    points[:, 2] = points[:, 2] * 2 - 11.0 # z: -15 to -7
    
    # Compute activation space
    computer = ActivationSpaceComputer(points)
    activation_space = computer.compute(display_figures=False)
    
    print(f"✓ Computed activation space: {activation_space.shape}")
    print(f"  - Total points: {n_points}")
    
    region_names = [
        "SA Node", "Right Atrium", "Left Atrium", "AV Node",
        "His Bundle", "Bundle Branches", "Apex", "Purkinje Fibers"
    ]
    
    for i in range(8):
        n_region_points = np.sum(activation_space[:, i])
        print(f"  - {region_names[i]}: {n_region_points} points ({n_region_points/n_points*100:.1f}%)")
    
    return activation_space


def test_activation_time():
    """Test ActivationTime computation with synthetic ECG."""
    print("\nTesting ActivationTime computation...")
    
    # Create synthetic ECG data
    duration_ms = 800  # 800ms for one beat
    sampling_rate = 1000  # 1 sample per ms
    t_ms = np.linspace(0, duration_ms, sampling_rate)
    
    # Synthetic ECG signal (simplified)
    signal = np.zeros(sampling_rate)
    
    # P wave (50-100 ms)
    p_indices = (t_ms >= 50) & (t_ms <= 100)
    signal[p_indices] = 0.2 * np.sin(np.pi * (t_ms[p_indices] - 50) / 50)
    
    # QRS complex (120-200 ms)
    qrs_indices = (t_ms >= 120) & (t_ms <= 200)
    signal[qrs_indices] = 1.0 * np.sin(np.pi * (t_ms[qrs_indices] - 120) / 80)
    
    # T wave (250-400 ms)
    t_indices = (t_ms >= 250) & (t_ms <= 400)
    signal[t_indices] = 0.3 * np.sin(np.pi * (t_ms[t_indices] - 250) / 150)
    
    # Define ECG events
    ecg_events = ECGEvents(
        p_onset=50,
        p_peak=75,
        p_offset=100,
        qrs_onset=120,
        r_peak=160,
        qrs_offset=200,
        t_onset=250,
        t_offset=400
    )
    
    # Compute activation time
    computer = ActivationTimeComputer(t_ms, ecg_events)
    activation_time = computer.compute(display_figure=False)
    
    print(f"✓ Computed activation time: {activation_time.shape}")
    print(f"  - Time samples: {len(t_ms)}")
    
    region_names = [
        "SA Node", "Right Atrium", "Left Atrium", "AV Node",
        "His Bundle", "Bundle Branches", "Apex", "Purkinje Fibers"
    ]
    
    for i in range(8):
        timeline = activation_time[i, :]
        active_samples = np.sum(timeline > 0)
        trigger_samples = np.sum(timeline == 1)
        depol_samples = np.sum(timeline == 2)
        repol_samples = np.sum(timeline == 3)
        
        print(f"  - {region_names[i]}:")
        print(f"      Active: {active_samples}ms, Trigger: {trigger_samples}ms, "
              f"Depol: {depol_samples}ms, Repol: {repol_samples}ms")
    
    return activation_time, signal, t_ms


def test_video_generation():
    """Test video generation with synthetic data."""
    print("\nTesting video generation...")
    
    from activation.video_generator import ActivationVideoGenerator
    
    # Create simple test data
    n_points = 100
    n_frames = 50
    
    points = np.random.randn(n_points, 3)
    signal_on_pc = np.random.randint(0, 4, size=(n_points, n_frames))
    signal = np.sin(np.linspace(0, 2*np.pi, n_frames))
    t_ms = np.linspace(0, 500, n_frames)
    
    generator = ActivationVideoGenerator(
        points=points,
        signal_on_pc=signal_on_pc,
        signal=signal,
        t_ms=t_ms,
        type_of_signal='ideal'
    )
    
    print(f"✓ Created video generator")
    print(f"  - Points: {n_points}")
    print(f"  - Frames: {n_frames}")
    print(f"  - Duration: {t_ms[-1]}ms")
    
    # Test frame rendering (without saving video)
    colors = generator.get_point_colors(0)
    print(f"✓ Generated colors for frame 0: {colors.shape}")
    
    print("\nNote: Full video generation requires FFmpeg and takes time.")
    print("      Use generate_video() method to create actual video files.")


if __name__ == '__main__':
    print("=" * 60)
    print("PointCloud Activation Service - Test Suite")
    print("=" * 60)
    
    try:
        # Run tests
        activation_space = test_activation_space()
        activation_time, signal, t_ms = test_activation_time()
        test_video_generation()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
