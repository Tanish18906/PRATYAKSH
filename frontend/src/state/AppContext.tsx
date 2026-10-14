// AppContext: Central React context for PUGMARK
// Implements investigation flows from docs/UI_UX_DESIGN.md section 5 and docs/FRONTEND.md section 8 & 9

import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import { AppState, initialState, appReducer, ActiveTab, ControlsState } from './reducer';
import * as api from '../api/client';

interface AppContextValue {
  state: AppState;
  setControls: (controls: Partial<ControlsState>) => void;
  setActiveTab: (tab: ActiveTab) => void;
  setSelectedPath: (pathId: string | null) => void;
  dismissError: () => void;
  openRevealDialog: (rowIndex: number, field: string, currentMaskedValue: string) => void;
  closeRevealDialog: () => void;
  setInjectDialogOpen: (open: boolean) => void;
  handleGenerate: () => Promise<void>;
  handleExportAndTrace: (messageId: number) => Promise<void>;
  handleTrace: () => Promise<void>;
  handleRevealConfirm: (reason: string) => Promise<void>;
  handleInjectConfirm: (actorId: string) => Promise<void>;
  handleCanaryAlert: (canaryId: string) => Promise<void>;
  handleRunBenchmark: () => Promise<void>;
  handleDownloadReport: () => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  const loadOfflineFallback = useCallback(async (errorMessage?: string) => {
    try {
      dispatch({ type: 'SET_BUSY', payload: { busy: true, message: 'Loading offline replay bundle...' } });
      const bundle = await api.fetchOfflineDemoBundle();
      dispatch({
        type: 'LOAD_BUNDLE',
        payload: {
          scenario: bundle.scenario,
          trace: bundle.trace,
          audit: bundle.audit,
          benchmark: bundle.benchmark,
          report_html: bundle.report_html,
          offlineReplay: true,
        },
      });
      if (errorMessage) {
        console.warn('Backend unavailable, running in Offline Replay mode:', errorMessage);
      }
    } catch (err: unknown) {
      dispatch({
        type: 'SET_ERROR',
        payload: err instanceof Error ? err.message : 'Failed to load demo bundle',
      });
    } finally {
      dispatch({ type: 'SET_BUSY', payload: { busy: false } });
    }
  }, []);

  // Startup initialization: Health check with 2-second timeout
  useEffect(() => {
    let mounted = true;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const init = async () => {
      try {
        await api.getHealth(controller.signal);
        clearTimeout(timeoutId);
        if (!mounted) return;

        // Backend is up! Generate initial seed 42 A1 scenario
        dispatch({ type: 'SET_BUSY', payload: { busy: true, message: 'Initializing simulated scenario...' } });
        const scn = await api.generateScenario({
          archetype: 'A1',
          seed: 42,
          log_loss: 0.4,
          canary_mode: true,
          scale: 'demo',
        });
        if (!mounted) return;
        dispatch({ type: 'SET_SCENARIO', payload: scn });
        dispatch({ type: 'SET_OFFLINE_REPLAY', payload: false });

        // Load audit
        try {
          const audit = await api.getAudit(scn.id);
          if (mounted) dispatch({ type: 'SET_AUDIT_ENTRIES', payload: audit.entries });
        } catch {
          // Non-critical audit fetch failure
        }
      } catch (err: unknown) {
        if (!mounted) return;
        // Backend failure or timeout: enter Offline Replay mode
        await loadOfflineFallback(err instanceof Error ? err.message : 'Connection failed');
      } finally {
        if (mounted) {
          dispatch({ type: 'SET_BUSY', payload: { busy: false } });
        }
      }
    };

    init();

    return () => {
      mounted = false;
      controller.abort();
      clearTimeout(timeoutId);
    };
  }, [loadOfflineFallback]);

  const setControls = useCallback((controls: Partial<ControlsState>) => {
    dispatch({ type: 'SET_CONTROLS', payload: controls });
  }, []);

  const setActiveTab = useCallback((tab: ActiveTab) => {
    dispatch({ type: 'SET_ACTIVE_TAB', payload: tab });
  }, []);

  const setSelectedPath = useCallback((pathId: string | null) => {
    dispatch({ type: 'SET_SELECTED_PATH', payload: pathId });
  }, []);

  const dismissError = useCallback(() => {
    dispatch({ type: 'SET_ERROR', payload: null });
  }, []);

  const openRevealDialog = useCallback((rowIndex: number, field: string, currentMaskedValue: string) => {
    dispatch({ type: 'OPEN_REVEAL_DIALOG', payload: { rowIndex, field, currentMaskedValue } });
  }, []);

