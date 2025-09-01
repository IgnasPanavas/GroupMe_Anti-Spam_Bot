import React from 'react';

const UptimeBars = ({ uptimeData, days = 90, serviceName }) => {
  // Calculate uptime percentage based on available data
  const calculateUptimePercentage = () => {
    if (!uptimeData || !uptimeData.length) return null;
    
    // Only count periods with actual data (not 'no_data')
    const periodsWithData = uptimeData.filter(period => period.status !== 'no_data');
    if (periodsWithData.length === 0) return null;
    
    const operationalCount = periodsWithData.filter(period => period.status === 'operational').length;
    return ((operationalCount / periodsWithData.length) * 100).toFixed(2);
  };

  // Generate bars based on real data or show grey for no data
  const generateBars = () => {
    const bars = [];
    
    // Exactly 90 bars representing 30-minute intervals
    const totalBars = 90;
    
    for (let i = 0; i < totalBars; i++) {
      let barColor = 'bg-gray-300'; // Default grey for no data
      let tooltip = `Period ${i + 1}: No data`;
      
      if (uptimeData && uptimeData[i]) {
        const periodData = uptimeData[i];
        switch (periodData.status) {
          case 'operational':
            barColor = 'bg-green-500';
            tooltip = `Period ${i + 1}: Operational`;
            break;
          case 'degraded':
            barColor = 'bg-yellow-500';
            tooltip = `Period ${i + 1}: Degraded`;
            break;
          case 'outage':
            barColor = 'bg-red-500';
            tooltip = `Period ${i + 1}: Outage`;
            break;
          case 'checking':
            barColor = 'bg-blue-500';
            tooltip = `Period ${i + 1}: Checking`;
            break;
          case 'no_data':
            barColor = 'bg-gray-300';
            tooltip = `Period ${i + 1}: No data available`;
            break;
          default:
            barColor = 'bg-gray-300';
            tooltip = `Period ${i + 1}: No data available`;
        }
      }
      
      bars.push(
        <div
          key={i}
          className={`w-1 h-4 ${barColor} rounded-sm mx-px transition-colors duration-200 hover:opacity-80`}
          title={tooltip}
        />
      );
    }
    
    return bars;
  };

  const uptimePercentage = calculateUptimePercentage();

  return (
    <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
          {uptimePercentage !== null ? (
            <span className={`text-sm font-semibold ${
              uptimePercentage >= 99.9 ? 'text-green-600' :
              uptimePercentage >= 99.0 ? 'text-yellow-600' :
              'text-red-600'
            }`}>
              {uptimePercentage}% uptime
            </span>
          ) : (
            <span className="text-sm font-semibold text-gray-500">
              {/* Insufficient data moved to right side */}
            </span>
          )}
        </div>
      
      <div className="flex items-center space-x-4">
        {/* Bars on the left */}
        <div className="flex-1">
          <div className="flex items-center space-x-px mb-2">
            {generateBars()}
          </div>
          
          <div className="flex justify-between text-xs text-gray-500">
            <span>45 hours ago</span>
          </div>
        </div>
        
        {/* Text info on the right */}
        <div className="flex-shrink-0 w-48 text-right flex flex-col justify-center">
          {uptimePercentage === null && (
            <>
              <div className="text-sm font-semibold text-gray-500 mb-2">
                Insufficient data
              </div>
              <div className="text-xs text-gray-400 mb-2">
                {uptimeData ? uptimeData.filter(period => period.status !== 'no_data').length : 0} of 90 periods available
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default UptimeBars;
