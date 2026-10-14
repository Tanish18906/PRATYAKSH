// Derived sentences for the answer banner and right rail. Reads TraceResult only; never recomputes scores or paths.

import { Evidence, Hypothesis, TraceResult } from '../types/contract';
import { displayName, formatDay, NameSource, prettyIds } from './names';

export function sourceSentence(trace: TraceResult, names?: NameSource | null): string | null {
  const origin = trace.hypotheses[0]?.origin_artifact;
  if (!origin) return null;
  const made = trace.graph.edges.find((e) => e.from === origin);
  const name = displayName(origin, names);
  if (!made) return name;
  return `${name}, ${prettyIds(made.label, names)}${made.ts ? ` on ${formatDay(made.ts)}` : ''}`;
}

export function originContainment(trace: TraceResult): number | null {
  const origin = trace.hypotheses[0]?.origin_artifact;
  return trace.origin_candidates.find((c) => c.artifact_id === origin)?.containment ?? null;
}

export function routeStops(h: Hypothesis): string[] {
  return h.hops.length ? [h.hops[0].from_loc, ...h.hops.map((hop) => hop.to_loc)] : [];
}

// "Ravi Menon: Bi Warehouse, then Ravi Menon laptop, then Telegram Leak Channel"
export function routeSentence(h: Hypothesis, names?: NameSource | null): string {
  const who = h.actors.map((a) => displayName(a, names)).join(' and ') || 'Unknown actor';
  return `${who}: ${routeStops(h).map((l) => displayName(l, names)).join(', then ')}`;
}

// Up to three bullets for "Why we think so": one per kind, in this order
const WHY_ORDER: Evidence['kind'][] = ['fingerprint', 'observed', 'inferred', 'anomaly'];

export function whyBullets(h: Hypothesis): Evidence[] {
  return WHY_ORDER.map((k) => h.evidence.find((e) => e.kind === k)).filter((e): e is Evidence => Boolean(e)).slice(0, 3);
}
