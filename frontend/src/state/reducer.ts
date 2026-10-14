// State management reducer for PUGMARK
// Follows state specification in docs/FRONTEND.md section 8

import {
  Archetype,
  ScenarioSummary,
  LeakSample,
  TraceResult,
  BenchmarkResult,
  AuditEntry,
} from '../types/contract';
import type { sendCanaryAlert } from '../api/client';

// Export and trace shows these steps in order while the real calls run underneath
export const TRACE_STEPS = [
  'Exporting the leaked file from the channel...',
  'Fingerprinting the leaked records against company exports...',
  'Tracing custody routes through the event logs...',
  'Ranking routes and finding where to cut...',
];

export type ActiveTab = 'investigation' | 'origin' | 'report' | 'audit' | 'benchmark';

export interface ControlsState {
  archetype: Archetype;
  seed: number;
  log_loss: number;
  canary_mode: boolean;
}

export interface RevealDialogState {
  open: boolean;
  rowIndex: number;
  field: string;
  currentMaskedValue: string;
}

export interface AppState {
  controls: ControlsState;
  scenario: ScenarioSummary | null;
  leakSample: LeakSample | null;
  trace: TraceResult | null;
  benchmark: BenchmarkResult | null;
  auditEntries: AuditEntry[];
  reportHtml: string | null;
  canaryAlert: Awaited<ReturnType<typeof sendCanaryAlert>>['alert'] | null;
  selectedPathId: string | null;
  activeTab: ActiveTab;
  offlineReplay: boolean;
  busy: boolean;
  busyMessage: string | null;
  error: string | null;
  revealDialog: RevealDialogState | null;
  revealedValue: string | null;
  injectDialogOpen: boolean;
}

export const initialControls: ControlsState = {
  archetype: 'A1',
  seed: 42,
  log_loss: 0.4,
  canary_mode: true,
};

export const initialState: AppState = {
  controls: initialControls,
  scenario: null,
  leakSample: null,
  trace: null,
  benchmark: null,
  auditEntries: [],
  reportHtml: null,
  canaryAlert: null,
  selectedPathId: null,
  activeTab: 'investigation',
  offlineReplay: false,
  busy: false,
  busyMessage: null,
  error: null,
  revealDialog: null,
  revealedValue: null,
  injectDialogOpen: false,
};

export type AppAction =
  | { type: 'SET_CONTROLS'; payload: Partial<ControlsState> }
  | { type: 'SET_SCENARIO'; payload: ScenarioSummary }
  | { type: 'SET_LEAK_SAMPLE'; payload: LeakSample }
  | { type: 'SET_TRACE'; payload: TraceResult }
  | { type: 'SET_BENCHMARK'; payload: BenchmarkResult | null }
  | { type: 'SET_AUDIT_ENTRIES'; payload: AuditEntry[] }
  | { type: 'SET_REPORT_HTML'; payload: string | null }
  | { type: 'SET_CANARY_ALERT'; payload: AppState['canaryAlert'] }
  | { type: 'SET_SELECTED_PATH'; payload: string | null }
  | { type: 'SET_ACTIVE_TAB'; payload: ActiveTab }
  | { type: 'SET_OFFLINE_REPLAY'; payload: boolean }
  | { type: 'SET_BUSY'; payload: { busy: boolean; message?: string | null } }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'OPEN_REVEAL_DIALOG'; payload: { rowIndex: number; field: string; currentMaskedValue: string } }
  | { type: 'CLOSE_REVEAL_DIALOG' }
  | { type: 'SET_REVEALED_VALUE'; payload: string | null }
  | { type: 'SET_INJECT_DIALOG_OPEN'; payload: boolean }
  | {
      type: 'LOAD_BUNDLE';
      payload: {
        scenario: ScenarioSummary;
        trace: TraceResult;
        audit: AuditEntry[];
        benchmark: BenchmarkResult | null;
        report_html: string;
        offlineReplay: boolean;
      };
    };

export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_CONTROLS':
      return {
        ...state,
        controls: { ...state.controls, ...action.payload },
      };

    case 'SET_SCENARIO':
      return {
        ...state,
        scenario: action.payload,
        leakSample: action.payload.leak_sample,
        // Reset old trace when a new scenario is loaded
        trace: null,
        reportHtml: null,
        canaryAlert: null,
        auditEntries: [],
        revealDialog: null,
        revealedValue: null,
        selectedPathId: null,
        controls: {
          archetype: action.payload.archetype,
          seed: action.payload.seed,
          log_loss: action.payload.params.log_loss,
          canary_mode: action.payload.params.canary_mode,
        },
      };

    case 'SET_LEAK_SAMPLE':
      return {
        ...state,
        leakSample: action.payload,
      };

    case 'SET_TRACE': {
      const topPathId = action.payload.hypotheses.length > 0 ? action.payload.hypotheses[0].path_id : null;
      return {
        ...state,
        trace: action.payload,
        reportHtml: null,
        canaryAlert: null,
        selectedPathId: topPathId,
        activeTab: 'investigation',
      };
    }

    case 'SET_BENCHMARK':
      return {
        ...state,
        benchmark: action.payload,
      };

    case 'SET_AUDIT_ENTRIES':
      return {
        ...state,
        auditEntries: action.payload,
      };

    case 'SET_REPORT_HTML':
      return {
        ...state,
        reportHtml: action.payload,
      };

    case 'SET_CANARY_ALERT':
      return { ...state, canaryAlert: action.payload };

    case 'SET_SELECTED_PATH':
      return {
        ...state,
        selectedPathId: action.payload,
      };

    case 'SET_ACTIVE_TAB':
      return {
        ...state,
        activeTab: action.payload,
      };

    case 'SET_OFFLINE_REPLAY':
      return {
        ...state,
        offlineReplay: action.payload,
      };

    case 'SET_BUSY':
      return {
        ...state,
        busy: action.payload.busy,
        busyMessage: action.payload.message || null,
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
      };

    case 'OPEN_REVEAL_DIALOG':
      return {
        ...state,
        revealDialog: {
          open: true,
          rowIndex: action.payload.rowIndex,
          field: action.payload.field,
          currentMaskedValue: action.payload.currentMaskedValue,
        },
        revealedValue: null,
        error: null, // a stale error must not appear inside the new dialog
      };

    case 'CLOSE_REVEAL_DIALOG':
      return {
        ...state,
        revealDialog: null,
        revealedValue: null,
      };

    case 'SET_REVEALED_VALUE':
      return {
        ...state,
        revealedValue: state.revealDialog?.open ? action.payload : null,
      };

    case 'SET_INJECT_DIALOG_OPEN':
      return {
        ...state,
        injectDialogOpen: action.payload,
        error: action.payload ? null : state.error,
      };

    // Offline replay starts at the empty state like a live run; the bundled trace arrives on Export and trace
    case 'LOAD_BUNDLE': {
      return {
        ...state,
        scenario: action.payload.scenario,
        leakSample: action.payload.scenario.leak_sample,
        trace: null,
        auditEntries: action.payload.audit,
        benchmark: action.payload.benchmark,
        reportHtml: null,
        selectedPathId: null,
        offlineReplay: action.payload.offlineReplay,
        controls: {
          archetype: action.payload.scenario.archetype,
          seed: action.payload.scenario.seed,
          log_loss: action.payload.scenario.params.log_loss,
          canary_mode: action.payload.scenario.params.canary_mode,
        },
      };
    }

    default:
      return state;
  }
}
