// ProvenanceGraph component
// Follows UI_UX_DESIGN.md section 5.4 and FRONTEND.md section 10

import React, { useEffect, useRef, useState } from 'react';
import cytoscape, { Core, EdgeSingular } from 'cytoscape';
import { Graph, Hypothesis } from '../types/contract';
import { formatProbability } from '../utils/format';
import { mapContractGraphToElements, cytoscapeStyles, getBreadthfirstLayoutConfig } from '../utils/graph';

// Exact tooltip microcopy from UI_UX_DESIGN.md section 9.3
const OBSERVED_TIP = 'Transfer supported by an available event record.';
const INFERRED_TIP = 'Possible transfer inferred because relevant logs are missing.';

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
  const hypothesesRef = useRef(hypotheses);
  hypothesesRef.current = hypotheses;
  const [hoverText, setHoverText] = useState<string | null>(null);

  // Build Cytoscape once per graph; selection changes only toggle classes below
  useEffect(() => {
    if (!containerRef.current || !graph) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements: mapContractGraphToElements(graph),
      style: cytoscapeStyles,
      layout: getBreadthfirstLayoutConfig(),
      boxSelectionEnabled: false,
      autounselectify: true,
      minZoom: 0.4,
      maxZoom: 2.5,
    });
    cyRef.current = cy;

    // Click to highlight: the best-ranked hypothesis (backend order) using the tapped element
    const selectBestPath = (pathIds: Set<string>) => {
      const best = hypothesesRef.current.find((h) => pathIds.has(h.path_id));
      if (best) onSelectPathRef.current(best.path_id);
    };
    cy.on('tap', 'edge', (evt) => selectBestPath(new Set(evt.target.data('path_ids') as string[])));
    cy.on('tap', 'node', (evt) => {
      const ids = new Set<string>();
      evt.target.connectedEdges().forEach((e: EdgeSingular) => {
        (e.data('path_ids') as string[]).forEach((id) => ids.add(id));
      });
      selectBestPath(ids);
    });

    cy.on('mouseover', 'node', (evt) => {
      const n = evt.target;
      n.addClass('hover');
      n.connectedEdges().addClass('hover');
      setHoverText(`${n.data('label')} · ${n.data('kind')}`);
    });
    cy.on('mouseover', 'edge', (evt) => {
      const e = evt.target;
      e.addClass('hover');
      setHoverText(`${e.data('label')} · ${e.data('kind') === 'inferred' ? INFERRED_TIP : OBSERVED_TIP}`);
    });
    cy.on('mouseout', 'node, edge', () => {
      cy.elements().removeClass('hover');
      setHoverText(null);
    });

    cy.ready(() => cy.fit(undefined, 30));

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [graph]);

  // Highlight the selected path and animate a dash overlay along it
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || !graph) return;

    const pathEdges = selectedPathId
      ? cy.edges().filter((e) => (e.data('path_ids') as string[] | undefined)?.includes(selectedPathId) ?? false)
      : cy.collection();
    const pathNodes = pathEdges.connectedNodes();

    cy.batch(() => {
      cy.elements().removeClass('on-path faded');
      if (pathEdges.empty()) return;
      pathEdges.addClass('on-path');
      pathNodes.addClass('on-path');
      cy.elements().not(pathEdges).not(pathNodes).addClass('faded');
    });

    if (pathEdges.empty() || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const flow = cy.add(
      pathEdges.map((e) => ({
        group: 'edges' as const,
        classes: 'flow',
        data: { id: `flow:${e.id()}`, source: e.data('source'), target: e.data('target') },
      }))
    );

    // One loop for all overlay edges, at most ~20 fps; rAF already pauses while the tab is hidden
    let raf = 0;
    let last = 0;
    let offset = 0;
    const tick = (t: number) => {
      if (t - last >= 50) {
        last = t;
        offset = (offset - 1.5) % 12;
        flow.style('line-dash-offset', offset);
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      if (!cy.destroyed()) cy.remove(flow);
    };
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
            Provenance graph
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
                  aria-pressed={isSelected}
                  title={`Relative likelihood ${formatProbability(hyp.probability)}`}
                  className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold transition-colors ${
                    isSelected
                      ? 'bg-accent text-background shadow-sm'
                      : 'bg-surface-raised text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Top {hyp.rank}
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
          <div className="absolute inset-0 flex items-center justify-center text-sm text-text-muted">
            No trace available. Export the simulated leak and run a trace.
          </div>
        )}
        {hoverText && (
          <div className="absolute left-2 top-2 z-10 max-w-[90%] px-2 py-1 rounded bg-surface-raised border border-border text-[11px] font-mono text-text-primary pointer-events-none">
            {hoverText}
          </div>
        )}
        <div ref={containerRef} className="w-full h-full" />
      </div>

      {/* Legend Footer */}
      <div className="px-4 py-2 bg-surface-raised border-t border-border flex flex-wrap items-center justify-between gap-3 text-[11px]">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5" title={OBSERVED_TIP}>
            <span className="w-4 h-0.5 bg-[#627D98] inline-block"></span>
            <span className="text-text-secondary">Observed Edge (Logged)</span>
          </div>

          <div className="flex items-center space-x-1.5" title={INFERRED_TIP}>
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
