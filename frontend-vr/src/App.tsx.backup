import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import ECGDisplay from './components/ECGDisplay';
import StatsCard from './components/StatsCard';
import HistoryChart from './components/HistoryChart';

interface ECGData {
  heart_rate: number;
  zone: number;
  zone_text: string;
  ecg_samples: number[];
  history: { value: number; timestamp: string }[];
  timestamp: string;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/ecg/latest';

function App() {
  const [ecgData, setEcgData] = useState<ECGData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [refreshRate, setRefreshRate] = useState(1000); // 1 second
  const updateTimerRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = async () => {
    try {
      const response = await fetch(API_URL);
      const data: ECGData = await response.json();
      setEcgData(data);
      setIsConnected(true);
    } catch (error) {
      console.error('Error fetching ECG data:', error);
      setIsConnected(false);
      // Set flatline data on error
      setEcgData(prev => prev ? {
        ...prev,
        ecg_samples: new Array(128).fill(0),
      } : null);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchData();

    // Set up polling
    updateTimerRef.current = setInterval(fetchData, refreshRate);

    return () => {
      if (updateTimerRef.current) {
        clearInterval(updateTimerRef.current);
      }
    };
  }, [refreshRate]);

  const handleRefreshRateChange = (rate: number) => {
    setRefreshRate(rate);
  };

  const getZoneDescription = (zone: number): string => {
    switch (zone) {
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
          <h1>🫀 XR ECG Twin Monitor</h1>
          <div className={`simulator-status ${isConnected ? 'status-connected' : 'status-disconnected'}`}>
            {isConnected ? 'Connected to patient data' : 'Connection lost. Retrying...'}
          </div>
        </header>

        <div className="stats-container">
          <StatsCard
            title="Heart Rate"
            value={ecgData?.heart_rate || 0}
            unit="BPM"
            zone={ecgData?.zone || 0}
          />
          <StatsCard
            title="Heart Rate Zone"
            value={ecgData?.zone_text || 'N/A'}
            unit=""
            zone={ecgData?.zone || 0}
            isZone={true}
          />
          <div className="stat-card">
            <h3>Zone Description</h3>
            <p className="zone-description">
              {ecgData ? getZoneDescription(ecgData.zone) : 'Waiting for data...'}
            </p>
          </div>
        </div>

        <div className="control-panel">
          <label htmlFor="refresh-rate">Update Rate:</label>
          <select
            id="refresh-rate"
            value={refreshRate}
            onChange={(e) => handleRefreshRateChange(Number(e.target.value))}
          >
            <option value={500}>0.5 seconds</option>
            <option value={1000}>1 second</option>
            <option value={2000}>2 seconds</option>
            <option value={5000}>5 seconds</option>
          </select>
        </div>

        <div className="chart-section">
          <h3>Real-Time ECG Signal</h3>
          <ECGDisplay
            samples={ecgData?.ecg_samples || []}
            isConnected={isConnected}
          />
        </div>

        <div className="chart-section">
          <h3>Heart Rate History (60 seconds)</h3>
          <HistoryChart history={ecgData?.history || []} />
        </div>
      </div>
    </div>
  );
}

export default App;
