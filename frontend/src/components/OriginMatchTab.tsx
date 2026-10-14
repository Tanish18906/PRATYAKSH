// OriginMatchTab component
// Follows UI_UX_DESIGN.md section 5.6 and FRONTEND.md section 5

import React from 'react';
import { OriginCandidate } from '../types/contract';
import { formatScore } from '../utils/format';

interface OriginMatchTabProps {
  candidates: OriginCandidate[];
}

export const OriginMatchTab: React.FC<OriginMatchTabProps> = ({ candidates }) => {
  if (!candidates || candidates.length === 0) {
    return (
      <div className="p-8 text-center text-text-muted">
        No candidate origin artifacts evaluated yet. Run a trace to match the leak sample against exports.
      </div>
    );
  }

  const formatPercentage = (val: number | null) => {
    if (val === null || val === undefined) return 'N/A';
    return `${(val * 100).toFixed(1)}%`;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
            Origin Matching & Exclusion Evaluation
          </h3>
          <p className="text-xs text-text-muted">
            Evaluates candidate exports using bottom-k sketch containment, schema matching, format similarity, and record watermarks.
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-surface-raised border border-border text-text-secondary">
          {candidates.length} Evaluated Exports
        </span>
      </div>

      <div className="overflow-x-auto rounded border border-border shadow-sm">
        <table className="w-full text-xs font-mono text-left bg-surface">
          <thead>
            <tr className="border-b border-border text-text-muted text-[11px] bg-surface-raised">
              <th className="p-3 font-semibold">Artifact ID</th>
              <th className="p-3 font-semibold">Verdict</th>
              <th className="p-3 font-semibold">Containment</th>
              <th className="p-3 font-semibold">Specificity</th>
              <th className="p-3 font-semibold">Format Sim</th>
              <th className="p-3 font-semibold">Watermark Term</th>
              <th className="p-3 font-semibold">Origin Fit Score</th>
              <th className="p-3 font-semibold">Exclusion Reason / Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {candidates.map((cand) => {
              const isExcluded = cand.verdict === 'excluded';

              return (
                <tr
                  key={cand.artifact_id}
                  className={`hover:bg-surface-raised/60 transition-colors ${
                    isExcluded ? 'opacity-70 bg-background/30' : 'bg-surface'
                  }`}
                >
                  <td className="p-3 font-bold text-text-primary">
                    {cand.artifact_id}
                  </td>

                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                        cand.verdict === 'candidate'
                          ? 'bg-success/20 text-success border-success/30'
                          : 'bg-danger/20 text-danger border-danger/30'
                      }`}
                    >
                      {cand.verdict}
                    </span>
                  </td>

                  <td className="p-3 text-text-secondary">
                    {formatPercentage(cand.containment)}
                  </td>

                  <td className="p-3 text-text-secondary">
                    {formatPercentage(cand.specificity)}
                  </td>

                  <td className="p-3 text-text-secondary">
                    {formatPercentage(cand.format_sim)}
                  </td>

                  <td className="p-3 text-text-secondary font-mono">
                    {cand.watermark_term !== null ? formatScore(cand.watermark_term) : 'N/A'}
                  </td>

                  <td className="p-3 font-bold text-accent font-mono">
                    {cand.origin_fit !== null ? formatScore(cand.origin_fit) : 'N/A'}
                  </td>

                  <td className="p-3 text-xs">
                    {cand.exclusion_rule ? (
                      <span className="text-danger font-semibold flex items-center space-x-1">
                        <span>⛔</span>
                        <span className="font-mono">{cand.exclusion_rule}</span>
                      </span>
                    ) : (
                      <span className="text-text-muted">None (Eligible)</span>
                    )}
                    {cand.notes && cand.notes.length > 0 && (
                      <div className="text-[10px] text-text-muted mt-0.5 font-sans">
                        {cand.notes.join('; ')}
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OriginMatchTab;
