// Typed API client for PUGMARK
// Implements endpoints specified in docs/01_DATA_CONTRACT.md section 12 and docs/FRONTEND.md section 7

import {
  Archetype,
  Scale,
  ScenarioSummary,
  PublicScenario,
  LeakSample,
  TraceResult,
  AuditEntry,
  BenchmarkResult,
  DemoBundle,
  ApiError,
} from '../types/contract';

export class ApiRequestError extends Error {
  code: string;
  status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.name = 'ApiRequestError';
    this.code = code;
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const res = await fetch(path, { ...options, headers });

  if (!res.ok) {
    let errorCode = 'bad_request';
    let errorMessage = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const errJson = (await res.json()) as ApiError;
      if (errJson && errJson.error) {
        errorCode = errJson.error.code;
        errorMessage = errJson.error.message;
      }
    } catch {
      // Non-json error response
    }
    throw new ApiRequestError(errorCode, errorMessage, res.status);
  }

  return (await res.json()) as T;
}

export async function getHealth(signal?: AbortSignal): Promise<{ status: string; contract_version: string; engine_version: string }> {
  return request<{ status: string; contract_version: string; engine_version: string }>('/api/health', {
    method: 'GET',
    signal,
  });
}

export async function generateScenario(params: {
  archetype: Archetype;
  seed: number;
  log_loss: number;
  canary_mode: boolean;
  scale: Scale;
}): Promise<ScenarioSummary> {
  return request<ScenarioSummary>('/api/scenario/generate', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getScenario(id: string, full = false): Promise<ScenarioSummary | PublicScenario> {
  const url = full ? `/api/scenario/${encodeURIComponent(id)}?full=true` : `/api/scenario/${encodeURIComponent(id)}`;
  return request<ScenarioSummary | PublicScenario>(url, { method: 'GET' });
}

export async function exportLeak(params: {
  scenario_id: string;
  message_id: number;
}): Promise<{ leak_sample: LeakSample; file: { name: string; size_bytes: number } }> {
  return request<{ leak_sample: LeakSample; file: { name: string; size_bytes: number } }>('/api/leak/export', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function traceScenario(params: {
  scenario_id: string;
  top_k?: number;
}): Promise<TraceResult> {
  return request<TraceResult>('/api/trace', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function injectLeak(params: {
  base_scenario_id: string;
  actor: string;
}): Promise<ScenarioSummary> {
  return request<ScenarioSummary>('/api/inject', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function sendCanaryAlert(params: {
  scenario_id: string;
  canary_id: string;
}): Promise<{
  alert: { canary_id: string; export_id: string; ts: string; message: string };
  trace: TraceResult;
}> {
  return request<{
    alert: { canary_id: string; export_id: string; ts: string; message: string };
    trace: TraceResult;
  }>('/api/canary/alert', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function revealValue(params: {
  scenario_id: string;
  object: 'leak_sample';
  row_index: number;
  field: string;
  reason: string;
}): Promise<{ value: string; audit_id: string }> {
  if (!params.reason || params.reason.trim().length < 8) {
    throw new ApiRequestError('reason_required', 'Reason must be at least 8 characters long', 400);
  }
  return request<{ value: string; audit_id: string }>('/api/reveal', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getAudit(scenario_id?: string): Promise<{ entries: AuditEntry[] }> {
  const url = scenario_id ? `/api/audit?scenario_id=${encodeURIComponent(scenario_id)}` : '/api/audit';
  return request<{ entries: AuditEntry[] }>(url, { method: 'GET' });
}

export async function runBenchmark(params: {
  seed_range: [number, number];
  loss_levels: number[];
  archetypes: Archetype[];
}): Promise<{ benchmark_id: string }> {
  return request<{ benchmark_id: string }>('/api/benchmark/run', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export async function getBenchmark(id: string): Promise<BenchmarkResult> {
  return request<BenchmarkResult>(`/api/benchmark/${encodeURIComponent(id)}`, { method: 'GET' });
}

export async function getReport(trace_id: string): Promise<string> {
  const res = await fetch(`/api/report/${encodeURIComponent(trace_id)}`);
  if (!res.ok) {
    throw new ApiRequestError('not_found', `Failed to load report: ${res.statusText}`, res.status);
  }
  return res.text();
}

export async function fetchOfflineDemoBundle(): Promise<DemoBundle> {
  const res = await fetch('/demo.json');
  if (!res.ok) {
    throw new Error(`Failed to load /demo.json: ${res.statusText}`);
  }
  const bundle = (await res.json()) as DemoBundle;
  if (bundle.contract_version !== '1.0') {
    throw new Error(`Incompatible contract version in demo.json: expected 1.0, got ${bundle.contract_version}`);
  }
  return bundle;
}
