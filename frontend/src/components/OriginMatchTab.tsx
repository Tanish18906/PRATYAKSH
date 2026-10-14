// Origin match: which company export the leaked file came from; decoys excluded in words (UI_LAYOUT.md section 5)

import React from 'react';
import { ExclusionRule, OriginCandidate } from '../types/contract';
import { formatScore } from '../utils/format';
import { displayName, NameSource, wholePercent } from '../utils/names';
import Icon from './Icon';

const EXCLUSION_LABEL: Record<ExclusionRule, string> = {
  schema: 'Different columns from the leaked file',
  watermark_before: 'Older than the newest record in the leak',
  after_found: 'Made after the leak was found',
};

interface OriginMatchTabProps {
  candidates: OriginCandidate[];
  names?: NameSource | null;
}

export const OriginMatchTab: React.FC<OriginMatchTabProps> = ({ candidates, names }) => {
  if (!candidates || candidates.length === 0) {
    return (
      <div className="rounded-card border border-line bg-surface p-8 text-center text-sm text-ink-3">
        The fingerprint match appears here after Export and trace.
      </div>
    );
  }

  // Candidates arrive sorted by origin fit, excluded last: the first candidate is the best match
  const winner = candidates.find((c) => c.verdict === 'candidate')?.artifact_id;

  return (
    <section className="rounded-card border border-line bg-surface">
      <div className="p-4">
        <h2 className="text-sm font-semibold text-ink">Origin match</h2>
        <p className="mt-0.5 text-[13px] text-ink-3">
          We match the leaked file's fingerprint against every company export, without reading the data. A match points to a source
          file, not to a person.
        </p>
      </div>

      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-y border-line bg-surface-2 text-[13px] text-ink-3">
            <th className="px-4 py-2 font-medium">Export</th>
            <th className="w-1/3 px-4 py-2 font-medium">Match</th>
            <th className="px-4 py-2 font-medium">Verdict</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {candidates.map((c) => {
            const isWinner = c.artifact_id === winner;
            const excluded = c.verdict === 'excluded';
            return (
              <tr key={c.artifact_id} className={isWinner ? 'bg-ok-tint' : ''}>
                <td className="px-4 py-3 font-medium text-ink">{displayName(c.artifact_id, names)}</td>
                <td className="px-4 py-3">
                  {c.containment === null ? (
                    <span className="text-ink-3">Not compared</span>
                  ) : (
                    <div className="flex items-center gap-3">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-line" aria-hidden="true">
                        <div
                          className={`bar-fill h-full rounded-full ${isWinner ? 'bg-ok' : 'bg-ink-3'}`}
                          style={{ width: `${c.containment * 100}%` }}
                        />
                      </div>
                      <span className="shrink-0 whitespace-nowrap text-[13px] text-ink-2 tabular">{wholePercent(c.containment)} of identifiers</span>
                    </div>
                  )}
                </td>
                <td className="px-4 py-3 text-[13px]">
                  {isWinner ? (
                    <span className="inline-flex items-center gap-1.5 font-semibold text-ok">
                      <Icon name="check" /> Most likely source
                    </span>
                  ) : excluded && c.exclusion_rule ? (
                    <span className="text-ink-3">Excluded: {EXCLUSION_LABEL[c.exclusion_rule].toLowerCase()}</span>
                  ) : (
                    <span className="text-ink-2">Possible, weaker fit</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <details className="border-t border-line px-4 py-3">
        <summary className="text-[13px] font-medium text-accent">Details</summary>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-left font-mono text-xs text-ink-2">
            <thead>
              <tr className="text-ink-3">
                {['artifact_id', 'verdict', 'exclusion_rule', 'containment', 'specificity', 'format_sim', 'watermark_term', 'origin_fit', 'notes'].map(
                  (h) => <th key={h} className="py-1 pr-4 font-medium">{h}</th>
                )}
              </tr>
            </thead>
            <tbody>
              {candidates.map((c) => (
                <tr key={c.artifact_id}>
                  <td className="py-1 pr-4">{c.artifact_id}</td>
                  <td className="py-1 pr-4">{c.verdict}</td>
                  <td className="py-1 pr-4">{c.exclusion_rule ?? '-'}</td>
                  <td className="py-1 pr-4">{c.containment ?? '-'}</td>
                  <td className="py-1 pr-4">{c.specificity ?? '-'}</td>
                  <td className="py-1 pr-4">{c.format_sim ?? '-'}</td>
                  <td className="py-1 pr-4">{c.watermark_term !== null ? formatScore(c.watermark_term) : '-'}</td>
                  <td className="py-1 pr-4">{c.origin_fit !== null ? formatScore(c.origin_fit) : '-'}</td>
                  <td className="py-1 pr-4 font-sans">{c.notes.join('; ') || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
};

export default OriginMatchTab;
