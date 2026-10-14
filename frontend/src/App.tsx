// PUGMARK app shell: header, Investigation grid, secondary tabs, Scenario drawer and dialogs
// Layout follows docs/ui-REDESIGN/UI_LAYOUT.md; behaviour follows docs/ui-REDESIGN/UX_FLOW.md

import React, { useRef, useState } from 'react';
import { AppProvider, useApp } from './state/AppContext';
import Header from './components/Header';
import ScenarioControls from './components/ScenarioControls';
import IncidentPanel from './components/IncidentPanel';
import AnswerBanner from './components/AnswerBanner';
import ProvenanceGraph from './components/ProvenanceGraph';
import HypothesisPanel from './components/HypothesisPanel';
import ContainmentTab from './components/ContainmentTab';
import OriginMatchTab from './components/OriginMatchTab';
import BenchmarkTab from './components/BenchmarkTab';
import ReportTab from './components/ReportTab';
import AuditTab from './components/AuditTab';
import RevealDialog from './components/RevealDialog';
import InjectDialog from './components/InjectDialog';
import ErrorMessage from './components/ErrorMessage';
import { prettyIds } from './utils/names';
import { TRACE_STEPS } from './state/reducer';

const FOOTER = 'Simulated data. Rankings are relative likelihoods, not a finding of responsibility.';