  const closeRevealDialog = useCallback(() => {
    dispatch({ type: 'CLOSE_REVEAL_DIALOG' });
  }, []);

  const setInjectDialogOpen = useCallback((open: boolean) => {
    dispatch({ type: 'SET_INJECT_DIALOG_OPEN', payload: open });
  }, []);

  // Action: Generate scenario
  const handleGenerate = useCallback(async () => {
    if (state.offlineReplay) return;
    try {
      dispatch({ type: 'SET_BUSY', payload: { busy: true, message: 'Generating simulated scenario...' } });
      dispatch({ type: 'SET_ERROR', payload: null });

      const scn = await api.generateScenario({
        archetype: state.controls.archetype,
        seed: Number(state.controls.seed),
        log_loss: Number(state.controls.log_loss),
        canary_mode: Boolean(state.controls.canary_mode),
        scale: 'demo',
      });
      dispatch({ type: 'SET_SCENARIO', payload: scn });

      const audit = await api.getAudit(scn.id);
      dispatch({ type: 'SET_AUDIT_ENTRIES', payload: audit.entries });
    } catch (err: unknown) {
      dispatch({ type: 'SET_ERROR', payload: err instanceof Error ? err.message : 'Generate failed' });
    } finally {
      dispatch({ type: 'SET_BUSY', payload: { busy: false } });
    }
  }, [state.offlineReplay, state.controls]);

  // Action: Export and Trace (core demo flow)
  const handleExportAndTrace = useCallback(async (messageId: number) => {
    if (!state.scenario) return;

    if (state.offlineReplay) {
      // In offline replay, demo bundle trace is already available
      dispatch({ type: 'SET_ACTIVE_TAB', payload: 'origin' });
      return;
    }

    try {
      dispatch({ type: 'SET_BUSY', payload: { busy: true, message: 'Fingerprinting leaked sample & tracing origin paths...' } });
      dispatch({ type: 'SET_ERROR', payload: null });

      // 1. Export leaked sample from simulated discovery
      const exportRes = await api.exportLeak({
        scenario_id: state.scenario.id,
        message_id: messageId,
      });
      dispatch({ type: 'SET_LEAK_SAMPLE', payload: exportRes.leak_sample });

      // 2. Run tracing engine
      const traceRes = await api.traceScenario({
        scenario_id: state.scenario.id,
        top_k: 5,
      });
      dispatch({ type: 'SET_TRACE', payload: traceRes });

      // 3. Refresh audit and HTML report
      try {
        const auditRes = await api.getAudit(state.scenario.id);
        dispatch({ type: 'SET_AUDIT_ENTRIES', payload: auditRes.entries });
        const reportRes = await api.getReport(traceRes.trace_id);
        dispatch({ type: 'SET_REPORT_HTML', payload: reportRes });
      } catch {
        // Non-fatal
      }
    } catch (err: unknown) {
      dispatch({ type: 'SET_ERROR', payload: err instanceof Error ? err.message : 'Export and trace failed' });
    } finally {
      dispatch({ type: 'SET_BUSY', payload: { busy: false } });
    }
  }, [state.scenario, state.offlineReplay]);

  // Action: Re-trace button
  const handleTrace = useCallback(async () => {
    if (!state.scenario || state.offlineReplay) return;
    try {
      dispatch({ type: 'SET_BUSY', payload: { busy: true, message: 'Re-evaluating custody paths...' } });
      dispatch({ type: 'SET_ERROR', payload: null });

      const traceRes = await api.traceScenario({
        scenario_id: state.scenario.id,
        top_k: 5,
      });
      dispatch({ type: 'SET_TRACE', payload: traceRes });

      const auditRes = await api.getAudit(state.scenario.id);
      dispatch({ type: 'SET_AUDIT_ENTRIES', payload: auditRes.entries });
    } catch (err: unknown) {
      dispatch({ type: 'SET_ERROR', payload: err instanceof Error ? err.message : 'Trace failed' });
    } finally {
      dispatch({ type: 'SET_BUSY', payload: { busy: false } });
    }
  }, [state.scenario, state.offlineReplay]);

