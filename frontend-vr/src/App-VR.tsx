import React, { useState, useEffect, useRef } from 'react';
import './App-VR.css';

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
  const [selectedView, setSelectedView] = useState<'overview' | 'ecg' | 'history'>('overview');
  
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
    const padding = 40;

    ctx.clearRect(0, 0, w, h);

    const minVal = Math.min(...ecgData);
    const maxVal = Math.max(...ecgData);
    const range = maxVal - minVal;

    if (range === 0) return;

    // Draw grid for depth
    ctx.strokeStyle = 'rgba(100, 200, 255, 0.2)';
    ctx.lineWidth = 1;
    
    for (let i = 0; i <= 10; i++) {
      const x = (i / 10) * w;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    
    for (let i = 0; i <= 5; i++) {
      const y = (i / 5) * h;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Draw ECG with glow effect
    const gradient = ctx.createLinearGradient(0, 0, 0, h);
    gradient.addColorStop(0, '#00d4ff');
    gradient.addColorStop(1, '#0088ff');
    
    ctx.shadowColor = '#00d4ff';
    ctx.shadowBlur = 15;
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 3;
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

  const drawHistory = () => {
    const canvas = historyCanvasRef.current;
    if (!canvas || !history.length) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const padding = 80;
    const chartW = w - padding * 2;
    const chartH = h - padding * 2;

    ctx.clearRect(0, 0, w, h);

    const minHR = 40;
    const maxHR = 180;
    const hrRange = maxHR - minHR;

    // Draw grid
    ctx.strokeStyle = 'rgba(100, 200, 255, 0.2)';
    ctx.lineWidth = 2;

    for (let bpm = 60; bpm <= 180; bpm += 20) {
      const y = h - padding - ((bpm - minHR) / hrRange) * chartH;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(w - padding, y);
      ctx.stroke();
    }

    // Draw BPM labels
    ctx.fillStyle = '#00d4ff';
    ctx.font = 'bold 18px Arial';
    ctx.textAlign = 'right';

    for (let bpm = 60; bpm <= 180; bpm += 20) {
      const y = h - padding - ((bpm - minHR) / hrRange) * chartH;
      ctx.fillText(`${bpm}`, padding - 15, y + 6);
    }

    // Draw line with glow
    ctx.strokeStyle = '#00d4ff';
    ctx.shadowColor = '#00d4ff';
    ctx.shadowBlur = 10;
    ctx.lineWidth = 4;
    ctx.beginPath();

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
    ctx.shadowColor = 'transparent';
    ctx.shadowBlur = 0;

    // Draw data points
    history.forEach((point, i) => {
      const x = padding + (i / Math.max(1, history.length - 1)) * chartW;
      const y = Math.max(padding, Math.min(h - padding, 
        h - padding - ((point.value - minHR) / hrRange) * chartH));
      
      ctx.fillStyle = '#00d4ff';
      ctx.shadowColor = '#00d4ff';
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.arc(x, y, 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowColor = 'transparent';
      ctx.shadowBlur = 0;
    });

    // Axis labels
    ctx.fillStyle = '#00d4ff';
    ctx.font = 'bold 20px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Time (seconds)', w / 2, h - 20);
    
    ctx.save();
    ctx.translate(30, h / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Heart Rate (BPM)', 0, 0);
    ctx.restore();
  };

  const getZoneDescription = (zoneNum: number): string => {
    switch (zoneNum) {
      case 0: return 'Below Resting';
      case 1: return 'Resting';
      case 2: return 'Light Activity';
      case 3: return 'Moderate Activity';
      case 4: return 'Intense Activity';
      case 5: return 'Maximum Effort';
      default: return 'Analyzing...';
    }
  };

  return (
    <div className="App-VR">
      <div className="vr-container">
        {/* Header with connection status */}
        <div className="vr-header">
          <h1 className="vr-title">ECG Monitor - HoloLens</h1>
          <div className={`vr-status ${isConnected ? 'connected' : 'disconnected'}`}>
            <div className="status-indicator"></div>
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>

        {/* Main view selector */}
        <div className="view-selector">
          <button 
            className={`view-btn ${selectedView === 'overview' ? 'active' : ''}`}
            onClick={() => setSelectedView('overview')}
          >
            Overview
          </button>
          <button 
            className={`view-btn ${selectedView === 'ecg' ? 'active' : ''}`}
            onClick={() => setSelectedView('ecg')}
          >
            ECG Signal
          </button>
          <button 
            className={`view-btn ${selectedView === 'history' ? 'active' : ''}`}
            onClick={() => setSelectedView('history')}
          >
            History
          </button>
        </div>

        {/* Overview View */}
        {selectedView === 'overview' && (
          <div className="vr-overview">
            <div className="vr-cards">
              <div className="vr-card primary">
                <div className="card-label">HEART RATE</div>
                <div className={`card-value zone-${zone}`}>{heartRate || '--'}</div>
                <div className="card-unit">BPM</div>
              </div>
              
              <div className="vr-card">
                <div className="card-label">ZONE</div>
                <div className={`card-value zone-${zone}`}>{zoneText}</div>
                <div className="card-unit">{getZoneDescription(zone)}</div>
              </div>
              
              <div className="vr-card">
                <div className="card-label">MONITOR TIME</div>
                <div className="card-value">{elapsedTime}</div>
                <div className="card-unit">Elapsed</div>
              </div>
            </div>

            <div className="mini-chart">
              <canvas 
                ref={ecgCanvasRef} 
                width={800}
                height={250}
              />
            </div>
          </div>
        )}

        {/* ECG View */}
        {selectedView === 'ecg' && (
          <div className="vr-ecg-view">
            <div className="vr-chart-title">
              ECG Signal - Real-time
              <span className="vr-chart-info">{heartRate} BPM</span>
            </div>
            <canvas 
              ref={ecgCanvasRef} 
              className="vr-canvas"
              width={1000}
              height={500}
            />
          </div>
        )}

        {/* History View */}
        {selectedView === 'history' && (
          <div className="vr-history-view">
            <div className="vr-chart-title">
              Heart Rate History
              <span className="vr-chart-info">{history.length} data points</span>
            </div>
            <canvas 
              ref={historyCanvasRef}
              className="vr-canvas"
              width={1000}
              height={500}
            />
          </div>
        )}

        {/* Quick stats footer */}
        <div className="vr-footer">
          <div className="footer-stat">
            <span className="stat-label">HR:</span>
            <span className={`stat-value zone-${zone}`}>{heartRate}</span>
          </div>
          <div className="footer-stat">
            <span className="stat-label">Zone:</span>
            <span className={`stat-value zone-${zone}`}>{zone}</span>
          </div>
          <div className="footer-stat">
            <span className="stat-label">Time:</span>
            <span className="stat-value">{elapsedTime}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
