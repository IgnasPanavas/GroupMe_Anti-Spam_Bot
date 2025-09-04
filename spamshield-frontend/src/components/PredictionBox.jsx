import React, { useState } from 'react';
import { apiService } from '../services/api';

const PredictionBox = () => {
  const [text, setText] = useState('selling concert tickets dm me');
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePredict = async () => {
    if (!text.trim()) {
      setError('Please enter some text to analyze');
      return;
    }

    setLoading(true);
    setError(null);
    setPrediction(null);

    try {
      const response = await apiService.predict(text);
      setPrediction(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to get prediction');
    } finally {
      setLoading(false);
    }
  };

  const getBorderColor = () => {
    if (!prediction) return '';
    return prediction.prediction === 'spam' ? 'border-flash-red' : 'border-flash-green';
  };

  return (
    <div className="py-16" style={{ backgroundColor: 'var(--bg-brownish-gray)' }} data-section="prediction">
      <div className="w-full max-w-[960px] mx-auto px-4 sm:px-6 lg:px-8" style={{ boxSizing: 'border-box' }}>
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold mb-4" style={{ color: 'var(--text-dark-gray)' }}>
            Try SpamShield Detection
          </h2>
          <p className="text-lg" style={{ color: 'var(--text-dark-gray)', opacity: 0.8 }}>
            Enter any message below to see if our AI detects it as spam
          </p>
        </div>

        <div className={`bg-white rounded-xl shadow-2xl p-8 border-2 border-transparent ${getBorderColor()}`}>
          {/* Input Section */}
          <div className="mb-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1">
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Enter a message to test spam detection..."
                  className="w-full h-24 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white"
                  style={{ color: 'var(--text-dark-gray)' }}
                  disabled={loading}
                />
              </div>
              <div className="flex flex-col gap-2">
                <button
                  onClick={handlePredict}
                  disabled={loading || !text.trim()}
                  className="px-6 py-2.5 text-white rounded-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  style={{ 
                    backgroundColor: 'var(--theme-primary)',
                    border: 'none'
                  }}
                  onMouseEnter={(e) => !e.target.disabled && (e.target.style.backgroundColor = 'var(--theme-primary-hover)')}
                  onMouseLeave={(e) => !e.target.disabled && (e.target.style.backgroundColor = 'var(--theme-primary)')}
                >
                  {loading ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Analyzing...
                    </div>
                  ) : (
                    'Analyze Message'
                  )}
                </button>
                <button
                  onClick={() => {
                    setText('');
                    setPrediction(null);
                    setError(null);
                  }}
                  className="px-6 py-2 border-2 rounded-lg font-semibold transition-colors"
                  style={{ 
                    color: 'var(--theme-primary)',
                    borderColor: 'var(--theme-primary)',
                    backgroundColor: 'transparent'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = 'var(--theme-primary)';
                    e.target.style.color = 'white';
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = 'transparent';
                    e.target.style.color = 'var(--theme-primary)';
                  }}
                >
                  Clear
                </button>
              </div>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Prediction Results */}
          <div className="bg-gray-50 rounded-lg p-4 min-h-[60px] flex items-start">
            <div className="text-left">
              {prediction ? (
                <span className="font-mono text-lg" style={{ color: 'var(--text-dark-gray)' }}>
                  {`{"response": "${prediction.prediction === 'spam' ? 'SPAM_DETECTED' : 'LEGITIMATE_MESSAGE'}"}`}
                </span>
              ) : (
                <span className="font-mono text-lg" style={{ color: 'var(--text-dark-gray)', opacity: 0.6 }}>
                  {`{"response": "waiting_for_analysis"}`}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictionBox;