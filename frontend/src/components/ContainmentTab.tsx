// Action cards for the right rail: where to cut, what to collect next, and the canary check (UI_LAYOUT.md section 2)

import React from 'react';
import { Chokepoint, EvidenceRequest } from '../types/contract';
import { displayName, formatDay, NameSource, prettyIds, wholePercent } from '../utils/names';
import type { AppState } from '../state/reducer';
import Icon from './Icon';

interface ContainmentTabProps {
  chokepoints: Chokepoint[];
  recommendedEvidence: EvidenceRequest[];
  originPinned: boolean;
  canaryHits: string[];
  canaryAlert: AppState['canaryAlert'];
  busy: boolean;
  offlineReplay: boolean;
  onCanaryAlert: (canary_id: string) => void;
  names?: NameSource | null;
}

const CARD = 'shrink-0 scroll-mt-4 rounded-card border border-line bg-surface p-4';

const Title: React.FC<{ icon: 'scissors' | 'search' | 'shield'; children: React.ReactNode }> = ({ icon, children }) => (
  <h2 className="flex items-center gap-2 text-sm font-semibold text-ink">
    <Icon name={icon} className="text-ink-3" />
    {children}
  </h2>
);

export const ContainmentTab: React.FC<ContainmentTabProps> = ({
  chokepoints,
  recommendedEvidence,
  originPinned,
  canaryHits,
  canaryAlert,
  busy,
  offlineReplay,
  onCanaryAlert,
  names,
}) => {
  const cut = chokepoints[0];
  const collect = recommendedEvidence[0];

  return (
    <>
      <section id="card-cut" aria-label="Where to cut" className={CARD}>
        <Title icon="scissors">Where to cut</Title>
        {cut ? (
          <>
            <p className="mt-2 text-sm leading-[21px] text-ink">{prettyIds(cut.action_text, names)}.</p>
            <p className="mt-1 text-sm text-ink-2">
              <span className="text-2xl font-semibold text-ink tabular">{wholePercent(cut.cumulative_coverage)}</span> of likely routes
              stopped
            </p>
            {chokepoints.length > 1 && (
              <details className="mt-2 border-t border-line pt-2">
                <summary className="text-[13px] font-medium text-accent">All {chokepoints.length} cut points</summary>
                <ol className="mt-2 space-y-1.5 text-[13px] text-ink">
                  {chokepoints.map((cp) => (
                    <li key={cp.rank} className="flex justify-between gap-3">
                      <span>{cp.rank}. {prettyIds(cp.action_text, names)}</span>
                      <span className="shrink-0 text-ink-3 tabular">{wholePercent(cp.cumulative_coverage)}</span>
                    </li>
                  ))}
                </ol>
                <p className="mt-2 font-mono text-xs text-ink-3">{chokepoints.map((cp) => `${cp.item_type} ${cp.item_id}`).join(' · ')}</p>
              </details>
            )}
            <p className="mt-2 text-xs text-ink-3">Advisory only. Nothing is changed on live systems.</p>
          </>
        ) : (
          <p className="mt-2 text-sm text-ink-3">No containment recommendation is available for this trace.</p>
        )}
      </section>

      <section id="card-collect" aria-label="What to collect next" className={CARD}>
        <Title icon="search">What to collect next</Title>
        {collect ? (
          <>
            <p className="mt-2 text-sm leading-[21px] text-ink">{prettyIds(collect.request_text, names)}.</p>
            <p className="mt-1.5 text-sm leading-[21px] text-ink-2">
              It settles the step from {displayName(collect.hop_ref.from_loc, names)} to {displayName(collect.hop_ref.to_loc, names)},
              which <span className="font-semibold text-ink tabular">{wholePercent(collect.mass)}</span> of likely routes depend on.
            </p>
            {recommendedEvidence.length > 1 && (
              <details className="mt-2 border-t border-line pt-2">
                <summary className="text-[13px] font-medium text-accent">All {recommendedEvidence.length} requests</summary>
                <ol className="mt-2 space-y-1.5 text-[13px] text-ink">
                  {recommendedEvidence.map((r) => (
                    <li key={r.rank}>{r.rank}. {prettyIds(r.request_text, names)}</li>
                  ))}
                </ol>
                <p className="mt-2 font-mono text-xs text-ink-3">
                  {recommendedEvidence.map((r) => `${r.hop_ref.from_loc}→${r.hop_ref.to_loc} ${r.informativeness.toFixed(4)} bits`).join(' · ')}
                </p>
              </details>
            )}
          </>
        ) : (
          <p className="mt-2 text-sm text-ink-3">No further evidence request for this trace.</p>
        )}
      </section>

      {(originPinned || canaryHits.length > 0) && (
        <section aria-label="Canary check" className={CARD}>
          <Title icon="shield">Canary check</Title>
          {originPinned && (
            <p className="mt-2 flex items-start gap-2 text-sm text-ink">
              <Icon name="check" className="mt-0.5 shrink-0 text-ok" />
              Simulated canary records were found in the leak, so the source export is pinned. The routes are still hypotheses.
            </p>
          )}
          {canaryHits.length > 0 && (
            <button
              type="button"
              onClick={() => onCanaryAlert(canaryHits[0])}
              disabled={busy || offlineReplay}
              className="mt-3 h-10 w-full rounded-ctl border border-line-strong bg-surface px-4 text-sm font-medium text-ink hover:bg-surface-2 disabled:opacity-50"
            >
              Simulate canary alert
            </button>
          )}
          {canaryAlert && (
            <div role="status" className="mt-3 border-t border-line pt-3 text-sm">
              <p className="font-medium text-ok">Simulated canary alert</p>
              <p className="text-ink">{prettyIds(canaryAlert.message, names)}</p>
              <p className="text-xs text-ink-3">{formatDay(canaryAlert.ts)}</p>
            </div>
          )}
        </section>
      )}
    </>
  );
};

export default ContainmentTab;
