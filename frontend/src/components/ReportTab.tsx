// ReportTab component
// Follows UI_UX_DESIGN.md section 5.9 and FRONTEND.md section 15

import React from 'react';

interface ReportTabProps {
  trace_id: string | null;
  reportHtml: string | null;
  busy: boolean;
  offlineReplay: boolean;
  onDownload: () => void;
}

export const ReportTab: React.FC<ReportTabProps> = ({
  trace_id,
  reportHtml,
  busy,
  offlineReplay: _offlineReplay,
  onDownload,
}) => {
  if (!reportHtml) {
    return (
      <div className="p-8 text-center text-text-muted space-y-2">
        <span className="text-3xl block">📄</span>
        <h3 className="text-lg font-semibold text-text-primary">Incident report</h3>
        <p className="text-sm">
          {busy ? 'Loading incident report...' : trace_id
            ? 'The incident report could not be loaded.'
            : 'No trace available. Export the simulated leak and run a trace.'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Action Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
            Incident report
          </h3>
          <p className="text-sm text-text-muted font-mono">
            Trace ID: {trace_id || 'N/A'} • Sandboxed Preview
          </p>
        </div>

        <button
          type="button"
          onClick={onDownload}
          className="px-3.5 py-1.5 rounded bg-accent hover:bg-accent/90 text-background font-bold text-sm flex items-center space-x-1.5 shadow-md transition-colors"
        >
          <span>⬇️</span>
          <span>Download report</span>
        </button>
      </div>

      {/* Sandboxed Iframe Preview */}
      <div className="bg-white rounded-lg border border-border overflow-hidden h-96 shadow-md">
        <iframe
          srcDoc={reportHtml}
          title="Incident Report Preview"
          sandbox=""
          className="w-full h-full border-0"
        />
      </div>

      {/* Mandatory Statutory Disclaimer */}
      <div className="p-3 bg-surface rounded border border-border text-center text-sm text-text-muted font-medium">
        Verify current legal timelines with counsel.
      </div>
    </div>
  );
};

export default ReportTab;
