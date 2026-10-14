// Audit: simple list, newest first (UI_LAYOUT.md section 5)

import React from 'react';
import { AuditEntry } from '../types/contract';
import { formatDay } from '../utils/names';

const ACTION_LABEL: Record<AuditEntry['action'], string> = {
  scenario_generate: 'Scenario generated',
  telegram_export: 'Leaked file exported from the channel',
  trace: 'Trace run',
  reveal: 'Masked value revealed',
  report_export: 'Report exported',
  inject: 'Leak injected',
  canary_alert: 'Canary alert simulated',
  benchmark_run: 'Benchmark run',
};

interface AuditTabProps {
  entries: AuditEntry[];
}

export const AuditTab: React.FC<AuditTabProps> = ({ entries }) => {
  const newestFirst = [...(entries || [])].reverse();

  return (
    <section className="rounded-card border border-line bg-surface">
      <div className="p-4">
        <h2 className="text-sm font-semibold text-ink">Audit log</h2>
        <p className="mt-0.5 text-[13px] text-ink-3">Log is append-only. Revealed values are never written to it.</p>
      </div>

      {newestFirst.length === 0 ? (
        <p className="border-t border-line p-4 text-sm text-ink-3">No audit events recorded yet.</p>
      ) : (
        <ol className="divide-y divide-line border-t border-line">
          {newestFirst.map((e) => (
            <li key={e.id} className="grid grid-cols-[150px_1fr] gap-4 px-4 py-2.5">
              <span className="text-[13px] text-ink-3 tabular">{formatDay(e.ts)}</span>
              <div className="min-w-0">
                <div className="flex flex-wrap items-baseline gap-x-2">
                  <span className={`text-sm font-medium ${e.action === 'reveal' ? 'text-inferred-text' : 'text-ink'}`}>
                    {ACTION_LABEL[e.action] ?? e.action}
                  </span>
                  <span className="text-xs text-ink-3">by {e.who}</span>
                </div>
                {e.reason && <p className="text-[13px] text-ink-2">Reason: {e.reason}</p>}
                {(e.object_id || e.field || e.scenario_id) && (
                  <details className="mt-0.5">
                    <summary className="text-xs text-accent">Details</summary>
                    <p className="font-mono text-xs text-ink-3">
                      {[e.id, e.scenario_id, e.object_id, e.field].filter(Boolean).join(' · ')}
                    </p>
                  </details>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
};

export default AuditTab;
