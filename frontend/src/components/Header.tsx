// Header component
// Follows UI_UX_DESIGN.md section 4 and FRONTEND.md section 5

import React from 'react';
import StatusBadge from './StatusBadge';

interface HeaderProps {
  offlineReplay: boolean;
  simulated?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ offlineReplay, simulated = true }) => {
  return (
    <header className="border-b border-border bg-surface px-6 py-3 flex items-center justify-between select-none">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded bg-surface-raised border border-border flex items-center justify-center">
            <span className="text-accent font-bold text-sm">P</span>
          </div>
          <h1 className="text-xl font-bold tracking-wider text-text-primary">
            PUGMARK
          </h1>
        </div>

        <span className="text-xs text-text-muted hidden sm:inline">|</span>
        <span className="text-xs text-text-muted hidden sm:inline">DATA LEAK FORENSICS</span>

        {simulated && <StatusBadge label="SIMULATED" kind="simulated" />}
        {offlineReplay && <StatusBadge label="OFFLINE REPLAY" kind="offline" />}
      </div>

      <div className="flex items-center space-x-6 text-sm text-text-secondary">
        <div className="flex items-center space-x-2">
          <span className={`h-2.5 w-2.5 rounded-full ${offlineReplay ? 'bg-inferred' : 'bg-success animate-pulse'}`}></span>
          <span className="text-xs font-medium">
            {offlineReplay ? 'OFFLINE REPLAY MODE' : 'BACKEND ONLINE'}
          </span>
        </div>
        <div className="border-l border-border pl-4 flex items-center space-x-2">
          <span className="text-xs font-mono text-text-muted">TIME ZONE</span>
          <span className="text-xs font-mono font-bold text-text-primary px-1.5 py-0.5 rounded bg-surface-raised border border-border">
            UTC
          </span>
        </div>
      </div>
    </header>
  );
};

export default Header;
