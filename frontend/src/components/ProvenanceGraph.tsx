// Provenance graph: preset left-to-right layout, node cards, pill edge labels, legend, route as text (UI_LAYOUT.md section 3)

import React, { useCallback, useLayoutEffect, useMemo, useRef, useState } from 'react';
import cytoscape, { Core, EdgeSingular } from 'cytoscape';
import { Graph, Hypothesis } from '../types/contract';
import { formatNumber } from '../utils/format';
import { ACTION_VERB, displayName, formatDay, NameSource, wholePercent } from '../utils/names';
import {
  byTime,
  CardData,
  computeLayout,
  cytoscapeStyles,
  edgeElements,
  edgeVerb,
  graphCards,
  PAD,
  ROUTE_H,
  SIDE_H,
  WIDE_CARD,
} from '../utils/graph';
import Icon from './Icon';

const reducedMotion = () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

interface ProvenanceGraphProps {
  graph: Graph | null;
  hypotheses: Hypothesis[];
  selectedPathId: string | null;
  onSelectPath: (path_id: string) => void;
  names?: NameSource | null;
  leak?: { location: string; found_ts: string } | null;
  busy?: boolean;
  stage: number; // 1 Discover, 2 Match, 3 Trace, 4 Act
}

interface Info {
  x: number;
  y: number;
  title: string;
  lines: string[];
}

const STAGES = ['Discover', 'Match', 'Trace', 'Act'];

const StageIndicator: React.FC<{ stage: number }> = ({ stage }) => (
  <ol aria-label="Trace progress" className="flex items-start gap-1">
    {STAGES.map((s, i) => {
      const done = i < stage;
      return (
        <li key={s} className="flex items-start" aria-current={i === stage - 1 ? 'step' : undefined}>
          <div className="flex w-14 flex-col items-center gap-1">
            <span className={`h-2.5 w-2.5 rounded-full transition-colors duration-200 ${done ? 'bg-accent' : 'border border-line-strong bg-surface'}`} />
            <span className={`text-xs ${done ? 'text-ink' : 'text-ink-3'}`}>{s}</span>
          </div>
          {i < STAGES.length - 1 && <span className={`mt-[5px] h-px w-4 ${i < stage - 1 ? 'bg-accent' : 'bg-line-strong'}`} />}
        </li>
      );
    })}
  </ol>
);

