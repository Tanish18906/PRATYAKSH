import React from 'react';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col">
      {/* Top Header */}
      <header className="border-b border-border bg-surface px-6 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-xl font-bold tracking-wider text-text-primary">
            PUGMARK
          </h1>
          <span className="px-2.5 py-0.5 rounded text-xs font-semibold bg-accent-dark text-accent border border-accent/30 tracking-wider">
            SIMULATED
          </span>
        </div>
        <div className="flex items-center space-x-6 text-sm text-text-secondary">
          <div className="flex items-center space-x-2">
            <span className="h-2 w-2 rounded-full bg-success"></span>
            <span>SYSTEM READY</span>
          </div>
          <span className="font-mono text-text-muted">UTC</span>
        </div>
      </header>

      {/* Main Shell Workspace */}
      <main className="flex-1 p-6 flex flex-col items-center justify-center text-center">
        <div className="max-w-md p-8 rounded-lg bg-surface border border-border">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-surface-raised flex items-center justify-center border border-border">
            <span className="text-accent text-2xl font-bold">P</span>
          </div>
          <h2 className="text-lg font-semibold text-text-primary mb-2">
            PUGMARK Forensic Investigation Shell
          </h2>
          <p className="text-sm text-text-secondary mb-4">
            Phase 0 scaffold loaded. Ready for investigation workspace, Cytoscape graph, and mock Telegram discovery.
          </p>
          <div className="inline-flex items-center px-3 py-1 rounded bg-surface-raised text-xs text-text-muted font-mono border border-border">
            Contract v1.0 • Offline Ready
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
