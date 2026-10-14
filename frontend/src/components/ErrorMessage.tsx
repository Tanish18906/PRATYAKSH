// Inline, calm error: one line and a dismiss button (UX_FLOW.md section 4)

import React from 'react';
import Icon from './Icon';

interface ErrorMessageProps {
  message: string | null;
  onDismiss: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onDismiss }) => {
  if (!message) return null;

  return (
    <div role="alert" className="flex shrink-0 items-center gap-2 rounded-card border border-line bg-leak-tint px-3 py-1.5 text-[13px] text-ink">
      <Icon name="alert" className="shrink-0 text-leak" />
      <span className="min-w-0 flex-1 truncate">{message}</span>
      <button
        type="button"
        onClick={onDismiss}
        className="h-8 shrink-0 rounded-ctl px-2 text-[13px] font-medium text-accent hover:underline"
      >
        Dismiss
      </button>
    </div>
  );
};

export default ErrorMessage;
