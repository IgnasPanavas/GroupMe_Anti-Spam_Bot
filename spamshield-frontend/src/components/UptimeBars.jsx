import React from 'react';

/**
 * A component to display a series of uptime bars representing the last 24 hours.
 * It creates a sliding window of bars, where each bar represents a 30-minute interval.
 *
 * @param {object} props - The component props.
 * @param {Array<object>} props.uptimeData - Array of uptime status objects, e.g., { timestamp: 'ISO_STRING', status: 'operational' }.
 * @param {string} props.serviceName - The name of the service being monitored.
 */
const UptimeBars = ({ uptimeData }) => {
  const [windowWidth, setWindowWidth] = React.useState(typeof window !== 'undefined' ? window.innerWidth : 1024);

  // Handle window resize
  React.useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('resize', handleResize);
      return () => window.removeEventListener('resize', handleResize);
    }
  }, []);

  // --- Uptime Percentage Calculation ---
  // We wrap this in useMemo so it only recalculates when uptimeData changes.
  const uptimePercentage = React.useMemo(() => {
    if (!uptimeData || uptimeData.length === 0) return null;

    const periodsWithData = uptimeData.filter(period => period.status !== 'no_data');
    if (periodsWithData.length === 0) return null;

    const operationalCount = periodsWithData.filter(period => period.status === 'operational').length;
    return ((operationalCount / periodsWithData.length) * 100).toFixed(2);
  }, [uptimeData]);

  // --- Bar Generation Logic ---
  // This is the core logic for creating the bars. It's wrapped in useMemo for performance.
  // It will only run when the uptimeData prop changes.
  const memoizedBars = React.useMemo(() => {
    // Responsive bar count based on screen size (each bar = 30 minutes)
    const getBarCount = () => {
      if (windowWidth < 640) return 30; // Mobile: 30 bars (15 hours)
      if (windowWidth < 1024) return 60; // Tablet: 60 bars (30 hours)
      return 90; // Desktop: 90 bars (45 hours)
    };
    
    const totalBars = getBarCount();
    const data = Array.isArray(uptimeData) ? uptimeData : [];

    // --- 1. Compress raw data into 30-minute intervals ---
    const compressedData = [];
    if (data.length > 0) {
      // Ensure data is sorted oldest to newest before processing.
      const sortedData = [...data].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

      let intervalStartTime = null;
      let intervalWorstStatus = null;
      const statusPriority = { 'outage': 3, 'degraded': 2, 'operational': 1, 'checking': 0, 'no_data': -1 };

      for (const record of sortedData) {
        const recordTime = new Date(record.timestamp);

        if (!intervalStartTime) {
          intervalStartTime = recordTime;
          intervalWorstStatus = record.status;
        } else {
          const diffMinutes = (recordTime - intervalStartTime) / (1000 * 60);

          if (diffMinutes >= 30) {
            compressedData.push({
              timestamp: intervalStartTime.toISOString(),
              status: intervalWorstStatus,
            });
            intervalStartTime = recordTime;
            intervalWorstStatus = record.status;
          } else {
            if (statusPriority[record.status] > statusPriority[intervalWorstStatus]) {
              intervalWorstStatus = record.status;
            }
          }
        }
      }

      if (intervalStartTime) {
        compressedData.push({
          timestamp: intervalStartTime.toISOString(),
          status: intervalWorstStatus,
        });
      }
    }

    // --- 2. Build the Timeline ---
    const recentData = compressedData.slice(-totalBars);
    const paddingCount = totalBars - recentData.length;
    const paddingBars = Array.from({ length: paddingCount }, (_, i) => ({
      id: `pad-${i}`,
      status: 'no_data',
      tooltip: 'No historical data available',
    }));
    const dataBars = recentData.map(d => ({
      id: d.timestamp,
      status: d.status,
      tooltip: `${d.status.charAt(0).toUpperCase() + d.status.slice(1)} at ${new Date(d.timestamp).toLocaleTimeString()}`
    }));
    const timeline = [...paddingBars, ...dataBars];

    // --- 3. Render the JSX Bars ---
    return timeline.map(barData => {
      let barColor = 'bg-gray-300'; // Default for 'no_data'
      switch (barData.status) {
        case 'operational': barColor = 'bg-green-500'; break;
        case 'degraded': barColor = 'bg-yellow-500'; break;
        case 'outage': barColor = 'bg-red-500'; break;
        case 'checking': barColor = 'bg-blue-500'; break;
        default: break;
      }

      // Responsive bar width
      const getBarWidth = () => {
        if (windowWidth < 640) return 'w-2'; // Mobile: wider bars
        if (windowWidth < 1024) return 'w-1.5'; // Tablet: medium bars
        return 'w-1'; // Desktop: thin bars
      };

      return (
        <div
          key={barData.id}
          className={`${getBarWidth()} h-4 ${barColor} rounded-sm mx-px transition-colors duration-200 hover:opacity-80`}
          title={barData.tooltip}
        />
      );
    });
  }, [uptimeData, windowWidth]);


  return (
    <div className="mt-4">
      <div className="flex items-center justify-between mb-2">
        {uptimePercentage !== null ? (
          <span className={`text-sm font-semibold ${
            uptimePercentage >= 90.9 ? 'text-green-600' :
            uptimePercentage >= 80.0 ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            {uptimePercentage}% uptime
          </span>
        ) : (
          <span className="text-sm font-semibold text-gray-500">
            {/* Insufficient data text is shown on the right side */}
          </span>
        )}
      </div>
      
      <div className="flex items-center space-x-4">
        {/* Bars on the left */}
        <div className="flex-1">
          <div className="flex items-center space-x-px mb-2">
            {memoizedBars}
          </div>
          
          <div className="flex justify-between text-xs text-gray-500">
            <span>
              {windowWidth < 640 ? '15 hours ago' : 
               windowWidth < 1024 ? '30 hours ago' : 
               '45 hours ago'}
            </span>
            
          </div>
        </div>
        
        
      </div>
    </div>
  );
};

export default UptimeBars;

