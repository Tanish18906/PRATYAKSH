// InjectDialog component
// Follows UI_UX_DESIGN.md section 5.11 and FRONTEND.md section 5

import React, { useEffect, useRef, useState } from 'react';
import { Actor } from '../types/contract';
import Icon from './Icon';

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(28,32,48,0.3)] p-4 fade-in">
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="inject-title"
        onKeyDown={handleKeyDown}
        className="w-full max-w-[420px] rounded-card bg-surface p-5 shadow-pop">
        <div className="flex items-center justify-between">
          <h2 id="inject-title" className="text-base font-semibold text-ink">Inject a simulated leak</h2>
          <button
            type="button"
            onClick={onCancel}
            aria-label="Cancel"
            className="inline-flex h-9 w-9 items-center justify-center rounded-ctl text-ink-3 hover:bg-surface-2 hover:text-ink"
          >
            <Icon name="x" />
          </button>
        </div>
        <p className="mt-1 text-[13px] text-ink-2">Pick anyone. A new synthetic scenario leaks through them, and it traces again.</p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label htmlFor="actor-select" className="block text-[13px] font-medium text-ink">Actor</label>
            <select
              id="actor-select"
              value={activeActorId}
              disabled={busy}
              onChange={(e) => setSelectedActor(e.target.value)}
              className="mt-1 h-10 w-full rounded-ctl border border-line-strong bg-surface px-3 text-sm text-ink"
            >
              {actors.map((actor) => (
                <option key={actor.id} value={actor.id}>
                  {actor.name} ({actor.role}, {actor.team})
                </option>
              ))}
            </select>
            {!activeActorId && <p className="mt-1 text-[13px] text-ink-3">Select an actor to create a simulated leak.</p>}
          </div>

          {error && <p role="alert" className="text-[13px] text-leak">{error}</p>}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onCancel}
              className="h-10 rounded-ctl border border-line-strong bg-surface px-4 text-sm font-medium text-ink hover:bg-surface-2"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={busy || !activeActorId}
              className="h-10 rounded-ctl bg-accent px-4 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-50"
            >
              {busy ? 'Generating scenario...' : 'Inject leak'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InjectDialog;
