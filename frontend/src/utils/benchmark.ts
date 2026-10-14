// Benchmark data transformation utilities
// Follows UI_UX_DESIGN.md section 5.8 and FRONTEND.md section 11

import { BenchmarkResult } from '../types/contract';

export interface TransformedBenchmarkDatum {
  lossLevel: string;
  pugmark_top1: number;
  pugmark_top3: number;
  baseline1_top1: number;
  baseline1_top3: number;
  baseline2_top1: number;
  baseline2_top3: number;
}

export function transformBenchmarkData(
  benchmark: BenchmarkResult,
  metricType: 'origin' | 'actor'
): TransformedBenchmarkDatum[] {
  const methodMap =
    metricType === 'origin'
      ? {
          primary: 'pugmark',
          b1: 'B3_largest_export',
          b2: 'B4_most_recent_export',
        }
      : {
          primary: 'pugmark',
          b1: 'B1_last_accessor',
          b2: 'B2_biggest_exporter',
        };

  const dataSource = metricType === 'origin' ? benchmark.origin : benchmark.actor;

  return benchmark.loss_levels.map((level) => {
    // Loss levels can be represented as "0.0", "0.2" etc or percentage
    const levelStr = String(level);
    const levelPercent = `${Math.round(level * 100)}%`;

    const getStats = (method: string) => {
      const byMethod = dataSource[method] || {};
      return byMethod[levelStr] || byMethod[levelPercent] || { top1: 0, top3: 0, n: 0, mean_rank: null };
    };

    const pugmarkStats = getStats(methodMap.primary);
    const b1Stats = getStats(methodMap.b1);
    const b2Stats = getStats(methodMap.b2);

    return {
      lossLevel: `${Math.round(level * 100)}% Loss`,
      pugmark_top1: Math.round(pugmarkStats.top1 * 100),
      pugmark_top3: Math.round(pugmarkStats.top3 * 100),
      baseline1_top1: Math.round(b1Stats.top1 * 100),
      baseline1_top3: Math.round(b1Stats.top3 * 100),
      baseline2_top1: Math.round(b2Stats.top1 * 100),
      baseline2_top3: Math.round(b2Stats.top3 * 100),
    };
  });
}
