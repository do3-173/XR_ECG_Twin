import React, { useEffect, useRef } from 'react';

interface ECGDisplayProps {
  samples: number[];
  isConnected: boolean;
}

const ECGDisplay: React.FC<ECGDisplayProps> = ({ samples, isConnected }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || !samples.length) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;

    const w = canvas.width;
    const h = canvas.height;

    // Clear canvas
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, w, h);

    // Draw grid (ECG paper style)
    ctx.strokeStyle = 'rgba(255, 182, 193, 0.3)';
    ctx.lineWidth = 0.5;

    // Major grid lines (every 50px)
    for (let x = 0; x < w; x += 50) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 50) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Minor grid lines (every 10px)
    ctx.strokeStyle = 'rgba(255, 182, 193, 0.15)';
    for (let x = 0; x < w; x += 10) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 10) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Draw ECG signal
    if (samples.length > 0) {
      const minVal = Math.min(...samples);
      const maxVal = Math.max(...samples);
      const range = maxVal - minVal || 1;

      ctx.strokeStyle = isConnected ? '#1976d2' : '#999';
      ctx.lineWidth = 2.5;
      ctx.beginPath();

      for (let i = 0; i < samples.length; i++) {
        const x = (i / (samples.length - 1)) * w;
        const y = h - ((samples[i] - minVal) / range) * h;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }

      ctx.stroke();

      // Draw axis labels
      ctx.fillStyle = '#333';
      ctx.font = '10px Arial';
      ctx.textAlign = 'center';

      // Time labels (x-axis)
      const totalSeconds = samples.length / 128; // Assuming 128 Hz sampling rate
      for (let i = 0; i <= 5; i++) {
        const x = (i / 5) * w;
        const timeLabel = ((i / 5) * totalSeconds).toFixed(1);
        ctx.fillText(timeLabel + 's', x, h - 5);
      }

      // Amplitude labels (y-axis)
      ctx.textAlign = 'right';
      for (let i = 0; i <= 4; i++) {
        const y = (i / 4) * h;
        const ampLabel = (maxVal - (i / 4) * range).toFixed(2);
        ctx.fillText(ampLabel, w - 5, y + 10);
      }
    }
  }, [samples, isConnected]);

  return (
    <div className="ecg-container">
      <canvas
        ref={canvasRef}
        className="ecg-monitor"
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};

export default ECGDisplay;
