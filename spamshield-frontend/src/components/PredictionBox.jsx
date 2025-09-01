import React, { useState } from 'react';
import { apiService } from '../services/api';

const PredictionBox = () => {
  const [text, setText] = useState('');
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const exampleMessages = [
    "selling concert tickets dm me",
    "Hello, how are you doing today?",
    "selling parking permit text 404-555-1234",
    "This is a legitimate message about our meeting tomorrow",
    "selling football tickets very urgent 2039095465"
  ];

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

  const handleExampleClick = (example) => {
    setText(example);
    setPrediction(null);
    setError(null);
  };

  const getPredictionColor = () => {
    if (!prediction) return '';
    return prediction.prediction === 'spam' ? 'text-red-600' : 'text-green-600';
  };

  const getPredictionIcon = () => {
    if (!prediction) return null;
    return prediction.prediction === 'spam' ? '🚫' : '✅';
  };

  const getConfidenceColor = () => {
    if (!prediction) return '';
    const confidence = prediction.confidence;
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBarColor = () => {
    if (!prediction) return '';
    const confidence = prediction.confidence;
    if (confidence >= 0.8) return '#10b981'; // green-500
    if (confidence >= 0.6) return '#eab308'; // yellow-500
    return '#ef4444'; // red-500
  };

  return (
    <div id="prediction-box" className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            🧪 Try SpamShield Detection
          </h2>
          <p className="text-lg text-gray-600">
            Enter any message below to see if our AI detects it as spam
          </p>
        </div>

        {/* Input Section */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Enter a message to test spam detection..."
                className="w-full h-32 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                disabled={loading}
              />
            </div>
            <div className="flex flex-col gap-2">
              <button
                onClick={handlePredict}
                disabled={loading || !text.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
                className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        {/* Example Messages */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Try these examples:</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {exampleMessages.map((example, index) => (
              <button
                key={index}
                onClick={() => handleExampleClick(example)}
                className="p-3 text-left bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors text-sm"
              >
                "{example.length > 40 ? example.substring(0, 40) + '...' : example}"
              </button>
            ))}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Prediction Results */}
        {prediction && (
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis Results</h3>
            

            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Prediction */}
              <div className="bg-white rounded-lg p-4 border">
                <div className="flex items-center mb-2">
                  <span className="text-2xl mr-2">{getPredictionIcon()}</span>
                  <h4 className="font-semibold text-gray-900">Prediction</h4>
                </div>
                <p className={`text-xl font-bold ${getPredictionColor()}`}>
                  {prediction.prediction === 'spam' ? 'SPAM DETECTED' : 'LEGITIMATE MESSAGE'}
                </p>
              </div>

              {/* Confidence */}
              <div className="bg-white rounded-lg p-4 border">
                <h4 className="font-semibold text-gray-900 mb-2">Confidence</h4>
                <p className={`text-xl font-bold ${getConfidenceColor()}`}>
                  {prediction.confidence_percentage}
                </p>
                <div className="mt-2">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="h-2 rounded-full"
                      style={{ 
                        width: `${prediction.confidence * 100}%`,
                        backgroundColor: getConfidenceBarColor()
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Processed Text */}
            {prediction.processed_text && (
              <div className="mt-4 bg-white rounded-lg p-4 border">
                <h4 className="font-semibold text-gray-900 mb-2">Processed Text</h4>
                <p className="text-gray-600 font-mono text-sm">
                  "{prediction.processed_text}"
                </p>
              </div>
            )}

            {/* Message */}
            <div className="mt-4">
              <p className="text-gray-700">{prediction.message}</p>
            </div>
          </div>
        )}

        {/* Info Section */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">How it works</h3>
          <p className="text-blue-800">
            SpamShield uses advanced machine learning algorithms to analyze message content, 
            patterns, and context. Our model has been trained on thousands of messages and 
            achieves 97.5% accuracy in detecting spam while minimizing false positives.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PredictionBox;
