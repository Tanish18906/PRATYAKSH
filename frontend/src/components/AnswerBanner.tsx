// Answer banner: source, route, likelihood in one read (UI_LAYOUT.md section 2, UX_FLOW.md section 1)

import React from 'react';
import { TraceResult } from '../types/contract';
import { NameSource, wholePercent } from '../utils/names';
import { originContainment, routeSentence, sourceSentence } from '../utils/answer';
import StatusBadge from './StatusBadge';
import Icon from './Icon';
import { TRACE_STEPS } from '../state/reducer';

interface AnswerBannerProps {
  trace: TraceResult | null;
  names: NameSource | null;
  busy: boolean;
  step?: number; // index into TRACE_STEPS while Export and trace runs, else -1
  onJump: (target: 'cut' | 'collect') => void;
}

const Label: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="text-[13px] text-ink-3">{children}</div>
);

export const AnswerBanner: React.FC<AnswerBannerProps> = ({ trace, names, busy, step = -1, onJump }) => {
  const top = trace?.hypotheses[0];

  if (!trace || !top) {
    return (
      <section aria-label="Answer" aria-busy={busy} className="shrink-0 rounded-card border border-line bg-surface p-4">
        {step >= 0 ? (
          <div role="status" aria-live="polite">
            <ol className="grid grid-cols-4 gap-3">
              {TRACE_STEPS.map((s, i) => (
                <li key={s} className="min-w-0">
                  <div className="h-1.5 overflow-hidden rounded-full bg-line">
                    <div
                      className={`h-full rounded-full bg-accent ${i === step ? 'step-fill' : ''}`}
                      style={{ width: i < step ? '100%' : i === step ? undefined : '0%' }}
                    />
                  </div>
                  <div className={`mt-2 flex items-start gap-1.5 text-[13px] leading-[18px] ${i <= step ? 'text-ink' : 'text-ink-3'}`}>
                    {i < step ? (
                      <Icon name="check" className="mt-px shrink-0 text-ok" />
                    ) : i === step ? (
                      <span className="mt-0.5 h-3.5 w-3.5 shrink-0 animate-spin rounded-full border-2 border-accent border-t-transparent" aria-hidden="true" />
                    ) : (
                      <span className="mt-[5px] h-1.5 w-1.5 shrink-0 rounded-full bg-line-strong" aria-hidden="true" />
                    )}
                    <span className={i === step ? 'font-medium' : ''}>{s.replace('...', '')}</span>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        ) : busy ? (
          <div className="space-y-3">
            <div className="skeleton h-6 w-3/4" />
            <div className="skeleton h-5 w-1/2" />
          </div>
        ) : (
          <p className="text-base text-ink-2">
            {trace ? 'No route survived the trace. Check the Origin match tab.' : 'Open the Telegram post and press Export and trace.'}
          </p>
        )}
      </section>
    );
  }

  const match = originContainment(trace);

  return (
    <section aria-label="Answer" className="fade-in shrink-0 rounded-card border border-line bg-surface px-4 py-3">
      <div className="flex items-center justify-between gap-3">
        <Label>Most likely source</Label>
        <div className="flex gap-1.5">
          {match !== null && <StatusBadge kind="success" label={`${wholePercent(match)} of identifiers match`} />}
          {trace.origin_pinned && <StatusBadge kind="success" label="Confirmed by canary" />}
        </div>
      </div>
      <p className="text-xl font-semibold leading-7 text-ink">{sourceSentence(trace, names)}</p>

      <div className="mt-2.5 flex items-center justify-between gap-3 border-t border-line pt-2.5">
        <Label>Most likely route</Label>
        <div className="flex items-center gap-2.5">
          <span className="text-sm text-ink-2">
            <span className="text-2xl font-semibold text-ink tabular">{wholePercent(top.probability)}</span> relative likelihood
          </span>
          <span className="h-1.5 w-24 overflow-hidden rounded-full bg-line" aria-hidden="true">
            <span className="block h-full rounded-full bg-accent" style={{ width: `${top.probability * 100}%` }} />
          </span>
        </div>
      </div>
      <p className="text-base font-medium leading-6 text-ink">{routeSentence(top, names)}</p>

      <div className="mt-1 flex gap-4">
        <button type="button" onClick={() => onJump('cut')} className="inline-flex h-9 items-center gap-1.5 text-sm font-medium text-accent hover:underline">
          <Icon name="scissors" /> Where to cut
        </button>
        <button type="button" onClick={() => onJump('collect')} className="inline-flex h-9 items-center gap-1.5 text-sm font-medium text-accent hover:underline">
          <Icon name="search" /> What to collect next
        </button>
      </div>
    </section>
  );
};

export default AnswerBanner;
