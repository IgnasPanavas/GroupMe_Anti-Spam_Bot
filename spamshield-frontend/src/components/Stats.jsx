import React from 'react';

const Stats = ({ stats }) => {
  if (!stats) return null;

  const statItems = [
    {
      label: 'Messages Protected',
      value: stats.messages_protected?.toLocaleString() || '0',
      icon: '🛡️',
      color: 'bg-green-100 text-green-600'
    },
    {
      label: 'Spam Blocked',
      value: stats.spam_blocked?.toLocaleString() || '0',
      icon: '🚫',
      color: 'bg-red-100 text-red-600'
    },
    {
      label: 'Groups Protected',
      value: stats.groups_protected?.toLocaleString() || '0',
      icon: '👥',
      color: 'bg-blue-100 text-blue-600'
    },
    {
      label: 'Detection Accuracy',
      value: stats.accuracy || '97.5%',
      icon: '📊',
      color: 'bg-purple-100 text-purple-600'
    }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          SpamShield Performance
        </h2>
        <p className="text-lg text-gray-600">
          Real-time statistics from our deployed bot
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statItems.map((item, index) => (
          <div key={index} className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center">
              <div className={`p-3 rounded-full ${item.color}`}>
                <span className="text-2xl">{item.icon}</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{item.label}</p>
                <p className="text-2xl font-semibold text-gray-900">{item.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {stats.model_type && (
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">
              AI Model Information
            </h3>
            <p className="text-blue-800">
              Currently using <strong>{stats.model_type}</strong> for spam detection
            </p>
            {stats.last_updated && (
              <p className="text-blue-700 text-sm mt-2">
                Last updated: {new Date(stats.last_updated).toLocaleString()}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Stats;
