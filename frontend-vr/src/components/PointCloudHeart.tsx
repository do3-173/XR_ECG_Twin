import React, { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

/**
 * PointCloud Heart Visualization Component
 *
 * Loads MATLAB data (pcheart.ply + binarymatrices.mat) converted to JSON
 * and visualizes the cardiac activation patterns in 3D with ECG waveform.
 */

interface ActivationData {
  pointcloud: {
    points: number[][];
    n_points: number;
  };
  ivt1: number[][];  // N x T - activation states (0=off, 1=trigger, 2=depol, 3=repol)
  evt1: number[][];  // N x T - eigenbeat amplitudes
  t_ms: number[];    // Time vector
  eigenbeat: number[]; // ECG signal
  activation_space: number[][];  // N x 8
  activation_time: number[][];   // 8 x T
  metadata: {
    n_points: number;
    n_samples: number;
    n_regions: number;
    region_names: string[];
    state_names: string[];
    state_colors: string[];
  };
}

export const PointCloudHeart: React.FC = () => {
  const [data, setData] = useState<ActivationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(1); // Display speed (user sees 0.25x to 4x)

  // Base speed multiplier to compensate for 152 samples vs original 31
  const baseSpeedMultiplier = 5;
  const actualSpeed = playSpeed * baseSpeedMultiplier;

  const containerRef = useRef<HTMLDivElement>(null);
  const ecgCanvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const pointsRef = useRef<THREE.Points | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  // Load MATLAB data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        // Use full data (152 samples) instead of reduced (31 samples)
        const response = await fetch('/matlab_data/activation_data.json');
        if (!response.ok) {
          throw new Error('Failed to load activation data');
        }
        const json = await response.json();

        // Debug: Log data structure
        console.log('[DATA LOADED]', {
          points: json.pointcloud?.n_points,
          samples: json.metadata?.n_samples,
          ivt1_shape: `${json.ivt1?.length} x ${json.ivt1?.[0]?.length}`,
          eigenbeat_length: json.eigenbeat?.length
        });

        setData(json);
        setError(null);
      } catch (err: any) {
        console.error('Error loading data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Initialize THREE.js scene
  useEffect(() => {
    if (!data || !containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x001020);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.set(0, 0, 10);
    cameraRef.current = camera;

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // OrbitControls - Enable mouse controls with better responsiveness
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.25; // Smooth and responsive
    controls.enableZoom = true;
    controls.zoomSpeed = 1.5; // Fast mouse wheel zoom
    controls.enableRotate = true;
    controls.rotateSpeed = 1.0;
    controls.enablePan = true;
    controls.panSpeed = 1.0;
    controls.minDistance = 2; // Allow closer zoom
    controls.maxDistance = 100; // Allow farther zoom
    controls.screenSpacePanning = false; // Pan in world space
    controls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.DOLLY,
      RIGHT: THREE.MOUSE.PAN
    };
    controlsRef.current = controls;

    // Create point cloud geometry
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(data.pointcloud.n_points * 3);
    const colors = new Float32Array(data.pointcloud.n_points * 3);

    data.pointcloud.points.forEach((point, i) => {
      positions[i * 3] = point[0];
      positions[i * 3 + 1] = point[1];
      positions[i * 3 + 2] = point[2];
    });

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    // Point material
    const material = new THREE.PointsMaterial({
      size: 0.05,
      vertexColors: true,
      sizeAttenuation: true
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);
    pointsRef.current = points;

    // Animation loop
    const animate = () => {
      animationFrameRef.current = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      controls.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [data]);

  // Update point colors based on activation state
  useEffect(() => {
    if (!data || !pointsRef.current) return;

    const points = pointsRef.current;
    const colors = points.geometry.attributes.color as THREE.BufferAttribute;

    // State color mapping for actual data values
    // Data has states: 0, 2, 3, 4, 5, 6, 9 (no state 1)
    const getStateColor = (state: number): number[] => {
      switch (state) {
        case 0:
          return [0.5, 0.5, 0.5];  // 0 = Inactive - gray
        case 2:
          return [0.0, 1.0, 0.0];  // 2 = Trigger/Early activation - green
        case 3:
          return [1.0, 0.0, 0.0];  // 3 = Depolarization - red
        case 4:
        case 5:
        case 6:
          return [0.0, 0.0, 1.0];  // 4,5,6 = Repolarization phases - blue
        case 9:
          return [1.0, 1.0, 0.0];  // 9 = Special state - yellow
        default:
          return [0.5, 0.5, 0.5];  // Unknown - gray
      }
    };

    // Validate data structure
    if (!data.ivt1 || !Array.isArray(data.ivt1) || data.ivt1.length === 0) {
      console.error('Invalid ivt1 data structure:', data.ivt1);
      return;
    }

    // Clamp currentTime to valid range
    const safeTime = Math.min(Math.max(0, currentTime), data.metadata.n_samples - 1);

    for (let i = 0; i < data.pointcloud.n_points; i++) {
      // Validate point data exists
      if (!data.ivt1[i] || !Array.isArray(data.ivt1[i])) {
        console.error(`Invalid ivt1 data at point ${i}`);
        continue;
      }

      // Get state with bounds checking
      const state = data.ivt1[i][safeTime] || 0;
      const color = getStateColor(state);

      colors.array[i * 3] = color[0];
      colors.array[i * 3 + 1] = color[1];
      colors.array[i * 3 + 2] = color[2];
    }

    colors.needsUpdate = true;
  }, [currentTime, data]);

  // Animation playback
  useEffect(() => {
    if (!isPlaying || !data) return;

    const interval = setInterval(() => {
      setCurrentTime(prev => {
        const next = prev + 1;
        if (next >= data.metadata.n_samples) {
          return 0; // Loop
        }
        return next;
      });
    }, 50 / actualSpeed); // 50ms base, adjusted by actual speed

    return () => clearInterval(interval);
  }, [isPlaying, actualSpeed, data]);

  // Draw ECG waveform
  useEffect(() => {
    if (!data || !ecgCanvasRef.current) return;

    const canvas = ecgCanvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.fillStyle = '#001020';
    ctx.fillRect(0, 0, width, height);

    const ecgSignal = data.eigenbeat;
    const timeVector = data.t_ms;
    const maxSamples = ecgSignal.length;

    const minVal = Math.min(...ecgSignal);
    const maxVal = Math.max(...ecgSignal);
    const range = maxVal - minVal || 1;

    // Draw ECG waveform
    ctx.strokeStyle = '#00d4ff';
    ctx.lineWidth = 2;
    ctx.beginPath();

    for (let i = 0; i < ecgSignal.length; i++) {
      const x = (i / (ecgSignal.length - 1)) * width;
      const y = height - ((ecgSignal[i] - minVal) / range) * (height * 0.8) - height * 0.1;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();

    // Draw current time indicator
    const currentX = (currentTime / (maxSamples - 1)) * width;
    ctx.strokeStyle = '#ff0000';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(currentX, 0);
    ctx.lineTo(currentX, height);
    ctx.stroke();

    // Draw labels
    ctx.fillStyle = '#00d4ff';
    ctx.font = '14px monospace';
    const currentTimeMs = timeVector[Math.min(currentTime, timeVector.length - 1)];
    ctx.fillText(`${currentTimeMs.toFixed(1)} ms`, 10, 20);
    ctx.fillText(`Sample ${currentTime + 1}/${maxSamples}`, 10, 40);
  }, [currentTime, data]);

  if (loading) {
    return (
      <div style={{ padding: '20px', color: '#00d4ff', textAlign: 'center' }}>
        <h2>Loading MATLAB data...</h2>
        <p>Please wait...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', color: '#ff4444', textAlign: 'center' }}>
        <h2>Error Loading Data</h2>
        <p>{error}</p>
        <p>Make sure you've run: cd matlab && source ../venv/bin/activate && python convert_matlab_to_json.py</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: '#001020',
      color: '#00d4ff'
    }}>
      {/* Header */}
      <div style={{ padding: '15px', borderBottom: '2px solid rgba(0, 212, 255, 0.3)' }}>
        <h2 style={{ margin: 0 }}>PointCloud Heart - Cardiac Activation Visualization</h2>
        <p style={{ margin: '5px 0', fontSize: '14px', color: '#888' }}>
          {data.pointcloud.n_points} points | {data.metadata.n_samples} time samples | MATLAB eigenbeat data
        </p>
      </div>

      {/* Main content */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* 3D Visualization */}
        <div style={{ flex: 2, position: 'relative' }}>
          <div
            ref={containerRef}
            style={{ width: '100%', height: '100%' }}
          />

          {/* Legend - overlaid on 3D view */}
          <div style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            background: 'rgba(0, 16, 32, 0.95)',
            padding: '10px',
            borderRadius: '5px',
            border: '1px solid rgba(0, 212, 255, 0.3)'
          }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '5px' }}>Activation States:</div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '3px', fontSize: '11px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                backgroundColor: '#808080',
                marginRight: '6px',
                border: '1px solid #00d4ff'
              }} />
              Inactive (0)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '3px', fontSize: '11px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                backgroundColor: '#00ff00',
                marginRight: '6px',
                border: '1px solid #00d4ff'
              }} />
              Trigger (2)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '3px', fontSize: '11px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                backgroundColor: '#ff0000',
                marginRight: '6px',
                border: '1px solid #00d4ff'
              }} />
              Depolarization (3)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '3px', fontSize: '11px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                backgroundColor: '#0000ff',
                marginRight: '6px',
                border: '1px solid #00d4ff'
              }} />
              Repolarization (4-6)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '3px', fontSize: '11px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                backgroundColor: '#ffff00',
                marginRight: '6px',
                border: '1px solid #00d4ff'
              }} />
              Special (9)
            </div>
          </div>

          {/* 3D Camera Controls - overlaid on left side of 3D view */}
          <div style={{
            position: 'absolute',
            left: '10px',
            top: '50%',
            transform: 'translateY(-50%)',
            background: 'rgba(0, 16, 32, 0.95)',
            padding: '12px',
            borderRadius: '5px',
            border: '1px solid rgba(0, 212, 255, 0.5)'
          }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '10px', color: '#00d4ff', textAlign: 'center' }}>
              Camera
            </div>

            {/* Zoom controls */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '10px', marginBottom: '5px', color: '#888', textAlign: 'center' }}>Zoom</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                <button
                  onClick={() => {
                    if (cameraRef.current && controlsRef.current) {
                      const camera = cameraRef.current;
                      const controls = controlsRef.current;
                      const direction = new THREE.Vector3();
                      direction.subVectors(camera.position, controls.target).normalize();
                      const currentDistance = camera.position.distanceTo(controls.target);
                      const newDistance = Math.max(controls.minDistance, currentDistance - 1.5);
                      camera.position.copy(controls.target).addScaledVector(direction, newDistance);
                      controls.update();
                    }
                  }}
                  style={{
                    padding: '8px 16px',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    backgroundColor: '#00d4ff',
                    color: '#001020',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer'
                  }}
                >
                  [+]
                </button>
                <button
                  onClick={() => {
                    if (cameraRef.current && controlsRef.current) {
                      const camera = cameraRef.current;
                      const controls = controlsRef.current;
                      const direction = new THREE.Vector3();
                      direction.subVectors(camera.position, controls.target).normalize();
                      const currentDistance = camera.position.distanceTo(controls.target);
                      const newDistance = Math.min(controls.maxDistance, currentDistance + 1.5);
                      camera.position.copy(controls.target).addScaledVector(direction, newDistance);
                      controls.update();
                    }
                  }}
                  style={{
                    padding: '8px 16px',
                    fontSize: '14px',
                    fontWeight: 'bold',
                    backgroundColor: '#00d4ff',
                    color: '#001020',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer'
                  }}
                >
                  [-]
                </button>
              </div>
            </div>

            {/* Rotation controls */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '10px', marginBottom: '5px', color: '#888', textAlign: 'center' }}>Rotate</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '5px' }}>
                <div></div>
                <button
                  onClick={() => {
                    if (cameraRef.current && controlsRef.current) {
                      const camera = cameraRef.current;
                      const controls = controlsRef.current;
                      const angle = 0.2;
                      const distance = camera.position.distanceTo(controls.target);
                      const direction = new THREE.Vector3().subVectors(camera.position, controls.target);
                      const horizontalDist = Math.sqrt(direction.x * direction.x + direction.z * direction.z);
                      const newY = controls.target.y + distance * Math.sin(Math.asin(direction.y / distance) + angle);
                      const newHorizontalDist = Math.sqrt(distance * distance - (newY - controls.target.y) * (newY - controls.target.y));
                      const scale = newHorizontalDist / horizontalDist;
                      camera.position.set(
                        controls.target.x + direction.x * scale,
                        newY,
                        controls.target.z + direction.z * scale
                      );
                      controls.update();
                    }
                  }}
                  style={{
                    padding: '6px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    backgroundColor: '#00d4ff',
                    color: '#001020',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    minWidth: '40px'
                  }}
                >
                  ▲
                </button>
                <div></div>

                <button
                  onClick={() => {
                    if (cameraRef.current && controlsRef.current) {
                      const camera = cameraRef.current;
                      const controls = controlsRef.current;
                      const angle = 0.2;
                      const direction = new THREE.Vector3().subVectors(camera.position, controls.target);
                      const newX = direction.x * Math.cos(angle) - direction.z * Math.sin(angle);
                      const newZ = direction.x * Math.sin(angle) + direction.z * Math.cos(angle);
                      camera.position.set(
                        controls.target.x + newX,
                        camera.position.y,
                        controls.target.z + newZ
                      );
                      controls.update();
                    }
                  }}
                  style={{
                    padding: '6px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    backgroundColor: '#00d4ff',
                    color: '#001020',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    minWidth: '40px'
                  }}
                >
                  ◄
                </button>
                <button
                  onClick={() => {
                    if (cameraRef.current && controlsRef.current) {
                      const camera = cameraRef.current;
                      const controls = controlsRef.current;
                      camera.position.set(0, 0, 10);
                      controls.target.set(0, 0, 0);
                      controls.update();
                    }
                  }}
                  style={{
                    padding: '6px',
                    fontSize: '9px',
                    fontWeight: 'bold',
                    backgroundColor: '#666',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    minWidth: '40px'
                  }}
                >
                  ●
                </button>
                <button
                  onClick={() => {
                    if (cameraRef.current && controlsRef.current) {
                      const camera = cameraRef.current;
                      const controls = controlsRef.current;
                      const angle = -0.2;
                      const direction = new THREE.Vector3().subVectors(camera.position, controls.target);
                      const newX = direction.x * Math.cos(angle) - direction.z * Math.sin(angle);
                      const newZ = direction.x * Math.sin(angle) + direction.z * Math.cos(angle);
                      camera.position.set(
                        controls.target.x + newX,
                        camera.position.y,
                        controls.target.z + newZ
                      );
                      controls.update();
                    }
                  }}
                  style={{
                    padding: '6px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    backgroundColor: '#00d4ff',
                    color: '#001020',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    minWidth: '40px'
                  }}
                >
                  ►
                </button>

                <div></div>
                <button
                  onClick={() => {
                    if (cameraRef.current && controlsRef.current) {
                      const camera = cameraRef.current;
                      const controls = controlsRef.current;
                      const angle = -0.2;
                      const distance = camera.position.distanceTo(controls.target);
                      const direction = new THREE.Vector3().subVectors(camera.position, controls.target);
                      const horizontalDist = Math.sqrt(direction.x * direction.x + direction.z * direction.z);
                      const newY = controls.target.y + distance * Math.sin(Math.asin(direction.y / distance) + angle);
                      const newHorizontalDist = Math.sqrt(distance * distance - (newY - controls.target.y) * (newY - controls.target.y));
                      const scale = newHorizontalDist / horizontalDist;
                      camera.position.set(
                        controls.target.x + direction.x * scale,
                        newY,
                        controls.target.z + direction.z * scale
                      );
                      controls.update();
                    }
                  }}
                  style={{
                    padding: '6px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    backgroundColor: '#00d4ff',
                    color: '#001020',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    minWidth: '40px'
                  }}
                >
                  ▼
                </button>
                <div></div>
              </div>
            </div>

            {/* Pan controls */}
            <div>
              <div style={{ fontSize: '10px', marginBottom: '5px', color: '#888', textAlign: 'center' }}>Pan</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '5px' }}>
                <div></div>
                <button
                  onClick={() => {
                    if (cameraRef.current && controlsRef.current) {
                      const controls = controlsRef.current;
                      const camera = cameraRef.current;
                      const panAmount = 0.5;
                      controls.target.y += panAmount;
                      camera.position.y += panAmount;
                      controls.update();
                    }
                  }}
                  style={{
                    padding: '6px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    backgroundColor: '#ff8800',
                    color: '#001020',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    minWidth: '40px'
                  }}
                >
                  ▲
                </button>
                <div></div>

                <button
                  onClick={() => {
                    if (cameraRef.current && controlsRef.current) {
                      const controls = controlsRef.current;
                      const camera = cameraRef.current;
                      const panAmount = 0.5;
                      controls.target.x -= panAmount;
                      camera.position.x -= panAmount;
                      controls.update();
                    }
                  }}
                  style={{
                    padding: '6px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    backgroundColor: '#ff8800',
                    color: '#001020',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    minWidth: '40px'
                  }}
                >
                  ◄
                </button>
                <div></div>
                <button
                  onClick={() => {
                    if (cameraRef.current && controlsRef.current) {
                      const controls = controlsRef.current;
                      const camera = cameraRef.current;
                      const panAmount = 0.5;
                      controls.target.x += panAmount;
                      camera.position.x += panAmount;
                      controls.update();
                    }
                  }}
                  style={{
                    padding: '6px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    backgroundColor: '#ff8800',
                    color: '#001020',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    minWidth: '40px'
                  }}
                >
                  ►
                </button>

                <div></div>
                <button
                  onClick={() => {
                    if (cameraRef.current && controlsRef.current) {
                      const controls = controlsRef.current;
                      const camera = cameraRef.current;
                      const panAmount = 0.5;
                      controls.target.y -= panAmount;
                      camera.position.y -= panAmount;
                      controls.update();
                    }
                  }}
                  style={{
                    padding: '6px',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    backgroundColor: '#ff8800',
                    color: '#001020',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    minWidth: '40px'
                  }}
                >
                  ▼
                </button>
                <div></div>
              </div>
            </div>
          </div>

          {/* Mouse hint - bottom left */}
          <div style={{
            position: 'absolute',
            bottom: '10px',
            left: '10px',
            background: 'rgba(0, 16, 32, 0.9)',
            padding: '6px 10px',
            borderRadius: '5px',
            border: '1px solid rgba(0, 212, 255, 0.3)',
            fontSize: '10px',
            color: '#888'
          }}>
            Mouse: Left-Drag to Rotate | Wheel to Zoom | Right-Drag to Pan
          </div>
        </div>

        {/* Right panel: ECG + Controls */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          padding: '15px',
          borderLeft: '2px solid rgba(0, 212, 255, 0.3)',
          gap: '15px'
        }}>
          {/* ECG Waveform */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ margin: '0 0 10px 0' }}>ECG Eigenbeat</h3>
            <canvas
              ref={ecgCanvasRef}
              width={400}
              height={200}
              style={{
                width: '100%',
                height: '200px',
                border: '1px solid rgba(0, 212, 255, 0.3)',
                borderRadius: '5px',
                backgroundColor: '#001020'
              }}
            />
          </div>

          {/* Controls */}
          <div>
            <h3 style={{ margin: '0 0 10px 0' }}>Animation Controls</h3>

            {/* Playback controls */}
            <div style={{
              display: 'flex',
              gap: '10px',
              marginBottom: '15px'
            }}>
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                style={{
                  flex: 1,
                  padding: '10px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  backgroundColor: isPlaying ? '#ff8800' : '#00d4ff',
                  color: '#001020',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                {isPlaying ? '[PAUSE]' : '[PLAY]'}
              </button>
              <button
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentTime(0);
                }}
                style={{
                  flex: 1,
                  padding: '10px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  backgroundColor: '#666',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                [RESET]
              </button>
            </div>

            {/* Speed control */}
            <div style={{ marginBottom: '15px' }}>
              <label style={{ fontSize: '12px', display: 'block', marginBottom: '5px' }}>
                Speed: {playSpeed}x
              </label>
              <input
                type="range"
                min="0.25"
                max="4"
                step="0.25"
                value={playSpeed}
                onChange={(e) => setPlaySpeed(parseFloat(e.target.value))}
                style={{ width: '100%' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#888' }}>
                <span>0.25x</span>
                <span>4x</span>
              </div>
            </div>

            {/* Time slider */}
            <div style={{ marginBottom: '15px' }}>
              <label style={{ fontSize: '12px', display: 'block', marginBottom: '5px' }}>
                Time: {currentTime} / {data.metadata.n_samples - 1}
              </label>
              <input
                type="range"
                min="0"
                max={data.metadata.n_samples - 1}
                value={currentTime}
                onChange={(e) => {
                  setIsPlaying(false);
                  setCurrentTime(parseInt(e.target.value));
                }}
                style={{ width: '100%' }}
              />
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};
