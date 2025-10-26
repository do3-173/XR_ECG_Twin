import React, { useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface HistoryChartProps {
  history: { value: number; timestamp: string }[];
}

const HistoryChart: React.FC<HistoryChartProps> = ({ history }) => {
  const chartRef = useRef<ChartJS<'line'>>(null);

  const timeWindowSeconds = 60;
  const timeStep = 5;
  const maxPoints = timeWindowSeconds / timeStep;

  const labels = [];
  const values = [];

  for (let i = 0; i <= maxPoints; i++) {
    const seconds = i * timeStep;
    labels.push(seconds + 's');

    if (i < history.length) {
      values.push(history[history.length - maxPoints - 1 + i]?.value || null);
    } else {
      values.push(null);
    }
  }

  const data = {
    labels,
    datasets: [
      {
        label: 'Heart Rate (BPM)',
        data: values,
        borderColor: 'rgb(33, 150, 243)',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 200,
        title: {
          display: true,
          text: 'BPM',
        },
      },
      x: {
        title: {
          display: true,
          text: 'Time',
        },
      },
    },
    animation: {
      duration: 0,
    },
  };

  return (
    <div style={{ height: '300px' }}>
      <Line ref={chartRef} data={data} options={options} />
    </div>
  );
};

export default HistoryChart;
