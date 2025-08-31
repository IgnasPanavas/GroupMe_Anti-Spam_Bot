import React from 'react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const Charts = () => {
  const spamData = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Spam Detected',
        data: [12, 19, 8, 15, 22, 18, 14],
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.1,
      },
    ],
  };

  const trendsData = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      {
        label: 'Messages Protected',
        data: [65, 59, 80, 81, 56, 55],
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <div className="space-y-6">
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Weekly Spam Detection</h4>
        <Line data={spamData} options={options} />
      </div>
      
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Monthly Protection Trends</h4>
        <Bar data={trendsData} options={options} />
      </div>
    </div>
  );
};

export default Charts;
