import React, { useState, useEffect, useRef } from 'react';
import './App.css';

interface HeartRateData {
  timestamp: string;
  heart_rate: number;
  zone: number;
  zone_text: string;
  history: Array<{ time: number; value: number; zone: number }>;
  ecg_samples: number[];
}

function App() {
  const [heartRate, setHeartRate] = useState<number>(0);
  const [zone, setZone] = useState<number>(1);
  const [zoneText, setZoneText] = useState<string>('--');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [elapsedTime, setElapsedTime] = useState<string>('00:00:00');
  const [ecgData, setEcgData] = useState<number[]>([]);
  const [history, setHistory] = useState<Array<{ time: number; value: number; zone: number }>>([]);
  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null);
  
  const ecgCanvasRef = useRef<HTMLCanvasElement>(null);
  const historyCanvasRef = useRef<HTMLCanvasElement>(null);
  const startTimeRef = useRef<Date>(new Date());

  const API_URL = '/api/heartrate/';
  const MAX_ECG_POINTS = 128 * 5;

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(API_URL);
        const data: HeartRateData = await response.json();
        
        setIsConnected(true);
        setHeartRate(data.heart_rate);
        setZone(data.zone);
        setZoneText(data.zone_text);
        setEcgData(data.ecg_samples?.slice(-MAX_ECG_POINTS) || []);
        setHistory(data.history || []);
      } catch (error) {
        console.error('Error fetching data:', error);
        setIsConnected(false);
        setEcgData(new Array(100).fill(0));
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      const elapsed = Math.floor((now.getTime() - startTimeRef.current.getTime()) / 1000);
      const hours = Math.floor(elapsed / 3600).toString().padStart(2, '0');
      const minutes = Math.floor((elapsed % 3600) / 60).toString().padStart(2, '0');
      const seconds = (elapsed % 60).toString().padStart(2, '0');
      setElapsedTime(`${hours}:${minutes}:${seconds}`);
    };

    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    drawECG();
  }, [ecgData]);

  useEffect(() => {
    drawHistory();
  }, [history]);

  const drawECG = () => {
    const canvas = ecgCanvasRef.current;
    if (!canvas || !ecgData.length) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const padding = 30;

    ctx.clearRect(0, 0, w, h);

    const minVal = Math.min(...ecgData);
    const maxVal = Math.max(...ecgData);
    const range = maxVal - minVal;

    if (range === 0) return;

    // Draw subtle grid
    ctx.strokeStyle = 'rgba(200, 200, 200, 0.3)';
    ctx.lineWidth = 0.5;
    
    // Vertical grid lines
    for (let i = 0; i <= 10; i++) {
      const x = (i / 10) * w;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    
    // Horizontal grid lines
    for (let i = 0; i <= 5; i++) {
      const y = (i / 5) * h;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Draw ECG signal with shadow and gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, h);
    gradient.addColorStop(0, '#1976d2');
    gradient.addColorStop(1, '#42a5f5');
    
    ctx.shadowColor = 'rgba(25, 118, 210, 0.4)';
    ctx.shadowBlur = 3;
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();

    for (let i = 0; i < ecgData.length; i++) {
      const x = (i / (ecgData.length - 1)) * w;
      const y = h - ((ecgData[i] - minVal) / range) * (h - padding * 2) - padding;

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }

    ctx.stroke();
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;
  };

  const handleHistoryClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = historyCanvasRef.current;
    if (!canvas || !history.length) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const padding = 60;
    const chartW = canvas.width - padding * 2;
    
    // Check if click is near any data point
    for (let i = 0; i < history.length; i++) {
      const pointX = padding + (i / Math.max(1, history.length - 1)) * chartW;
      const distance = Math.abs(x - pointX);
      
      if (distance < 10) {
        setHoveredPoint(i);
        return;
      }
    }
    setHoveredPoint(null);
  };

  const drawHistory = () => {
    const canvas = historyCanvasRef.current;
    if (!canvas || !history.length) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const padding = 60;
    const chartW = w - padding * 2;
    const chartH = h - padding * 2;

    ctx.clearRect(0, 0, w, h);

    const minHR = 40;
    const maxHR = 180;
    const hrRange = maxHR - minHR;

    // Draw background with zone colors
    const zones = [
      { max: 60, color: 'rgba(158, 158, 158, 0.1)' },   // Zone 0-1
      { max: 90, color: 'rgba(76, 175, 80, 0.1)' },     // Zone 2
      { max: 120, color: 'rgba(255, 193, 7, 0.1)' },    // Zone 3
      { max: 150, color: 'rgba(255, 152, 0, 0.1)' },    // Zone 4
      { max: 180, color: 'rgba(244, 67, 54, 0.1)' }     // Zone 5
    ];

    let prevY = h - padding;
    zones.forEach(zone => {
      const y = h - padding - ((zone.max - minHR) / hrRange) * chartH;
      ctx.fillStyle = zone.color;
      ctx.fillRect(padding, y, chartW, prevY - y);
      prevY = y;
    });

    // Draw horizontal grid lines and BPM labels
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#666';
    ctx.font = '12px Arial';
    ctx.textAlign = 'right';

    for (let bpm = 60; bpm <= 180; bpm += 20) {
      const y = h - padding - ((bpm - minHR) / hrRange) * chartH;
      
      // Grid line
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(w - padding, y);
      ctx.stroke();
      
      // BPM label
      ctx.fillText(`${bpm}`, padding - 10, y + 4);
    }

    // Draw vertical time grid lines and labels
    ctx.textAlign = 'center';
    const numTimeLabels = 5;
    const timeRange = history.length > 0 ? history[history.length - 1].time - history[0].time : 60;
    
    for (let i = 0; i <= numTimeLabels; i++) {
      const x = padding + (i / numTimeLabels) * chartW;
      
      // Vertical grid line
      ctx.strokeStyle = '#f0f0f0';
      ctx.beginPath();
      ctx.moveTo(x, padding);
      ctx.lineTo(x, h - padding);
      ctx.stroke();
      
      // Time label (seconds ago)
      if (history.length > 0) {
        const secondsAgo = Math.round((timeRange / numTimeLabels) * (numTimeLabels - i));
        ctx.fillStyle = '#666';
        ctx.fillText(`-${secondsAgo}s`, x, h - padding + 20);
      }
    }

    // Draw heart rate line with gradient
    const gradient = ctx.createLinearGradient(0, padding, 0, h - padding);
    gradient.addColorStop(0, '#f44336');  // Red at top
    gradient.addColorStop(0.33, '#ff9800');  // Orange
    gradient.addColorStop(0.66, '#ffc107');  // Amber
    gradient.addColorStop(1, '#4caf50');  // Green at bottom

    ctx.strokeStyle = '#2196F3';
    ctx.lineWidth = 2.5;
    ctx.beginPath();

    // Draw the line with zone coloring
    history.forEach((point, i) => {
      const x = padding + (i / Math.max(1, history.length - 1)) * chartW;
      const y = Math.max(padding, Math.min(h - padding, 
        h - padding - ((point.value - minHR) / hrRange) * chartH));

      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Draw data points with hover effect
    history.forEach((point, i) => {
      const x = padding + (i / Math.max(1, history.length - 1)) * chartW;
      const y = Math.max(padding, Math.min(h - padding, 
        h - padding - ((point.value - minHR) / hrRange) * chartH));
      
      const isHovered = hoveredPoint === i;
      
      // Draw point shadow for depth
      if (isHovered) {
        ctx.shadowColor = 'rgba(25, 118, 210, 0.5)';
        ctx.shadowBlur = 8;
      }
      
      ctx.fillStyle = isHovered ? '#ff9800' : '#1976d2';
      ctx.beginPath();
      ctx.arc(x, y, isHovered ? 6 : 4, 0, Math.PI * 2);
      ctx.fill();
      
      ctx.shadowColor = 'transparent';
      ctx.shadowBlur = 0;
      
      // Draw tooltip for hovered point
      if (isHovered) {
        const tooltipText = `${point.value} BPM`;
        ctx.font = 'bold 14px Arial';
        ctx.fillStyle = '#fff';
        
        const textWidth = ctx.measureText(tooltipText).width;
        const tooltipX = x - textWidth / 2 - 10;
        const tooltipY = y - 35;
        const tooltipW = textWidth + 20;
        const tooltipH = 25;
        
        // Tooltip background
        ctx.fillStyle = 'rgba(33, 33, 33, 0.9)';
        ctx.beginPath();
        ctx.roundRect(tooltipX, tooltipY, tooltipW, tooltipH, 5);
        ctx.fill();
        
        // Tooltip text
        ctx.fillStyle = '#fff';
        ctx.textAlign = 'center';
        ctx.fillText(tooltipText, x, tooltipY + 17);
        
        // Tooltip arrow
        ctx.beginPath();
        ctx.moveTo(x - 5, tooltipY + tooltipH);
        ctx.lineTo(x + 5, tooltipY + tooltipH);
        ctx.lineTo(x, tooltipY + tooltipH + 5);
        ctx.closePath();
        ctx.fill();
      }
    });

    // Draw axes labels
    ctx.fillStyle = '#333';
    ctx.font = 'bold 14px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Time (seconds ago)', w / 2, h - 5);
    
    ctx.save();
    ctx.translate(15, h / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Heart Rate (BPM)', 0, 0);
    ctx.restore();

    // Draw legend
    ctx.textAlign = 'left';
    ctx.font = '11px Arial';
    const legendX = w - padding - 150;
    const legendY = padding + 10;
    
    ctx.fillStyle = '#666';
    ctx.fillText('HR Zones:', legendX, legendY);
    
    const zoneLabels = [
      { text: '60-90: Light', color: '#4caf50' },
      { text: '90-120: Moderate', color: '#ffc107' },
      { text: '120-150: Intense', color: '#ff9800' },
      { text: '150+: Maximum', color: '#f44336' }
    ];
    
    zoneLabels.forEach((zone, i) => {
      const y = legendY + 15 + (i * 15);
      ctx.fillStyle = zone.color;
      ctx.fillRect(legendX, y - 8, 10, 10);
      ctx.fillStyle = '#666';
      ctx.fillText(zone.text, legendX + 15, y);
    });
  };

  const getZoneDescription = (zoneNum: number): string => {
    switch (zoneNum) {
      case 0: return 'Below normal resting heart rate';
      case 1: return 'Normal resting heart rate';
      case 2: return 'Light activity (walking)';
      case 3: return 'Moderate activity (brisk walking)';
      case 4: return 'Intense activity (jogging)';
      case 5: return 'Maximum effort (running)';
      default: return 'Analyzing...';
    }
  };

  return (
    <div className="App">
      <div className="container">
        <header>
          <h1>ECG Monitoring System</h1>
          <p>Real-time cardiac monitoring with smartwatch data</p>
        </header>

        <div className={`simulator-status ${isConnected ? 'status-connected' : 'status-disconnected'}`}>
          {isConnected ? 'Connected to patient data' : 'Connecting to patient data...'}
        </div>

        <div className="stats-container">
          <div className="stat-card">
            <h3>Heart Rate</h3>
            <div className="stat-value">{heartRate || '--'}</div>
            <div>Beats per minute</div>
          </div>
          <div className="stat-card">
            <h3>Heart Rate Zone</h3>
            <div className={`stat-value zone-${zone}`}>{zoneText}</div>
            <div>{getZoneDescription(zone)}</div>
          </div>
          <div className="stat-card">
            <h3>Monitor Time</h3>
            <div className="stat-value">{elapsedTime}</div>
            <div>Elapsed time</div>
          </div>
        </div>

        <h3>ECG Signal</h3>
        <div className="ecg-container">
          <div className="ecg-grid"></div>
          <div className="ecg-axis-labels y-axis-label">Amplitude (mV)</div>
          <div className="ecg-axis-labels x-axis-label">Time (seconds)</div>
          <canvas 
            ref={ecgCanvasRef} 
            className="ecg-monitor"
            width={1200}
            height={300}
          />
        </div>

        <div className="chart-container">
          <h3>Heart Rate History (Click points for details)</h3>
          <canvas 
            ref={historyCanvasRef}
            width={1200}
            height={400}
            onClick={handleHistoryClick}
            style={{ cursor: 'pointer' }}
          />
        </div>

        <footer>
          <p>&copy; 2025 XR ECG Twin - Real-time Cardiac Monitoring System</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
