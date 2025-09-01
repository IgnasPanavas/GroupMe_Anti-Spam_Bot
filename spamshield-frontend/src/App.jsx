import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import PredictionBox from './components/PredictionBox';
import Stats from './components/Stats';
import StatusPage from './components/StatusPage';
import Footer from './components/Footer';
import { apiService } from './services/api';

function App() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState('main'); // 'main' or 'status'

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await apiService.getStats();
        setStats(response.data);
      } catch (err) {
        console.error('Error fetching stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const renderPage = () => {
    if (currentPage === 'status') {
      return <StatusPage onBack={() => setCurrentPage('main')} />;
    }

    return (
      <>
        <Hero />
        <PredictionBox />
        {stats && <Stats stats={stats} />}
      </>
    );
  };

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
    <div className="min-h-screen bg-gray-50">
      <Header onStatusClick={() => setCurrentPage('status')} />
      {renderPage()}
      <Footer />
    </div>
  );
}

export default App;
