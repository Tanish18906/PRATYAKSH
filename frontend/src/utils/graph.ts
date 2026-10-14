// Provenance graph model: layout sized to the canvas, node card data, Cytoscape elements and edge styles (UI_LAYOUT.md section 3)
// Cytoscape draws only the edges and handles pointer events; node cards and edge labels are HTML on top, so text stays sharp.

import { ElementDefinition, StylesheetStyle } from 'cytoscape';
import { Graph as ContractGraph, Hypothesis } from '../types/contract';
import { ACTION_VERB, displayName, formatDay, NameSource } from './names';
import { IconName } from './icons';
import { TOKENS } from './tokens';

type NodeKind = ContractGraph['nodes'][number]['kind'];

// Card and spacing limits, in CSS px at zoom 1. The layout stretches between them to fill the canvas,
// so the graph is drawn at zoom 1 whenever it fits (spec's fixed 168px cards on a 240px grid were zoomed to ~0.7 at 1366).
export const PAD = 20;
export const ROUTE_H = 64; // cards on the selected route: name and time
export const SIDE_H = 48; // cards on other routes: compact
const CARD_W_MIN = 120;
const CARD_W_MAX = 212;
const GAP_MIN = 64; // room for the edge label pill between two cards
const GAP_MAX = 140;
const ROW_MIN = ROUTE_H / 2 + SIDE_H / 2 + 10;
const ROW_MAX = 120;
export const WIDE_CARD = 168; // below this the icon moves into the time row

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

export interface GraphLayout {
  positions: Record<string, { x: number; y: number }>;
  cardW: number;
  onRoute: Set<string>; // node ids on the selected route
}

// Left to right by hop depth; the selected route on one straight line, other routes on lanes below and above
export function computeLayout(
  graph: ContractGraph,
  hypotheses: Hypothesis[],
  selectedPathId: string | null,
  box: { w: number; h: number } = { w: 1100, h: 600 }
): GraphLayout {
  const depth: Record<string, number> = Object.fromEntries(graph.nodes.map((n) => [n.id, 0]));
  // Longest-path depth by relaxation; the node count bounds it and guards against a cycle
  for (let i = 0; i < graph.nodes.length; i++) {
    let changed = false;
    for (const e of graph.edges) {
      if (depth[e.to] < depth[e.from] + 1) {
        depth[e.to] = depth[e.from] + 1;
        changed = true;
      }
    }
    if (!changed) break;
  }

  const order = [
    ...hypotheses.filter((h) => h.path_id === selectedPathId),
    ...hypotheses.filter((h) => h.path_id !== selectedPathId),
  ];
  const lane: Record<string, number> = {};
  let next = 0;
  const laneValue = (k: number) => (k === 0 ? 0 : k % 2 ? (k + 1) / 2 : -k / 2); // 0, 1, -1, 2, -2 ...
  for (const h of order) {
    const value = laneValue(next++);
    for (const e of graph.edges) {
      if (!e.path_ids.includes(h.path_id)) continue;
      lane[e.from] ??= value;
      lane[e.to] ??= value;
    }
  }
  for (const n of graph.nodes) lane[n.id] ??= laneValue(next++);

  const cols = Math.max(...graph.nodes.map((n) => depth[n.id]), 0) + 1;
  const lanes = graph.nodes.map((n) => lane[n.id]);
  const span = Math.max(...lanes, 0) - Math.min(...lanes, 0);
  const innerW = box.w - 2 * PAD;
  const cardW = 2 * Math.floor(clamp((innerW - (cols - 1) * GAP_MIN) / cols, CARD_W_MIN, CARD_W_MAX) / 2); // even: no half-pixel text
  const gap = cols > 1 ? Math.floor(clamp((innerW - cols * cardW) / (cols - 1), GAP_MIN, GAP_MAX)) : 0;
  const row = span ? Math.floor(clamp((box.h - 2 * PAD - SIDE_H) / span, ROW_MIN, ROW_MAX)) : 0;

  const onRoute = new Set<string>();
  for (const e of graph.edges) {
    if (selectedPathId && e.path_ids.includes(selectedPathId)) {
      onRoute.add(e.from);
      onRoute.add(e.to);
    }
  }

  const positions = Object.fromEntries(
    graph.nodes.map((n) => [n.id, { x: Math.round(depth[n.id] * (cardW + gap)), y: Math.round(lane[n.id] * row) }])
  );
  return { positions, cardW, onRoute };
}

// Kept for callers that only need positions
export const computePositions = (
  graph: ContractGraph,
  hypotheses: Hypothesis[],
  selectedPathId: string | null,
  box?: { w: number; h: number }
) => computeLayout(graph, hypotheses, selectedPathId, box).positions;

