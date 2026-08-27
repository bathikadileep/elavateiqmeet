import React from 'react';

export interface BrandLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  className?: string;
}

const sizeMap = {
  sm: 'w-8 h-8 rounded-lg',
  md: 'w-10 h-10 rounded-xl',
  lg: 'w-12 h-12 rounded-2xl',
  xl: 'w-16 h-16 rounded-2xl',
};

export const BrandLogo: React.FC<BrandLogoProps> = ({
  size = 'md',
  showText = false,
  className = '',
}) => {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div
        className={`${sizeMap[size]} overflow-hidden shadow-lg shadow-cyan-500/10 border border-white/10 ring-1 ring-white/5 shrink-0 transition-transform duration-200 group-hover:scale-105`}
      >
        <img
          src="/logo.jpg"
          alt="ElevateIQ Meet Logo"
          className="w-full h-full object-cover"
        />
      </div>

      {showText && (
        <div className="flex flex-col">
          <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-gray-100 to-orange-200 bg-clip-text text-transparent">
            Elevate<span className="text-[#F26522]">IQ</span>{' '}
            <span className="text-[#00AEEF]">MEET</span>
          </span>
          <span className="text-[10px] tracking-widest text-cyan-400 font-semibold uppercase -mt-0.5">
            Video Collaboration
          </span>
        </div>
      )}
    </div>
  );
};

export default BrandLogo;
