// AuditTab component
// Follows UI_UX_DESIGN.md section 5.10 and FRONTEND.md section 5

import React from 'react';
import { AuditEntry } from '../types/contract';
import { formatUtcTime } from '../utils/format';

interface AuditTabProps {
  entries: AuditEntry[];
}

export const AuditTab: React.FC<AuditTabProps> = ({ entries }) => {
  if (!entries || entries.length === 0) {
    return (
      <div className="p-8 text-center text-text-muted">
        No audit events recorded yet.
      </div>
    );
  }

  const getActionBadge = (action: string) => {
    switch (action) {
      case 'reveal':
        return 'bg-inferred/20 text-inferred border-inferred/40';
      case 'trace':
        return 'bg-accent/20 text-accent border-accent/40';
      case 'inject':
        return 'bg-danger/20 text-danger border-danger/40';
      case 'canary_alert':
        return 'bg-accent-dark text-accent border-accent/50';
      default:
        return 'bg-surface-raised text-text-secondary border-border';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
            Audit log
          </h3>
          <p className="text-xs text-text-muted">
            Append-only record of forensic actions. Unmasked values are never logged to protect investigator integrity.
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface-raised border border-border text-text-secondary">
          {entries.length} Logged Entries
        </span>
      </div>

      <div className="overflow-x-auto rounded border border-border shadow-sm max-h-96">
        <table className="w-full text-xs font-mono text-left bg-surface">
          <thead className="sticky top-0 z-10 bg-surface-raised border-b border-border text-text-muted text-[11px]">
            <tr>
              <th className="p-3 font-semibold">Audit ID</th>
              <th className="p-3 font-semibold">UTC Timestamp</th>
              <th className="p-3 font-semibold">Who</th>
              <th className="p-3 font-semibold">Action</th>
              <th className="p-3 font-semibold">Scenario ID</th>
              <th className="p-3 font-semibold">Object Ref</th>
              <th className="p-3 font-semibold">Field</th>
              <th className="p-3 font-semibold">Justification / Reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {entries.map((entry) => (
              <tr key={entry.id} className="hover:bg-surface-raised/50 transition-colors">
                <td className="p-3 font-bold text-accent">
                  {entry.id}
                </td>
                <td className="p-3 text-text-muted whitespace-nowrap">
                  {formatUtcTime(entry.ts)}
                </td>
                <td className="p-3 text-text-secondary">
                  {entry.who}
                </td>
                <td className="p-3">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getActionBadge(entry.action)}`}>
                    {entry.action}
                  </span>
                </td>
                <td className="p-3 text-text-muted text-[11px]">
                  {entry.scenario_id || '-'}
                </td>
                <td className="p-3 text-text-secondary">
                  {entry.object_id || '-'}
                </td>
                <td className="p-3 text-text-secondary">
                  {entry.field || '-'}
                </td>
                <td className="p-3 text-text-primary italic max-w-xs truncate">
                  {entry.reason ? `"${entry.reason}"` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AuditTab;
