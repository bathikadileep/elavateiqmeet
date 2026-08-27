import React from 'react';

export interface AvatarProps {
  src?: string | null;
  name: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  status?: 'online' | 'busy' | 'offline';
  className?: string;
}

export const Avatar: React.FC<AvatarProps> = ({
  src,
  name,
  size = 'md',
  status,
  className = '',
}) => {
  const getInitials = (n: string) => {
    if (!n) return '?';
    const parts = n.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return n.slice(0, 2).toUpperCase();
  };

  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
    xl: 'w-16 h-16 text-xl',
  };

  const statusColorMap = {
    online: 'bg-emerald-500',
    busy: 'bg-rose-500',
    offline: 'bg-gray-500',
  };

  return (
    <div className="relative inline-block select-none">
      <div
        className={`rounded-full flex items-center justify-center font-bold text-white bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-500 ring-2 ring-white/10 shadow-inner overflow-hidden ${sizeClasses[size]} ${className}`}
      >
        {src ? (
          <img src={src} alt={name} className="w-full h-full object-cover" />
        ) : (
          <span>{getInitials(name)}</span>
        )}
      </div>

      {status && (
        <span
          className={`absolute bottom-0 right-0 rounded-full ring-2 ring-[#080911] ${statusColorMap[status]} ${
            size === 'sm' ? 'w-2 h-2' : 'w-3 h-3'
          }`}
        />
      )}
    </div>
  );
};

export default Avatar;
