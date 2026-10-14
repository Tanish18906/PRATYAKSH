// InjectDialog component
// Follows UI_UX_DESIGN.md section 5.11 and FRONTEND.md section 5

import React, { useEffect, useRef, useState } from 'react';
import { Actor } from '../types/contract';

interface InjectDialogProps {
  open: boolean;
  actors: Actor[];
  busy: boolean;
  error: string | null;
  onConfirm: (actorId: string) => void;
  onCancel: () => void;
}

export const InjectDialog: React.FC<InjectDialogProps> = ({
  open,
  actors,
  busy,
  error,
  onConfirm,
  onCancel,
}) => {
  const [selectedActor, setSelectedActor] = useState<string>('');
  const dialogRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const previousFocus = document.activeElement as HTMLElement | null;
    dialogRef.current?.querySelector('select')?.focus();
    return () => previousFocus?.focus();
  }, [open]);

  if (!open) return null;

  const activeActorId = actors.some((a) => a.id === selectedActor) ? selectedActor : actors[0]?.id || '';

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onCancel();
      return;
    }
    if (e.key !== 'Tab' || !dialogRef.current) return;
    const items = dialogRef.current.querySelectorAll<HTMLElement>('button:not([disabled]), select:not([disabled])');
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (activeActorId && !busy) {
      onConfirm(activeActorId);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="inject-title"
        onKeyDown={handleKeyDown}
        className="bg-surface-raised border border-border rounded-lg max-w-md w-full p-6 shadow-2xl space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center space-x-2">
            <span className="text-xl">⚖️</span>
            <h3 id="inject-title" className="text-lg font-bold text-text-primary">
              Inject a SIMULATED leak
            </h3>
          </div>
          <button
            type="button"
            onClick={onCancel}
            aria-label="Cancel"
            className="text-text-muted hover:text-text-primary text-sm font-bold"
          >
            ✕
          </button>
        </div>

        <p className="text-base text-text-secondary leading-relaxed">
          A new synthetic leak scenario will be generated using this actor.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="actor-select" className="block text-sm font-semibold text-text-primary mb-1.5">
              Choose an actor
            </label>
            <select
              id="actor-select"
              value={activeActorId}
              disabled={busy}
              onChange={(e) => setSelectedActor(e.target.value)}
              className="w-full bg-surface border border-border rounded p-2.5 text-sm text-text-primary focus:border-accent focus:outline-none font-mono"
            >
              {actors.map((actor) => (
                <option key={actor.id} value={actor.id}>
                  {actor.name} ({actor.role} • {actor.team}) [{actor.id}]
                </option>
              ))}
            </select>
            {!activeActorId && <p className="text-sm text-text-muted">Select an actor to create a simulated leak.</p>}
          </div>

          {error && <p role="alert" className="text-sm text-danger">{error}</p>}

          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-border">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-semibold rounded bg-surface hover:bg-surface-hover text-text-secondary border border-border"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={busy || !activeActorId}
              className="px-4 py-2 text-base font-bold rounded bg-accent hover:bg-accent/90 text-background shadow-md disabled:opacity-50"
            >
              {busy ? 'Generating synthetic scenario...' : 'Inject leak'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InjectDialog;
