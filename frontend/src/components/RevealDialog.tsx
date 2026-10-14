// RevealDialog component
// Follows UI_UX_DESIGN.md section 5.12 and FRONTEND.md section 5

import React, { useState } from 'react';

interface RevealDialogProps {
  open: boolean;
  field: string;
  rowIndex: number;
  currentMaskedValue: string;
  revealedValue: string | null;
  busy: boolean;
  onConfirm: (reason: string) => void;
  onCancel: () => void;
}

export const RevealDialog: React.FC<RevealDialogProps> = ({
  open,
  field,
  rowIndex,
  currentMaskedValue,
  revealedValue,
  busy,
  onConfirm,
  onCancel,
}) => {
  const [reason, setReason] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  if (!open) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (reason.trim().length < 8) {
      setValidationError('Reason must be at least 8 characters long to satisfy privacy compliance.');
      return;
    }
    setValidationError(null);
    onConfirm(reason.trim());
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4">
      <div className="bg-surface-raised border border-border rounded-lg max-w-md w-full p-6 shadow-2xl space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-border">
          <div className="flex items-center space-x-2">
            <span className="text-xl">🔓</span>
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
              Request Forensic Data Reveal
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

        {/* Notice */}
        <div className="p-3 bg-inferred/10 border-l-4 border-inferred rounded text-xs text-text-primary">
          <p className="font-semibold text-inferred mb-0.5">Privacy & Audit Requirement</p>
          <p className="text-text-secondary text-[11px]">
            Unmasking sensitive personal values is strictly audited. Your identity, target field, and stated justification will be permanently written to the audit log.
          </p>
        </div>

        {/* Target Details */}
        <div className="bg-surface p-3 rounded border border-border space-y-1 text-xs font-mono">
          <div className="flex justify-between">
            <span className="text-text-muted">Target Column:</span>
            <span className="text-text-primary font-bold">{field}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Row Index:</span>
            <span className="text-text-primary font-bold">{rowIndex + 1}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-text-muted">Current Masked:</span>
            <span className="text-accent">{currentMaskedValue}</span>
          </div>
        </div>

        {/* Revealed Result (if already completed) */}
        {revealedValue && (
          <div className="bg-success/10 border border-success/30 p-3 rounded text-center space-y-1">
            <span className="text-[10px] text-success font-bold uppercase tracking-wider font-mono">
              Unmasked Value
            </span>
            <div className="text-base font-bold font-mono text-text-primary selection:bg-accent selection:text-background">
              {revealedValue}
            </div>
          </div>
        )}

        {/* Form */}
        {!revealedValue && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="reveal-reason" className="block text-xs font-semibold text-text-primary mb-1">
                Forensic Justification (Min 8 Characters)
              </label>
              <textarea
                id="reveal-reason"
                rows={3}
                value={reason}
                onChange={(e) => {
                  setReason(e.target.value);
                  if (validationError && e.target.value.trim().length >= 8) {
                    setValidationError(null);
                  }
                }}
                placeholder="e.g. Identity verification for customer leak notification..."
                className="w-full bg-surface border border-border rounded p-2 text-xs text-text-primary focus:border-accent focus:outline-none resize-none"
              />
              {validationError && (
                <p className="text-danger text-[11px] mt-1">{validationError}</p>
              )}
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2 border-t border-border">
              <button
                type="button"
                onClick={onCancel}
                className="px-4 py-2 text-xs font-semibold rounded bg-surface hover:bg-surface-hover text-text-secondary border border-border"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={busy || reason.trim().length < 8}
                className="px-4 py-2 text-xs font-bold rounded bg-accent hover:bg-accent/90 text-background shadow-md disabled:opacity-50"
              >
                {busy ? 'Auditing...' : 'Reveal Value'}
              </button>
            </div>
          </form>
        )}

        {revealedValue && (
          <div className="flex justify-end pt-2 border-t border-border">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-xs font-bold rounded bg-surface-raised hover:bg-surface-hover text-text-primary border border-border"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default RevealDialog;
