import React from 'react';
import HeroVisual from './HeroVisual';
import InfrastructureGrid from './InfrastructureGrid';
import PredictionBox from './PredictionBox';
const Hero = () => {

  return (
    <div className="min-h-fit" style={{ backgroundColor: 'var(--bg-brownish-gray)' }}>
      {/* Hero Section */}
      <div className="justify-center pt-40 pb-32">
        <div className="w-fit mx-auto px-4 sm:px-6 lg:px-8" style={{ boxSizing: 'border-box' }}>
          {/* Hero Text and Phone Side by Side */}
          <div className="flex flex-col lg:flex-row justify-end items-center gap-12">
            {/* Left: Hero Text */}
            <div className="text-center lg:text-left max-w-2xl">
              <h1 className="text-5xl md:text-6xl font-light mb-8" style={{ color: 'var(--text-dark-gray)' }}>
                SpamShield AI
              </h1>
              <p className="text-xl md:text-2xl mb-8 font-light leading-relaxed" style={{ color: 'var(--text-dark-gray)', opacity: 0.8 }}>
                Intelligent spam detection that keeps your GroupMe conversations clean and focused. 
                Our advanced AI analyzes messages in real-time, protecting your community from unwanted spam, 
                scams, and promotional content while preserving genuine conversations.
              </p>
              
              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-6 justify-center lg:justify-start">
                <button 
                  onClick={() => {
                    const predictionSection = document.querySelector('[data-section="prediction"]');
                    if (predictionSection) {
                      predictionSection.scrollIntoView({ behavior: 'smooth' });
                    }
                  }}
                  className="px-10 py-4 text-white rounded-lg font-semibold transition-colors text-lg"
                  style={{ 
                    backgroundColor: 'var(--theme-primary)',
                    border: 'none'
                  }}
                  onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--theme-primary-hover)'}
                  onMouseLeave={(e) => e.target.style.backgroundColor = 'var(--theme-primary)'}
                >
                  Try Spam Detection
                </button>
                <button 
                  onClick={() => {
                    const learnMoreSection = document.getElementById('learn-more');
                    if (learnMoreSection) {
                      learnMoreSection.scrollIntoView({ behavior: 'smooth' });
                    }
                  }}
                  className="px-10 py-4 border-2 rounded-lg font-semibold transition-colors text-lg"
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
                  Learn More
                </button>
              </div>
            </div>

            {/* Right: Phone Mockup */}
            <div className="flex justify-center max-w-2xl">
              <HeroVisual />
            </div>
          </div>
        </div>
      </div>
      <PredictionBox />
      {/* Learn More Section */}
      <div className="section-divider" id="learn-more">
        <div className="w-full max-w-[960px] mx-auto py-24" style={{ boxSizing: 'border-box' }}>
          {/* Section Header */}
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              About SpamShield
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Learn how SpamShield protects your GroupMe communities with AI-powered spam detection
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
            <div className="bg-white/60 backdrop-blur-sm rounded-lg shadow-lg p-6">
              <div className="bg-blue-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">AI-Powered Detection</h3>
              <p className="text-gray-600">
                Our machine learning model achieves 97.5% accuracy in detecting spam messages, 
                using advanced natural language processing techniques.
              </p>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-lg shadow-lg p-6">
              <div className="bg-green-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Real-time Protection</h3>
              <p className="text-gray-600">
                Messages are analyzed instantly as they arrive, providing immediate protection 
                without slowing down your group conversations.
              </p>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-lg shadow-lg p-6">
              <div className="bg-purple-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Easy Management</h3>
              <p className="text-gray-600">
                Simple commands and an intuitive dashboard make it easy to manage your 
                spam protection settings and monitor activity.
              </p>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-lg shadow-lg p-6">
              <div className="bg-orange-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Privacy Focused</h3>
              <p className="text-gray-600">
                Your messages are processed securely and never stored. We only analyze 
                content for spam detection purposes.
              </p>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-lg shadow-lg p-6">
              <div className="bg-red-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Open Source</h3>
              <p className="text-gray-600">
                SpamShield is completely open source, allowing you to review the code, 
                contribute improvements, and customize for your needs.
              </p>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-lg shadow-lg p-6">
              <div className="bg-indigo-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">Analytics & Insights</h3>
              <p className="text-gray-600">
                Get detailed insights into spam patterns, detection accuracy, and 
                community health metrics through our dashboard.
              </p>
            </div>
          </div>

          {/* Infrastructure Grid */}
          <InfrastructureGrid />

          
        </div>
      </div>

    </div>
  );
};

export default Hero;
