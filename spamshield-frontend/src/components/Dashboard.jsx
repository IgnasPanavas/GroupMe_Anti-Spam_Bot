import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import Charts from './Charts';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [groups, setGroups] = useState([]);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsRes, groupsRes, activityRes] = await Promise.all([
          apiService.getStats(),
          apiService.getGroups(),
          apiService.getActivity()
        ]);

        setStats(statsRes.data);
        setGroups(groupsRes.data);
        setActivity(activityRes.data);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error('Error fetching dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Monitor your SpamShield protection</p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100 text-green-600">
                <span className="text-xl">🛡️</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Messages Protected</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.messages_protected?.toLocaleString() || '0'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-red-100 text-red-600">
                <span className="text-xl">🚫</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Spam Blocked</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.spam_blocked?.toLocaleString() || '0'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-blue-100 text-blue-600">
                <span className="text-xl">👥</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Groups Protected</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.groups_protected?.toLocaleString() || '0'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-purple-100 text-purple-600">
                <span className="text-xl">📊</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Accuracy</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.accuracy || '97.5%'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts and Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Spam Detection Activity</h3>
          <Charts />
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {activity.map((item, index) => (
              <div key={index} className="flex items-center p-3 bg-gray-50 rounded">
                <div className={`w-2 h-2 rounded-full mr-3 ${
                  item.type === 'spam_blocked' ? 'bg-red-500' : 'bg-green-500'
                }`}></div>
                <div>
                  <p className="text-sm font-medium">{item.message}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(item.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Protected Groups */}
      {groups.length > 0 && (
        <div className="mt-8 bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold">Protected Groups</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {groups.map((group) => (
                <div key={group.id} className="border rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900">{group.name}</h3>
                  <p className="text-sm text-gray-600">ID: {group.id}</p>
                  <p className="text-sm text-gray-600">{group.members} members</p>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    {group.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
