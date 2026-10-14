// Benchmark data transformation utilities
// Follows UI_UX_DESIGN.md section 5.8 and FRONTEND.md section 11

import { BenchmarkResult, MethodStats } from '../types/contract';

export type BenchmarkView = 'origin' | 'actor';

export const BENCHMARK_METHODS: Record<BenchmarkView, Array<{ id: string; label: string }>> = {
  origin: [
    { id: 'pugmark', label: 'PUGMARK' },
    { id: 'B3_largest_export', label: 'B3 largest export' },
    { id: 'B4_most_recent_export', label: 'B4 most recent export' },
  ],
  actor: [
    { id: 'pugmark', label: 'PUGMARK' },
    { id: 'B1_last_accessor', label: 'B1 last accessor' },
    { id: 'B2_biggest_exporter', label: 'B2 biggest exporter' },
  ],
};

// Backend keys losses as Python str(float(loss)): 0 -> "0.0", 0.2 -> "0.2"
export const lossKey = (level: number): string => (Number.isInteger(level) ? level.toFixed(1) : String(level));

export function getStats(benchmark: BenchmarkResult, view: BenchmarkView, method: string, level: number): MethodStats | null {
  return benchmark[view][method]?.[lossKey(level)] ?? null;
}

// One row per loss level; values are percentages of the returned top1/top3, null when the backend sent none
export type TransformedBenchmarkDatum = { lossLevel: string } & Record<string, number | null | string>;

export function transformBenchmarkData(
  benchmark: BenchmarkResult,
  view: BenchmarkView,
  metric: 'top1' | 'top3'
): TransformedBenchmarkDatum[] {
  return benchmark.loss_levels.map((level) => {
    const row: TransformedBenchmarkDatum = { lossLevel: `${Math.round(level * 100)}%` };
    for (const m of BENCHMARK_METHODS[view]) {
      const s = getStats(benchmark, view, m.id, level);
      row[m.id] = s ? Math.round(s[metric] * 1000) / 10 : null;
    }
    return row;
  });
}
