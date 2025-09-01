import React, { useState, useEffect, useCallback } from 'react';
import Header from './Header';
import Footer from './Footer';

const StatusPage = ({ onBack }) => {
  const [services, setServices] = useState({
    api: { status: 'checking', uptime: null, name: 'API', lastCheck: null },
    lambda: { status: 'checking', uptime: null, name: 'Lambda Function', lastCheck: null },
    ec2: { status: 'checking', uptime: null, name: 'EC2 Instance', lastCheck: null, instanceInfo: null },
    groupme: { status: 'checking', uptime: null, name: 'GroupMe Bot', lastCheck: null, botInfo: null }
  });

  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [loading, setLoading] = useState(true);

  const checkServiceHealth = useCallback(async () => {
    console.log('🔄 Health check started at:', new Date().toLocaleTimeString());
    const newServices = { ...services };
    const API_BASE = 'https://qtwso5m6o6.execute-api.us-east-1.amazonaws.com/prod';
    
    try {
      // Check Lambda API health
      const response = await fetch(`${API_BASE}/api/health`);
      
      if (response.ok) {
        const healthData = await response.json();
        newServices.lambda = {
          ...newServices.lambda,
          status: 'operational',
          lastCheck: new Date(),
          healthData
        };
      } else {
        newServices.lambda = {
          ...newServices.lambda,
          status: 'degraded',
          lastCheck: new Date()
        };
      }
    } catch (error) {
      newServices.lambda = {
        ...newServices.lambda,
        status: 'outage',
        lastCheck: new Date()
      };
    }

    // Check API endpoint
    try {
      const response = await fetch(`${API_BASE}/api/stats`);
      
      if (response.ok) {
        const statsData = await response.json();
        newServices.api = {
          ...newServices.api,
          status: 'operational',
          lastCheck: new Date(),
          statsData
        };
      } else {
        newServices.api = {
          ...newServices.api,
          status: 'degraded',
          lastCheck: new Date()
        };
      }
    } catch (error) {
      newServices.api = {
        ...newServices.api,
        status: 'outage',
        lastCheck: new Date()
      };
    }

    // Check EC2 instance status - real health check from instance
    try {
      // Try to connect to the health check server running on the EC2 instance
      const response = await fetch(`http://3.91.154.73:8080/health`, {
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });
      
      if (response.ok) {
        const healthData = await response.json();
        newServices.ec2 = {
          ...newServices.ec2,
          status: healthData.status === 'healthy' ? 'operational' : 'degraded',
          lastCheck: new Date(),
          instanceInfo: {
            state: healthData.status,
            healthData: healthData.data,
            note: 'Real-time health data from EC2 instance'
          }
        };
      } else {
        newServices.ec2 = {
          ...newServices.ec2,
          status: 'degraded',
          lastCheck: new Date(),
          instanceInfo: {
            instanceId: 'i-0a0001f601291b280',
            state: 'unhealthy',
            error: 'Health check returned unhealthy status'
          }
        };
      }
    } catch (error) {
      // Health check failed - instance might be down or health server not running
      newServices.ec2 = {
        ...newServices.ec2,
        status: 'outage',
        lastCheck: new Date(),
        instanceInfo: {
          instanceId: 'i-0a0001f601291b280',
          state: 'unreachable',
          publicIp: '3.91.154.73',
          error: 'Health check server not responding'
        }
      };
    }

    // GroupMe Bot status - check real bot status from EC2 instance
    try {
      const response = await fetch(`http://3.91.154.73:8080/health`, {
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });
      
      if (response.ok) {
        const healthData = await response.json();
        newServices.groupme = {
          ...newServices.groupme,
          status: healthData.data.bot_status?.running ? 'operational' : 'degraded',
          lastCheck: new Date(),
          botInfo: {
            active: healthData.data.bot_status?.running || false,
            processes: healthData.data.bot_status?.count || 0,
            healthData: healthData.data
          }
        };
      } else {
        newServices.groupme = {
          ...newServices.groupme,
          status: 'degraded',
          lastCheck: new Date(),
          botInfo: {
            active: false,
            error: 'Bot status check failed'
          }
        };
      }
    } catch (error) {
      newServices.groupme = {
        ...newServices.groupme,
        status: 'outage',
        lastCheck: new Date(),
        botInfo: {
          active: false,
          error: 'Cannot reach bot status endpoint'
        }
      };
    }

    setServices(newServices);
    setLastUpdated(new Date());
    setLoading(false);
  }, []); // Empty dependency array to prevent infinite loops

  useEffect(() => {
    checkServiceHealth();
    const interval = setInterval(checkServiceHealth, 900000); // Check every 15 minutes (900,000 ms)
    
    return () => clearInterval(interval);
  }, [checkServiceHealth]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'outage': return 'text-red-600';
      case 'checking': return 'text-blue-600';
      case 'unknown': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusBackground = (status) => {
    switch (status) {
      case 'operational': return 'bg-green-100';
      case 'degraded': return 'bg-yellow-100';
      case 'outage': return 'bg-red-100';
      case 'checking': return 'bg-blue-100';
      case 'unknown': return 'bg-gray-100';
      default: return 'bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'operational': return '🟢';
      case 'degraded': return '🟡';
      case 'outage': return '🔴';
      case 'checking': return '🔵';
      case 'unknown': return '⚪';
      default: return '⚪';
    }
  };

  const renderServiceDetails = (service) => {
    if (service.healthData) {
      return (
        <div className="mt-2 text-sm text-gray-600">
          <p>Model loaded: {service.healthData.model_loaded ? 'Yes' : 'No'}</p>
          <p>Model type: {service.healthData.model_type || 'Unknown'}</p>
        </div>
      );
    }
    
    if (service.statsData) {
      return (
        <div className="mt-2 text-sm text-gray-600">
          <p>Total predictions: {service.statsData.total_predictions || 'N/A'}</p>
          <p>Accuracy: {service.statsData.accuracy || 'N/A'}</p>
        </div>
      );
    }
    
    if (service.instanceInfo) {
      return (
        <div className="mt-2 text-sm text-gray-600">
          <p>State: {service.instanceInfo.state}</p>
          {service.instanceInfo.note && (
            <p className="text-blue-600 italic">{service.instanceInfo.note}</p>
          )}
          {service.instanceInfo.error && (
            <p className="text-red-600">Error: {service.instanceInfo.error}</p>
          )}
          {service.instanceInfo.healthData && (
            <div className="mt-2 p-2 bg-gray-100 rounded">
              <p className="font-medium">System Health:</p>
              <p>CPU: {service.instanceInfo.healthData.system_health?.cpu_percent || 'N/A'}%</p>
              <p>Memory: {service.instanceInfo.healthData.system_health?.memory_percent || 'N/A'}%</p>
              <p>Disk: {service.instanceInfo.healthData.system_health?.disk_percent || 'N/A'}%</p>
              <p>Uptime: {Math.round((service.instanceInfo.healthData.uptime || 0) / 3600)} hours</p>
            </div>
          )}
        </div>
      );
    }
    
    if (service.botInfo) {
      return (
        <div className="mt-2 text-sm text-gray-600">
          <p>Active: {service.botInfo.active ? '✅ Yes' : '❌ No'}</p>
          <p>Processes: {service.botInfo.processes || 'N/A'}</p>
          {service.botInfo.healthData && (
            <div className="mt-2 p-2 bg-gray-100 rounded">
              <p className="font-medium">Bot Details:</p>
              <p>Group ID: 109638241 (Nest Run Club)</p>
              <p>Confidence Threshold: 80%</p>
              <p>Check Interval: 60 seconds</p>
              {service.botInfo.healthData.bot_status?.processes && (
                <div className="mt-2 pt-2 border-t border-gray-300">
                  <p className="font-medium">Process Info:</p>
                  {service.botInfo.healthData.bot_status.processes.map((proc, index) => (
                    <div key={index} className="text-xs">
                      <p>PID: {proc.pid} | CPU: {proc.cpu_percent}% | Memory: {proc.memory_percent}%</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      );
    }
    
    return null;
  };

  const isAllOperational = Object.values(services).every(service => 
    service.status === 'operational' || service.status === 'unknown'
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <Header showBackButton={true} onBackClick={onBack} />
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Checking system status...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <Header showBackButton={true} onBackClick={onBack} />
      
      {/* Overall Status Banner */}
      <div className={`${isAllOperational ? 'bg-green-500' : 'bg-red-500'} text-white py-6`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-xl font-semibold">
            {isAllOperational ? 'All Systems Operational' : 'System Issues Detected'}
          </h2>
          <p className="mt-2 opacity-90 text-sm">
            Last updated: {lastUpdated.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Services Overview */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <p className="text-gray-600">
            Real-time system status monitoring. All data is live from actual services.
          </p>
          <button 
            onClick={checkServiceHealth}
            className="mt-2 text-sm italic text-blue-600 hover:text-blue-800 underline"
          >
            Refresh Status Now
          </button>
        </div>

        {/* Services Grid */}
        <div className="space-y-6">
          {Object.entries(services).map(([key, service]) => (
            <div key={key} className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <h3 className="text-lg font-semibold text-gray-900">{service.name}</h3>
                  <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBackground(service.status)} ${getStatusColor(service.status)}`}>
                    {getStatusIcon(service.status)} {service.status.charAt(0).toUpperCase() + service.status.slice(1)}
                  </span>
                </div>
              </div>
              
              {renderServiceDetails(service)}
              
              <div className="mt-4">
                <div className="flex justify-between items-center">
                  <span className="text-lg text-gray-600">
                    Status: {service.status}
                  </span>
                  <div className="text-sm text-gray-500">
                    <span>Last check: {service.lastCheck.toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Additional Info */}
        <div className="mt-12 bg-gray-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-600">
            <div>
              <p><span className="font-medium">Region:</span> us-east-1 (N. Virginia)</p>
              <p><span className="font-medium">Instance Type:</span> t2.micro</p>
              <p><span className="font-medium">Monitoring:</span> Real-time (15 min intervals)</p>
            </div>
            <div>
              <p><span className="font-medium">Lambda Memory:</span> 1024 MB</p>
              <p><span className="font-medium">Lambda Timeout:</span> 30 seconds</p>
              <p><span className="font-medium">Last Health Check:</span> {lastUpdated.toLocaleTimeString()}</p>
              <p><span className="font-medium">Overall Status:</span> {isAllOperational ? 'Healthy' : 'Needs Attention'}</p>
            </div>
          </div>
        </div>
      </div>
      
      <Footer />
    </div>
  );
};

export default StatusPage;
