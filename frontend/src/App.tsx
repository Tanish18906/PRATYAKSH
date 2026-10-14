// Main App Component for PUGMARK
// Follows UI_UX_DESIGN.md section 4 & 5 and FRONTEND.md section 4

import React from 'react';
import { AppProvider, useApp } from './state/AppContext';
import Header from './components/Header';
import ScenarioControls from './components/ScenarioControls';
import IncidentPanel from './components/IncidentPanel';
import ProvenanceGraph from './components/ProvenanceGraph';
import HypothesisPanel from './components/HypothesisPanel';
import OriginMatchTab from './components/OriginMatchTab';
import ContainmentTab from './components/ContainmentTab';
import BenchmarkTab from './components/BenchmarkTab';
import ReportTab from './components/ReportTab';
import AuditTab from './components/AuditTab';
import RevealDialog from './components/RevealDialog';
import InjectDialog from './components/InjectDialog';
import ErrorMessage from './components/ErrorMessage';
import { ActiveTab } from './state/reducer';

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

  const hasTraced = Boolean(trace && trace.hypotheses.length > 0);

  const tabs: Array<{ id: ActiveTab; label: string; badge?: number | string }> = [
    {
      id: 'origin',
      label: 'Origin match',
      badge: trace?.origin_candidates.length,
    },
    {
      id: 'containment',
      label: 'Containment',
      badge: trace?.chokepoints.length,
    },
    {
      id: 'benchmark',
      label: 'Benchmark',
    },
    {
      id: 'report',
      label: 'Report',
      badge: reportHtml ? 'Ready' : undefined,
    },
    {
      id: 'audit',
      label: 'Audit',
      badge: auditEntries.length > 0 ? auditEntries.length : undefined,
    },
  ];

  return (
    <div className="min-h-screen bg-background text-text-primary flex flex-col font-sans select-text">
      {/* 1. Header */}
      <Header offlineReplay={offlineReplay} simulated={true} />

      {/* 2. Top Bar Controls */}
      <ScenarioControls
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

      {/* Main Content Area */}
      <main className="flex-1 p-4 lg:p-6 space-y-6 max-w-[1720px] mx-auto w-full">
        {/* Error Alert */}
        <ErrorMessage message={error} onDismiss={dismissError} />

        {/* 3. Three-Column Investigation Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left Column: Incident Panel (approx 25% = 3 cols) */}
          <div className="lg:col-span-3">
            <IncidentPanel
              scenario={scenario}
              leakSample={leakSample}
              hasTraced={hasTraced}
              offlineReplay={offlineReplay}
              busy={busy}
              onReveal={(rIdx, field, val) => openRevealDialog(rIdx, field, val)}
              onExportAndTrace={handleExportAndTrace}
            />
          </div>

          {/* Center Column: Provenance Graph (approx 50% = 6 cols) */}
          <div className="lg:col-span-6 flex flex-col">
            <div className="flex-1 min-h-[480px]">
              <ProvenanceGraph
                graph={trace?.graph || null}
                hypotheses={trace?.hypotheses || []}
                selectedPathId={selectedPathId}
                onSelectPath={setSelectedPath}
              />
            </div>
          </div>

          {/* Right Column: Ranked Hypotheses (approx 25% = 3 cols) */}
          <div className="lg:col-span-3">
            <HypothesisPanel
              hypotheses={trace?.hypotheses || []}
              selectedPathId={selectedPathId}
              onSelectPath={setSelectedPath}
            />
          </div>
        </div>

        {/* 4. Investigation Tabs Section */}
        <div className="bg-surface rounded-lg border border-border overflow-hidden shadow-sm">
          {/* Tab Navigation Header */}
          <div className="flex border-b border-border bg-surface-raised px-4 pt-2 space-x-1 overflow-x-auto">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2.5 text-xs font-semibold rounded-t-md transition-colors flex items-center space-x-2 border-t-2 ${
                    isActive
                      ? 'bg-surface text-accent border-accent shadow-xs'
                      : 'text-text-muted hover:text-text-primary border-transparent hover:bg-surface/50'
                  }`}
                >
                  <span>{tab.label}</span>
                  {tab.badge !== undefined && (
                    <span
                      className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                        isActive
                          ? 'bg-accent-dark text-accent'
                          : 'bg-surface text-text-muted border border-border'
                      }`}
                    >
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Tab Content Panel */}
          <div className="p-4 lg:p-6 bg-surface min-h-[300px]">
            {activeTab === 'origin' && (
              <OriginMatchTab candidates={trace?.origin_candidates || []} />
            )}

            {activeTab === 'containment' && (
              <ContainmentTab
                chokepoints={trace?.chokepoints || []}
                recommendedEvidence={trace?.recommended_evidence || []}
                originPinned={Boolean(trace?.origin_pinned)}
                canaryHits={leakSample?.canary_hits || []}
                offlineReplay={offlineReplay}
                onCanaryAlert={handleCanaryAlert}
              />
            )}

            {activeTab === 'benchmark' && (
              <BenchmarkTab
                benchmark={benchmark}
                busy={busy}
                offlineReplay={offlineReplay}
                onRun={handleRunBenchmark}
              />
            )}

            {activeTab === 'report' && (
              <ReportTab
                trace_id={trace?.trace_id || null}
                reportHtml={reportHtml}
                busy={busy}
                offlineReplay={offlineReplay}
                onDownload={handleDownloadReport}
              />
            )}

            {activeTab === 'audit' && <AuditTab entries={auditEntries} />}
          </div>
        </div>
      </main>

      {/* 5. Modals & Dialogs */}
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

      {scenario && (
        <InjectDialog
          open={injectDialogOpen}
          actors={scenario.actors}
          busy={busy}
          onConfirm={handleInjectConfirm}
          onCancel={() => setInjectDialogOpen(false)}
        />
      )}

      {/* Busy Spinner Overlay */}
      {busy && (
        <div className="fixed bottom-6 right-6 z-50 bg-surface-raised border border-accent/40 rounded-lg px-4 py-3 shadow-2xl flex items-center space-x-3">
          <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs font-mono font-medium text-text-primary">
            {busyMessage || 'Processing forensic operation...'}
          </span>
        </div>
      )}
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AppProvider>
      <Dashboard />
    </AppProvider>
  );
};

export default App;
