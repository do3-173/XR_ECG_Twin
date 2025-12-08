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

interface AnalysisResult {
  job_id: string;
  result: any;
  processing_time_ms: number;
}

interface AnalysisPlots {
  wavelet_scales?: string;
  wavelet_xcorr?: string;
  wavelet_xcorr_sequences?: string;
  graph_matlab?: string;
  [key: string]: string | undefined;
}

function App() {
  const [heartRate, setHeartRate] = useState<number>(0);
  const [zone, setZone] = useState<number>(1);
  const [zoneText, setZoneText] = useState<string>('--');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [elapsedTime, setElapsedTime] = useState<string>('00:00:00');
  const [ecgData, setEcgData] = useState<number[]>([]);
  const [history, setHistory] = useState<Array<{ time: number; value: number; zone: number }>>([]);
  const [selectedView, setSelectedView] = useState<'overview' | 'ecg' | 'history' | 'analysis'>('overview');

  // Analysis State
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [runContinuousAnalysis, setRunContinuousAnalysis] = useState<boolean>(false);
  const [analysisStatus, setAnalysisStatus] = useState<string>('Ready');
  const [analysisPlots, setAnalysisPlots] = useState<AnalysisPlots>({});

  // Expanded View State
  const [expandedPlot, setExpandedPlot] = useState<string | null>(null);

  const ecgCanvasRef = useRef<HTMLCanvasElement>(null);
  const historyCanvasRef = useRef<HTMLCanvasElement>(null);
  const startTimeRef = useRef<Date>(new Date());
  const analysisTimerRef = useRef<NodeJS.Timeout | null>(null);

  const API_URL = '/api/heartrate/';
  const ANALYSIS_API_URL = 'http://localhost:8003/api/analysis';
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
    if (selectedView === 'ecg') {
      drawECG();
    }
  }, [ecgData, selectedView]);

  useEffect(() => {
    if (selectedView === 'history') {
      drawHistory();
    }
  }, [history, selectedView]);

  // Continuous Analysis Effect
  useEffect(() => {
    if (runContinuousAnalysis) {
      if (!analysisTimerRef.current) {
        triggerAnalysis(); // Run immediately
        analysisTimerRef.current = setInterval(triggerAnalysis, 5000);
      }
    } else {
      if (analysisTimerRef.current) {
        clearInterval(analysisTimerRef.current);
        analysisTimerRef.current = null;
      }
    }
    return () => {
      if (analysisTimerRef.current) {
        clearInterval(analysisTimerRef.current);
      }
    };
  }, [runContinuousAnalysis]);

  const triggerAnalysis = async () => {
    if (isAnalyzing) return;

    setIsAnalyzing(true);
    setAnalysisStatus('Fetching ECG data...');

    try {
      // Fetch fresh ECG data directly from API (exactly like analysis_dashboard.html does)
      const ecgResponse = await fetch('http://localhost:8000/api/heartrate');
      const ecgApiData = await ecgResponse.json();

      if (!ecgApiData.ecg_samples || !Array.isArray(ecgApiData.ecg_samples)) {
        setAnalysisStatus('No ECG data available from API');
        setIsAnalyzing(false);
        return;
      }

      setAnalysisStatus('Processing...');

      // Run analysis with fresh data
      const response = await fetch(`${ANALYSIS_API_URL}/process/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ecg_samples: ecgApiData.ecg_samples,
          sampling_frequency: 128,
          wavelet_type: 'sym4',
          device_id: 'hololens_vr_dashboard',
          participant_id: 1
        })
      });

      const data = await response.json();

      if (!response.ok) throw new Error(data.error || 'Analysis failed');

      const timeStr = new Date().toLocaleTimeString();
      const hr = ecgApiData.heart_rate || 0;
      setAnalysisStatus(`Updated at ${timeStr} (HR: ${hr} bpm, ${data.processing_time_ms}ms)`);

      // Fetch plots
      await fetchPlots(data.job_id);

    } catch (error: any) {
      console.error('Analysis error:', error);
      setAnalysisStatus(`Error: ${error.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const fetchPlots = async (jobId: string) => {
    try {
      const response = await fetch(`${ANALYSIS_API_URL}/plots/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobId })
      });

      const data = await response.json();
      if (response.ok && data.plots) {
        // Only update if we have valid plots - preserve previous otherwise
        setAnalysisPlots(prev => ({
          ...prev,  // Keep previous plots as fallback
          ...data.plots  // Overwrite with new plots
        }));
      }
    } catch (error) {
      console.error('Plot fetch error:', error);
      // Don't clear plots on error - keep showing previous ones
    }
  };

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

  const handlePlotClick = (plotKey: string) => {
    if (analysisPlots[plotKey]) {
      setExpandedPlot(plotKey);
    }
  };

  const closeExpandedView = () => {
    setExpandedPlot(null);
  };

  const savePlot = (plotKey: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent expanding when clicking save
    const base64Data = analysisPlots[plotKey];
    if (!base64Data) return;

    const link = document.createElement('a');
    link.href = `data:image/png;base64,${base64Data}`;
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    link.download = `${plotKey}_${timestamp}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
          <button
            className={`view-btn ${selectedView === 'analysis' ? 'active' : ''}`}
            onClick={() => setSelectedView('analysis')}
          >
            Analysis
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

        {/* Analysis View (New) */}
        {selectedView === 'analysis' && (
          <div className="vr-analysis-view">
            <div className="analysis-controls">
              <button
                className={`control-btn ${runContinuousAnalysis ? 'stop' : 'primary'}`}
                onClick={() => setRunContinuousAnalysis(!runContinuousAnalysis)}
              >
                {runContinuousAnalysis ? '⏹ Stop Analysis' : '▶ Start Continuous Analysis'}
              </button>

              <div className="analysis-status">
                Status: {analysisStatus}
              </div>

              {!runContinuousAnalysis && (
                <button
                  className="control-btn secondary"
                  onClick={triggerAnalysis}
                  disabled={isAnalyzing}
                >
                  Create Single Snapshot
                </button>
              )}
            </div>

            <div className="analysis-grid">
              <div className="analysis-card" onClick={() => handlePlotClick('wavelet_scales')}>
                <div className="card-header">
                  <h3>Wavelet Decomposition</h3>
                  {analysisPlots.wavelet_scales && (
                    <button className="save-btn" onClick={(e) => savePlot('wavelet_scales', e)}>💾 Save</button>
                  )}
                </div>
                <div className="analysis-content">
                  {analysisPlots.wavelet_scales ? (
                    <img src={`data:image/png;base64,${analysisPlots.wavelet_scales}`} alt="Wavelet Scales" />
                  ) : (
                    <div className="placeholder">No Data</div>
                  )}
                </div>
              </div>

              <div className="analysis-card" onClick={() => handlePlotClick('wavelet_xcorr')}>
                <div className="card-header">
                  <h3>Cross-Correlation Matrix</h3>
                  {analysisPlots.wavelet_xcorr && (
                    <button className="save-btn" onClick={(e) => savePlot('wavelet_xcorr', e)}>💾 Save</button>
                  )}
                </div>
                <div className="analysis-content">
                  {analysisPlots.wavelet_xcorr ? (
                    <img src={`data:image/png;base64,${analysisPlots.wavelet_xcorr}`} alt="Correlation Matrix" />
                  ) : (
                    <div className="placeholder">No Data</div>
                  )}
                </div>
              </div>

              <div className="analysis-card" onClick={() => handlePlotClick('wavelet_xcorr_sequences')}>
                <div className="card-header">
                  <h3>Cross-Correlation Sequences</h3>
                  {analysisPlots.wavelet_xcorr_sequences && (
                    <button className="save-btn" onClick={(e) => savePlot('wavelet_xcorr_sequences', e)}>💾 Save</button>
                  )}
                </div>
                <div className="analysis-content">
                  {analysisPlots.wavelet_xcorr_sequences ? (
                    <img src={`data:image/png;base64,${analysisPlots.wavelet_xcorr_sequences}`} alt="Correlation Sequences" />
                  ) : (
                    <div className="placeholder">No Data</div>
                  )}
                </div>
              </div>

              <div className="analysis-card" onClick={() => handlePlotClick('graph_matlab')}>
                <div className="card-header">
                  <h3>Network Topology (MATLAB)</h3>
                  {analysisPlots.graph_matlab && (
                    <button className="save-btn" onClick={(e) => savePlot('graph_matlab', e)}>💾 Save</button>
                  )}
                </div>
                <div className="analysis-content">
                  {analysisPlots.graph_matlab ? (
                    <img src={`data:image/png;base64,${analysisPlots.graph_matlab}`} alt="Graph Topology" />
                  ) : (
                    <div className="placeholder">No Data</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Expanded View Modal */}
        {expandedPlot && analysisPlots[expandedPlot] && (
          <div className="expanded-overlay" onClick={closeExpandedView}>
            <div className="expanded-content" onClick={(e) => e.stopPropagation()}>
              <h2 className="expanded-title">
                {expandedPlot === 'wavelet_scales' && 'Wavelet Decomposition'}
                {expandedPlot === 'wavelet_xcorr' && 'Cross-Correlation Matrix'}
                {expandedPlot === 'wavelet_xcorr_sequences' && 'Cross-Correlation Sequences'}
                {expandedPlot === 'graph_matlab' && 'Network Topology (MATLAB)'}
              </h2>
              <div className="expanded-image-container">
                <img
                  src={`data:image/png;base64,${analysisPlots[expandedPlot]}`}
                  className="expanded-image"
                  alt="Expanded Plot"
                />
              </div>
              <button className="close-expanded-btn" onClick={closeExpandedView}>
                Close View
              </button>
            </div>
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
