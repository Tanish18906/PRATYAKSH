// Report: paper-style preview on the left, Download and Copy summary on the right (UI_LAYOUT.md section 5)

import React, { useState } from 'react';
import Icon from './Icon';

interface ReportTabProps {
  trace_id: string | null;
  reportHtml: string | null;
  busy: boolean;
  offlineReplay: boolean;
  onDownload: () => void;
  summary?: string | null;
}

export const ReportTab: React.FC<ReportTabProps> = ({
  trace_id,
  reportHtml,
  busy,
  offlineReplay: _offlineReplay,
  onDownload,
  summary,
}) => {
  const [copied, setCopied] = useState(false);

  if (!reportHtml) {
    return (
      <div className="rounded-card border border-line bg-surface p-8 text-center">
        <Icon name="document" size={20} className="mx-auto text-ink-3" />
        <p className="mt-2 text-sm text-ink-2">
          {busy
            ? 'Loading incident report...'
            : trace_id
              ? 'The incident report could not be loaded.'
              : 'The incident report appears here after Export and trace.'}
        </p>
      </div>
    );
  }

  const copy = async () => {
    if (!summary) return;
    try {
      await navigator.clipboard.writeText(summary);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,1fr)_260px]">
      <div className="h-[calc(100vh-140px)] min-h-[420px] overflow-hidden rounded-card border border-line bg-surface">
        <iframe srcDoc={reportHtml} title="Incident report preview" sandbox="" className="h-full w-full border-0" />
      </div>

      <aside className="space-y-3">
        <div className="rounded-card border border-line bg-surface p-4">
          <h2 className="text-sm font-semibold text-ink">Incident report</h2>
          <p className="mt-0.5 text-[13px] text-ink-3">A ranked set of hypotheses for a human investigator.</p>
          <div className="mt-3 space-y-2">
            <button
              type="button"
              onClick={onDownload}
              className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-ctl bg-accent px-4 text-sm font-semibold text-white hover:bg-accent-hover"
            >
              <Icon name="download" /> Download
            </button>
            <button
              type="button"
              onClick={copy}
              disabled={!summary}
              className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-ctl border border-line-strong bg-surface px-4 text-sm font-medium text-ink hover:bg-surface-2 disabled:opacity-50"
            >
              <Icon name={copied ? 'check' : 'copy'} /> {copied ? 'Copied' : 'Copy summary'}
            </button>
          </div>
        </div>
        <p className="rounded-card border border-line bg-surface p-4 text-[13px] text-ink-2">Verify current legal timelines with counsel.</p>
        <details className="px-1 text-xs text-ink-3">
          <summary className="text-[13px] font-medium text-accent">Details</summary>
          <p className="mt-1 font-mono">{trace_id} · sandboxed preview</p>
        </details>
      </aside>
    </div>
  );
};

export default ReportTab;