const Dashboard: React.FC = () => {
  const {
    state,
    setControls,
    setActiveTab,
    setSelectedPath,
    dismissError,
    openRevealDialog,
    closeRevealDialog,
    setInjectDialogOpen,
    handleGenerate,
    handleExportAndTrace,
    handleTrace,
    handleRevealConfirm,
    handleInjectConfirm,
    handleCanaryAlert,
    handleRunBenchmark,
    handleDownloadReport,
  } = useApp();

  const {
    controls,
    scenario,
    leakSample,
    trace,
    benchmark,
    auditEntries,
    reportHtml,
    canaryAlert,
    selectedPathId,
    activeTab,
    offlineReplay,
    busy,
    busyMessage,
    error,
    revealDialog,
    revealedValue,
    injectDialogOpen,
  } = state;

  const [drawerOpen, setDrawerOpen] = useState(false);
  const scenarioButtonRef = useRef<HTMLButtonElement | null>(null);
  const closeDrawer = () => {
    setDrawerOpen(false);
    scenarioButtonRef.current?.focus();
  };

  const hypotheses = trace?.hypotheses || [];
  const sample = leakSample || scenario?.leak_sample || null;
  // Stage dots: 1 Discover, 2 Match (exporting), 3 Trace (engine running), 4 Act (result shown)
  const step = busy && busyMessage ? TRACE_STEPS.indexOf(busyMessage) : -1;
  const stage = trace ? 4 : step >= 2 ? 3 : step >= 0 ? 2 : scenario ? 1 : 0;

  const jumpTo = (target: 'cut' | 'collect') => {
    const smooth = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    document.getElementById(`card-${target}`)?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto', block: 'start' });
  };

  const tabPanel = (children: React.ReactNode) => (
    <div role="tabpanel" aria-labelledby={`tab-${activeTab}`} className="h-full overflow-y-auto p-4">
      <div className="mx-auto max-w-[1280px] space-y-4">
        <ErrorMessage message={error} onDismiss={dismissError} />
        {children}
      </div>
    </div>
  );

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-bg text-ink">
      <Header
        offlineReplay={offlineReplay}
        simulated
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onOpenScenario={() => setDrawerOpen(true)}
        scenarioButtonRef={scenarioButtonRef}
      />

      <main className="min-h-0 flex-1">
        {activeTab === 'investigation' ? (
          <div
            role="tabpanel"
            aria-labelledby="tab-investigation"
            className="grid h-full grid-cols-1 gap-4 overflow-y-auto p-4 pb-2 xl:grid-cols-[264px_minmax(0,1fr)_320px] xl:overflow-hidden wide:grid-cols-[320px_minmax(0,1fr)_380px]"
          >
            <div className="min-h-0">
              <IncidentPanel
                scenario={scenario}
                leakSample={leakSample}
                hasTraced={hypotheses.length > 0}
                offlineReplay={offlineReplay}
                busy={busy}
                onReveal={(rIdx, field, val) => openRevealDialog(rIdx, field, val)}
                onExportAndTrace={handleExportAndTrace}
              />
            </div>

            <div className="flex min-h-[560px] flex-col gap-3 xl:min-h-0">
              <ErrorMessage message={error} onDismiss={dismissError} />
              <AnswerBanner trace={trace} names={scenario} busy={busy} step={step} onJump={jumpTo} />
              <div className="min-h-0 flex-1">
                <ProvenanceGraph
                  graph={trace?.graph || null}
                  hypotheses={hypotheses}
                  selectedPathId={selectedPathId}
                  onSelectPath={setSelectedPath}
                  names={scenario}
                  leak={sample ? { location: sample.found_at, found_ts: sample.found_ts } : null}
                  busy={busy}
                  stage={stage}
                />
              </div>
            </div>

            <div className="flex min-h-0 flex-col gap-4 xl:overflow-y-auto">
              <HypothesisPanel
                hypotheses={hypotheses}
                selectedPathId={selectedPathId}
                onSelectPath={setSelectedPath}
                names={scenario}
                busy={busy}
              />
              {trace && (
                <ContainmentTab
                  chokepoints={trace.chokepoints}
                  recommendedEvidence={trace.recommended_evidence}
                  originPinned={trace.origin_pinned}
                  canaryHits={sample?.canary_hits || []}
                  canaryAlert={canaryAlert}
                  busy={busy}
                  offlineReplay={offlineReplay}
                  onCanaryAlert={handleCanaryAlert}
                  names={scenario}
                />
              )}
            </div>
          </div>
        ) : activeTab === 'origin' ? (
          tabPanel(<OriginMatchTab candidates={trace?.origin_candidates || []} names={scenario} />)
        ) : activeTab === 'report' ? (
          tabPanel(
            <ReportTab
              trace_id={trace?.trace_id || null}
              reportHtml={reportHtml}
              busy={busy}
              offlineReplay={offlineReplay}
              onDownload={handleDownloadReport}
              summary={hypotheses[0] ? prettyIds(hypotheses[0].summary_text, scenario) : null}
            />
          )
        ) : activeTab === 'audit' ? (
          tabPanel(<AuditTab entries={auditEntries} />)
        ) : (
          tabPanel(<BenchmarkTab benchmark={benchmark} busy={busy} offlineReplay={offlineReplay} onRun={handleRunBenchmark} />)
        )}
      </main>

      <footer className="shrink-0 px-4 pb-2 text-xs text-ink-3">{FOOTER}</footer>

      <ScenarioControls
        open={drawerOpen}
        onClose={closeDrawer}
        scenario={scenario}
        controls={controls}
        busy={busy}
        offlineReplay={offlineReplay}
        onControlsChange={setControls}
        onGenerate={handleGenerate}
        onTrace={handleTrace}
        onInject={() => setInjectDialogOpen(true)}
        onBenchmark={() => {
          setActiveTab('benchmark');
          handleRunBenchmark();
        }}
      />

      {revealDialog && (
        <RevealDialog
          open={revealDialog.open}
          field={revealDialog.field}
          rowIndex={revealDialog.rowIndex}
          currentMaskedValue={revealDialog.currentMaskedValue}
          revealedValue={revealedValue}
          error={error}
          busy={busy}
          onConfirm={handleRevealConfirm}
          onCancel={closeRevealDialog}
        />
      )}

      {scenario && injectDialogOpen && (
        <InjectDialog
          open={injectDialogOpen}
          actors={scenario.actors}
          busy={busy}
          error={error}
          onConfirm={handleInjectConfirm}
          onCancel={() => setInjectDialogOpen(false)}
        />
      )}

      {busy && busyMessage && step < 0 && (
        <div role="status" aria-live="polite" className="fixed bottom-8 right-4 z-30 flex items-center gap-2.5 rounded-ctl border border-line bg-surface px-3 py-2 text-[13px] text-ink-2 shadow-pop">
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-accent border-t-transparent" aria-hidden="true" />
          {busyMessage}
        </div>
      )}
    </div>
  );
};

export const App: React.FC = () => (
  <AppProvider>
    <Dashboard />
  </AppProvider>
);

export default App;
