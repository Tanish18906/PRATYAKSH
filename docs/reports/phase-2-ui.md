# Phase 2 report: ui
Developer: Anmol | Date: 2026-10-14

Phase 1 already wired generate, export, trace and the panels to the API client. Phase 2 work closed the gaps between that and `FRONTEND.md` §10 / `UI_UX_DESIGN.md` §5.4–5.6, §9, §10, verified against the live backend on seed 42.

## Done
- Provenance graph: Cytoscape is built once per graph. Selecting a path now only toggles classes, where it used to rebuild the whole graph. Edges are matched to the selected path by `path_ids` (IDs only, never labels). Unrelated elements are faded. Inferred edges stay dashed amber. Edge labels from the backend show on the selected path and on hover.
- Moving dash along the selected path: derived `straight` overlay edges (never written into `TraceResult`) driven by one rAF loop capped at about 20 fps. The loop stops on path change and unmount, rAF pauses while the tab is hidden, and the overlay is skipped entirely under `prefers-reduced-motion`.
- Click to highlight: tapping a node or edge selects the best-ranked hypothesis (backend order) that uses it. Hover shows label plus kind and the observed/inferred tooltip text, with a thicker border and emphasized connected edges.
- Path selector buttons read `Top 1/2/3` with the relative likelihood in their tooltip.
- Hypothesis cards: the bar width is the real `probability`. The old 5% minimum, which made 1.2% look like 5%, is removed. The selected card lists its hops (from → to, Observed/Inferred, actor, UTC time, action, rows). Inferred hops show `Log missing. Estimated loss: N%.` when `est_loss` is present, otherwise `Log missing.` Each card has a semantic `Select path` button for keyboard users, plus the rankings notice and likelihood tooltip.
- Origin match table: keeps contract order, shows N/A for nulls, and puts a readable label next to each exclusion enum. Column names follow the §9.2 microcopy.
- Reveal dialog: closes on Escape, keeps Tab focus inside, focuses the reason box on open, and shows backend errors inside the dialog (they were hidden behind the overlay). A stale error is cleared when the dialog opens. Labels follow the microcopy.
- Audit tab: microcopy only. It already refreshed after every action.
- Error handling: every request has a 30 s timeout. Network failure, timeout and Vite-proxy 5xx map to `Cannot connect to the local backend.` and the `ApiError` codes map to the exact §9.4 text. The report fetch uses the same normalized path. Loading text follows the §8 microcopy, with export and trace shown as separate steps.
- Tab labels follow the microcopy: Origin match, Containment, Benchmark, Report, Audit.

## Files created or changed
- `frontend/src/api/client.ts`
- `frontend/src/state/AppContext.tsx`
- `frontend/src/state/reducer.ts`
- `frontend/src/utils/graph.ts`
- `frontend/src/components/ProvenanceGraph.tsx`
- `frontend/src/components/HypothesisPanel.tsx`
- `frontend/src/components/OriginMatchTab.tsx`
- `frontend/src/components/RevealDialog.tsx`
- `frontend/src/components/AuditTab.tsx`
- `frontend/src/App.tsx`
- `docs/reports/phase-2-ui.md`

No backend files changed.

## Commands run and real output
```
$ cd frontend && npm run build
✓ built in 6.04s            (only the existing >500 kB chunk-size warning)
$ cd frontend && npm run lint
> eslint .                  (no output: 0 errors, 0 warnings)

$ curl -X POST /api/trace {"scenario_id":"scn:A1-42-L40-C","top_k":5}
real 0m0.038s
art:E1 candidate None 1.0607
art:E2 excluded watermark_before  ['Created before the newest leaked record existed.']
art:E3 excluded schema            ['The export lacks columns that appear in the leaked file.']
1 hyp:1 0.8142 ['act:ravi-menon']  observed bi-warehouse→ep:ravi-menon, inferred ep:ravi-menon→ext:telegram-leak-channel
```

Browser run (Playwright, live backend `uvicorn :8000` + `npm run dev`, seed 42 A1 loss 0.4):
- Export and trace: E1 origin, Ravi's path highlighted, dashed final hop. Read from the Cytoscape instance: Top 2 selected → 3 `on-path` edges (`art:E1>sys:bi-warehouse`, `sys:bi-warehouse>ext:unknown-host`, `ext:unknown-host>telegram`), 3 overlay edges, dash offset changing between reads (-7.5 → -4.5). 22 elements total = 8 nodes + 11 edges + 3 overlay, so no leftover overlays.
- Tapping node `ep:reyan-nivan` selects Top 3 (hyp:3).
- Reveal: submit is disabled under 8 characters. With a valid reason the value shows, it is gone after Close, and the audit tab shows `aud:0010 … reveal … leak:A1-42#0 phone "Verify leaked row for incident notification"` with no raw value.
- Origin tab rows in backend order: E1, E4, E5, E6 candidates; E2 `watermark_before`, E3 `schema`, each with a readable reason. Nulls show N/A.
- Backend stopped, Re-trace clicked: banner shows `Cannot connect to the local backend.` and the previous trace stays on screen.
- Reload with the backend down: OFFLINE REPLAY loads `demo.json` and the top path is highlighted.
- No console warnings during the live run. The only console error is the browser logging the failed request while the backend was down.

## Gate checks (FRONTEND.md §18 Phase 2)
- [x] Seed 42 A1 completes Export and trace against the live backend
- [x] UI shows real engine output (no seed-42 hardcoding anywhere)
- [x] Graph path selection works (buttons, cards, node/edge click)
- [x] Observed and inferred edges stay visually distinct, including on the selected path
- [x] Origin candidates show exclusion reasons; excluded rows stay visible
- [x] Reveal dialog and audit tab work against the live API
- [ ] Joint offline demo steps 1–5 from `DEMO_AND_PITCH.md` (Anmol + Tanish, wifi off): not done by the agent. That file does not exist in `docs/`.

## Not done / cut
- Origin tab "selected artifact" detail box from the §5.6 wireframe: skipped, because the table already shows every field it would show.
- `score_parts` on cards (optional in §5.5): skipped.
- The "No supported leak path was found" empty state, for a trace that comes back with zero hypotheses, needs a prop the spec doesn't list. The panels show the no-trace text instead.
- Graph labels are small at the current fit zoom. Projector readability is a Phase 3 item.

## Contract or spec discrepancies
- `05_PHASES.md` gate refers to `DEMO_AND_PITCH.md`, which is not in `docs/`.

## Risks for integration
- The dash overlay relies on Cytoscape keeping `straight` edges out of bezier bundling (checked in cytoscape 3.30 source, `findEdgeControlPoints`). Where two parallel edges join the same pair of nodes, the overlay draws the straight centre line, slightly off the curved edges.

STOPPED. Waiting for APPROVED PHASE 2.
