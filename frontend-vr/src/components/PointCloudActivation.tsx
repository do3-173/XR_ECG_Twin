import React, { useState, useEffect, useRef } from 'react';

interface PointCloudActivationProps {
  apiUrl?: string;
}

interface Point3D {
  x: number;
  y: number;
  z: number;
  state: number; // 0=inactive, 1=trigger, 2=depolarization, 3=repolarization
}

interface AnalysisData {
  id: number;
  name: string;
  status: string;
  pointcloud_name: string;
  ecg_data_name: string;
  processing_time: number | null;
  created_at: string;
  activation_space?: number[][];  // NxT matrix
  activation_time?: number[][];   // 8xT matrix
}

interface VideoData {
  id: number;
  name: string;
  status: string;
  video_type: string;
  frame_rate: number;
  video_file: string;
  video_url?: string;
  duration: number | null;
  generation_time: number | null;
  created_at: string;
}

export const PointCloudActivation: React.FC<PointCloudActivationProps> = ({ 
  apiUrl = 'http://localhost:8004/api' 
}) => {
  const [mode, setMode] = useState<'continuous' | 'recording'>('continuous');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(10); // seconds
  const [frameRate, setFrameRate] = useState(30);
  const [videoType, setVideoType] = useState<'ideal' | 'eigen'>('ideal');
  
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisData | null>(null);
  const [currentVideo, setCurrentVideo] = useState<VideoData | null>(null);
  const [statusMessage, setStatusMessage] = useState('Ready');
  const [error, setError] = useState<string | null>(null);

  // Continuous mode: Update activation display every X seconds
  const [continuousInterval, setContinuousInterval] = useState(5); // seconds
  const [activationData, setActivationData] = useState<any>(null);
  
  // 3D Visualization state
  const [pointCloudPoints, setPointCloudPoints] = useState<Point3D[]>([]);
  const [currentTimeIndex, setCurrentTimeIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    if (mode === 'continuous' && !isProcessing) {
      const interval = setInterval(() => {
        fetchActivationData();
      }, continuousInterval * 1000);
      
      // Fetch immediately on mount
      fetchActivationData();
      
      // Start animation in continuous mode
      setIsPlaying(true);
      
      return () => {
        clearInterval(interval);
        setIsPlaying(false);
      };
    }
  }, [mode, continuousInterval, isProcessing]);

  const fetchActivationData = async () => {
    try {
      setStatusMessage('Fetching activation data...');
      
      // Fetch latest ECG data from gateway
      const ecgResponse = await fetch('http://localhost:8000/api/heartrate');
      const ecgData = await ecgResponse.json();
      
      if (!ecgData.ecg_samples || ecgData.ecg_samples.length === 0) {
        setStatusMessage('No ECG data available');
        return;
      }

      // For continuous mode, we just display the latest state
      // In a full implementation, this would compute activation on the fly
      setActivationData({
        heartRate: ecgData.heart_rate,
        timestamp: new Date().toISOString(),
        sampleCount: ecgData.ecg_samples.length
      });
      
      setStatusMessage(`Updated: ${new Date().toLocaleTimeString()}`);
    } catch (err: any) {
      setError(err.message);
      setStatusMessage('Error fetching data');
    }
  };

  const startRecording = async () => {
    setIsRecording(true);
    setIsProcessing(true);
    setStatusMessage('Recording ECG data...');
    setError(null);

    try {
      // Collect ECG data for the specified duration
      const startTime = Date.now();
      const samples: number[] = [];
      const seenSamples = new Set<string>(); // Track unique samples
      const collectionInterval = 100; // ms
      
      const collectData = async () => {
        const elapsed = Date.now() - startTime;
        
        if (elapsed >= recordingDuration * 1000) {
          // Recording complete
          await processRecording(samples);
          return;
        }

        // Fetch current ECG sample
        try {
          const response = await fetch('http://localhost:3002/api/heartrate/');
          const data = await response.json();
          
          if (data.ecg_samples && data.ecg_samples.length > 0) {
            // Take only new unique samples
            const latestSamples = data.ecg_samples.slice(-10);
            latestSamples.forEach((sample: number) => {
              const key = `${sample}_${samples.length}`;
              if (!seenSamples.has(key)) {
                seenSamples.add(key);
                samples.push(sample);
              }
            });
          }
          
          const progress = Math.min(100, (elapsed / (recordingDuration * 1000)) * 100);
          setStatusMessage(`Recording... ${progress.toFixed(0)}% (${samples.length} unique samples)`);
          
          setTimeout(collectData, collectionInterval);
        } catch (err) {
          console.error('Error collecting sample:', err);
          setTimeout(collectData, collectionInterval);
        }
      };

      collectData();
      
    } catch (err: any) {
      setError(err.message);
      setStatusMessage('Recording failed');
      setIsRecording(false);
      setIsProcessing(false);
    }
  };

  const processRecording = async (samples: number[]) => {
    try {
      setStatusMessage('Processing recorded data...');

      // Step 1: Upload point cloud (for demo, using sample data)
      setStatusMessage('Uploading point cloud...');
      const pcResponse = await fetch(`${apiUrl}/pointclouds/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `Heart Model ${new Date().toISOString()}`,
          description: 'Auto-generated from recording',
          points_data: generateSamplePointCloud() // In production, load from file
        })
      });
      
      if (!pcResponse.ok) throw new Error('Failed to upload point cloud');
      const pcData = await pcResponse.json();

      // Step 2: Upload ECG data with landmarks
      setStatusMessage('Uploading ECG data...');
      const landmarks = detectECGLandmarks(samples);
      
      const ecgResponse = await fetch(`${apiUrl}/ecg-data/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `ECG Recording ${new Date().toISOString()}`,
          description: `Recorded for ${recordingDuration}s`,
          signal_data: samples,
          time_data: samples.map((_, i) => i * (1000 / 128)), // Assuming 128 Hz
          ...landmarks
        })
      });
      
      if (!ecgResponse.ok) throw new Error('Failed to upload ECG data');
      const ecgData = await ecgResponse.json();

      // Step 3: Compute activation
      setStatusMessage('Computing activation...');
      const analysisResponse = await fetch(`${apiUrl}/activation-analysis/compute/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pointcloud_id: pcData.id,
          ecg_data_id: ecgData.id,
          name: `Analysis ${new Date().toISOString()}`,
          description: 'Auto-generated from VR recording'
        })
      });
      
      if (!analysisResponse.ok) throw new Error('Failed to compute activation');
      const analysisData = await analysisResponse.json();
      setCurrentAnalysis(analysisData);
      
      // Initialize 3D visualization with computed activation
      initializeVisualization(pcData.points_data, analysisData);

      // Step 4: Generate video
      setStatusMessage('Generating video...');
      const videoResponse = await fetch(`${apiUrl}/activation-video/generate/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          analysis_id: analysisData.id,
          name: `Video ${new Date().toISOString()}`,
          video_type: videoType,
          frame_rate: frameRate,
          description: `${recordingDuration}s recording at ${frameRate}fps`
        })
      });
      
      if (!videoResponse.ok) throw new Error('Failed to generate video');
      const videoData = await videoResponse.json();
      setCurrentVideo(videoData);

      setStatusMessage('Complete! Video generated successfully.');
      
    } catch (err: any) {
      setError(err.message);
      setStatusMessage('Processing failed');
    } finally {
      setIsRecording(false);
      setIsProcessing(false);
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    setStatusMessage('Recording stopped');
  };

  // Helper function to generate sample point cloud (replace with actual data)
  const generateSamplePointCloud = () => {
    const points = [];
    for (let i = 0; i < 100; i++) {
      points.push([
        Math.random() * 5 + 1,
        Math.random() * 6 + 1,
        Math.random() * 5 - 12
      ]);
    }
    return points;
  };

  // Simple ECG landmark detection (simplified - replace with actual algorithm)
  const detectECGLandmarks = (samples: number[]) => {
    const samplesCount = samples.length;
    const timePerSample = 1000 / 128; // ms per sample at 128 Hz
    
    // Find R peaks (simplified - just find max values)
    let maxIdx = 0;
    let maxVal = samples[0];
    samples.forEach((val, idx) => {
      if (val > maxVal) {
        maxVal = val;
        maxIdx = idx;
      }
    });
    
    const rPeakTime = maxIdx * timePerSample;
    
    // Estimate other landmarks relative to R peak
    return {
      p_onset: Math.max(0, rPeakTime - 150),
      p_peak: Math.max(0, rPeakTime - 100),
      p_offset: Math.max(0, rPeakTime - 50),
      qrs_onset: Math.max(0, rPeakTime - 40),
      r_peak: rPeakTime,
      qrs_offset: Math.min(samplesCount * timePerSample, rPeakTime + 40),
      t_onset: Math.min(samplesCount * timePerSample, rPeakTime + 100),
      t_offset: Math.min(samplesCount * timePerSample, rPeakTime + 200)
    };
  };

  // Initialize 3D visualization
  const initializeVisualization = (points: number[][], analysis: any) => {
    if (!analysis.activation_space || !analysis.activation_time) return;
    
    const activationSpace = analysis.activation_space; // NxT matrix
    const activationTime = analysis.activation_time; // 8xT matrix
    
    // Create point cloud with initial states
    const initialPoints: Point3D[] = points.map((pt, idx) => ({
      x: pt[0],
      y: pt[1],
      z: pt[2],
      state: 0 // Start with inactive
    }));
    
    setPointCloudPoints(initialPoints);
    setCurrentTimeIndex(0);
  };

  // Update point cloud colors based on current time
  const updatePointCloudAtTime = (timeIndex: number) => {
    if (!currentAnalysis || !currentAnalysis.activation_space || !currentAnalysis.activation_time) return;
    
    const activationSpace = currentAnalysis.activation_space;
    const activationTime = currentAnalysis.activation_time;
    
    // Update each point's state based on its region's activation at this time
    const updatedPoints = pointCloudPoints.map((pt, idx) => {
      // Find which region this point belongs to
      let state = 0; // inactive by default
      for (let region = 0; region < 8; region++) {
        if (activationSpace[idx]?.[region] === 1 && activationTime[region]) {
          state = activationTime[region][timeIndex] || 0;
          break;
        }
      }
      return { ...pt, state };
    });
    
    setPointCloudPoints(updatedPoints);
    drawPointCloud(updatedPoints);
  };

  // Draw point cloud on canvas
  const drawPointCloud = (points: Point3D[]) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Clear canvas
    ctx.fillStyle = 'rgba(0, 10, 20, 0.95)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    if (points.length === 0) return;
    
    // State colors (matching MATLAB)
    const stateColors = [
      'rgba(128, 128, 128, 0.8)', // 0: inactive - gray
      'rgba(0, 255, 0, 1.0)',      // 1: trigger - green
      'rgba(255, 0, 0, 1.0)',      // 2: depolarization - red
      'rgba(0, 0, 255, 1.0)'       // 3: repolarization - blue
    ];
    
    // Find bounding box
    const xs = points.map(p => p.x);
    const ys = points.map(p => p.y);
    const zs = points.map(p => p.z);
    
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    const minZ = Math.min(...zs);
    const maxZ = Math.max(...zs);
    
    const rangeX = maxX - minX || 1;
    const rangeY = maxY - minY || 1;
    const rangeZ = maxZ - minZ || 1;
    
    const padding = 40;
    const width = canvas.width - 2 * padding;
    const height = canvas.height - 2 * padding;
    
    // Sort points by z-depth for proper rendering (back to front)
    const sortedPoints = [...points].sort((a, b) => a.z - b.z);
    
    // Draw points with better 3D projection
    sortedPoints.forEach(pt => {
      // 3D to 2D projection with perspective
      const scale = 1 / (1 + (pt.z - minZ) / rangeZ * 0.3);
      const x = padding + ((pt.x - minX) / rangeX) * width;
      const y = padding + ((pt.y - minY) / rangeY) * height;
      
      // Point size based on depth and state
      const depth = (pt.z - minZ) / rangeZ;
      let size = 3 + (1 - depth) * 2; // Closer points are bigger
      
      // Make active states more visible
      if (pt.state > 0) {
        size *= 1.5;
      }
      
      // Draw point with glow effect for active states
      if (pt.state > 0) {
        ctx.shadowBlur = 8;
        ctx.shadowColor = stateColors[pt.state];
      } else {
        ctx.shadowBlur = 0;
      }
      
      ctx.fillStyle = stateColors[pt.state] || stateColors[0];
      ctx.beginPath();
      ctx.arc(x, y, size * scale, 0, Math.PI * 2);
      ctx.fill();
    });
    
    ctx.shadowBlur = 0;
    
    // Draw title
    ctx.font = 'bold 16px monospace';
    ctx.fillStyle = '#00d4ff';
    ctx.fillText('3D Heart Activation', 10, 25);
    
    // Draw legend
    ctx.font = '11px monospace';
    const legendY = canvas.height - 10;
    const legendSpacing = 120;
    
    ['Inactive', 'Trigger', 'Depolarize', 'Repolarize'].forEach((label, idx) => {
      const legendX = 10 + idx * legendSpacing;
      ctx.fillStyle = stateColors[idx];
      ctx.fillRect(legendX, legendY - 8, 12, 12);
      ctx.strokeStyle = '#00d4ff';
      ctx.strokeRect(legendX, legendY - 8, 12, 12);
      ctx.fillStyle = '#00d4ff';
      ctx.fillText(label, legendX + 18, legendY + 2);
    });
  };

  // Animation loop
  useEffect(() => {
    if (isPlaying && currentAnalysis && currentAnalysis.activation_time) {
      const maxTime = currentAnalysis.activation_time[0]?.length || 0;
      
      const animate = () => {
        setCurrentTimeIndex(prev => {
          const next = (prev + 1) % maxTime;
          updatePointCloudAtTime(next);
          return next;
        });
        
        animationRef.current = requestAnimationFrame(animate);
      };
      
      animationRef.current = requestAnimationFrame(animate);
      
      return () => {
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
      };
    }
  }, [isPlaying, currentAnalysis]);

  // Draw initial state
  useEffect(() => {
    if (pointCloudPoints.length > 0) {
      drawPointCloud(pointCloudPoints);
    }
  }, [pointCloudPoints]);

  return (
    <div style={{
      padding: '20px',
      backgroundColor: 'rgba(0, 20, 40, 0.95)',
      borderRadius: '15px',
      border: '2px solid rgba(0, 212, 255, 0.3)',
      maxWidth: '800px',
      margin: '0 auto'
    }}>
      <h2 style={{ color: '#00d4ff', marginBottom: '20px' }}>
        PointCloud Heart Activation
      </h2>

      {/* Mode Selection */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ color: '#00d4ff', marginRight: '20px' }}>
          <input
            type="radio"
            value="continuous"
            checked={mode === 'continuous'}
            onChange={(e) => setMode(e.target.value as any)}
            disabled={isProcessing}
          />
          <span style={{ marginLeft: '5px' }}>Continuous Display</span>
        </label>
        <label style={{ color: '#00d4ff' }}>
          <input
            type="radio"
            value="recording"
            checked={mode === 'recording'}
            onChange={(e) => setMode(e.target.value as any)}
            disabled={isProcessing}
          />
          <span style={{ marginLeft: '5px' }}>Record & Generate Video</span>
        </label>
      </div>

      {/* Continuous Mode Controls */}
      {mode === 'continuous' && (
        <div style={{ marginBottom: '20px' }}>
          <label style={{ color: '#00d4ff', display: 'block', marginBottom: '10px' }}>
            Update Interval: {continuousInterval}s
            <input
              type="range"
              min="1"
              max="30"
              value={continuousInterval}
              onChange={(e) => setContinuousInterval(Number(e.target.value))}
              style={{ width: '100%', marginTop: '5px' }}
            />
          </label>
          
          {activationData && (
            <div style={{
              padding: '15px',
              backgroundColor: 'rgba(0, 100, 150, 0.2)',
              borderRadius: '10px',
              marginTop: '15px'
            }}>
              <div style={{ color: '#00ff88', fontSize: '24px', fontWeight: 'bold' }}>
                {activationData.heartRate} BPM
              </div>
              <div style={{ color: '#00d4ff', fontSize: '14px', marginTop: '5px' }}>
                Samples: {activationData.sampleCount}
              </div>
              <div style={{ color: '#888', fontSize: '12px', marginTop: '5px' }}>
                {new Date(activationData.timestamp).toLocaleTimeString()}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recording Mode Controls */}
      {mode === 'recording' && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ color: '#00d4ff', display: 'block', marginBottom: '5px' }}>
              Recording Duration: {recordingDuration}s
            </label>
            <input
              type="range"
              min="5"
              max="60"
              value={recordingDuration}
              onChange={(e) => setRecordingDuration(Number(e.target.value))}
              disabled={isProcessing}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ color: '#00d4ff', display: 'block', marginBottom: '5px' }}>
              Frame Rate: {frameRate} fps
            </label>
            <input
              type="range"
              min="15"
              max="60"
              step="15"
              value={frameRate}
              onChange={(e) => setFrameRate(Number(e.target.value))}
              disabled={isProcessing}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ color: '#00d4ff', marginRight: '20px' }}>
              <input
                type="radio"
                value="ideal"
                checked={videoType === 'ideal'}
                onChange={(e) => setVideoType(e.target.value as any)}
                disabled={isProcessing}
              />
              <span style={{ marginLeft: '5px' }}>Ideal (Discrete States)</span>
            </label>
            <label style={{ color: '#00d4ff' }}>
              <input
                type="radio"
                value="eigen"
                checked={videoType === 'eigen'}
                onChange={(e) => setVideoType(e.target.value as any)}
                disabled={isProcessing}
              />
              <span style={{ marginLeft: '5px' }}>Eigen (Continuous)</span>
            </label>
          </div>

          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isProcessing && !isRecording}
            style={{
              width: '100%',
              padding: '15px',
              fontSize: '18px',
              fontWeight: 'bold',
              backgroundColor: isRecording ? '#ff4444' : '#00d4ff',
              color: isRecording ? '#fff' : '#001020',
              border: 'none',
              borderRadius: '10px',
              cursor: isProcessing && !isRecording ? 'not-allowed' : 'pointer',
              opacity: isProcessing && !isRecording ? 0.5 : 1
            }}
          >
            {isRecording ? '⏹ Stop Recording' : '⏺ Start Recording'}
          </button>
        </div>
      )}

      {/* Status Display */}
      <div style={{
        padding: '15px',
        backgroundColor: 'rgba(0, 50, 80, 0.5)',
        borderRadius: '10px',
        marginBottom: '15px'
      }}>
        <div style={{ color: '#00d4ff', fontSize: '14px' }}>
          Status: {statusMessage}
        </div>
        {isProcessing && (
          <div style={{
            marginTop: '10px',
            height: '4px',
            backgroundColor: 'rgba(0, 212, 255, 0.2)',
            borderRadius: '2px',
            overflow: 'hidden'
          }}>
            <div style={{
              height: '100%',
              backgroundColor: '#00d4ff',
              animation: 'progress 1.5s infinite'
            }} />
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          padding: '15px',
          backgroundColor: 'rgba(255, 0, 0, 0.2)',
          border: '1px solid #ff4444',
          borderRadius: '10px',
          marginBottom: '15px',
          color: '#ff8888'
        }}>
          Error: {error}
        </div>
      )}

      {/* 3D Visualization - Always visible */}
      <div style={{
        padding: '15px',
        backgroundColor: 'rgba(0, 50, 80, 0.5)',
        borderRadius: '10px',
        marginBottom: '15px'
      }}>
        <h3 style={{ color: '#00d4ff', marginBottom: '10px' }}>
          3D Heart Activation {mode === 'continuous' ? '(Live)' : ''}
        </h3>
        
        <canvas
          ref={canvasRef}
          width={600}
          height={400}
          style={{
            width: '100%',
            maxWidth: '600px',
            border: '1px solid rgba(0, 212, 255, 0.3)',
            borderRadius: '10px',
            display: 'block',
            margin: '0 auto',
            backgroundColor: 'rgba(0, 10, 20, 0.95)'
          }}
        />
        
        {pointCloudPoints.length > 0 && (
          <div style={{ 
            marginTop: '15px',
            display: 'flex',
            gap: '10px',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              disabled={mode === 'continuous'}
              style={{
                padding: '10px 20px',
                backgroundColor: mode === 'continuous' ? '#666' : (isPlaying ? '#ff4444' : '#00ff88'),
                color: mode === 'continuous' ? '#aaa' : '#001020',
                border: 'none',
                borderRadius: '5px',
                cursor: mode === 'continuous' ? 'not-allowed' : 'pointer',
                fontWeight: 'bold',
                opacity: mode === 'continuous' ? 0.5 : 1
              }}
            >
              {isPlaying ? '⏸ Pause' : '▶ Play'}
            </button>
            
            <button
              onClick={() => {
                setCurrentTimeIndex(0);
                updatePointCloudAtTime(0);
              }}
              disabled={isPlaying || mode === 'continuous'}
              style={{
                padding: '10px 20px',
                backgroundColor: '#00d4ff',
                color: '#001020',
                border: 'none',
                borderRadius: '5px',
                cursor: (isPlaying || mode === 'continuous') ? 'not-allowed' : 'pointer',
                fontWeight: 'bold',
                opacity: (isPlaying || mode === 'continuous') ? 0.5 : 1
              }}
            >
              ⏮ Reset
            </button>
            
            <div style={{ color: '#00d4ff', fontSize: '14px', marginLeft: '10px' }}>
              {mode === 'continuous' ? 'Continuous Mode' : `Frame: ${currentTimeIndex + 1} / ${currentAnalysis?.activation_time?.[0]?.length || 0}`}
            </div>
          </div>
        )}
        
        <div style={{
          marginTop: '10px',
          padding: '10px',
          backgroundColor: 'rgba(0, 212, 255, 0.1)',
          borderRadius: '5px',
          color: '#00d4ff',
          fontSize: '12px',
          textAlign: 'center'
        }}>
          💡 {mode === 'continuous' ? 'Live activation display updating every ' + continuousInterval + 's' : 'Visualization shows electrical activation propagating through 8 cardiac regions'}
        </div>
      </div>

      {/* Video Player for Generated Videos */}
      {currentVideo && currentVideo.status === 'completed' && currentVideo.video_url && (
        <div style={{
          padding: '15px',
          backgroundColor: 'rgba(0, 255, 136, 0.1)',
          border: '1px solid #00ff88',
          borderRadius: '10px',
          marginTop: '15px'
        }}>
          <h3 style={{ color: '#00ff88', marginBottom: '10px' }}>
            ✓ Video Generated Successfully
          </h3>
          
          {/* Video Player */}
          <video
            controls
            autoPlay
            loop
            key={currentVideo.video_url}
            style={{
              width: '100%',
              maxWidth: '600px',
              borderRadius: '10px',
              border: '2px solid #00ff88',
              display: 'block',
              margin: '0 auto 15px auto',
              backgroundColor: '#000'
            }}
            onError={(e) => {
              console.error('Video failed to load:', currentVideo.video_url);
              console.error('Error event:', e);
            }}
            onLoadedData={() => {
              console.log('Video loaded successfully:', currentVideo.video_url);
            }}
          >
            <source src={currentVideo.video_url} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          
          <div style={{ 
            fontSize: '11px', 
            color: '#666', 
            marginBottom: '10px',
            fontFamily: 'monospace',
            wordBreak: 'break-all'
          }}>
            URL: {currentVideo.video_url}
          </div>
          
          <div style={{ color: '#00d4ff', fontSize: '14px', marginBottom: '15px' }}>
            <div><strong>Name:</strong> {currentVideo.name}</div>
            <div><strong>Duration:</strong> {currentVideo.duration?.toFixed(2)}s</div>
            <div><strong>Frame Rate:</strong> {currentVideo.frame_rate} fps</div>
            <div><strong>Type:</strong> {currentVideo.video_type}</div>
            <div><strong>Generation Time:</strong> {currentVideo.generation_time?.toFixed(2)}s</div>
          </div>
          
          <button
            onClick={() => window.open(currentVideo.video_url || currentVideo.video_file, '_blank')}
            style={{
              padding: '10px 20px',
              backgroundColor: '#00ff88',
              color: '#001020',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontWeight: 'bold',
              width: '100%'
            }}
          >
            📥 Download Video
          </button>
        </div>
      )}

      {/* Results Display */}
      {currentVideo && currentVideo.status === 'completed' && !currentVideo.video_url && (
        <div style={{
          padding: '15px',
          backgroundColor: 'rgba(0, 255, 136, 0.1)',
          border: '1px solid #00ff88',
          borderRadius: '10px',
          marginTop: '15px'
        }}>
          <h3 style={{ color: '#00ff88', marginBottom: '10px' }}>
            ✓ Video Generated
          </h3>
          <div style={{ color: '#00d4ff', fontSize: '14px' }}>
            <div>Name: {currentVideo.name}</div>
            <div>Duration: {currentVideo.duration?.toFixed(2)}s</div>
            <div>Frame Rate: {currentVideo.frame_rate} fps</div>
            <div>Type: {currentVideo.video_type}</div>
            <div>Generation Time: {currentVideo.generation_time?.toFixed(2)}s</div>
          </div>
          <button
            onClick={() => window.open(currentVideo.video_url || currentVideo.video_file, '_blank')}
            style={{
              marginTop: '10px',
              padding: '10px 20px',
              backgroundColor: '#00ff88',
              color: '#001020',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            📥 Download Video
          </button>
        </div>
      )}
    </div>
  );
};
