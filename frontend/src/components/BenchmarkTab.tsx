// BenchmarkTab component
// Follows UI_UX_DESIGN.md section 5.8 and FRONTEND.md section 11

import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, LabelList } from 'recharts';
import { BenchmarkResult } from '../types/contract';
import { BENCHMARK_METHODS, BenchmarkView, getStats, transformBenchmarkData } from '../utils/benchmark';
import { TOKENS } from '../utils/tokens';

const BENCHMARK_TIP = 'Tests PUGMARK on generated scenarios with known synthetic ground truth.';

interface BenchmarkTabProps {
  benchmark: BenchmarkResult | null;
  busy: boolean;
  offlineReplay: boolean;
  onRun: () => void;
}

export const BenchmarkTab: React.FC<BenchmarkTabProps> = ({ benchmark, busy, offlineReplay, onRun }) => {
  const [view, setView] = useState<BenchmarkView>('origin');
  const running = benchmark?.status === 'running';

  const runButton = (
    <button
      type="button"
      disabled={busy || offlineReplay || running}
      onClick={onRun}
      title={BENCHMARK_TIP}
      className="h-10 rounded-ctl border border-line-strong bg-surface px-4 text-sm font-medium text-ink hover:bg-surface-2 disabled:opacity-50"
    >
      Run benchmark
    </button>
  );

  if (!benchmark) {
    return (
      <div className="space-y-4 rounded-card border border-line bg-surface p-8 text-center text-ink-2">
        <p className="text-sm">No benchmark results available. Run the synthetic benchmark.</p>
        {runButton}
      </div>
    );
  }

  if (benchmark.status === 'running') {
    const pct = Math.round(benchmark.progress * 100);
    return (
      <div className="mx-auto max-w-md space-y-3 rounded-card border border-line bg-surface p-8 text-center">
        <p className="text-sm text-ink">Running synthetic benchmark... {pct}%</p>
        <div
          className="h-1.5 w-full overflow-hidden rounded-full bg-line"
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${pct}%` }} />
        </div>
        <p className="text-xs text-ink-3">{benchmark.note}</p>
      </div>
    );
  }

  if (benchmark.status === 'failed') {
    return (
      <div className="space-y-4 rounded-card border border-line bg-surface p-8 text-center">
        <p className="text-sm text-leak">Synthetic benchmark failed. No results were recorded.</p>
        {runButton}
      </div>
    );
  }

  const methods = BENCHMARK_METHODS[view];

  // PUGMARK against the best baseline at each loss level; null stays null (never invented)
  const vsBest = (metric: 'top1' | 'top3') =>
    transformBenchmarkData(benchmark, view, metric).map((row) => {
      const base = methods.slice(1).map((m) => row[m.id]).filter((v): v is number => typeof v === 'number');
      return { lossLevel: row.lossLevel, pugmark: row.pugmark, best: base.length ? Math.max(...base) : null };
    });

  const pct = (v: unknown) => (v === null || v === undefined ? 'N/A' : `${Math.round(Number(v))}%`);

  const chart = (metric: 'top1' | 'top3', title: string) => (
    <div className="rounded-card border border-line bg-surface p-4">
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      <p className="mt-0.5 flex items-center gap-3 text-xs text-ink-3">
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-accent" />PUGMARK</span>
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm bg-ink-3" />Best baseline</span>
      </p>
      <div className="mt-2 h-60">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={vsBest(metric)} margin={{ top: 18, right: 8, left: 0, bottom: 14 }} barGap={4}>
            <CartesianGrid vertical={false} stroke={TOKENS.line} />
            <XAxis
              dataKey="lossLevel"
              stroke={TOKENS.ink3}
              fontSize={12}
              tickLine={false}
              label={{ value: 'Log loss', position: 'insideBottom', offset: -8, fill: TOKENS.ink3, fontSize: 12 }}
            />
            <YAxis stroke={TOKENS.ink3} fontSize={12} domain={[0, 100]} unit="%" tickLine={false} axisLine={false} />
            <Tooltip
              cursor={{ fill: TOKENS.surface2 }}
              contentStyle={{ backgroundColor: TOKENS.surface, borderColor: TOKENS.line, color: TOKENS.ink, fontSize: '12px', borderRadius: 8 }}
              formatter={(value) => pct(value)}
            />
            <Bar dataKey="pugmark" name="PUGMARK" fill={TOKENS.accent} radius={[3, 3, 0, 0]}>
              <LabelList dataKey="pugmark" position="top" formatter={pct} fontSize={11} fill={TOKENS.ink2} />
            </Bar>
            <Bar dataKey="best" name="Best baseline" fill={TOKENS.ink3} radius={[3, 3, 0, 0]}>
              <LabelList dataKey="best" position="top" formatter={pct} fontSize={11} fill={TOKENS.ink2} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-ink" title={BENCHMARK_TIP}>Benchmark</h2>
          <p className="text-[13px] text-ink-3">
            Simulated incidents. Tuned on {benchmark.tuned_on}, reported on {benchmark.reported_on}.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div role="group" aria-label="Measure" className="flex rounded-ctl border border-line bg-surface p-0.5 text-sm">
            {(['origin', 'actor'] as const).map((v) => (
              <button
                key={v}
                type="button"
                aria-pressed={view === v}
                onClick={() => setView(v)}
                className={`h-8 rounded-md px-3 ${view === v ? 'bg-accent font-semibold text-white' : 'text-ink-2 hover:bg-surface-2'}`}
              >
                {v === 'origin' ? 'Source export' : 'Actor'}
              </button>
            ))}
          </div>
          {runButton}
        </div>
      </div>

      <p className="rounded-card border border-line bg-inferred-tint p-3 text-[13px] text-inferred-text">{benchmark.note}</p>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {chart('top1', 'Right answer ranked first')}
        {chart('top3', 'Right answer in the top three')}
      </div>

      <div className="overflow-x-auto rounded-card border border-line bg-surface">
        <table className="w-full text-left text-[13px]">
          <thead>
            <tr className="border-b border-line bg-surface-2 text-ink-3">
              <th className="px-4 py-2 font-medium">Method</th>
              {benchmark.loss_levels.map((l) => (
                <th key={l} className="px-4 py-2 font-medium">
                  Log loss {Math.round(l * 100)}%: mean rank · n
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {methods.map((m) => (
              <tr key={m.id}>
                <td className="px-4 py-2 font-medium text-ink">{m.label}</td>
                {benchmark.loss_levels.map((l) => {
                  const s = getStats(benchmark, view, m.id, l);
                  return (
                    <td key={l} className="px-4 py-2 text-ink-2 tabular">
                      {s ? `${s.mean_rank === null ? 'N/A' : s.mean_rank.toFixed(2)} · ${s.n}` : 'N/A'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default BenchmarkTab;
