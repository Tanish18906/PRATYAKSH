// Chip: 24px, tinted background with matching text (UI_LAYOUT.md section 4)

import React from 'react';

interface StatusBadgeProps {
  label: string;
  kind?: 'simulated' | 'offline' | 'status' | 'danger' | 'success' | 'accent';
  className?: string;
}

const STYLE: Record<NonNullable<StatusBadgeProps['kind']>, string> = {
  simulated: 'bg-inferred-tint text-inferred-text uppercase',
  offline: 'bg-line text-ink uppercase',
  status: 'bg-surface-2 text-ink-2 border border-line',
  danger: 'bg-leak-tint text-leak',
  success: 'bg-ok-tint text-ok',
  accent: 'bg-accent-tint text-accent',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ label, kind = 'simulated', className = '' }) => (
  <span
    className={`inline-flex h-6 shrink-0 items-center whitespace-nowrap rounded-full px-2.5 text-xs font-medium ${STYLE[kind]} ${className}`}
  >
    {label}
  </span>
);

export default StatusBadge;
