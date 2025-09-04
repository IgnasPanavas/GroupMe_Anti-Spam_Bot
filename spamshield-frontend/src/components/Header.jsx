import React from 'react';
import { Link } from 'react-router-dom';

const Header = () => {
  const menuItems = [
    { name: 'Learn More', path: '/learn-more' }
  ];

  return (
    <div className="fixed top-0 left-0 right-0 z-50 backdrop-blur-sm border-b border-gray-200" style={{ backgroundColor: 'var(--bg-brownish-gray)', opacity: 0.95 }}>
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex items-center py-4">
          <div className="flex items-center min-w-[120px]">
            <Link to="/" className="text-2xl font-light text-gray-900 hover:theme-hover transition-colors">
              SpamShield
            </Link>
          </div>
          
          {/* Center Navigation Links */}
          <div className="flex-1 flex justify-center">
            <div className="flex items-center space-x-6">
              {menuItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className="text-gray-700 font-light cursor-pointer theme-hover transition-colors"
                >
                  {item.name}
                </Link>
              ))}
            </div>
          </div>

          <div className="min-w-[120px] flex justify-end">
            <Link 
              to="/status" 
              className="text-gray-700 font-light hover:theme-hover transition-colors"
            >
              Status
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;

