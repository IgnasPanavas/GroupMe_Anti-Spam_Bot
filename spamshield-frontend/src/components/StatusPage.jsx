import React, { useState, useEffect, useCallback, useRef } from 'react';
import Footer from './Footer';
import UptimeBars from './UptimeBars';
import { apiService } from '../services/api';

const StatusPage = () => {
  const [services, setServices] = useState({
    api: { status: 'checking', uptime: null, name: 'API', lastCheck: null },
    lambda: { status: 'checking', uptime: null, name: 'Lambda Function', lastCheck: null },
    ec2: { status: 'checking', uptime: null, name: 'EC2 Instance', lastCheck: null, instanceInfo: null },
    groupme: { status: 'checking', uptime: null, name: 'SpamShield Platform', lastCheck: null, botInfo: null }
  });

  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [dataSource, setDataSource] = useState('live');
  const [uptimeWindowHours, setUptimeWindowHours] = useState(45);
  const servicesRef = useRef(services);

  // Determine how many minutes of history are required for the bars on this device
  const computeUptimeMinutes = () => {
    const width = typeof window !== 'undefined' ? window.innerWidth : 1280;
    const barCount = width < 640 ? 30 : width < 1024 ? 60 : 90; // must match UptimeBars.jsx
    const minutes = barCount * 30; // 30 minutes per bar
    setUptimeWindowHours((minutes / 60));
    return minutes;
  };

  const checkServiceHealthFallback = useCallback(async (isManualRefresh = false) => {
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

    // Check EC2 instance status
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

    // SpamShield Platform status
    try {
      const response = await apiService.getBotStatus();
      const platformData = response.data;
      
      let platformStatus = 'outage';
      if (platformData.active && platformData.platform_status === 'running') {
        platformStatus = 'operational';
      } else if (platformData.active && platformData.platform_status === 'stopped') {
        platformStatus = 'degraded';
      }
      
      newServices.groupme = {
        ...newServices.groupme,
        name: 'SpamShield Platform',
        status: platformStatus,
        lastCheck: new Date(),
        botInfo: {
          ...platformData,
          displayStatus: platformData.active ? 'Active' : 'Inactive',
          groupsInfo: `${platformData.active_groups || 0}/${platformData.total_groups || 0} groups active`,
          workersInfo: `${platformData.workers || 0} workers running`,
          healthInfo: `DB: ${platformData.database_status || 'unknown'}, Metrics: ${platformData.metrics_status || 'unknown'}`
        }
      };
    } catch (error) {
      newServices.groupme = {
        ...newServices.groupme,
        name: 'SpamShield Platform',
        status: 'outage',
        lastCheck: new Date(),
        botInfo: { 
          active: false, 
          error: 'Cannot reach SpamShield platform endpoint',
          displayStatus: 'Offline',
          groupsInfo: '0/0 groups active',
          workersInfo: '0 workers running',
          healthInfo: 'Components unknown'
        }
      };
    }

    // Fetch uptime history for all services
    try {
      const minutes = computeUptimeMinutes();
      const limit = minutes * 2; // ensure enough records beyond default backend cap
      console.log(`📊 Fetching uptime history for ${minutes/60} hours with limit ${limit}...`);
      const uptimeResponse = await apiService.getUptimeHistory({ minutes, limit });
      const uptimeRecords = uptimeResponse.data.records || [];
      console.log('📊 Uptime history fetched:', uptimeRecords.length, 'records');
      
      // Group uptime data by service
      const uptimeByService = {};
      uptimeRecords.forEach(record => {
        if (!uptimeByService[record.service]) {
          uptimeByService[record.service] = [];
        }
        uptimeByService[record.service].push({
          timestamp: record.timestamp,
          status: record.status
        });
      });

      // Add uptime data to each service
      Object.keys(newServices).forEach(serviceKey => {
        const serviceName = serviceKey === 'groupme' ? 'bot' : serviceKey;
        newServices[serviceKey].uptimeData = uptimeByService[serviceName] || [];
      });
    } catch (error) {
      console.error('Error fetching uptime history:', error);
      // Don't fail the entire health check if uptime data fails
    }

    setServices(newServices);
    setLastUpdated(new Date());
    setLoading(false);
    if (isManualRefresh) {
      setRefreshing(false);
    }
    servicesRef.current = newServices;
    setDataSource('fallback');
  }, []);

  const checkServiceHealth = useCallback(async (isManualRefresh = false) => {
    console.log('🔄 Health check started at:', new Date().toLocaleTimeString());
    if (isManualRefresh) {
      setRefreshing(true);
    }
    
    try {
      // Use the new fast status summary endpoint
      const response = await apiService.getStatusSummary();
      const statusData = response.data;
      
      console.log('📊 Status summary data:', statusData);
      setDataSource(statusData.data_source || 'live');
      
      const newServices = { ...servicesRef.current };
      
      // Update API status
      newServices.api = {
        ...newServices.api,
        status: statusData.api?.status || 'unknown',
        lastCheck: statusData.api?.lastCheck ? new Date(statusData.api.lastCheck) : new Date(),
        healthData: statusData.api
      };
      
      // Update Lambda status
      newServices.lambda = {
        ...newServices.lambda,
        status: statusData.lambda?.status || 'unknown',
        lastCheck: statusData.lambda?.lastCheck ? new Date(statusData.lambda.lastCheck) : new Date(),
        healthData: statusData.lambda
      };
      
      // Update EC2 status
      newServices.ec2 = {
        ...newServices.ec2,
        status: statusData.ec2?.status || 'unknown',
        lastCheck: statusData.ec2?.lastCheck ? new Date(statusData.ec2.lastCheck) : new Date(),
        instanceInfo: statusData.ec2
      };
      
      // Update SpamShield Platform status
      newServices.groupme = {
        ...newServices.groupme,
        name: 'SpamShield Platform',
        status: statusData.bot?.status || 'unknown',
        lastCheck: statusData.bot?.lastCheck ? new Date(statusData.bot.lastCheck) : new Date(),
        botInfo: {
          ...statusData.bot,
          // Add display-friendly fields
          displayStatus: statusData.bot?.platform_status === 'running' ? 'Active' : 'Inactive',
          groupsInfo: `${statusData.bot?.active_groups || 0}/${statusData.bot?.total_groups || 0} groups active`,
          workersInfo: `${statusData.bot?.workers || 0} workers running`,
          healthInfo: `Platform: ${statusData.bot?.platform_status || 'unknown'}`
        }
      };
      
      // Fetch uptime history for all services
      try {
        const minutes = computeUptimeMinutes();
        const limit = minutes * 2; // ensure enough records beyond default backend cap
        console.log(`📊 Fetching uptime history for ${minutes/60} hours with limit ${limit}...`);
        const uptimeResponse = await apiService.getUptimeHistory({ minutes, limit });
        const uptimeRecords = uptimeResponse.data.records || [];
        console.log('📊 Uptime history fetched:', uptimeRecords.length, 'records');
        
        // Group uptime data by service
        const uptimeByService = {};
        uptimeRecords.forEach(record => {
          if (!uptimeByService[record.service]) {
            uptimeByService[record.service] = [];
          }
          uptimeByService[record.service].push({
            timestamp: record.timestamp,
            status: record.status
          });
        });

        // Add uptime data to each service
        Object.keys(newServices).forEach(serviceKey => {
          const serviceName = serviceKey === 'groupme' ? 'bot' : serviceKey;
          newServices[serviceKey].uptimeData = uptimeByService[serviceName] || [];
        });
      } catch (error) {
        console.error('Error fetching uptime history:', error);
        // Don't fail the entire health check if uptime data fails
      }

      setServices(newServices);
      setLastUpdated(new Date());
      setLoading(false);
      if (isManualRefresh) {
        setRefreshing(false);
      }
      servicesRef.current = newServices;
      
    } catch (error) {
      console.error('Error fetching status summary:', error);
      
      // Fallback to individual API calls if the fast endpoint fails
      console.log('🔄 Falling back to individual API calls...');
      await checkServiceHealthFallback(isManualRefresh);
    }
  }, [checkServiceHealthFallback]);

  useEffect(() => {
    checkServiceHealth();
    const interval = setInterval(checkServiceHealth, 300000); // Check every 5 minutes (300,000 ms)
    
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
          {service.instanceInfo.state && (
            <p><span className="font-medium">State:</span> {service.instanceInfo.state}</p>
          )}
          {service.instanceInfo.publicIp && (
            <p><span className="font-medium">IP:</span> {service.instanceInfo.publicIp}</p>
          )}
        </div>
      );
    }
    
    if (service.botInfo && service.name === 'SpamShield Platform') {
      return (
        <div className="mt-2 text-sm text-gray-600 space-y-1">
          <p><span className="font-medium">Status:</span> {service.botInfo.displayStatus}</p>
          <p><span className="font-medium">Groups:</span> {service.botInfo.groupsInfo}</p>
          <p><span className="font-medium">Workers:</span> {service.botInfo.workersInfo}</p>
          <p><span className="font-medium">Health:</span> {service.botInfo.healthInfo}</p>
          {service.botInfo.error && (
            <p className="text-red-600 mt-2">Error: {service.botInfo.error}</p>
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
    <div className="min-h-screen bg-white flex flex-col section-divider">
      <div className="flex-grow py-16">
        {/* Overall Status Banner */}
      <div className={`${isAllOperational ? 'bg-green-500' : 'bg-orange-500'} text-white py-6`}>
        <div className="w-full max-w-[960px] mx-auto px-4 sm:px-6 lg:px-8 text-center" style={{ boxSizing: 'border-box' }}>
          <h2 className="text-xl font-semibold">
            {isAllOperational ? 'All Systems Operational' : 'System Issues Detected'}
          </h2>
          <p className="mt-2 opacity-90 text-sm">
            Last updated: {lastUpdated.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Services Overview */}
      <div className="w-full max-w-[960px] mx-auto px-4 sm:px-6 lg:px-8 py-8" style={{ boxSizing: 'border-box' }}>
        <div className="mb-8">
          <p className="text-gray-600">
            Real-time system status monitoring. {dataSource === 'uptime_logs' ? 'Data from server-side monitoring system.' : 'Data from live API calls.'}
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Uptime over the past {uptimeWindowHours} hours (30-minute periods). Recent bars show current status; grey bars indicate no historical data yet.
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

        
      </div>
      </div>
      
      <Footer />
    </div>
  );
};

export default StatusPage;
