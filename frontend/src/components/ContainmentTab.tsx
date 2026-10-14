// ContainmentTab component
// Follows UI_UX_DESIGN.md section 5.7 and FRONTEND.md section 5

import React from 'react';
import { Chokepoint, EvidenceRequest } from '../types/contract';
import { formatProbability, formatUtcTime } from '../utils/format';
import type { AppState } from '../state/reducer';

interface ContainmentTabProps {
  chokepoints: Chokepoint[];
  recommendedEvidence: EvidenceRequest[];
  originPinned: boolean;
  canaryHits: string[];
  canaryAlert: AppState['canaryAlert'];
  busy: boolean;
  offlineReplay: boolean;
  onCanaryAlert: (canary_id: string) => void;
}

export const ContainmentTab: React.FC<ContainmentTabProps> = ({
  chokepoints,
  recommendedEvidence,
  originPinned,
  canaryHits,
  canaryAlert,
  busy,
  offlineReplay,
  onCanaryAlert,
}) => {
  return (
    <div className="space-y-6">
      {/* Canary Status Banner */}
      {originPinned && (
        <div className="p-4 rounded-lg bg-accent-dark/30 border border-accent/40 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <span className="text-xl">🎯</span>
            <div>
              <span className="text-sm font-bold font-mono text-accent uppercase">
                Canary Pinned Origin
              </span>
              <p className="text-sm text-text-primary">
                SIMULATED canary match: the backend pinned the origin export. Custody paths remain hypotheses.
              </p>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded text-sm font-bold bg-accent text-background font-mono">
            PINNED
          </span>
        </div>
      )}

      {/* Canary Simulation Action (if canaries available) */}
      {canaryHits.length > 0 && (
        <div className="p-3 bg-surface rounded border border-border flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm text-text-secondary">
            SIMULATED canary hits: <span className="text-accent font-mono">{canaryHits.join(', ')}</span>
          </div>
          <button
            type="button"
            onClick={() => onCanaryAlert(canaryHits[0])}
            disabled={busy || offlineReplay}
            className="px-3 py-2 bg-accent/20 hover:bg-accent/30 text-accent border border-accent/40 rounded text-base font-semibold disabled:opacity-50"
          >
            Simulate canary alert
          </button>
        </div>
      )}

      {canaryAlert && (
        <div role="status" className="p-4 rounded border border-accent/40 bg-accent-dark/30 text-base">
          <p className="font-semibold">SIMULATED canary alert</p>
          <p>{canaryAlert.message}</p>
          <p className="text-sm text-text-secondary">
            {canaryAlert.canary_id} · {canaryAlert.export_id} · {formatUtcTime(canaryAlert.ts)}
          </p>
        </div>
      )}

      {/* Chokepoint Recommendations Card */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-bold text-text-primary">
              Chokepoint recommendations
            </h3>
            <p className="text-sm text-text-muted">
              Suggested containment actions covering plausible leak paths.
            </p>
          </div>
          <span className="text-sm text-text-muted italic">
            Advisory recommendations. No changes made to live systems.
          </span>
        </div>

        {chokepoints.length === 0 ? (
          <div className="p-6 rounded bg-surface border border-border text-center text-text-muted text-sm">
            No containment recommendation is available for this trace.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {chokepoints.map((cp) => (
              <div
                key={cp.rank}
                className="p-4 rounded-lg bg-surface border border-border flex flex-col justify-between space-y-3 shadow-sm hover:border-accent/40 transition-colors"
              >
                <div>
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
                    <span className="w-5 h-5 rounded-full bg-accent text-background text-sm font-bold font-mono flex items-center justify-center">
                      {cp.rank}
                    </span>
                    <span className="text-sm font-mono font-bold text-accent">
                      Cumulative coverage: {formatProbability(cp.cumulative_coverage)}
                    </span>
                  </div>

                  <h4 className="text-base font-semibold text-text-primary mb-1">
                    {cp.action_text}
                  </h4>
                  <div className="text-sm font-mono text-text-muted">
                    Target: <span className="text-text-secondary">{cp.item_id}</span> ({cp.item_type})
                  </div>
                </div>

                <div className="pt-2 border-t border-border flex flex-wrap items-center justify-between gap-3 text-sm text-text-muted">
                  <span>Single-action marginal:</span>
                  <span className="font-mono font-bold text-text-primary">
                    {formatProbability(cp.marginal)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Evidence to Collect Card */}
      {recommendedEvidence.length > 0 && (
        <div className="space-y-3 pt-4 border-t border-border">
          <div>
            <h3 className="text-lg font-bold text-text-primary">
              Evidence to collect
            </h3>
            <p className="text-sm text-text-muted">
              Recover these logs to help distinguish the candidate paths.
            </p>
          </div>

          <div className="space-y-2">
            {recommendedEvidence.map((evReq, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-lg bg-surface border border-inferred/40 flex items-start space-x-3 shadow-sm"
              >
                <span className="text-lg text-inferred">📋</span>
                <div className="flex-1 text-sm">
                  <div className="font-semibold text-text-primary text-sm mb-1">
                    {evReq.request_text}
                  </div>
                  <div className="text-text-muted font-mono text-sm flex flex-wrap items-center gap-3">
                    <span>
                      Hop: {evReq.hop_ref.from_loc} → {evReq.hop_ref.to_loc}
                    </span>
                    <span>•</span>
                    <span>Relative path mass: {formatProbability(evReq.mass)}</span>
                    <span>•</span>
                    <span>Informativeness: {evReq.informativeness.toFixed(4)} bits</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ContainmentTab;
