import assert from 'node:assert/strict';
import { test } from 'node:test';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { BenchmarkTab } from '../src/components/BenchmarkTab';
import { lossKey, transformBenchmarkData } from '../src/utils/benchmark';
import { BenchmarkResult } from '../src/types/contract';

const NOTE = 'Synthetic data. Numbers measure the engine on our simulator, not real-world accuracy.';
const s = (top1: number, top3: number, mean_rank: number | null, n: number) => ({ top1, top3, mean_rank, n });

// Shape and keys copied from a live GET /api/benchmark/{id} (seeds 50-61)
const done: BenchmarkResult = {
  benchmark_id: 'bench:0001',
  status: 'done',
  progress: 1,
  tuned_on: 'seeds 0-49',
  reported_on: 'seeds 50-61',
  loss_levels: [0.0, 0.2],
  origin: {
    pugmark: { '0.0': s(1, 1, 1, 12), '0.2': s(1, 1, 1, 12) },
    B3_largest_export: { '0.0': s(0, 0, 4.5, 12) },
    B4_most_recent_export: { '0.0': s(0, 0.8333, 2.1, 12), '0.2': s(0, 0.8333, 2.1, 12) },
  },
  actor: {
    pugmark: { '0.0': s(1, 1, 1, 12), '0.2': s(0.6667, 0.75, 2.4, 12) },
    B1_last_accessor: { '0.0': s(0.0833, 0.1667, 6, 12), '0.2': s(0, 0.0833, 7, 12) },
    B2_biggest_exporter: { '0.0': s(0, 0.5833, 3.0833, 12), '0.2': s(0, 0.5833, 8, 12) },
  },
  note: NOTE,
};

const render = (b: BenchmarkResult | null) =>
  renderToStaticMarkup(<BenchmarkTab benchmark={b} busy={false} offlineReplay={false} onRun={() => {}} />);

test('loss keys match the backend str(float) form', () => {
  assert.deepEqual([0, 0.2, 0.4, 0.6].map(lossKey), ['0.0', '0.2', '0.4', '0.6']);
});

test('transform reads returned top1/top3 and never invents a missing value', () => {
  const top3 = transformBenchmarkData(done, 'origin', 'top3');
  assert.deepEqual(top3[0], { lossLevel: '0%', pugmark: 100, B3_largest_export: 0, B4_most_recent_export: 83.3 });
  assert.equal(top3[1].B3_largest_export, null); // backend sent no 0.2 entry for B3
  const actorTop1 = transformBenchmarkData(done, 'actor', 'top1');
  assert.equal(actorTop1[1].pugmark, 66.7);
  assert.equal(actorTop1[0].B1_last_accessor, 8.3);
});

test('running shows progress and no table, failed shows the error and no table', () => {
  const running = render({ ...done, status: 'running', progress: 0.35 });
  assert.match(running, /35%/);
  assert.doesNotMatch(running, /<table/);
  const failed = render({ ...done, status: 'failed' });
  assert.match(failed, /Synthetic benchmark failed\. No results were recorded\./);
  assert.doesNotMatch(failed, /<table/);
});

test('done shows mean rank, n, N/A for missing stats and the note verbatim', () => {
  const html = render(done);
  assert.match(html, /1\.00 · 12/);
  assert.match(html, /2\.10 · 12/);
  assert.match(html, /N\/A/);
  assert.ok(html.includes(NOTE));
  assert.match(render(null), /No benchmark results available\. Run the synthetic benchmark\./);
});
