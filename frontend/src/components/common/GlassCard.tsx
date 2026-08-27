import React from 'react';

export interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  variant?: 'default' | 'hover' | 'subtle' | 'glow';
  className?: string;
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  variant = 'default',
  className = '',
  ...props
}) => {
  const variantStyles = {
    default: 'glass-card',
    hover: 'glass-card glass-card-hover cursor-pointer',
    subtle: 'bg-white/[0.02] backdrop-blur-md border border-white/[0.05]',
    glow: 'glass-card border-indigo-500/30 shadow-[0_0_30px_rgba(99,102,241,0.15)]',
  };

  return (
    <div
      className={`rounded-2xl p-6 transition-all duration-300 ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default GlassCard;