// Node card: HTML on top of the canvas so the text is rendered by the browser, not scaled as a bitmap
const Card: React.FC<{ card: CardData; w: number; h: number; route: boolean; elRef: (el: HTMLDivElement | null) => void }> = ({
  card,
  w,
  h,
  route,
  elRef,
}) => {
  const wide = w >= WIDE_CARD;
  const border = card.tone === 'leak' ? 'border-leak' : card.tone === 'origin' ? 'border-ok' : route ? 'border-line-strong' : 'border-line';
  const iconBox = card.tone === 'leak' ? 'bg-leak-tint text-leak' : card.tone === 'origin' ? 'bg-ok-tint text-ok' : 'bg-surface-2 text-ink-2';
  const iconText = card.tone === 'leak' ? 'text-leak' : card.tone === 'origin' ? 'text-ok' : 'text-ink-3';
  return (
    <div
      ref={elRef}
      title={card.name}
      style={{ width: w, height: h }}
      className={`absolute left-0 top-0 flex origin-top-left items-center rounded-[10px] bg-surface transition-[opacity,border-color] duration-200 data-[hover=true]:border-ink-3 ${
        card.tone ? 'border-[1.5px]' : 'border'
      } ${border} ${route ? 'gap-2.5 px-3 shadow-[0_1px_2px_rgba(28,32,48,0.06),0_4px_12px_rgba(28,32,48,0.06)]' : 'gap-2 px-2.5 opacity-60'}`}
    >
      {wide && route && (
        <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${iconBox}`}>
          <Icon name={card.icon} />
        </span>
      )}
      {wide && !route && <Icon name={card.icon} className={`shrink-0 ${iconText}`} />}
      <span className="min-w-0 flex-1">
        <span
          className={`block font-semibold text-ink ${route || !wide ? 'line-clamp-2' : 'truncate'} ${
            wide && route ? 'text-sm leading-[18px]' : 'text-[13px] leading-[17px]'
          }`}
        >
          {card.name}
        </span>
        {/* Narrow side cards have room for the name only; the popover and tooltip carry the rest */}
        {(wide || route) && (
          <span className="mt-0.5 block truncate text-xs leading-4 text-ink-3 tabular">
            {wide ? card.when : card.when.replace(/^(Made|Found) /, '')}
          </span>
        )}
      </span>
    </div>
  );
};

export const ProvenanceGraph: React.FC<ProvenanceGraphProps> = ({
  graph,
  hypotheses,
  selectedPathId,
  onSelectPath,
  names = null,
  leak = null,
  busy = false,
  stage,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);
  const cardEls = useRef(new Map<string, HTMLDivElement>());
  const pillEls = useRef(new Map<string, HTMLDivElement>());
  const [info, setInfo] = useState<Info | null>(null);
  const [box, setBox] = useState<{ w: number; h: number } | null>(null);
  const [revealing, setRevealing] = useState(false);
  // A tapped node's popover, shown after the route change and refit it may trigger
  const pendingInfo = useRef<{ id: string; title: string; lines: string[] } | null>(null);

  // Handlers read the latest props through refs so the graph is built once per trace
  const latest = useRef({ onSelectPath, hypotheses, selectedPathId, names });
  latest.current = { onSelectPath, hypotheses, selectedPathId, names };

  const layout = useMemo(
    () => (graph && box ? computeLayout(graph, hypotheses, selectedPathId, box) : null),
    [graph, hypotheses, selectedPathId, box]
  );
  const leakLocation = leak?.location;
  const leakFound = leak?.found_ts;
  const cards = useMemo(
    () => (graph ? graphCards(graph, hypotheses, names, leakLocation && leakFound ? { location: leakLocation, found_ts: leakFound } : null) : []),
    [graph, hypotheses, names, leakLocation, leakFound]
  );
  const edgeOrder = useMemo(() => (graph ? [...graph.edges].sort(byTime).map((e) => e.id) : []), [graph]);
  // Off-route cards name the best-ranked route through them instead of a time they rarely have
  const routeOf = useMemo(() => {
    const best: Record<string, Hypothesis> = {};
    for (const e of graph?.edges ?? []) {
      for (const id of e.path_ids) {
        const h = hypotheses.find((x) => x.path_id === id);
        if (!h) continue;
        for (const n of [e.from, e.to]) if (!best[n] || h.rank < best[n].rank) best[n] = h;
      }
    }
    return best;
  }, [graph, hypotheses]);
  const routeEdges = useMemo(
    () => (graph && selectedPathId ? graph.edges.filter((e) => e.path_ids.includes(selectedPathId)) : []),
    [graph, selectedPathId]
  );

  // Place every card and pill over its Cytoscape element; runs on each canvas render (pan, zoom, layout animation)
  const sync = useCallback(() => {
    const cy = cyRef.current;
    if (!cy) return;
    const z = cy.zoom();
    cardEls.current.forEach((el, id) => {
      const n = cy.getElementById(id);
      if (n.empty()) return;
      const p = n.renderedPosition();
      // Whole pixels: text on a half-pixel offset renders soft
      el.style.transform = `translate(${Math.round(p.x - (n.data('w') * z) / 2)}px, ${Math.round(p.y - (n.data('h') * z) / 2)}px) scale(${z})`;
    });
    pillEls.current.forEach((el, id) => {
      const e = cy.getElementById(id);
      if (e.empty()) return;
      const m = e.renderedMidpoint();
      // Just above the connector so the line itself (solid or dashed) stays visible
      el.style.transform = `translate(${Math.round(m.x - (el.offsetWidth * z) / 2)}px, ${Math.round(m.y - (el.offsetHeight + 6) * z)}px) scale(${z})`;
    });
  }, []);

  // Viewport that fits the layout, never above zoom 1, so cards stay at their designed size
  const fitView = useCallback(() => {
    const cy = cyRef.current;
    if (!cy || !box) return;
    const bb = cy.nodes().boundingBox({ includeLabels: false, includeOverlays: false });
    if (!isFinite(bb.w) || bb.w === 0) return;
    const fit = Math.min(1, (box.w - 2 * PAD) / bb.w, (box.h - 2 * PAD) / bb.h);
    const zoom = fit > 0.97 ? 1 : fit; // a few px into the padding beats scaled, softer text
    cy.viewport({ zoom, pan: { x: Math.round(box.w / 2 - (bb.x1 + bb.w / 2) * zoom), y: Math.round(box.h / 2 - (bb.y1 + bb.h / 2) * zoom) } });
  }, [box]);

  // Track the canvas size; the layout stretches to it
  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const measure = () => {
      const w = Math.round(el.clientWidth);
      const h = Math.round(el.clientHeight);
      setBox((b) => (b && b.w === w && b.h === h ? b : { w, h }));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Build Cytoscape once per graph: invisible node hit boxes and the edges
  useLayoutEffect(() => {
    if (!containerRef.current || !graph) return;
    const container = containerRef.current;
    const cy = cytoscape({
      container,
      elements: [
        ...graph.nodes.map((n) => ({ data: { id: n.id, w: ROUTE_H, h: ROUTE_H } })),
        ...edgeElements(graph, latest.current.hypotheses),
      ],
      style: cytoscapeStyles,
      layout: { name: 'preset', fit: false }, // the layout effect below sets positions and the viewport
      boxSelectionEnabled: false,
      autounselectify: true,
      minZoom: 0.5,
      maxZoom: 2,
    });
    cyRef.current = cy;
    cy.on('render', sync);

    const hopTo = (loc: string) => {
      const { hypotheses: hs, selectedPathId: s } = latest.current;
      const ordered = [...hs.filter((h) => h.path_id === s), ...hs];
      for (const h of ordered) {
        const hop = h.hops.find((x) => x.to_loc === loc);
        if (hop) return hop;
      }
      return undefined;
    };

    cy.on('tap', 'node', (evt) => {
      const n = evt.target;
      const ids = new Set<string>();
      n.connectedEdges().forEach((e: EdgeSingular) => (e.data('path_ids') as string[]).forEach((id) => ids.add(id)));
      const best = latest.current.hypotheses.find((h) => ids.has(h.path_id));

      const hop = hopTo(n.id());
      const card = cardEls.current.get(n.id());
      const lines: string[] = [];
      if (hop) {
        lines.push(hop.kind === 'observed' ? 'Observed in the logs' : 'Inferred: no log found for this step');
        if (hop.ts) lines.push(formatDay(hop.ts));
        if (hop.rows !== null) lines.push(`${formatNumber(hop.rows)} rows moved`);
        lines.push(`By ${displayName(hop.actor, latest.current.names)}`);
      } else if (card) {
        lines.push(card.querySelector('.tabular')?.textContent ?? '');
      }
      const title = card?.title ?? n.id();
      if (best && best.path_id !== latest.current.selectedPathId) {
        pendingInfo.current = { id: n.id(), title, lines };
        latest.current.onSelectPath(best.path_id);
        return;
      }
      const p = n.renderedPosition();
      setInfo({ x: p.x, y: p.y - (n.data('h') * cy.zoom()) / 2 - 8, title, lines });
    });
    cy.on('tap', (evt) => {
      if (evt.target === cy) setInfo(null);
    });
    cy.on('mouseover', 'node', (evt) => {
      container.style.cursor = 'pointer';
      cardEls.current.get(evt.target.id())?.setAttribute('data-hover', 'true');
    });
    cy.on('mouseout', 'node', (evt) => {
      container.style.cursor = '';
      cardEls.current.get(evt.target.id())?.removeAttribute('data-hover');
    });
    cy.on('mouseover', 'edge', (evt) => {
      const e = evt.target;
      e.addClass('hover');
      container.style.cursor = 'pointer';
      const inferred = e.data('kind') === 'inferred';
      const hop = latest.current.hypotheses.flatMap((h) => h.hops).find((h) => h.event_id && h.event_id === e.data('event_id'));
      const lines = [inferred ? 'No log found for this step' : 'Logged event'];
      if (e.data('ts')) lines.push(formatDay(e.data('ts')));
      if (hop?.rows != null) lines.push(`${formatNumber(hop.rows)} rows`);
      const mid = e.renderedMidpoint();
      const verb: string = e.data('verb');
      setInfo({ x: mid.x, y: mid.y - 18, title: inferred ? 'Inferred step' : `${verb[0].toUpperCase()}${verb.slice(1)}`, lines });
    });
    cy.on('mouseout', 'edge', () => {
      cy.edges().removeClass('hover');
      container.style.cursor = '';
      setInfo(null);
    });
    cy.on('viewport', () => setInfo(null));

    // Trace reveal: edges draw in time order, then the inferred edge on the route pulses once
    const timers: number[] = [];
    if (!reducedMotion()) {
      setRevealing(true);
      const ordered = cy.edges().sort((a, b) => byTime({ ts: a.data('ts') }, { ts: b.data('ts') }));
      ordered.addClass('hidden-draw');
      ordered.forEach((e, i) => {
        timers.push(window.setTimeout(() => e.removeClass('hidden-draw'), 120 * (i + 1)));
      });
      const end = 120 * (ordered.length + 1);
      timers.push(
        window.setTimeout(() => {
          setRevealing(false);
          const pulse = cy.edges('[kind = "inferred"].on-path').last();
          pulse.addClass('pulse');
          timers.push(window.setTimeout(() => pulse.removeClass('pulse'), 400));
        }, end)
      );
    }

    return () => {
      timers.forEach(clearTimeout);
      cy.destroy();
      cyRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- rebuild only for a new trace graph
  }, [graph]);

  // Apply the layout: route on one line, others faded; animate only when the route changed, not on resize
  const lastRoute = useRef<string | null>(null);
  useLayoutEffect(() => {
    const cy = cyRef.current;
    if (!cy || !layout) return;
    setInfo(null);
    const routeChanged = lastRoute.current !== null && lastRoute.current !== selectedPathId;
    lastRoute.current = selectedPathId;

    cy.batch(() => {
      cy.nodes().forEach((n) => {
        n.data({ w: layout.cardW, h: layout.onRoute.has(n.id()) ? ROUTE_H : SIDE_H });
      });
      cy.edges().removeClass('on-path faded');
      cy.edges().forEach((e) => {
        e.addClass(selectedPathId && (e.data('path_ids') as string[]).includes(selectedPathId) ? 'on-path' : 'faded');
      });
    });

    if (routeChanged && !reducedMotion()) {
      // Fit to where the nodes end up, then animate them there from where they are
      const current = Object.fromEntries(cy.nodes().map((n) => [n.id(), { ...n.position() }]));
      cy.nodes().positions((n) => layout.positions[n.id()]);
      fitView();
      cy.nodes().positions((n) => current[n.id()]);
      cy.nodes().forEach((n) => {
        n.animate({ position: layout.positions[n.id()] }, { duration: 250, easing: 'ease-out-cubic' });
      });
    } else {
      cy.nodes().positions((n) => layout.positions[n.id()]);
      fitView();
    }
    sync();

    const pending = pendingInfo.current;
    pendingInfo.current = null;
    if (pending && layout.positions[pending.id]) {
      const z = cy.zoom();
      const pan = cy.pan();
      const p = layout.positions[pending.id];
      const h = layout.onRoute.has(pending.id) ? ROUTE_H : SIDE_H;
      setInfo({ x: p.x * z + pan.x, y: (p.y - h / 2) * z + pan.y - 8, title: pending.title, lines: pending.lines });
    }
  }, [layout, selectedPathId, fitView, sync]);

  const tabs = hypotheses.slice(0, 3);
  const selected = hypotheses.find((h) => h.path_id === selectedPathId) ?? null;

  const onTabsKey = (e: React.KeyboardEvent) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const i = Math.max(0, tabs.findIndex((h) => h.path_id === selectedPathId));
    const next = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
    onSelectPath(next.path_id);
    document.getElementById(`route-tab-${next.rank}`)?.focus();
  };

  return (
    <div className="flex h-full min-h-0 flex-col gap-3">
      <div className="flex shrink-0 items-start justify-between gap-4">
        <StageIndicator stage={stage} />
        {tabs.length > 0 && (
          <div className="flex items-center gap-2">
            <div role="tablist" aria-label="Routes" onKeyDown={onTabsKey} className="flex rounded-ctl border border-line bg-surface p-0.5">
              {tabs.map((h) => {
                const isSel = h.path_id === selectedPathId;
                return (
                  <button
                    key={h.path_id}
                    id={`route-tab-${h.rank}`}
                    type="button"
                    role="tab"
                    aria-selected={isSel}
                    tabIndex={isSel ? 0 : -1}
                    onClick={() => onSelectPath(h.path_id)}
                    className={`h-8 rounded-md px-3 text-sm tabular transition-colors duration-150 ${
                      isSel ? 'bg-accent text-white font-semibold' : 'text-ink-2 hover:bg-surface-2'
                    }`}
                  >
                    #{h.rank}&nbsp;&nbsp;{wholePercent(h.probability)}
                  </button>
                );
              })}
            </div>
            <button
              type="button"
              onClick={fitView}
              aria-label="Fit graph to view"
              title="Fit graph to view"
              className="inline-flex h-9 w-9 items-center justify-center rounded-ctl border border-line bg-surface text-ink-2 hover:bg-surface-2"
            >
              <Icon name="fit" />
            </button>
          </div>
        )}
      </div>

      <section aria-label="Provenance graph" className="dot-grid relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-card border border-line">
        <div className="relative min-h-0 flex-1">
          <div ref={containerRef} className="absolute inset-0" aria-hidden={!graph} />

          {graph && layout && (
            <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
              {cards.map((c) => (
                <Card
                  key={c.id}
                  card={layout.onRoute.has(c.id) || !routeOf[c.id] ? c : { ...c, when: `Route #${routeOf[c.id].rank} · ${wholePercent(routeOf[c.id].probability)}` }}
                  w={layout.cardW}
                  h={layout.onRoute.has(c.id) ? ROUTE_H : SIDE_H}
                  route={layout.onRoute.has(c.id)}
                  elRef={(el) => (el ? cardEls.current.set(c.id, el) : cardEls.current.delete(c.id))}
                />
              ))}
              {routeEdges.map((e) => {
                const inferred = e.kind === 'inferred';
                const narrow = layout.cardW < WIDE_CARD;
                return (
                  <div
                    key={`${selectedPathId}:${e.id}`}
                    ref={(el) => (el ? pillEls.current.set(e.id, el) : pillEls.current.delete(e.id))}
                    style={revealing ? { animationDelay: `${120 * (edgeOrder.indexOf(e.id) + 1)}ms` } : undefined}
                    className={`appear absolute left-0 top-0 origin-top-left rounded-md border text-center font-medium leading-4 ${
                      narrow ? 'px-1.5 py-0.5 text-[11px]' : 'px-2 py-1 text-xs'
                    } ${inferred ? 'border-inferred-tint bg-inferred-tint text-inferred-text' : 'border-line bg-surface text-ink-2'}`}
                  >
                    {inferred ? (
                      <>
                        inferred,
                        <br />
                        no log found
                      </>
                    ) : (
                      edgeVerb(e, hypotheses)
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {!graph && !busy && (
            <div className="absolute inset-0 flex items-center justify-center p-6 text-center text-sm text-ink-3">
              The route will be drawn here after Export and trace.
            </div>
          )}
          {!graph && busy && (
            <div aria-busy="true" className="absolute inset-0 flex items-center justify-center gap-16">
              {[0, 1, 2, 3].map((i) => <div key={i} className="skeleton h-14 w-40" />)}
            </div>
          )}

          {info && (
            <div
              role="tooltip"
              className="pointer-events-none absolute z-10 w-max max-w-[240px] -translate-x-1/2 -translate-y-full rounded-ctl border border-line bg-surface px-3 py-2 shadow-pop"
              style={{ left: info.x, top: info.y }}
            >
              <div className="text-[13px] font-semibold text-ink">{info.title}</div>
              {info.lines.map((l, i) => (
                <div key={i} className="text-xs text-ink-2">{l}</div>
              ))}
            </div>
          )}

          {graph && (
            <ul aria-label="Legend" className="absolute bottom-3 left-3 flex gap-4 rounded-ctl border border-line bg-surface px-3 py-1.5 text-xs text-ink-2">
              <li className="flex items-center gap-1.5">
                <svg width="24" height="6" aria-hidden="true"><line x1="0" y1="3" x2="24" y2="3" stroke="var(--observed)" strokeWidth="2" /></svg>
                Observed
              </li>
              <li className="flex items-center gap-1.5">
                <svg width="24" height="6" aria-hidden="true"><line x1="0" y1="3" x2="24" y2="3" stroke="var(--inferred)" strokeWidth="2" strokeDasharray="6 4" /></svg>
                Inferred
              </li>
              <li className="flex items-center gap-1.5">
                <span className="h-3 w-4 rounded-sm border-[1.5px] border-leak" aria-hidden="true" />
                Leak location
              </li>
            </ul>
          )}
        </div>

        {selected && (
          <details className="shrink-0 border-t border-line bg-surface">
            <summary className="flex h-9 items-center px-4 text-[13px] font-medium text-accent">Route as text</summary>
            <ol className="max-h-40 space-y-1 overflow-y-auto px-4 pb-3 text-[13px] text-ink">
              {selected.hops.map((hop, i) => (
                <li key={i}>
                  {i + 1}. {displayName(hop.from_loc, names)} to {displayName(hop.to_loc, names)}, by {displayName(hop.actor, names)}:{' '}
                  {hop.kind === 'observed' ? (
                    <>
                      {hop.action ? ACTION_VERB[hop.action] : 'moved'}
                      {hop.ts && `, ${formatDay(hop.ts)}`}
                      {hop.rows !== null && `, ${formatNumber(hop.rows)} rows`} (observed)
                    </>
                  ) : (
                    <span className="text-inferred-text">inferred, no log found for this step</span>
                  )}
                </li>
              ))}
            </ol>
          </details>
        )}
      </section>
    </div>
  );
};

export default ProvenanceGraph;
