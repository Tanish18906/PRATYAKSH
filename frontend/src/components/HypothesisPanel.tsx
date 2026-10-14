// HypothesisPanel component
// Follows UI_UX_DESIGN.md section 5.5 and FRONTEND.md section 5

import React from 'react';
import { Hypothesis } from '../types/contract';
import { formatNumber, formatProbability, formatUtcShort } from '../utils/format';

const LIKELIHOOD_TIP = 'A score normalized across candidate paths. It is not a calibrated probability.';

interface HypothesisPanelProps {
  hypotheses: Hypothesis[];
  selectedPathId: string | null;
  onSelectPath: (pathId: string) => void;
}

export const HypothesisPanel: React.FC<HypothesisPanelProps> = ({
  hypotheses,
  selectedPathId,
  onSelectPath,
}) => {
  if (!hypotheses || hypotheses.length === 0) {
    return (
      <div className="bg-surface rounded-lg border border-border p-6 text-center text-text-muted">
        <p className="text-xs">No trace available. Export the simulated leak and run a trace.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-border">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-text-primary">
            Ranked hypotheses
          </h2>
          <span className="text-[11px] text-text-muted block">
            Rankings express relative likelihood, not a finding of responsibility.
          </span>
        </div>
        <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-surface-raised border border-border text-text-secondary">
          {hypotheses.length} Candidates
        </span>
      </div>

      <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
        {hypotheses.map((hyp) => {
          const isSelected = selectedPathId === hyp.path_id;

          return (
            <div
              key={hyp.path_id}
              onClick={() => onSelectPath(hyp.path_id)}
              className={`p-3.5 rounded-lg border transition-all cursor-pointer ${
                isSelected
                  ? 'bg-surface-raised border-accent shadow-md shadow-accent/5 ring-1 ring-accent'
                  : 'bg-surface border-border hover:bg-surface-raised/70'
              }`}
            >
              {/* Card Header: Rank, Likelihood, Path ID */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold font-mono ${
                      hyp.rank === 1
                        ? 'bg-accent text-background'
                        : 'bg-surface-raised border border-border text-text-secondary'
                    }`}
                  >
                    #{hyp.rank}
                  </span>
                  <span className="text-xs font-mono font-bold text-text-primary">
                    {hyp.path_id}
                  </span>
                </div>

                <div className="text-right">
                  <span className="text-xs font-mono font-bold text-accent">
                    {formatProbability(hyp.probability)}
                  </span>
                  <span className="text-[10px] text-text-muted block" title={LIKELIHOOD_TIP}>
                    Relative likelihood
                  </span>
                </div>
              </div>

              {/* Likelihood Bar */}
              <div className="w-full bg-surface-raised h-1.5 rounded-full overflow-hidden mb-3 border border-border">
                <div
                  className="bg-accent h-full transition-all duration-300"
                  style={{ width: `${hyp.probability * 100}%` }}
                ></div>
              </div>

              {/* Plain-English Summary */}
              <p className="text-xs text-text-primary mb-3 leading-relaxed font-sans">
                {hyp.summary_text}
              </p>

              {/* Origin Artifact Tag */}
              <div className="mb-3 text-[11px] font-mono flex items-center space-x-1.5 bg-surface/80 p-1.5 rounded border border-border">
                <span className="text-text-muted">Origin:</span>
                <span className="text-inferred font-semibold">{hyp.origin_artifact}</span>
                <span className="text-text-muted">• Actors:</span>
                <span className="text-text-secondary">{hyp.actors.join(', ')}</span>
              </div>

              {isSelected && (
                <ol className="mb-3 space-y-1 text-[11px] font-mono">
                  {hyp.hops.map((hop, i) => (
                    <li
                      key={i}
                      className={`p-1.5 rounded border ${
                        hop.kind === 'inferred' ? 'border-dashed border-inferred/50' : 'border-border'
                      }`}
                    >
                      <div className="text-text-primary">
                        {hop.from_loc} → {hop.to_loc}
                      </div>
                      <div className="text-text-muted">
                        <span className={hop.kind === 'inferred' ? 'text-inferred font-semibold' : 'text-success'}>
                          {hop.kind === 'inferred' ? 'Inferred' : 'Observed'}
                        </span>
                        {' · '}
                        {hop.actor} · {formatUtcShort(hop.ts)}
                        {hop.action && ` · ${hop.action}`}
                        {hop.rows !== null && ` · ${formatNumber(hop.rows)} rows`}
                      </div>
                      {hop.kind === 'inferred' && (
                        <div className="text-inferred">
                          {hop.est_loss !== null
                            ? `Log missing. Estimated loss: ${Math.round(hop.est_loss * 100)}%.`
                            : 'Log missing.'}
                        </div>
                      )}
                    </li>
                  ))}
                </ol>
              )}

              {/* Evidence Items */}
              {hyp.evidence && hyp.evidence.length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-border">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted block">
                    Evidence
                  </span>
                  <div className="space-y-1">
                    {hyp.evidence.map((ev, evIdx) => {
                      const getBadgeColor = (kind: string) => {
                        switch (kind) {
                          case 'observed':
                            return 'bg-success/20 text-success border-success/30';
                          case 'inferred':
                            return 'bg-inferred/20 text-inferred border-inferred/30';
                          case 'anomaly':
                            return 'bg-danger/20 text-danger border-danger/30';
                          case 'fingerprint':
                            return 'bg-accent/20 text-accent border-accent/30';
                          default:
                            return 'bg-surface-raised text-text-secondary border-border';
                        }
                      };

                      return (
                        <div
                          key={evIdx}
                          className="flex items-start space-x-2 text-[11px] bg-surface-raised/40 p-1.5 rounded"
                        >
                          <span
                            className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-bold uppercase border mt-0.5 shrink-0 ${getBadgeColor(
                              ev.kind
                            )}`}
                          >
                            {ev.kind}
                          </span>
                          <span className="flex-1 text-text-secondary text-[11px] leading-tight">
                            {ev.text}
                          </span>
                          {ev.ts && (
                            <span className="text-[10px] font-mono text-text-muted shrink-0">
                              {formatUtcShort(ev.ts)}
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectPath(hyp.path_id);
                }}
                aria-pressed={isSelected}
                className={`mt-3 w-full px-2 py-1 rounded text-[11px] font-semibold border ${
                  isSelected
                    ? 'bg-accent/15 text-accent border-accent/40'
                    : 'bg-surface-raised text-text-secondary border-border hover:text-text-primary'
                }`}
              >
                {isSelected ? 'Path selected' : 'Select path'}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default HypothesisPanel;
