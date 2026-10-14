// ProvenanceGraph component
// Follows UI_UX_DESIGN.md section 5.4 and FRONTEND.md section 10

import React, { useEffect, useRef } from 'react';
import cytoscape, { Core } from 'cytoscape';
import { Graph, Hypothesis } from '../types/contract';
import { mapContractGraphToElements, cytoscapeStyles, getBreadthfirstLayoutConfig } from '../utils/graph';

interface ProvenanceGraphProps {
  graph: Graph | null;
  hypotheses: Hypothesis[];
  selectedPathId: string | null;
  onSelectPath: (path_id: string) => void;
}

export const ProvenanceGraph: React.FC<ProvenanceGraphProps> = ({
  graph,
  hypotheses,
  selectedPathId,
  onSelectPath,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  const onSelectPathRef = useRef(onSelectPath);
  onSelectPathRef.current = onSelectPath;

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current || !graph) return;

    // Destroy existing instance
    if (cyRef.current) {
      cyRef.current.destroy();
      cyRef.current = null;
    }

    const elements = mapContractGraphToElements(graph, selectedPathId);

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: cytoscapeStyles,
      layout: getBreadthfirstLayoutConfig(),
      boxSelectionEnabled: false,
      autounselectify: true,
      minZoom: 0.4,
      maxZoom: 2.5,
    });

    cyRef.current = cy;

    // Node click handler
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const connectedEdges = node.connectedEdges();
      const pathIds = new Set<string>();
      connectedEdges.forEach((edge: cytoscape.EdgeSingular) => {
        const pids = edge.data('path_ids') as string[];
        pids?.forEach((pid) => pathIds.add(pid));
      });
      // If connected to selected path or has paths, select the first path
      if (pathIds.size > 0) {
        const firstPid = Array.from(pathIds)[0];
        onSelectPathRef.current(firstPid);
      }
    });

    // Fit on ready
    cy.ready(() => {
      cy.fit(undefined, 30);
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [graph, selectedPathId]); // Re-create when graph or path changes

  // Update selection without rebuilding the entire graph
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || !graph) return;

    cy.batch(() => {
      // 1. Reset classes
      cy.nodes().removeClass('highlighted dimmed');

      // 2. Update edge selected_path attribute
      cy.edges().forEach((edge) => {
        const pathIds = (edge.data('path_ids') as string[]) || [];
        const isSelected = selectedPathId ? pathIds.includes(selectedPathId) : false;
        edge.data('selected_path', isSelected ? 'true' : 'false');
      });

      // 3. Highlight nodes on the selected path
      if (selectedPathId) {
        const selectedEdges = cy.edges('[selected_path = "true"]');
        const connectedNodes = selectedEdges.connectedNodes();
        connectedNodes.addClass('highlighted');
        cy.nodes().not(connectedNodes).addClass('dimmed');
      }
    });
  }, [selectedPathId, graph]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (cyRef.current) {
        cyRef.current.resize();
        cyRef.current.fit(undefined, 30);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const top3Hypotheses = hypotheses.slice(0, 3);

  return (
    <div className="bg-surface rounded-lg border border-border flex flex-col h-full overflow-hidden shadow-sm">
      {/* Top Bar: Path Selectors & Actions */}
      <div className="px-4 py-2.5 border-b border-border bg-surface-raised flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-bold uppercase tracking-wider text-text-primary">
            Provenance Graph
          </span>
          <span className="text-[10px] text-text-muted hidden sm:inline">• Custody Chain</span>
        </div>

        {/* Top 3 Path Toggles */}
        {top3Hypotheses.length > 0 && (
          <div className="flex items-center space-x-1.5 bg-surface p-1 rounded border border-border">
            <span className="text-[10px] text-text-muted px-1 uppercase font-mono">Highlight:</span>
            {top3Hypotheses.map((hyp) => {
              const isSelected = selectedPathId === hyp.path_id;
              return (
                <button
                  key={hyp.path_id}
                  type="button"
                  onClick={() => onSelectPath(hyp.path_id)}
                  className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold transition-colors ${
                    isSelected
                      ? 'bg-accent text-background shadow-sm'
                      : 'bg-surface-raised text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Top #{hyp.rank} ({Math.round(hyp.probability * 100)}%)
                </button>
              );
            })}
          </div>
        )}

        <button
          type="button"
          onClick={() => {
            if (cyRef.current) {
              cyRef.current.fit(undefined, 30);
            }
          }}
          className="text-xs text-text-muted hover:text-text-primary px-2 py-1 rounded bg-surface border border-border"
          title="Reset graph view"
        >
          Reset View
        </button>
      </div>

      {/* Graph Canvas */}
      <div className="flex-1 min-h-[420px] relative bg-background/50">
        {!graph && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-text-muted">
            <span className="text-3xl mb-2">🕸️</span>
            <p className="text-sm font-semibold text-text-secondary">No graph data</p>
            <p className="text-xs">Run a trace or load an incident to view reconstructed provenance edges.</p>
          </div>
        )}
        <div ref={containerRef} className="w-full h-full" />
      </div>

      {/* Legend Footer */}
      <div className="px-4 py-2 bg-surface-raised border-t border-border flex flex-wrap items-center justify-between gap-3 text-[11px]">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5">
            <span className="w-4 h-0.5 bg-[#627D98] inline-block"></span>
            <span className="text-text-secondary">Observed Edge (Logged)</span>
          </div>

          <div className="flex items-center space-x-1.5">
            <span className="w-4 h-0.5 border-t border-dashed border-[#F5B95C] inline-block"></span>
            <span className="text-inferred font-semibold">Missing Log (Inferred Hop)</span>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-[10px] text-text-muted">
          <span>● Actor</span>
          <span>■ System</span>
          <span>◆ Endpoint</span>
          <span>▲ External</span>
          <span>⬡ Dataset</span>
          <span>▭ Artifact</span>
        </div>
      </div>
    </div>
  );
};

export default ProvenanceGraph;
