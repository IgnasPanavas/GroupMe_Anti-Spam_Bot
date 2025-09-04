import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

const BotStatusOptimized = () => {
  const [platformStatus, setPlatformStatus] = useState({
    active: false,
    status: 'checking',
    platform_status: 'checking',
    main_pid: null,
    health_status: 'unknown',
    orchestrator_running: false,
    total_groups: 0,
    active_groups: 0,
    workers: 0,
    database_status: 'unknown',
    metrics_status: 'unknown',
    last_checked: null,
    service_type: 'spamshield_platform'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dataSource, setDataSource] = useState('live');

  useEffect(() => {
    const checkPlatformStatus = async () => {
      try {
        setError(null);
        
        // Try the fast status summary endpoint first
        try {
          const response = await apiService.getStatusSummary();
          const statusData = response.data;
          
          if (statusData.bot) {
            setDataSource(statusData.data_source || 'live');
            setPlatformStatus({
              active: statusData.bot.platform_status === 'running',
              status: statusData.bot.status || 'unknown',
              platform_status: statusData.bot.platform_status || 'unknown',
              main_pid: null, // Not available in status summary
              health_status: statusData.bot.platform_status || 'unknown',
              orchestrator_running: true, // Assume running if platform is running
              total_groups: statusData.bot.total_groups || 0,
              active_groups: statusData.bot.active_groups || 0,
              workers: statusData.bot.workers || 0,
              database_status: 'healthy', // Assume healthy if platform is running
              metrics_status: 'healthy', // Assume healthy if platform is running
              last_checked: statusData.bot.lastCheck || new Date().toISOString(),
              service_type: 'spamshield_platform',
              note: 'Data from fast status endpoint'
            });
            setLoading(false);
            return;
          }
        } catch (fastError) {
          console.log('Fast endpoint failed, falling back to individual API call:', fastError);
        }
        
        // Fallback to individual bot status API call
        const response = await apiService.getBotStatus();
        const data = response.data;
        
        setPlatformStatus({
          active: data.active || false,
          status: data.status || 'unknown',
          platform_status: data.platform_status || 'unknown',
          main_pid: data.main_pid || null,
          health_status: data.health_status || 'unknown',
          orchestrator_running: data.orchestrator_running || false,
          total_groups: data.total_groups || 0,
          active_groups: data.active_groups || 0,
          workers: data.workers || 0,
          database_status: data.database_status || 'unknown',
          metrics_status: data.metrics_status || 'unknown',
          last_checked: data.last_checked || new Date().toISOString(),
          service_type: data.service_type || 'spamshield_platform',
          note: data.note,
          error: data.error
        });
        setDataSource('individual_api');

        setLoading(false);
      } catch (error) {
        console.error('Error checking platform status:', error);
        setError(error.message);
        setPlatformStatus(prev => ({
          ...prev,
          active: false,
          status: 'outage',
          platform_status: 'error'
        }));
        setLoading(false);
      }
    };

    checkPlatformStatus();
    
    // Refresh every 30 seconds
    const interval = setInterval(checkPlatformStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational':
      case 'running':
      case 'healthy': 
        return 'text-green-600 bg-green-100';
      case 'outage':
      case 'error':
      case 'stopped':
        return 'text-red-600 bg-red-100';
      case 'checking':
      case 'unknown':
        return 'text-yellow-600 bg-yellow-100';
      default: 
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'operational':
      case 'running':
      case 'healthy':
        return '🟢';
      case 'outage':
      case 'error':
      case 'stopped':
        return '🔴';
      case 'checking':
      case 'unknown':
        return '🟡';
      default: 
        return '⚪';
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8" data-bot-status>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Checking SpamShield Platform status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8" data-bot-status>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-2xl font-bold text-red-900 mb-4">❌ Connection Error</h2>
          <p className="text-red-700 mb-4">Unable to connect to SpamShield Platform:</p>
          <p className="text-red-600 font-mono text-sm bg-red-100 p-3 rounded">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8" data-bot-status>
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">
          🛡️ SpamShield Platform Dashboard
        </h2>
        
        {/* Data Source Indicator */}
        <div className="mb-4 text-center">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            dataSource === 'uptime_logs' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
          }`}>
            {dataSource === 'uptime_logs' ? '📊 Server-side monitoring' : '🔄 Live API calls'}
          </span>
        </div>
        
        {/* Platform Status Banner */}
        <div className={`rounded-lg p-4 mb-6 ${platformStatus.active ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">{platformStatus.active ? '🟢' : '🔴'}</span>
              <div>
                <h3 className={`text-lg font-semibold ${platformStatus.active ? 'text-green-900' : 'text-red-900'}`}>
                  Platform {platformStatus.active ? 'Operational' : 'Offline'}
                </h3>
                <p className={`text-sm ${platformStatus.active ? 'text-green-700' : 'text-red-700'}`}>
                  Status: {platformStatus.status} • Platform: {platformStatus.platform_status}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Process ID: {platformStatus.main_pid || 'N/A'}</p>
              <p className="text-xs text-gray-500">
                Last checked: {platformStatus.last_checked ? new Date(platformStatus.last_checked).toLocaleTimeString() : 'Unknown'}
              </p>
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Platform Health */}
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Platform Health</h3>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(platformStatus.health_status)}`}>
                {getStatusIcon(platformStatus.health_status)} {platformStatus.health_status}
              </span>
            </div>
            <div className="space-y-2 text-sm text-gray-600">
              <p><span className="font-medium">Database:</span> {platformStatus.database_status}</p>
              <p><span className="font-medium">Metrics:</span> {platformStatus.metrics_status}</p>
              <p><span className="font-medium">Orchestrator:</span> {platformStatus.orchestrator_running ? 'Running' : 'Stopped'}</p>
              <p><span className="font-medium">Workers:</span> {platformStatus.workers} active</p>
            </div>
          </div>

          {/* Group Management */}
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Groups</h3>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${platformStatus.active_groups > 0 ? 'text-green-600 bg-green-100' : 'text-gray-600 bg-gray-100'}`}>
                {platformStatus.active_groups > 0 ? '🟢' : '⚪'} {platformStatus.active_groups} / {platformStatus.total_groups}
              </span>
            </div>
            <div className="space-y-2 text-sm text-gray-600">
              <p><span className="font-medium">Total Groups:</span> {platformStatus.total_groups}</p>
              <p><span className="font-medium">Active Groups:</span> {platformStatus.active_groups}</p>
              <p><span className="font-medium">Workers Assigned:</span> {platformStatus.workers}</p>
              <p><span className="font-medium">Service Type:</span> {platformStatus.service_type}</p>
            </div>
          </div>

          {/* System Info */}
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">System Info</h3>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(platformStatus.platform_status)}`}>
                {getStatusIcon(platformStatus.platform_status)} {platformStatus.platform_status}
              </span>
            </div>
            <div className="space-y-2 text-sm text-gray-600">
              <p><span className="font-medium">Instance:</span> i-0a0001f601291b280</p>
              <p><span className="font-medium">Region:</span> us-east-1</p>
              <p><span className="font-medium">Platform:</span> SpamShield v2.0</p>
              <p><span className="font-medium">Architecture:</span> Microservices</p>
            </div>
          </div>
        </div>

        {/* Status Details */}
        <div className="bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-4">Platform Details</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="font-medium text-blue-900">SpamShield Platform:</p>
              <p className="text-blue-700">
                Next-generation anti-spam platform running on AWS EC2. Features real-time monitoring, 
                multi-group support, and scalable worker architecture.
              </p>
            </div>
            <div>
              <p className="font-medium text-blue-900">Group Management:</p>
              <p className="text-blue-700">
                Dynamic group addition/removal with automatic worker assignment. Each group gets 
                dedicated monitoring with configurable spam detection thresholds.
              </p>
            </div>
            <div>
              <p className="font-medium text-blue-900">Real-time Monitoring:</p>
              <p className="text-blue-700">
                Comprehensive health checks, metrics collection, and uptime tracking. 
                All components are monitored with automatic alerting on issues.
              </p>
            </div>
            <div>
              <p className="font-medium text-blue-900">Performance Optimization:</p>
              <p className="text-blue-700">
                {dataSource === 'uptime_logs' 
                  ? 'Using server-side monitoring for faster, more reliable status updates.'
                  : 'Using live API calls for real-time status information.'
                }
              </p>
            </div>
          </div>
          
          {/* Error Display */}
          {(platformStatus.error || platformStatus.note) && (
            <div className="mt-4 p-3 bg-yellow-100 border border-yellow-200 rounded">
              <p className="text-sm text-yellow-800">
                <span className="font-medium">Note:</span> {platformStatus.note || platformStatus.error}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BotStatusOptimized;
