import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
  return (
    <footer className=" text-gray-800 py-10 pb-36 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex justify-center">
            <div className="text-left max-w-xs">
              <h3 className="text-lg font-semibold mb-4 text-gray-900">SpamShield</h3>
              <a 
                href="mailto:ignaspanavas1@gmail.com?subject=SpamShield Inquiry" 
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                Contact Us
              </a>
            </div>
          </div>
          
          <div className="flex justify-center">
            <div className="text-left max-w-xs">
              <h3 className="text-lg font-semibold mb-4 text-gray-900">Features</h3>
              <ul className="space-y-2 text-gray-600">
                <li>AI-Powered Detection</li>
                <li>Real-time Protection</li>
                <li>97.5% Accuracy</li>
                <li>Easy Management</li>
              </ul>
            </div>
          </div>
          
          <div className="flex justify-center">
            <div className="text-left max-w-xs">
              <h3 className="text-lg font-semibold mb-4 text-gray-900">Navigation</h3>
              <ul className="space-y-2 text-gray-600">
                <li>
                  <Link to="/" className="hover:text-gray-900 transition-colors">
                    Home
                  </Link>
                </li>
                <li>
                  <Link to="/status" className="hover:text-gray-900 transition-colors">
                    Status Dashboard
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
        
        <div className="border-t border-gray-300 mt-8 pt-8 text-center text-gray-600">
          <p>&copy; 2025 SpamShield. Built with Passion.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
