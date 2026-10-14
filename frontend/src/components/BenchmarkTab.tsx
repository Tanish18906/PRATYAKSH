// BenchmarkTab component
// Follows UI_UX_DESIGN.md section 5.8 and FRONTEND.md section 11

import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';
import { BenchmarkResult } from '../types/contract';
import { BENCHMARK_METHODS, BenchmarkView, getStats, transformBenchmarkData } from '../utils/benchmark';

// PUGMARK in accent, baselines in neutral graph tones
const METHOD_COLORS = ['#5EEAD4', '#627D98', '#8576AF'];
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
      className="px-4 py-2 rounded bg-accent hover:bg-accent/90 text-background font-bold text-xs shadow-md disabled:opacity-50"
    >
      Run benchmark
    </button>
  );

  if (!benchmark) {
    return (
      <div className="p-8 text-center text-text-muted space-y-4">
        <p className="text-sm">No benchmark results available. Run the synthetic benchmark.</p>
        {runButton}
      </div>
    );
  }

  if (benchmark.status === 'running') {
    const pct = Math.round(benchmark.progress * 100);
    return (
      <div className="p-8 space-y-3 max-w-md mx-auto text-center">
        <p className="text-sm text-text-primary">Running synthetic benchmark... {pct}%</p>
        <div
          className="w-full h-2 bg-surface-raised rounded-full overflow-hidden border border-border"
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div className="h-full bg-accent transition-all" style={{ width: `${pct}%` }} />
        </div>
        <p className="text-xs text-text-muted">{benchmark.note}</p>
      </div>
    );
  }

  if (benchmark.status === 'failed') {
    return (
      <div className="p-8 text-center space-y-4">
        <p className="text-sm text-danger">Synthetic benchmark failed. No results were recorded.</p>
        {runButton}
      </div>
    );
  }

  const methods = BENCHMARK_METHODS[view];

  const chart = (metric: 'top1' | 'top3', title: string) => (
    <div className="bg-surface rounded-lg border border-border p-4">
      <h4 className="text-xs font-bold uppercase tracking-wider text-text-primary mb-2">{title}</h4>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={transformBenchmarkData(benchmark, view, metric)} margin={{ top: 10, right: 10, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#344754" />
            <XAxis
              dataKey="lossLevel"
              stroke="#B9C8D2"
              fontSize={12}
              tickLine={false}
              label={{ value: 'Log loss', position: 'insideBottom', offset: -5, fill: '#B9C8D2', fontSize: 12 }}
            />
            <YAxis stroke="#B9C8D2" fontSize={12} domain={[0, 100]} unit="%" tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: '#121D27', borderColor: '#344754', color: '#F2F7FA', fontSize: '12px' }}
              formatter={(value) => (value === null || value === undefined ? 'N/A' : `${value}%`)}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '14px' }} />
            {methods.map((m, i) => (
              <Bar key={m.id} dataKey={m.id} name={m.label} fill={METHOD_COLORS[i]} radius={[3, 3, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider" title={BENCHMARK_TIP}>
            Benchmark
          </h3>
          <p className="text-xs text-text-muted font-mono">
            Synthetic benchmark complete • Tuned on {benchmark.tuned_on} • Reported on {benchmark.reported_on}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-surface-raised p-1 rounded border border-border text-xs">
            {(['origin', 'actor'] as const).map((v) => (
              <button
                key={v}
                type="button"
                aria-pressed={view === v}
                onClick={() => setView(v)}
                className={`px-3 py-1 rounded font-semibold ${
                  view === v ? 'bg-accent text-background' : 'text-text-secondary hover:text-text-primary'
                }`}
              >
                {v === 'origin' ? 'Origin' : 'Actor'}
              </button>
            ))}
          </div>
          {runButton}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {chart('top1', 'Top-1 accuracy')}
        {chart('top3', 'Top-3 accuracy')}
      </div>

      <div className="overflow-x-auto rounded border border-border">
        <table className="w-full text-xs font-mono text-left">
          <thead>
            <tr className="border-b border-border text-text-muted bg-surface-raised">
              <th className="p-2 font-semibold">Method</th>
              {benchmark.loss_levels.map((l) => (
                <th key={l} className="p-2 font-semibold">
                  Log loss {Math.round(l * 100)}%: mean rank · n
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {methods.map((m) => (
              <tr key={m.id}>
                <td className="p-2 font-bold text-text-primary">{m.label}</td>
                {benchmark.loss_levels.map((l) => {
                  const s = getStats(benchmark, view, m.id, l);
                  return (
                    <td key={l} className="p-2 text-text-secondary">
                      {s ? `${s.mean_rank === null ? 'N/A' : s.mean_rank.toFixed(2)} · ${s.n}` : 'N/A'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="p-3 bg-surface rounded border border-border text-center text-xs text-text-muted">{benchmark.note}</p>
    </div>
  );
};

export default BenchmarkTab;
