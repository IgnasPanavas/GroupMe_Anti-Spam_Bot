import React from 'react';
import HeroVisual from './HeroVisual';

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
                  onClick={() => window.location.href = '/learn-more'}
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
                  Get Started
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

    </div>
  );
};

export default Hero;
