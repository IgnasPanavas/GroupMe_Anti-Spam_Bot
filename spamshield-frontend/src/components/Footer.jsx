import React from 'react';

const Footer = () => {
  return (
    <footer className="bg-gray-800 text-white py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-lg font-semibold mb-4">SpamShield</h3>
            <p className="text-gray-300">
              Professional AI-powered spam protection for GroupMe communities.
            </p>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-4">Features</h3>
            <ul className="space-y-2 text-gray-300">
              <li>• AI-Powered Detection</li>
              <li>• Real-time Protection</li>
              <li>• 97.5% Accuracy</li>
              <li>• Easy Management</li>
            </ul>
          </div>
          
          <div>
            <h3 className="text-lg font-semibold mb-4">Commands</h3>
            <ul className="space-y-2 text-gray-300">
              <li>• /spam-bot: activate</li>
              <li>• /spam-bot: deactivate</li>
              <li>• /spam-bot: status</li>
              <li>• /spam-bot: help</li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-700 mt-8 pt-8 text-center text-gray-300">
          <p>&copy; 2024 SpamShield. Built with React and Python.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
