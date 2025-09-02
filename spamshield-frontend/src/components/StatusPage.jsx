import React, { useState, useEffect, useCallback, useRef } from 'react';
import Footer from './Footer';
import UptimeBars from './UptimeBars';
import { apiService } from '../services/api';

const StatusPage = () => {
  const [services, setServices] = useState({
    api: { status: 'checking', uptime: null, name: 'API', lastCheck: null },
    lambda: { status: 'checking', uptime: null, name: 'Lambda Function', lastCheck: null },
    ec2: { status: 'checking', uptime: null, name: 'EC2 Instance', lastCheck: null, instanceInfo: null },
    groupme: { status: 'checking', uptime: null, name: 'GroupMe Bot', lastCheck: null, botInfo: null }
  });

  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const servicesRef = useRef(services);



  // No synthetic uptime generation. Bars display only persisted history.

  const checkServiceHealth = useCallback(async (isManualRefresh = false) => {
    console.log('🔄 Health check started at:', new Date().toLocaleTimeString());
    if (isManualRefresh) {
      setRefreshing(true);
    }
    const newServices = { ...servicesRef.current };
    
    try {
      // Check API health via API Gateway
      const response = await apiService.health();
      newServices.api = {
        ...newServices.api,
        status: response.status === 200 ? 'operational' : 'degraded',
        lastCheck: new Date(),
        healthData: response.data
      };
    } catch (error) {
      newServices.api = {
        ...newServices.api,
        status: 'outage',
        lastCheck: new Date()
      };
    }

    // Check Lambda function status
    try {
      // Consider Lambda reachable if API health is OK
      const response = await apiService.health();
      newServices.lambda = {
        ...newServices.lambda,
        status: response.status === 200 ? 'operational' : 'degraded',
        lastCheck: new Date(),
        healthData: response.data
      };
    } catch (error) {
      newServices.lambda = {
        ...newServices.lambda,
        status: 'outage',
        lastCheck: new Date()
      };
    }

    // Check EC2 instance status - use API Gateway endpoint
    try {
      const response = await apiService.getEc2Status();
      const ec2Data = response.data;
      const ec2Status = ec2Data.state === 'running' ? 'operational' : 'degraded';
      newServices.ec2 = {
        ...newServices.ec2,
        status: ec2Status,
        lastCheck: new Date(),
        instanceInfo: ec2Data
      };
    } catch (error) {
      newServices.ec2 = {
        ...newServices.ec2,
        status: 'outage',
        lastCheck: new Date(),
        instanceInfo: { error: 'Cannot reach EC2 status endpoint' }
      };
    }

    // GroupMe Bot status - use API Gateway endpoint
    try {
      const response = await apiService.getBotStatus();
      const botData = response.data;
      const botStatus = botData.active ? 'operational' : 'degraded';
      newServices.groupme = {
        ...newServices.groupme,
        status: botStatus,
        lastCheck: new Date(),
        botInfo: botData
      };
    } catch (error) {
      newServices.groupme = {
        ...newServices.groupme,
        status: 'outage',
        lastCheck: new Date(),
        botInfo: { active: false, error: 'Cannot reach bot status endpoint' }
      };
    }

    // Persist per-service statuses to uptime history
    try {
      const persist = async (serviceKey, statusValue, details = {}) => {
        await apiService.postUptimeRecord({ service: serviceKey, status: statusValue, details });
      };
      await Promise.all([
        persist('api', newServices.api.status),
        persist('lambda', newServices.lambda.status),
        persist('ec2', newServices.ec2.status),
        persist('bot', newServices.groupme.status),
      ]);
    } catch (e) {
      // Non-blocking
    }

    // Fetch and apply uptime history for bars (real persistent data)
    const totalBars = 90; // 5-minute intervals
    const fetchHistory = async (serviceKey, fallbackStatus = 'no_data') => {
      try {
        const resp = await apiService.getUptimeHistory({ minutes: 450, limit: totalBars, service: serviceKey });
        const records = resp?.data?.records || [];
        const historyData = records.slice(-totalBars).map(r => ({ timestamp: r.timestamp, status: r.status || 'no_data' }));
        
        // Always add current status as the most recent bar
        const currentTime = new Date().toISOString();
        const currentStatus = newServices[serviceKey === 'bot' ? 'groupme' : serviceKey]?.status || fallbackStatus;
        
        // Add current status to the end of history
        historyData.push({ timestamp: currentTime, status: currentStatus });
        
        return historyData;
      } catch (error) {
        console.warn(`Failed to fetch uptime history for ${serviceKey}:`, error);
        // Return fallback data showing current status and some historical context
        const fallbackData = [];
        const currentTime = new Date();
        const currentStatus = newServices[serviceKey === 'bot' ? 'groupme' : serviceKey]?.status || fallbackStatus;
        
        // Generate minimal fallback data with current status as the latest bar
        for (let i = 0; i < totalBars - 1; i++) {
          const timestamp = new Date(currentTime.getTime() - (totalBars - 1 - i) * 5 * 60 * 1000);
          fallbackData.push({ timestamp: timestamp.toISOString(), status: 'no_data' });
        }
        
        // Add current status as the most recent bar
        fallbackData.push({ timestamp: currentTime.toISOString(), status: currentStatus });
        
        return fallbackData;
      }
    };

    try {
      const [apiBars, lambdaBars, ec2Bars, botBars] = await Promise.all([
        fetchHistory('api'),
        fetchHistory('lambda'),
        fetchHistory('ec2'),
        fetchHistory('bot'),
      ]);

      newServices.api = { ...newServices.api, uptimeData: apiBars };
      newServices.lambda = { ...newServices.lambda, uptimeData: lambdaBars };
      newServices.ec2 = { ...newServices.ec2, uptimeData: ec2Bars };
      newServices.groupme = { ...newServices.groupme, uptimeData: botBars };
    } catch (e) {
      // Fallback: ensure all services have at least basic uptime data
      const fallbackData = Array(totalBars).fill(null).map((_, i) => ({
        timestamp: new Date(Date.now() - (totalBars - 1 - i) * 5 * 60 * 1000).toISOString(),
        status: i === totalBars - 1 ? 'outage' : 'no_data' // Latest bar shows outage, others no data
      }));
      
      newServices.api = { ...newServices.api, uptimeData: fallbackData };
      newServices.lambda = { ...newServices.lambda, uptimeData: fallbackData };
      newServices.ec2 = { ...newServices.ec2, uptimeData: fallbackData };
      newServices.groupme = { ...newServices.groupme, uptimeData: fallbackData };
    }

    setServices(newServices);
    setLastUpdated(new Date());
    setLoading(false);
    if (isManualRefresh) {
      setRefreshing(false);
    }
    servicesRef.current = newServices;
  }, []); // No dependencies needed now

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

  

  const renderServiceDetails = (service) => {
    if (service.instanceInfo) {
      return (
        <div className="mt-2 text-sm text-gray-600">
          {service.instanceInfo.error && (
            <p className="text-red-600">Error: {service.instanceInfo.error}</p>
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
          <p className="text-sm text-gray-500 mt-2">
            Uptime over the past 45 hours (30-minute periods). Recent bars show current status, grey bars indicate no historical data available yet.
          </p>
          <button 
            onClick={() => checkServiceHealth(true)}
            disabled={refreshing}
            className={`mt-2 text-sm italic text-blue-600 hover:text-blue-800 underline transition-opacity ${
              refreshing ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {refreshing ? '🔄 Refreshing...' : 'Refresh Status Now'}
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
                    {service.status.charAt(0).toUpperCase() + service.status.slice(1)}
                  </span>
                </div>
              </div>
              
              {renderServiceDetails(service)}
              
              {/* Uptime Bars - Always show */}
              <UptimeBars 
                uptimeData={service.uptimeData || []} 
                days={90} 
                serviceName={service.name}
                currentStatus={service.status}
              />
              
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

        {/* Additional Info section removed to avoid hardcoded values */}
      </div>
      
      <Footer />
    </div>
  );
};

export default StatusPage;
