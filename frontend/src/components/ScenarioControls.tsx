// Scenario drawer: all simulator controls, 360px from the right, closes on Esc and overlay click (UI_LAYOUT.md section 4)

import React, { useEffect, useRef } from 'react';
import { Archetype, ScenarioSummary } from '../types/contract';
import { ControlsState } from '../state/reducer';
import Icon from './Icon';

interface ScenarioControlsProps {
  open: boolean;
  onClose: () => void;
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

const LOSS_LEVELS = [0, 0.2, 0.4, 0.6];
const FIELD = 'h-10 w-full rounded-ctl border border-line-strong bg-surface px-3 text-sm text-ink disabled:opacity-50';
const PRIMARY = 'h-10 w-full rounded-ctl bg-accent px-4 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-50';
const SECONDARY = 'h-10 w-full rounded-ctl border border-line-strong bg-surface px-4 text-sm font-medium text-ink hover:bg-surface-2 disabled:opacity-50';

export const ScenarioControls: React.FC<ScenarioControlsProps> = ({
  open,
  onClose,
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
  const panelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (open) panelRef.current?.querySelector<HTMLElement>('button, select')?.focus();
  }, [open]);

  if (!open) return null;

  const locked = busy || offlineReplay;
  const run = (fn: () => void) => () => {
    onClose();
    fn();
  };

  // Esc closes; Tab stays inside the drawer
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
      return;
    }
    if (e.key !== 'Tab' || !panelRef.current) return;
    const items = panelRef.current.querySelectorAll<HTMLElement>(
      'button:not([disabled]), select:not([disabled]), input:not([disabled])'
    );
    const first = items[0];
    const last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };

  return (
    <div className="fixed inset-0 z-40" onKeyDown={onKeyDown}>
      <div className="absolute inset-0 bg-[rgba(28,32,48,0.3)] fade-in" onClick={onClose} aria-hidden="true" />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="scenario-title"
        className="slide-in absolute right-0 top-0 flex h-full w-[360px] max-w-full flex-col bg-surface shadow-pop"
      >
        <div className="flex h-14 items-center justify-between border-b border-line px-4">
          <h2 id="scenario-title" className="text-sm font-semibold text-ink">Scenario</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close scenario drawer"
            className="inline-flex h-9 w-9 items-center justify-center rounded-ctl text-ink-3 hover:bg-surface-2 hover:text-ink"
          >
            <Icon name="x" />
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto p-4">
          {offlineReplay && (
            <p className="rounded-ctl bg-surface-2 p-3 text-[13px] text-ink-2">
              The backend is not reachable, so controls are locked and the bundled demo is shown.
            </p>
          )}

          <div className="space-y-1.5">
            <label htmlFor="archetype-select" className="block text-[13px] text-ink-2">Archetype</label>
            <select
              id="archetype-select"
              value={controls.archetype}
              disabled={locked}
              onChange={(e) => onControlsChange({ archetype: e.target.value as Archetype })}
              className={FIELD}
            >
              <option value="A1">A1: Insider laptop</option>
              <option value="A2">A2: Compromised key</option>
              <option value="A3">A3: Vendor SFTP</option>
              <option value="A4">A4: Public bucket</option>
              <option value="A5">A5: Backup copy</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="seed-input" className="block text-[13px] text-ink-2">Seed</label>
            <input
              id="seed-input"
              type="number"
              value={controls.seed}
              disabled={locked}
              onChange={(e) => onControlsChange({ seed: parseInt(e.target.value, 10) || 0 })}
              className={`${FIELD} tabular`}
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="loss-slider" className="flex justify-between text-[13px] text-ink-2">
              <span>Log loss</span>
              <span className="font-semibold text-ink tabular">{Math.round(controls.log_loss * 100)}%</span>
            </label>
            <input
              id="loss-slider"
              type="range"
              min="0"
              max="0.6"
              step="0.2"
              value={controls.log_loss}
              title="Percentage of simulated event records removed."
              aria-valuetext={`${Math.round(controls.log_loss * 100)}%`}
              disabled={locked}
              onChange={(e) => onControlsChange({ log_loss: parseFloat(e.target.value) })}
              className="h-9 w-full cursor-pointer accent-[var(--accent)] disabled:opacity-50"
            />
            <div className="flex justify-between text-xs text-ink-3 tabular" aria-hidden="true">
              {LOSS_LEVELS.map((l) => <span key={l}>{l * 100}%</span>)}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span id="canary-label" className="text-[13px] text-ink-2" title="Adds synthetic identifiers used to trace a leaked export.">
              Canary mode
            </span>
            <button
              type="button"
              id="canary-mode"
              role="switch"
              aria-checked={controls.canary_mode}
              aria-labelledby="canary-label"
              disabled={locked}
              onClick={() => onControlsChange({ canary_mode: !controls.canary_mode })}
              className={`relative h-6 w-11 rounded-full transition-colors duration-150 disabled:opacity-50 ${
                controls.canary_mode ? 'bg-accent' : 'bg-line-strong'
              }`}
            >
              <span
                className={`absolute left-0 top-0.5 h-5 w-5 rounded-full bg-surface transition-transform duration-150 ${
                  controls.canary_mode ? 'translate-x-[22px]' : 'translate-x-0.5'
                }`}
              />
            </button>
          </div>

          <div className="space-y-2 border-t border-line pt-5">
            <button type="button" disabled={locked} onClick={run(onGenerate)} className={PRIMARY}>
              Generate
            </button>
            <button
              type="button"
              disabled={locked || !scenario}
              onClick={run(onInject)}
              title="Creates a new synthetic scenario through the selected actor."
              className={SECONDARY}
            >
              Inject leak
            </button>
            <button type="button" disabled={locked || !scenario} onClick={run(onTrace)} className={SECONDARY}>
              Trace again
            </button>
            <button type="button" disabled={locked} onClick={run(onBenchmark)} className={SECONDARY}>
              Run benchmark
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScenarioControls;
