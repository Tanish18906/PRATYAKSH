// ScenarioControls component
// Follows UI_UX_DESIGN.md section 4 & FRONTEND.md section 5

import React from 'react';
import { Archetype, ScenarioSummary } from '../types/contract';
import { ControlsState } from '../state/reducer';

interface ScenarioControlsProps {
  scenario: ScenarioSummary | null;
  controls: ControlsState;
  busy: boolean;
  offlineReplay: boolean;
  onControlsChange: (controls: Partial<ControlsState>) => void;
  onGenerate: () => void;
  onTrace: () => void;
  onInject: () => void;
  onBenchmark: () => void;
}

export const ScenarioControls: React.FC<ScenarioControlsProps> = ({
  scenario,
  controls,
  busy,
  offlineReplay,
  onControlsChange,
  onGenerate,
  onTrace,
  onInject,
  onBenchmark,
}) => {
  return (
    <div className="bg-surface px-6 py-3 border-b border-border flex flex-wrap items-center justify-between gap-4">
      {/* Parameter Controls */}
      <div className="flex flex-wrap items-center gap-4">
        {/* Archetype */}
        <div className="flex items-center space-x-2">
          <label htmlFor="archetype-select" className="text-sm text-text-muted font-medium uppercase tracking-wider">
            Archetype
          </label>
          <select
            id="archetype-select"
            value={controls.archetype}
            disabled={busy || offlineReplay}
            onChange={(e) => onControlsChange({ archetype: e.target.value as Archetype })}
            className="bg-surface-raised border border-border text-text-primary text-sm rounded px-2.5 py-1.5 focus:border-accent focus:outline-none disabled:opacity-50 font-mono"
          >
            <option value="A1">A1: Insider Laptop</option>
            <option value="A2">A2: Compromised Key</option>
            <option value="A3">A3: Vendor SFTP</option>
            <option value="A4">A4: Public Bucket</option>
            <option value="A5">A5: Backup Copy</option>
          </select>
        </div>

        {/* Seed */}
        <div className="flex items-center space-x-2">
          <label htmlFor="seed-input" className="text-sm text-text-muted font-medium uppercase tracking-wider">
            Seed
          </label>
          <input
            id="seed-input"
            type="number"
            value={controls.seed}
            disabled={busy || offlineReplay}
            onChange={(e) => onControlsChange({ seed: parseInt(e.target.value, 10) || 0 })}
            className="w-16 bg-surface-raised border border-border text-text-primary text-sm rounded px-2 py-1.5 text-center focus:border-accent focus:outline-none disabled:opacity-50 font-mono"
          />
        </div>

        {/* Log Loss Slider */}
        <div className="flex items-center space-x-2 pl-2 border-l border-border">
          <label htmlFor="loss-slider" className="text-sm text-text-muted font-medium uppercase tracking-wider flex items-center space-x-1">
            <span>Log loss</span>
            <span className="text-accent font-mono font-bold">
              {(controls.log_loss * 100).toFixed(0)}%
            </span>
          </label>
          <input
            id="loss-slider"
            type="range"
            min="0"
            max="0.6"
            step="0.1"
            value={controls.log_loss}
            title="Percentage of simulated event records removed."
            aria-valuetext={`${(controls.log_loss * 100).toFixed(0)}%`}
            disabled={busy || offlineReplay}
            onChange={(e) => onControlsChange({ log_loss: parseFloat(e.target.value) })}
            className="w-24 accent-accent cursor-pointer disabled:opacity-50 h-1.5 bg-surface-raised rounded-lg"
          />
        </div>

        {/* Canary Mode Toggle */}
        <div className="flex items-center space-x-2 pl-2 border-l border-border">
          <label htmlFor="canary-mode" className="text-sm text-text-muted font-medium uppercase tracking-wider">
            Canary mode
          </label>
          <button
            type="button"
            id="canary-mode"
            aria-label="Canary mode"
            aria-pressed={controls.canary_mode}
            title="Adds synthetic identifiers used to trace a leaked export."
            disabled={busy || offlineReplay}
            onClick={() => onControlsChange({ canary_mode: !controls.canary_mode })}
            className={`px-2.5 py-1 text-sm font-mono font-bold rounded border transition-colors ${
              controls.canary_mode
                ? 'bg-accent-dark/60 text-accent border-accent/40'
                : 'bg-surface-raised text-text-muted border-border'
            } disabled:opacity-50`}
          >
            {controls.canary_mode ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Primary Actions */}
      <div className="flex items-center space-x-3">
        <button
          type="button"
          disabled={busy || offlineReplay}
          onClick={onGenerate}
          className="px-3.5 py-1.5 text-sm font-semibold rounded bg-surface-raised hover:bg-surface-hover text-text-primary border border-border transition-colors disabled:opacity-50"
        >
          Generate
        </button>

        <button
          type="button"
          disabled={busy || offlineReplay || !scenario}
          onClick={onTrace}
          className="px-3.5 py-1.5 text-sm font-semibold rounded bg-accent/20 hover:bg-accent/30 text-accent border border-accent/40 transition-colors disabled:opacity-50"
        >
          Trace
        </button>

        <button
          type="button"
          disabled={busy || offlineReplay || !scenario}
          onClick={onInject}
          title="Creates a new synthetic scenario through the selected actor."
          className="px-3 py-1.5 text-sm font-semibold rounded bg-accent/20 hover:bg-accent/30 text-accent border border-accent/40 transition-colors disabled:opacity-50"
        >
          Inject leak (judge picks)
        </button>

        <button
          type="button"
          disabled={busy || offlineReplay}
          onClick={onBenchmark}
          className="px-3 py-1.5 text-sm font-semibold rounded bg-surface-raised hover:bg-surface-hover text-text-secondary border border-border transition-colors disabled:opacity-50"
        >
          Run benchmark
        </button>
      </div>
    </div>
  );
};

export default ScenarioControls;
