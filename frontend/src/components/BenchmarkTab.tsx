// BenchmarkTab component
// Follows UI_UX_DESIGN.md section 5.8 and FRONTEND.md section 11

import React, { useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { BenchmarkResult } from '../types/contract';
import { transformBenchmarkData } from '../utils/benchmark';

interface BenchmarkTabProps {
  benchmark: BenchmarkResult | null;
  busy: boolean;
  offlineReplay: boolean;
  onRun: () => void;
}

export const BenchmarkTab: React.FC<BenchmarkTabProps> = ({
  benchmark,
  busy,
  offlineReplay,
  onRun,
}) => {
  const [metricType, setMetricType] = useState<'origin' | 'actor'>('origin');

  if (!benchmark) {
    return (
      <div className="p-8 text-center text-text-muted space-y-4">
        <span className="text-3xl block">📊</span>
        <h3 className="text-sm font-semibold text-text-primary">No Benchmark Data Available</h3>
        <p className="text-xs max-w-md mx-auto text-text-secondary">
          Run synthetic benchmark evaluation across 200 held-out seeds to compare PUGMARK against naive baseline heuristics at multiple log-loss levels.
        </p>
        <button
          type="button"
          disabled={busy || offlineReplay}
          onClick={onRun}
          className="px-4 py-2 rounded bg-accent hover:bg-accent/90 text-background font-bold text-xs shadow-md transition-colors disabled:opacity-50"
        >
          {busy ? 'Running Benchmark...' : 'Run Benchmark (Seeds 50-199)'}
        </button>
      </div>
    );
  }

  const chartData = transformBenchmarkData(benchmark, metricType);

  const baselineLabels =
    metricType === 'origin'
      ? { b1: 'B3: Largest Export', b2: 'B4: Most Recent Export' }
      : { b1: 'B1: Last Accessor', b2: 'B2: Biggest Exporter' };

  return (
    <div className="space-y-4">
      {/* Top Header & View Toggle */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
            Synthetic Benchmark Evaluation
          </h3>
          <p className="text-xs text-text-muted font-mono">
            Tuned on: {benchmark.tuned_on} • Reported on: {benchmark.reported_on}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1 bg-surface-raised p-1 rounded border border-border text-xs">
            <button
              type="button"
              onClick={() => setMetricType('origin')}
              className={`px-3 py-1 rounded font-semibold transition-colors ${
                metricType === 'origin'
                  ? 'bg-accent text-background shadow-sm'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              Origin Ranking
            </button>
            <button
              type="button"
              onClick={() => setMetricType('actor')}
              className={`px-3 py-1 rounded font-semibold transition-colors ${
                metricType === 'actor'
                  ? 'bg-accent text-background shadow-sm'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              Actor Ranking
            </button>
          </div>

          <button
            type="button"
            disabled={busy || offlineReplay}
            onClick={onRun}
            className="px-3 py-1.5 rounded bg-surface-raised hover:bg-surface-hover text-text-secondary border border-border text-xs font-semibold disabled:opacity-50"
          >
            {busy ? 'Running...' : 'Re-run Benchmark'}
          </button>
        </div>
      </div>

      {/* Recharts Chart Container */}
      <div className="bg-surface rounded-lg border border-border p-4 h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#344754" />
            <XAxis dataKey="lossLevel" stroke="#B9C8D2" fontSize={11} tickLine={false} />
            <YAxis
              stroke="#B9C8D2"
              fontSize={11}
              domain={[0, 100]}
              unit="%"
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#121D27',
                borderColor: '#344754',
                color: '#F2F7FA',
                fontSize: '11px',
                borderRadius: '6px',
              }}
              formatter={(value: number) => [`${value}%`, 'Accuracy']}
            />
            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
              iconType="circle"
            />
            {/* PUGMARK vs Baselines */}
            <Bar dataKey="pugmark_top1" name="PUGMARK (Top-1)" fill="#5EEAD4" radius={[3, 3, 0, 0]} />
            <Bar dataKey="pugmark_top3" name="PUGMARK (Top-3)" fill="#164F4C" radius={[3, 3, 0, 0]} />
            <Bar dataKey="baseline1_top1" name={`${baselineLabels.b1} (Top-1)`} fill="#627D98" radius={[3, 3, 0, 0]} />
            <Bar dataKey="baseline2_top1" name={`${baselineLabels.b2} (Top-1)`} fill="#8576AF" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Benchmark Note (Verbatim from spec) */}
      <div className="p-3 bg-surface rounded border border-border text-center text-xs text-text-muted italic">
        {benchmark.note || 'Synthetic data. Numbers measure the engine on our simulator, not real-world accuracy.'}
      </div>
    </div>
  );
};

export default BenchmarkTab;
