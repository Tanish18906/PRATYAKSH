import assert from 'node:assert/strict';
import { test } from 'node:test';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { appReducer, initialState } from '../src/state/reducer';
import { ContainmentTab } from '../src/components/ContainmentTab';
import { InjectDialog } from '../src/components/InjectDialog';
import { ReportTab } from '../src/components/ReportTab';
import { TelegramChat } from '../src/components/TelegramChat';
import { IncidentPanel } from '../src/components/IncidentPanel';
import { DemoBundle } from '../src/types/contract';
import demo from '../public/demo.json';

const bundle = demo as DemoBundle;
const noop = () => {};

test('a new trace invalidates the previous report', () => {
  const state = { ...initialState, reportHtml: '<p>Old investigation</p>' };
  assert.equal(appReducer(state, { type: 'SET_TRACE', payload: bundle.trace }).reportHtml, null);
});

test('switching scenarios clears audit and revealed data from the previous investigation', () => {
  const state = {
    ...initialState, auditEntries: bundle.audit, revealedValue: 'test-only-sensitive-value',
    revealDialog: { open: true, rowIndex: 0, field: 'phone', currentMaskedValue: '***' },
  };
  const next = appReducer(state, { type: 'SET_SCENARIO', payload: bundle.scenario });
  assert.equal(next.revealedValue, null);
  assert.equal(next.revealDialog, null);
  assert.deepEqual(next.auditEntries, []);
});

test('a reveal response arriving after close is discarded', () => {
  const next = appReducer(initialState, { type: 'SET_REVEALED_VALUE', payload: 'test-only-sensitive-value' });
  assert.equal(next.revealedValue, null);
});

test('judge picker includes every returned actor, including service accounts', () => {
  const html = renderToStaticMarkup(<InjectDialog open actors={bundle.scenario.actors} busy={false}
    error={null} onConfirm={noop} onCancel={noop} />);
  for (const actor of bundle.scenario.actors) assert.ok(html.includes(`value="${actor.id}"`), actor.id);
  assert.ok(html.includes('role="dialog"'));
});

test('a pinned origin still permits a simulated canary alert, with offline and busy guards', () => {
  const props = { chokepoints: [], recommendedEvidence: [], originPinned: true,
    canaryHits: ['can:example'], canaryAlert: null, offlineReplay: false, busy: false, onCanaryAlert: noop };
  const live = renderToStaticMarkup(<ContainmentTab {...props} />);
  assert.match(live, /Simulate canary alert/);
  assert.doesNotMatch(live, /100% confidence/);
  for (const guard of [{ offlineReplay: true }, { busy: true }]) {
    assert.match(renderToStaticMarkup(<ContainmentTab {...props} {...guard} />), /<button[^>]* disabled=""/);
  }
});

test('report preview is sandboxed without script or same-origin privileges', () => {
  const html = renderToStaticMarkup(<ReportTab trace_id="trc:test" reportHtml="<p>Report</p>"
    busy={false} offlineReplay={false} onDownload={noop} />);
  assert.match(html, /sandbox=""/);
});

test('offline replay disables the Telegram export action', () => {
  const html = renderToStaticMarkup(<TelegramChat discovery={bundle.scenario.discovery}
    scenario_id={bundle.scenario.id} busy={false} offlineReplay onExportAndTrace={noop} />);
  assert.match(html, /<button[^>]* disabled=""/);
});

test('masked cells have keyboard-accessible reveal buttons, disabled during offline replay', () => {
  for (const offlineReplay of [false, true]) {
    const html = renderToStaticMarkup(<IncidentPanel scenario={bundle.scenario} leakSample={bundle.scenario.leak_sample}
      hasTraced busy={false} offlineReplay={offlineReplay} onReveal={noop} onExportAndTrace={noop} />);
    const buttons = html.match(/<button[^>]*aria-label="Reveal [^"]+"[^>]*>/g) || [];
    assert.equal(buttons.length, bundle.scenario.leak_sample.masked_preview.length * bundle.scenario.leak_sample.columns.length);
    for (const button of buttons) assert.equal(button.includes(' disabled=""'), offlineReplay);
  }
});
