// Cytoscape graph data mapping and styling utilities
// Follows UI_UX_DESIGN.md section 5.4 and FRONTEND.md section 10

import { Graph as ContractGraph } from '../types/contract';
import cytoscape, { ElementDefinition, StylesheetStyle } from 'cytoscape';

export function mapContractGraphToElements(graph: ContractGraph): ElementDefinition[] {
  const elements: ElementDefinition[] = [];

  for (const node of graph.nodes) {
    elements.push({ data: { id: node.id, label: node.label || node.id, kind: node.kind } });
  }

  for (const edge of graph.edges) {
    elements.push({
      data: {
        id: edge.id,
        source: edge.from,
        target: edge.to,
        label: edge.label || (edge.kind === 'inferred' ? 'Log missing' : ''),
        kind: edge.kind,
        ts: edge.ts,
        event_id: edge.event_id,
        path_ids: edge.path_ids,
      },
    });
  }

  return elements;
}

export const cytoscapeStyles: StylesheetStyle[] = [
  // Base Node Styling
  {
    selector: 'node',
    style: {
      label: 'data(label)',
      color: '#F2F7FA',
      'font-size': '16px',
      'font-weight': 600,
      'text-valign': 'bottom',
      'text-margin-y': 6,
      'text-wrap': 'wrap',
      'text-max-width': '150px',
      'text-background-opacity': 0.8,
      'text-background-color': '#091119',
      'text-background-padding': '3px',
      'text-background-shape': 'roundrectangle',
      width: 42,
      height: 42,
      'border-width': 2,
    },
  },

  // Kind-specific node styling (from UI_UX_DESIGN.md table)
  {
    selector: 'node[kind = "actor"]',
    style: {
      shape: 'ellipse',
      'background-color': '#6489C6',
      'border-color': '#9DB9EA',
    },
  },
  {
    selector: 'node[kind = "system"]',
    style: {
      shape: 'roundrectangle',
      'background-color': '#486C79',
      'border-color': '#91B2BD',
    },
  },
  {
    selector: 'node[kind = "endpoint"]',
    style: {
      shape: 'diamond',
      'background-color': '#8576AF',
      'border-color': '#C3B6EB',
    },
  },
  {
    selector: 'node[kind = "external"]',
    style: {
      shape: 'triangle',
      'background-color': '#AC685B',
      'border-color': '#E9A99D',
    },
  },
  {
    selector: 'node[kind = "dataset"]',
    style: {
      shape: 'hexagon',
      'background-color': '#417F73',
      'border-color': '#89CABB',
    },
  },
  {
    selector: 'node[kind = "artifact"]',
    style: {
      shape: 'rectangle',
      'background-color': '#99834D',
      'border-color': '#DDCB92',
    },
  },

  // Base Edge Styling
  {
    selector: 'edge',
    style: {
      width: 2,
      'curve-style': 'bezier',
      'target-arrow-shape': 'triangle',
      'arrow-scale': 1.1,
      'font-size': '14px',
      'text-wrap': 'wrap',
      'text-max-width': '170px',
      'font-family': 'monospace',
      'text-background-opacity': 0.85,
      'text-background-color': '#121D27',
      'text-background-padding': '2px',
      'text-background-shape': 'roundrectangle',
    },
  },

  // Observed Edge (solid slate)
  {
    selector: 'edge[kind = "observed"]',
    style: {
      'line-color': '#627D98',
      'target-arrow-color': '#627D98',
      'line-style': 'solid',
      color: '#B9C8D2',
    },
  },

  // Inferred Edge (dashed amber)
  {
    selector: 'edge[kind = "inferred"]',
    style: {
      'line-color': '#F5B95C',
      'target-arrow-color': '#F5B95C',
      'line-style': 'dashed',
      'line-dash-pattern': [6, 4],
      width: 2.5,
      color: '#F5B95C',
    },
  },

  // Hover: thicker border, emphasized connected edges
  {
    selector: 'node.hover',
    style: { 'border-width': 4 },
  },
  {
    selector: 'edge.hover',
    style: { width: 3.5, label: 'data(label)' },
  },

  // Selected path: classes set by ProvenanceGraph, edge kind styling preserved
  {
    selector: 'edge.on-path',
    style: { width: 5, 'z-index': 99, label: 'data(label)', color: '#F2F7FA' },
  },
  {
    selector: 'edge.on-path[kind = "observed"]',
    style: { 'line-color': '#5EEAD4', 'target-arrow-color': '#5EEAD4' },
  },
  {
    selector: 'node.on-path',
    style: { 'border-width': 4, 'border-color': '#5EEAD4', 'z-index': 100 },
  },
  {
    selector: '.faded',
    style: { opacity: 0.3 },
  },

  // Moving-dash overlay drawn over selected-path edges (visual only, never part of TraceResult)
  {
    selector: 'edge.flow',
    style: {
      'curve-style': 'straight', // straight edges are not bundled with the bezier edges underneath
      width: 2,
      'line-color': '#F2F7FA',
      'line-style': 'dashed',
      'line-dash-pattern': [2, 10],
      'target-arrow-shape': 'none',
      opacity: 0.9,
      'z-index': 101,
      events: 'no',
    },
  },
];

export function getBreadthfirstLayoutConfig(): cytoscape.BreadthFirstLayoutOptions {
  return {
    name: 'breadthfirst',
    directed: true,
    padding: 30,
    spacingFactor: 1.25,
    animate: false,
  };
}
