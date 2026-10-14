// StatusBadge presentation component
// Follows docs/FRONTEND.md section 5

import React from 'react';

interface StatusBadgeProps {
  label: string;
  kind?: 'simulated' | 'offline' | 'status' | 'danger' | 'success';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ label, kind = 'simulated' }) => {
  const getStyle = () => {
    switch (kind) {
      case 'simulated':
        return 'bg-accent-dark/80 text-accent border border-accent/40 font-bold';
      case 'offline':
        return 'bg-danger/20 text-danger border border-danger/40 font-bold';
      case 'status':
        return 'bg-surface-raised text-text-secondary border border-border';
      case 'danger':
        return 'bg-danger/20 text-danger border border-danger/40';
      case 'success':
        return 'bg-success/20 text-success border border-success/40';
      default:
        return 'bg-surface-raised text-text-secondary border border-border';
    }
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs tracking-wider uppercase ${getStyle()}`}>
      {label}
    </span>
  );
};

export default StatusBadge;
