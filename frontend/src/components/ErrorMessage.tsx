// ErrorMessage presentation component
// Follows docs/FRONTEND.md section 5

import React from 'react';

interface ErrorMessageProps {
  message: string | null;
  onDismiss: () => void;
}

export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onDismiss }) => {
  if (!message) return null;

  return (
    <div className="bg-danger/10 border-l-4 border-danger text-text-primary px-4 py-3 rounded mb-4 flex items-center justify-between shadow-md">
      <div className="flex items-center space-x-3">
        <span className="text-danger font-bold text-lg">⚠️</span>
        <div>
          <p className="text-sm font-semibold text-danger">Investigation Alert</p>
          <p className="text-xs text-text-secondary">{message}</p>
        </div>
      </div>
      <button
        onClick={onDismiss}
        className="text-text-muted hover:text-text-primary px-2 py-1 text-sm font-bold"
        aria-label="Dismiss error"
      >
        ✕
      </button>
    </div>
  );
};

export default ErrorMessage;
