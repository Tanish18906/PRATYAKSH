// ContainmentTab component
// Follows UI_UX_DESIGN.md section 5.7 and FRONTEND.md section 5

import React from 'react';
import { Chokepoint, EvidenceRequest } from '../types/contract';
import { formatProbability } from '../utils/format';

interface ContainmentTabProps {
  chokepoints: Chokepoint[];
  recommendedEvidence: EvidenceRequest[];
  originPinned: boolean;
  canaryHits: string[];
  offlineReplay: boolean;
  onCanaryAlert: (canary_id: string) => void;
}

export const ContainmentTab: React.FC<ContainmentTabProps> = ({
  chokepoints,
  recommendedEvidence,
  originPinned,
  canaryHits,
  offlineReplay,
  onCanaryAlert,
}) => {
  return (
    <div className="space-y-6">
      {/* Canary Status Banner */}
      {originPinned && (
        <div className="p-4 rounded-lg bg-accent-dark/30 border border-accent/40 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-xl">🎯</span>
            <div>
              <span className="text-xs font-bold font-mono text-accent uppercase">
                Canary Pinned Origin
              </span>
              <p className="text-xs text-text-primary">
                A planted decoy identifier was found in the leaked sample ({canaryHits.join(', ')}). Origin artifact is pinned with 100% confidence.
              </p>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-accent text-background font-mono">
            PINNED
          </span>
        </div>
      )}

      {/* Canary Simulation Action (if canaries available) */}
      {!originPinned && canaryHits && canaryHits.length > 0 && !offlineReplay && (
        <div className="p-3 bg-surface rounded border border-border flex items-center justify-between">
          <div className="text-xs text-text-secondary">
            Simulated canary hit detected: <span className="text-accent font-mono">{canaryHits[0]}</span>
          </div>
          <button
            type="button"
            onClick={() => onCanaryAlert(canaryHits[0])}
            className="px-3 py-1 bg-accent/20 hover:bg-accent/30 text-accent border border-accent/40 rounded text-xs font-semibold"
          >
            Simulate Canary Alert
          </button>
        </div>
      )}

      {/* Chokepoint Recommendations Card */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
              Chokepoint Recommendations
            </h3>
            <p className="text-xs text-text-muted">
              Optimal interventions to close the maximum share of plausible leak paths (greedy sequence).
            </p>
          </div>
          <span className="text-[10px] text-text-muted italic">
            Advisory recommendations. No changes made to live systems.
          </span>
        </div>

        {chokepoints.length === 0 ? (
          <div className="p-6 rounded bg-surface border border-border text-center text-text-muted text-xs">
            No chokepoints computed yet. Run a trace to determine optimal containment actions.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {chokepoints.map((cp) => (
              <div
                key={cp.rank}
                className="p-4 rounded-lg bg-surface border border-border flex flex-col justify-between space-y-3 shadow-sm hover:border-accent/40 transition-colors"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="w-5 h-5 rounded-full bg-accent text-background text-xs font-bold font-mono flex items-center justify-center">
                      {cp.rank}
                    </span>
                    <span className="text-xs font-mono font-bold text-accent">
                      Covers {formatProbability(cp.cumulative_coverage)} of paths
                    </span>
                  </div>

                  <h4 className="text-sm font-semibold text-text-primary mb-1">
                    {cp.action_text}
                  </h4>
                  <div className="text-[11px] font-mono text-text-muted">
                    Target: <span className="text-text-secondary">{cp.item_id}</span> ({cp.item_type})
                  </div>
                </div>

                <div className="pt-2 border-t border-border flex items-center justify-between text-xs text-text-muted">
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
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
              Evidence to Collect
            </h3>
            <p className="text-xs text-text-muted">
              Log sources whose recovery would provide the highest informativeness (binary entropy of path mass).
            </p>
          </div>

          <div className="space-y-2">
            {recommendedEvidence.map((evReq, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-lg bg-surface border border-inferred/40 flex items-start space-x-3 shadow-sm"
              >
                <span className="text-lg text-inferred">📋</span>
                <div className="flex-1 text-xs">
                  <div className="font-semibold text-text-primary text-xs mb-1">
                    {evReq.request_text}
                  </div>
                  <div className="text-text-muted font-mono text-[11px] flex items-center space-x-3">
                    <span>
                      Hop: {evReq.hop_ref.from_loc} → {evReq.hop_ref.to_loc}
                    </span>
                    <span>•</span>
                    <span>Path mass: {formatProbability(evReq.mass)}</span>
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