  // Action: Confirm Reveal with Reason
  const handleRevealConfirm = useCallback(async (reason: string) => {
    if (!state.scenario || !state.revealDialog || state.offlineReplay) return;
    try {
      dispatch({ type: 'SET_BUSY', payload: { busy: true, message: 'Auditing and revealing data...' } });
      dispatch({ type: 'SET_ERROR', payload: null });

      const res = await api.revealValue({
        scenario_id: state.scenario.id,
        object: 'leak_sample',
        row_index: state.revealDialog.rowIndex,
        field: state.revealDialog.field,
        reason,
      });

      dispatch({ type: 'SET_REVEALED_VALUE', payload: res.value });

      // Refresh audit
      const auditRes = await api.getAudit(state.scenario.id);
      dispatch({ type: 'SET_AUDIT_ENTRIES', payload: auditRes.entries });
    } catch (err: unknown) {
      dispatch({ type: 'SET_ERROR', payload: err instanceof Error ? err.message : 'Reveal failed' });
    } finally {
      dispatch({ type: 'SET_BUSY', payload: { busy: false } });
    }
  }, [state.scenario, state.revealDialog, state.offlineReplay]);

  // Action: Judge Inject
  const handleInjectConfirm = useCallback(async (actorId: string) => {
    if (!state.scenario || state.offlineReplay) return;
    try {
      dispatch({ type: 'SET_BUSY', payload: { busy: true, message: `Injecting leak via ${actorId}...` } });
      dispatch({ type: 'SET_ERROR', payload: null });
      dispatch({ type: 'SET_INJECT_DIALOG_OPEN', payload: false });

      const newScenario = await api.injectLeak({
        base_scenario_id: state.scenario.id,
        actor: actorId,
      });
      dispatch({ type: 'SET_SCENARIO', payload: newScenario });

      const auditRes = await api.getAudit(newScenario.id);
      dispatch({ type: 'SET_AUDIT_ENTRIES', payload: auditRes.entries });
    } catch (err: unknown) {
      dispatch({ type: 'SET_ERROR', payload: err instanceof Error ? err.message : 'Injection failed' });
    } finally {
      dispatch({ type: 'SET_BUSY', payload: { busy: false } });
    }
  }, [state.scenario, state.offlineReplay]);

  // Action: Canary Alert
  const handleCanaryAlert = useCallback(async (canaryId: string) => {
    if (!state.scenario || state.offlineReplay) return;
    try {
      dispatch({ type: 'SET_BUSY', payload: { busy: true, message: 'Simulating canary trigger...' } });
      dispatch({ type: 'SET_ERROR', payload: null });

      const res = await api.sendCanaryAlert({
        scenario_id: state.scenario.id,
        canary_id: canaryId,
      });

      dispatch({ type: 'SET_TRACE', payload: res.trace });

      const auditRes = await api.getAudit(state.scenario.id);
      dispatch({ type: 'SET_AUDIT_ENTRIES', payload: auditRes.entries });
    } catch (err: unknown) {
      dispatch({ type: 'SET_ERROR', payload: err instanceof Error ? err.message : 'Canary alert failed' });
    } finally {
      dispatch({ type: 'SET_BUSY', payload: { busy: false } });
    }
  }, [state.scenario, state.offlineReplay]);

  // Action: Benchmark
  const handleRunBenchmark = useCallback(async () => {
    if (state.offlineReplay) return;
    try {
      dispatch({ type: 'SET_BUSY', payload: { busy: true, message: 'Starting benchmark run across loss levels...' } });
      dispatch({ type: 'SET_ERROR', payload: null });

      const runRes = await api.runBenchmark({
        seed_range: [50, 199],
        loss_levels: [0.0, 0.2, 0.4, 0.6],
        archetypes: ['A1', 'A2', 'A3'],
      });

      // Poll until done
      let result = await api.getBenchmark(runRes.benchmark_id);
      while (result.status === 'running') {
        dispatch({ type: 'SET_BENCHMARK', payload: result });
        await new Promise((r) => setTimeout(r, 1000));
        result = await api.getBenchmark(runRes.benchmark_id);
      }
      dispatch({ type: 'SET_BENCHMARK', payload: result });

      if (state.scenario) {
        const auditRes = await api.getAudit(state.scenario.id);
        dispatch({ type: 'SET_AUDIT_ENTRIES', payload: auditRes.entries });
      }
    } catch (err: unknown) {
      dispatch({ type: 'SET_ERROR', payload: err instanceof Error ? err.message : 'Benchmark run failed' });
    } finally {
      dispatch({ type: 'SET_BUSY', payload: { busy: false } });
    }
  }, [state.offlineReplay, state.scenario]);

  // Action: Download HTML report
  const handleDownloadReport = useCallback(() => {
    if (!state.reportHtml) return;
    const blob = new Blob([state.reportHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `pugmark-incident-report-${state.trace?.trace_id || 'export'}.html`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }, [state.reportHtml, state.trace]);

  const value: AppContextValue = {
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
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// eslint-disable-next-line react-refresh/only-export-components
export const useApp = (): AppContextValue => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
