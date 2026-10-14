// IncidentPanel component
// Follows UI_UX_DESIGN.md section 5.3 and FRONTEND.md section 5

import React from 'react';
import { ScenarioSummary, LeakSample } from '../types/contract';
import TelegramChat from './TelegramChat';
import { formatUtcTime, formatNumber } from '../utils/format';

interface IncidentPanelProps {
  scenario: ScenarioSummary | null;
  leakSample: LeakSample | null;
  hasTraced: boolean;
  offlineReplay: boolean;
  busy: boolean;
  onReveal: (rowIndex: number, field: string, currentMaskedValue: string) => void;
  onExportAndTrace: (messageId: number) => void;
}

export const IncidentPanel: React.FC<IncidentPanelProps> = ({
  scenario,
  leakSample,
  hasTraced: _hasTraced,
  offlineReplay,
  busy,
  onReveal,
  onExportAndTrace,
}) => {
  if (!scenario) {
    return (
      <div className="bg-surface rounded-lg border border-border p-6 text-center text-text-muted">
        Loading incident context...
      </div>
    );
  }

  const sample = leakSample || scenario.leak_sample;

  return (
    <div className="flex flex-col space-y-4">
      {/* Incident Header Card */}
      <div className="bg-surface rounded-lg border border-border p-4 shadow-sm">
        <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wider text-text-primary flex items-center space-x-2">
              <span>Incident Investigation</span>
            </h2>
            <p className="text-xs text-text-muted">{scenario.company} • Case #{scenario.id}</p>
          </div>
          <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-accent-dark text-accent border border-accent/40">
            SIMULATED
          </span>
        </div>

        {/* Telegram Mock Discovery */}
        <div className="mb-4">
          <TelegramChat
            discovery={scenario.discovery}
            scenario_id={scenario.id}
            busy={busy}
            offlineReplay={offlineReplay}
            onExportAndTrace={onExportAndTrace}
          />
        </div>

        {/* Leak Artifact Properties */}
        {sample && (
          <div className="space-y-3 pt-2">
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-surface-raised p-2 rounded border border-border">
                <span className="text-text-muted block text-[10px] uppercase font-mono">Found Timestamp</span>
                <span className="font-mono text-text-primary text-[11px]">
                  {formatUtcTime(sample.found_ts)}
                </span>
              </div>

              <div className="bg-surface-raised p-2 rounded border border-border">
                <span className="text-text-muted block text-[10px] uppercase font-mono">Leaked Records</span>
                <span className="font-mono font-bold text-accent text-sm">
                  {formatNumber(sample.row_count)} rows
                </span>
              </div>
            </div>

            <div className="bg-surface-raised p-2 rounded border border-border text-xs">
              <span className="text-text-muted block text-[10px] uppercase font-mono mb-1">
                Newest Record Watermark
              </span>
              <span className="font-mono text-inferred text-xs font-semibold">
                {formatUtcTime(sample.newest_record_ts)}
              </span>
              <span className="text-[10px] text-text-muted block mt-0.5">
                (Exports predating this watermark are logically excluded)
              </span>
            </div>

            {/* Columns Chips */}
            <div>
              <span className="text-text-muted block text-[10px] uppercase font-mono mb-1.5">
                Observed Columns in Sample
              </span>
              <div className="flex flex-wrap gap-1.5">
                {sample.columns.map((col) => (
                  <span
                    key={col}
                    className="px-2 py-0.5 rounded bg-surface-raised border border-border text-xs font-mono text-text-secondary"
                  >
                    {col}
                  </span>
                ))}
              </div>
            </div>

            {/* Format Fingerprint Chips */}
            <div>
              <span className="text-text-muted block text-[10px] uppercase font-mono mb-1.5">
                Format Fingerprint
              </span>
              <div className="grid grid-cols-2 gap-1.5 text-[11px] font-mono">
                <div className="bg-surface-raised px-2 py-1 rounded border border-border flex justify-between">
                  <span className="text-text-muted">Delimiter:</span>
                  <span className="text-accent">{sample.format_profile.delimiter === ',' ? 'comma (,)' : sample.format_profile.delimiter}</span>
                </div>
                <div className="bg-surface-raised px-2 py-1 rounded border border-border flex justify-between">
                  <span className="text-text-muted">Quoting:</span>
                  <span className="text-accent">{sample.format_profile.quoting}</span>
                </div>
                <div className="bg-surface-raised px-2 py-1 rounded border border-border flex justify-between">
                  <span className="text-text-muted">Line Ending:</span>
                  <span className="text-accent">{sample.format_profile.line_ending}</span>
                </div>
                <div className="bg-surface-raised px-2 py-1 rounded border border-border flex justify-between">
                  <span className="text-text-muted">Encoding:</span>
                  <span className="text-accent">{sample.format_profile.encoding}</span>
                </div>
              </div>
            </div>

            {/* Masked Preview Table */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-text-muted block text-[10px] uppercase font-mono">
                  Masked Preview (Max 5 Rows)
                </span>
                <span className="text-[10px] text-text-muted italic">Click any cell to request reveal</span>
              </div>

              <div className="overflow-x-auto rounded border border-border">
                <table className="w-full text-[11px] font-mono text-left bg-surface-raised">
                  <thead>
                    <tr className="border-b border-border text-text-muted text-[10px] bg-surface">
                      {sample.columns.map((c) => (
                        <th key={c} className="p-2 font-semibold">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {sample.masked_preview.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-surface-hover/50">
                        {sample.columns.map((col) => {
                          const val = row[col] || '';
                          return (
                            <td
                              key={col}
                              onClick={() => {
                                if (!offlineReplay) {
                                  onReveal(rIdx, col, val);
                                }
                              }}
                              className={`p-2 truncate max-w-[120px] transition-colors ${
                                offlineReplay
                                  ? 'cursor-not-allowed text-text-secondary'
                                  : 'cursor-pointer hover:text-accent hover:underline text-text-primary'
                              }`}
                              title={offlineReplay ? 'Reveal unavailable during offline replay' : 'Click to request reveal with audit reason'}
                            >
                              {val}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IncidentPanel;
