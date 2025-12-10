import React from 'react';

interface HeaderProps {
  title?: string;
  subtitle?: string;
  showLogo?: boolean;
}

const Header: React.FC<HeaderProps> = ({ 
  title = 'Financial Close & Reporting Platform', 
  subtitle,
  showLogo = true 
}) => {
  return (
    <div className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between relative">
          {showLogo && (
            <img 
              src="/logo.png" 
              alt="Plainflow Logo" 
              className="h-12 w-auto"
            />
          )}
          <div className="absolute left-1/2 transform -translate-x-1/2">
            <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
            {subtitle && (
              <p className="text-sm text-gray-600 mt-1 text-center">{subtitle}</p>
            )}
          </div>
          <div className="w-12"></div> {/* Spacer for balance */}
        </div>
      </div>
    </div>
  );
};

export default Header;
