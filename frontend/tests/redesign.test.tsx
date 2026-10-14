import assert from 'node:assert/strict';
import { test } from 'node:test';
import { displayName, prettyIds, formatDay, wholePercent } from '../src/utils/names';
import { originContainment, routeSentence, routeStops, sourceSentence, whyBullets } from '../src/utils/answer';
import { computeLayout, computePositions, graphCards, PAD, ROUTE_H, SIDE_H } from '../src/utils/graph';
import { DemoBundle } from '../src/types/contract';
import demo from '../public/demo.json';

const bundle = demo as DemoBundle;
const ID = /\b(art|act|sys|ep|ch|ds|hyp):[\w-]+/;

test('displayName resolves scenario names and falls back to a readable label', () => {
  assert.equal(displayName('act:ravi-menon', bundle.scenario), 'Ravi Menon');
  assert.equal(displayName('ep:ravi-menon', bundle.scenario), 'Ravi Menon laptop');
  assert.equal(displayName('art:E1', bundle.scenario), 'Export E1');
  assert.equal(displayName('sys:never-seen', bundle.scenario), 'Never Seen');
  assert.equal(displayName('src:bi-warehouse'), 'Bi Warehouse logs');
});

test('prettyIds removes every internal id and ISO time from engine text', () => {
  for (const h of bundle.trace.hypotheses) {
    const out = prettyIds(h.summary_text, bundle.scenario);
    assert.doesNotMatch(out, ID, out);
    assert.doesNotMatch(out, /\d{4}-\d{2}-\d{2}T/, out);
  }
  assert.equal(prettyIds('in art:E1 at 2026-10-09T21:40:00Z'), 'in Export E1 at 9 Oct, 21:40 UTC');
});

test('answer sentences are derived from the top hypothesis without ids', () => {
  const t = bundle.trace;
  assert.equal(sourceSentence(t, bundle.scenario), 'Export E1, created by etl-nightly on 9 Oct, 02:10 UTC');
  assert.equal(wholePercent(originContainment(t)), '100%');
  assert.equal(routeSentence(t.hypotheses[0], bundle.scenario),
    'Ravi Menon: Bi Warehouse, then Ravi Menon laptop, then Telegram Leak Channel');
  assert.deepEqual(whyBullets(t.hypotheses[0]).map((e) => e.kind), ['fingerprint', 'observed', 'inferred']);
  assert.deepEqual(whyBullets(t.hypotheses[1]).map((e) => e.kind), ['fingerprint', 'inferred']);
});

test('preset layout puts the selected route on one line, left to right, other routes on their own lanes', () => {
  const t = bundle.trace;
  for (const h of t.hypotheses) {
    const pos = computePositions(t.graph, t.hypotheses, h.path_id);
    const stops = routeStops(h);
    assert.ok(stops.every((s) => pos[s].y === 0), h.path_id);
    for (let i = 1; i < stops.length; i++) assert.ok(pos[stops[i]].x > pos[stops[i - 1]].x);
    const laptops = t.hypotheses.map((x) => pos[x.hops[0].to_loc].y);
    assert.equal(new Set(laptops).size, t.hypotheses.length);
  }
  for (const c of graphCards(t.graph, t.hypotheses, bundle.scenario, null)) assert.doesNotMatch(`${c.name} ${c.when}`, ID, c.name);
});

test('layout stretches to the canvas so the graph is drawn at zoom 1 when it fits', () => {
  const t = bundle.trace;
  const sel = t.hypotheses[0].path_id;
  for (const box of [{ w: 1150, h: 620 }, { w: 716, h: 380 }]) {
    const { positions, cardW, onRoute } = computeLayout(t.graph, t.hypotheses, sel, box);
    const xs = Object.values(positions).map((p) => p.x);
    const half = (id: string) => (onRoute.has(id) ? ROUTE_H : SIDE_H) / 2;
    const top = Math.min(...Object.entries(positions).map(([id, p]) => p.y - half(id)));
    const bottom = Math.max(...Object.entries(positions).map(([id, p]) => p.y + half(id)));
    assert.ok(Math.max(...xs) - Math.min(...xs) + cardW <= box.w - 2 * PAD, `width fits at ${box.w}`);
    assert.ok(bottom - top <= box.h - 2 * PAD + 1, `height fits at ${box.h}: ${bottom - top}`);
    assert.equal(cardW % 2, 0);
    assert.deepEqual([...onRoute].sort(), [...new Set(routeStops(t.hypotheses[0]).concat(t.hypotheses[0].origin_artifact))].sort());
  }
});

test('dates and likelihoods use the copy rules', () => {
  assert.equal(formatDay('2026-10-09T02:10:00Z'), '9 Oct, 02:10 UTC');
  assert.equal(formatDay(null), 'Time unknown');
  assert.equal(wholePercent(0.8791), '88%');
});
