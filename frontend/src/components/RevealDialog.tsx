// RevealDialog component
// Centred 420px dialog; a reason of at least 8 characters is required (UI_LAYOUT.md section 4)

import React, { useEffect, useRef, useState } from 'react';
import Icon from './Icon';

interface RevealDialogProps {
  open: boolean;
  field: string;
  rowIndex: number;
  currentMaskedValue: string;
  revealedValue: string | null;
  error: string | null;
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
  error,
  busy,
  onConfirm,
  onCancel,
}) => {
  const [reason, setReason] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const dialogRef = useRef<HTMLDivElement | null>(null);

  const shown = Boolean(revealedValue);
  // Also refocus when the value appears: the submit button is gone, and focus must stay inside so Esc still closes
  useEffect(() => {
    const d = dialogRef.current;
    (d?.querySelector('textarea') ?? d?.querySelector('button'))?.focus();
  }, [open, shown]);

  if (!open) return null;

  // Escape closes without submitting; Tab cycles within the dialog
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onCancel();
      return;
    }
    if (e.key !== 'Tab' || !dialogRef.current) return;
    const items = dialogRef.current.querySelectorAll<HTMLElement>('button:not([disabled]), textarea');
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
    if (reason.trim().length < 8) {
      setValidationError('Enter a reason of at least 8 characters.');
      return;
    }
    setValidationError(null);
    onConfirm(reason.trim());
  };

  const len = reason.trim().length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(28,32,48,0.3)] p-4 fade-in">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="reveal-title"
        onKeyDown={handleKeyDown}
        className="w-full max-w-[420px] rounded-card bg-surface p-5 shadow-pop"
      >
        <div className="flex items-center justify-between">
          <h2 id="reveal-title" className="text-base font-semibold text-ink" title="Requires a reason and creates an audit entry.">
            Reveal a masked value
          </h2>
          <button
            type="button"
            onClick={onCancel}
            aria-label="Cancel"
            className="inline-flex h-9 w-9 items-center justify-center rounded-ctl text-ink-3 hover:bg-surface-2 hover:text-ink"
          >
            <Icon name="x" />
          </button>
        </div>

        <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 rounded-ctl bg-surface-2 p-3 text-[13px]">
          <dt className="text-ink-3">Column</dt>
          <dd className="text-ink">{field}</dd>
          <dt className="text-ink-3">Row</dt>
          <dd className="text-ink tabular">{rowIndex + 1}</dd>
          <dt className="text-ink-3">Masked value</dt>
          <dd className="text-ink tabular">{currentMaskedValue}</dd>
        </dl>
        <p className="mt-3 flex gap-2 text-[13px] text-ink-2">
          <Icon name="shield" className="mt-0.5 shrink-0 text-inferred-text" />
          Your reason, the column and the time are written to the audit log. The value itself is not.
        </p>

        {revealedValue ? (
          <>
            <div className="mt-4 rounded-ctl bg-ok-tint p-3 text-center">
              <div className="text-xs text-ok">Revealed value</div>
              <div className="mt-0.5 text-base font-semibold text-ink">{revealedValue}</div>
            </div>
            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={onCancel}
                className="h-10 rounded-ctl border border-line-strong bg-surface px-4 text-sm font-medium text-ink hover:bg-surface-2"
              >
                Close
              </button>
            </div>
          </>
        ) : (
          <form onSubmit={handleSubmit} className="mt-4">
            <div className="flex items-baseline justify-between">
              <label htmlFor="reveal-reason" className="text-[13px] font-medium text-ink">Reason for reveal</label>
              <span className={`text-xs tabular ${len >= 8 ? 'text-ok' : 'text-ink-3'}`} aria-live="polite">
                {len} characters, 8 minimum
              </span>
            </div>
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
              placeholder="For example: verify the customer before notification"
              className="mt-1 w-full resize-none rounded-ctl border border-line-strong bg-surface p-2.5 text-sm text-ink placeholder:text-ink-3"
            />
            {(validationError || error) && (
              <p role="alert" className="mt-1 text-[13px] text-leak">{validationError || error}</p>
            )}
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={onCancel}
                className="h-10 rounded-ctl border border-line-strong bg-surface px-4 text-sm font-medium text-ink hover:bg-surface-2"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={busy || len < 8}
                className="h-10 rounded-ctl bg-accent px-4 text-sm font-semibold text-white hover:bg-accent-hover disabled:opacity-50"
              >
                {busy ? 'Recording reveal...' : 'Reveal'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default RevealDialog;
