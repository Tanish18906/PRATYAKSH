// Right rail: ranked routes, then "Why we think so" for the selected route (UI_LAYOUT.md section 2)

import React from 'react';
import { Evidence, Hypothesis } from '../types/contract';
import { formatNumber } from '../utils/format';
import { displayName, formatDay, NameSource, prettyIds, wholePercent } from '../utils/names';
import { routeStops, whyBullets } from '../utils/answer';

const LIKELIHOOD_TIP = 'A score normalized across candidate paths. It is not a calibrated probability.';

const DOT: Record<Evidence['kind'], string> = {
  fingerprint: 'bg-ok',
  observed: 'bg-observed',
  inferred: 'bg-inferred',
  anomaly: 'bg-leak',
};

const KIND_LABEL: Record<Evidence['kind'], string> = {
  fingerprint: 'Fingerprint',
  observed: 'Observed',
  inferred: 'Inferred',
  anomaly: 'Unusual volume',
};

interface HypothesisPanelProps {
  hypotheses: Hypothesis[];
  selectedPathId: string | null;
  onSelectPath: (pathId: string) => void;
  names?: NameSource | null;
  busy?: boolean;
}

export const HypothesisPanel: React.FC<HypothesisPanelProps> = ({
  hypotheses,
  selectedPathId,
  onSelectPath,
  names,
  busy = false,
}) => {
  if (!hypotheses || hypotheses.length === 0) {
    return (
      <section aria-label="Ranked routes" aria-busy={busy} className="rounded-card border border-line bg-surface p-4">
        {busy ? (
          <div className="space-y-3">
            {[0, 1, 2].map((i) => <div key={i} className="skeleton h-12" />)}
          </div>
        ) : (
          <p className="text-sm text-ink-3">Ranked routes appear here after a trace.</p>
        )}
      </section>
    );
  }

  const rows = hypotheses.slice(0, 3);
  const selected = hypotheses.find((h) => h.path_id === selectedPathId) ?? hypotheses[0];

  // Arrow keys move the selection between rows
  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    e.preventDefault();
    const i = Math.max(0, rows.findIndex((h) => h.path_id === selected.path_id));
    const next = rows[(i + (e.key === 'ArrowDown' ? 1 : rows.length - 1)) % rows.length];
    onSelectPath(next.path_id);
    document.getElementById(`route-row-${next.rank}`)?.focus();
  };

  return (
    <>
      <section aria-label="Ranked routes" className="shrink-0 rounded-card border border-line bg-surface">
        <div className="flex items-baseline justify-between px-4 pb-2 pt-3">
          <h2 className="text-sm font-semibold text-ink">Likely routes</h2>
          <span className="text-xs text-ink-3" title={LIKELIHOOD_TIP}>relative likelihood</span>
        </div>
        <div role="listbox" aria-label="Likely routes" onKeyDown={onKeyDown} className="divide-y divide-line border-t border-line">
          {rows.map((h) => {
            const isSel = h.path_id === selected.path_id;
            // "!" so the left border colour beats the list's divide-line colour
            return (
              <button
                key={h.path_id}
                id={`route-row-${h.rank}`}
                type="button"
                role="option"
                aria-selected={isSel}
                tabIndex={isSel ? 0 : -1}
                onClick={() => onSelectPath(h.path_id)}
                className={`block w-full border-l-[3px] px-4 py-2.5 text-left transition-colors duration-150 ${
                  isSel ? '!border-l-accent bg-accent-tint' : '!border-l-transparent hover:bg-surface-2'
                } ${h.rank === rows.length ? 'rounded-b-card' : ''}`}
              >
                <div className="flex items-baseline justify-between gap-2">
                  <span className="truncate text-sm font-semibold text-ink">
                    <span className="mr-1.5 text-ink-3 tabular">#{h.rank}</span>
                    {h.actors.map((a) => displayName(a, names)).join(' and ')}
                  </span>
                  <span className="shrink-0 text-sm font-semibold text-ink tabular">{wholePercent(h.probability)}</span>
                </div>
                <div className="mt-0.5 truncate text-xs text-ink-3">
                  {routeStops(h).slice(1).map((l) => displayName(l, names)).join(' → ')}
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-line" aria-hidden="true">
                  <div className="h-full rounded-full bg-accent" style={{ width: `${h.probability * 100}%` }} />
                </div>
              </button>
            );
          })}
        </div>
      </section>

      <section aria-label="Why we think so" className="shrink-0 rounded-card border border-line bg-surface p-4">
        <h2 className="text-sm font-semibold text-ink">Why we think so</h2>
        <ul className="mt-3 space-y-3">
          {whyBullets(selected).map((ev, i) => (
            <li key={i} className="flex gap-2.5">
              <span className={`mt-[5px] h-2 w-2 shrink-0 rounded-full ${DOT[ev.kind]}`} aria-hidden="true" />
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between gap-2">
                  <span className={`text-xs font-medium ${ev.kind === 'inferred' ? 'text-inferred-text' : 'text-ink-2'}`}>
                    {KIND_LABEL[ev.kind]}
                  </span>
                  {ev.ts && <span className="shrink-0 text-xs text-ink-3 tabular">{formatDay(ev.ts)}</span>}
                </div>
                <p className="text-sm leading-[21px] text-ink">{prettyIds(ev.text, names)}</p>
              </div>
            </li>
          ))}
        </ul>

        <details className="mt-3 border-t border-line pt-2">
          <summary className="text-[13px] font-medium text-accent">Details</summary>
          <div className="mt-2 space-y-2 font-mono text-xs text-ink-2">
            <p>
              {selected.path_id} · origin {selected.origin_artifact} · actors {selected.actors.join(', ')}
            </p>
            <p>
              score {selected.score} · origin_fit {selected.score_parts.origin_fit} · path_cost {selected.score_parts.path_cost} · anomaly{' '}
              {selected.score_parts.anomaly}
            </p>
            <p className="font-sans text-[13px] text-ink">{selected.summary_text}</p>
            <ol className="space-y-1">
              {selected.hops.map((hop, i) => (
                <li key={i}>
                  {hop.from_loc} → {hop.to_loc} · {hop.kind} · {hop.actor}
                  {hop.event_id && ` · ${hop.event_id}`}
                  {hop.action && ` · ${hop.action}`}
                  {hop.rows !== null && ` · ${formatNumber(hop.rows)} rows`}
                  {hop.est_loss !== null && ` · est. loss ${Math.round(hop.est_loss * 100)}%`}
                  {hop.note && ` · ${hop.note}`}
                </li>
              ))}
            </ol>
            <ul className="space-y-1">
              {selected.evidence.map((ev, i) => (
                <li key={i}>
                  [{ev.kind}] {ev.text}
                  {ev.event_id && ` (${ev.event_id})`}
                </li>
              ))}
            </ul>
          </div>
        </details>
      </section>
    </>
  );
};

export default HypothesisPanel;
