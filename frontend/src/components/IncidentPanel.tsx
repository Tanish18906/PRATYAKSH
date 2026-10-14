// Left rail: the Telegram post, then the incident facts (UI_LAYOUT.md section 2)

import React from 'react';
import { ScenarioSummary, LeakSample } from '../types/contract';
import TelegramChat from './TelegramChat';
import { formatNumber } from '../utils/format';
import { formatDay } from '../utils/names';
import Icon from './Icon';

interface IncidentPanelProps {
  scenario: ScenarioSummary | null;
  leakSample: LeakSample | null;
  hasTraced: boolean;
  offlineReplay: boolean;
  busy: boolean;
  onReveal: (rowIndex: number, field: string, currentMaskedValue: string) => void;
  onExportAndTrace: (messageId: number) => void;
}

const Fact: React.FC<{ label: string; value: React.ReactNode; wide?: boolean }> = ({ label, value, wide }) => (
  <div className={wide ? 'col-span-2' : undefined}>
    <dt className="text-xs text-ink-3">{label}</dt>
    <dd className="mt-0.5 text-base font-semibold text-ink tabular">{value}</dd>
  </div>
);

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
      <div aria-busy="true" className="space-y-3 rounded-card border border-line bg-surface p-4">
        <div className="skeleton h-5 w-2/3" />
        <div className="skeleton h-16" />
        <div className="skeleton h-10" />
      </div>
    );
  }

  const sample = leakSample || scenario.leak_sample;

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <div className="flex max-h-[55%] min-h-0 flex-col">
        <TelegramChat
          discovery={scenario.discovery}
          scenario_id={scenario.id}
          busy={busy}
          offlineReplay={offlineReplay}
          onExportAndTrace={onExportAndTrace}
        />
      </div>

      {sample && (
        <section aria-label="Incident facts" className="min-h-0 shrink overflow-y-auto rounded-card border border-line bg-surface p-4">
          <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
            <Fact label="Found" value={formatDay(sample.found_ts)} wide />
            <Fact label="Leaked records" value={formatNumber(sample.row_count)} />
            <Fact label="Columns" value={sample.columns.length} />
            <Fact label="Company" value={scenario.company} wide />
          </dl>

          <details className="mt-4 border-t border-line pt-3">
            <summary className="text-[13px] font-medium text-accent">Masked sample ({sample.masked_preview.length} rows)</summary>
            <p className="mt-2 flex items-center gap-1.5 text-xs text-ink-3">
              <Icon name="shield" />
              {offlineReplay
                ? 'Reveal is unavailable during offline replay.'
                : 'Values are masked. Reveal needs a reason and writes an audit entry.'}
            </p>
            <div className="mt-2 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-line text-ink-3">
                    {sample.columns.map((c) => (
                      <th key={c} className="px-1 py-1.5 font-medium">{c}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {sample.masked_preview.map((row, rIdx) => (
                    <tr key={rIdx}>
                      {sample.columns.map((col) => {
                        const val = row[col] || '';
                        return (
                          <td key={col} className="px-0.5 py-0.5">
                            <button
                              type="button"
                              aria-label={`Reveal ${col}, row ${rIdx + 1}`}
                              disabled={busy || offlineReplay}
                              onClick={() => onReveal(rIdx, col, val)}
                              className="min-h-[28px] max-w-[120px] truncate rounded px-1 text-left text-ink-2 tabular hover:bg-accent-tint hover:text-accent disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-ink-2"
                              title={offlineReplay ? 'Reveal unavailable during offline replay' : 'Requires a reason and creates an audit entry.'}
                            >
                              {val}
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </section>
      )}
    </div>
  );
};

export default IncidentPanel;