// Short verb for an edge: the hop action when the edge is observed, "inferred, no log found" otherwise
export function edgeVerb(edge: ContractGraph['edges'][number], hypotheses: Hypothesis[]): string {
  if (edge.kind === 'inferred') return 'inferred, no log found';
  const hop = edge.event_id
    ? hypotheses.flatMap((h) => h.hops).find((x) => x.event_id === edge.event_id)
    : undefined;
  if (hop?.action) return ACTION_VERB[hop.action];
  return /created/i.test(edge.label) ? 'exported' : 'moved';
}

const KIND_ICON: Record<NodeKind, IconName> = {
  artifact: 'document',
  dataset: 'document',
  system: 'server',
  endpoint: 'laptop',
  external: 'server', // the paper plane is kept for the leak location
  actor: 'user',
};

const KIND_WORD: Record<NodeKind, string> = {
  artifact: 'Export',
  dataset: 'Dataset',
  system: 'System',
  endpoint: 'Laptop',
  external: 'Outside the company',
  actor: 'Person',
};

export interface CardData {
  id: string;
  kind: NodeKind;
  name: string;
  when: string;
  icon: IconName;
  tone: 'leak' | 'origin' | null;
}

const shortDay = (iso: string) => formatDay(iso).replace(' UTC', '');

export function graphCards(
  graph: ContractGraph,
  hypotheses: Hypothesis[],
  names: NameSource | null,
  leak: { location: string; found_ts: string } | null
): CardData[] {
  const origin = hypotheses[0]?.origin_artifact;
  return graph.nodes.map((n) => {
    const isLeak = n.id === leak?.location;
    const incoming = graph.edges.find((e) => e.to === n.id && e.ts);
    const outgoing = graph.edges.find((e) => e.from === n.id && e.ts);
    const hasIncoming = graph.edges.some((e) => e.to === n.id);
    const when = isLeak && leak
      ? `Found ${shortDay(leak.found_ts)}`
      : incoming?.ts
        ? shortDay(incoming.ts)
        : n.kind === 'artifact' && outgoing?.ts
          ? `Made ${shortDay(outgoing.ts)}`
          : hasIncoming
            ? 'Time unknown'
            : KIND_WORD[n.kind];
    const known = names?.locations.some((l) => l.id === n.id) || n.kind === 'artifact';
    return {
      id: n.id,
      kind: n.kind,
      name: known ? displayName(n.id, names) : n.label,
      when,
      icon: isLeak ? 'send' : KIND_ICON[n.kind],
      tone: isLeak ? 'leak' : n.id === origin ? 'origin' : null,
    };
  });
}

export function edgeElements(graph: ContractGraph, hypotheses: Hypothesis[]): ElementDefinition[] {
  return graph.edges.map((e) => ({
    data: {
      id: e.id,
      source: e.from,
      target: e.to,
      kind: e.kind,
      ts: e.ts,
      event_id: e.event_id,
      path_ids: e.path_ids,
      verb: edgeVerb(e, hypotheses),
    },
  }));
}

// Same order for the canvas reveal and the label pills: by time, unknown times last
export const byTime = (a: { ts: string | null }, b: { ts: string | null }) => (a.ts ?? '~').localeCompare(b.ts ?? '~');

export const cytoscapeStyles: StylesheetStyle[] = [
  {
    // Invisible hit boxes, sized like the HTML cards so edges end at the card border
    selector: 'node',
    style: {
      shape: 'round-rectangle',
      width: 'data(w)',
      height: 'data(h)',
      'background-opacity': 0,
      'border-width': 0,
      'overlay-opacity': 0,
    },
  },
  {
    selector: 'edge',
    style: {
      width: 2,
      'curve-style': 'bezier',
      'target-arrow-shape': 'triangle',
      'arrow-scale': 1.1,
      'line-color': TOKENS.observed,
      'target-arrow-color': TOKENS.observed,
      'overlay-opacity': 0,
      'transition-property': 'opacity, width',
      'transition-duration': 250,
    },
  },
  {
    selector: 'edge[kind = "inferred"]',
    style: {
      'line-color': TOKENS.inferred,
      'target-arrow-color': TOKENS.inferred,
      'line-style': 'dashed',
      'line-dash-pattern': [6, 4],
    },
  },
  { selector: 'edge.on-path', style: { width: 2.5, 'z-index': 10 } },
  { selector: 'edge.hover', style: { width: 3.5 } },
  { selector: 'edge.faded', style: { opacity: 0.3 } },
  { selector: 'edge.hidden-draw', style: { opacity: 0 } },
  { selector: 'edge.pulse', style: { width: 5 } },
];
