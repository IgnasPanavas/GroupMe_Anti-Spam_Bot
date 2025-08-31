import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Hero from './components/Hero';
import PredictionBox from './components/PredictionBox';
import Dashboard from './components/Dashboard';
import Stats from './components/Stats';
import Charts from './components/Charts';
import Footer from './components/Footer';
import { apiService } from './services/api';

function App() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await apiService.getStats();
        setStats(response.data);
      } catch (err) {
        setError('Failed to load statistics');
        console.error('Error fetching stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading SpamShield...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Header />
        
        <Routes>
          <Route path="/" element={
            <div>
              <Hero />
              <PredictionBox />
              {stats && <Stats stats={stats} />}
            </div>
          } />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
        
        <Footer />
      </div>
    </Router>
  );
}

export default App;
