// InjectDialog component
// Follows UI_UX_DESIGN.md section 5.11 and FRONTEND.md section 5

import React, { useState } from 'react';
import { Actor } from '../types/contract';

interface InjectDialogProps {
  open: boolean;
  actors: Actor[];
  busy: boolean;
  onConfirm: (actorId: string) => void;
  onCancel: () => void;
}

export const InjectDialog: React.FC<InjectDialogProps> = ({
  open,
  actors,
  busy,
  onConfirm,
  onCancel,
}) => {
  const [selectedActor, setSelectedActor] = useState<string>('');

  if (!open) return null;

  const validActors = actors.filter((a) => a.kind === 'user');
  const activeActorId = selectedActor || (validActors.length > 0 ? validActors[0].id : '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (activeActorId) {
      onConfirm(activeActorId);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
      <div className="bg-surface-raised border border-border rounded-lg max-w-md w-full p-6 shadow-2xl space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center space-x-2">
            <span className="text-xl">⚖️</span>
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
              Inject Leak Scenario (Judge Driven)
            </h3>
          </div>
          <button
            type="button"
            onClick={onCancel}
            className="text-text-muted hover:text-text-primary text-sm font-bold"
          >
            ✕
          </button>
        </div>

        <p className="text-xs text-text-secondary leading-relaxed">
          Select any user or employee. The simulator will synthesize a new incident where the chosen actor becomes the leaker, complete with new decoys, lossy logs, and Telegram discovery.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="actor-select" className="block text-xs font-semibold text-text-primary mb-1.5">
              Select Perpetrator Actor
            </label>
            <select
              id="actor-select"
              value={activeActorId}
              onChange={(e) => setSelectedActor(e.target.value)}
              className="w-full bg-surface border border-border rounded p-2.5 text-xs text-text-primary focus:border-accent focus:outline-none font-mono"
            >
              {validActors.map((actor) => (
                <option key={actor.id} value={actor.id}>
                  {actor.name} ({actor.role} • {actor.team}) [{actor.id}]
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-border">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-xs font-semibold rounded bg-surface hover:bg-surface-hover text-text-secondary border border-border"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={busy || !activeActorId}
              className="px-4 py-2 text-xs font-bold rounded bg-inferred hover:bg-inferred/90 text-background shadow-md disabled:opacity-50"
            >
              {busy ? 'Injecting...' : 'Synthesize Scenario'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InjectDialog;
