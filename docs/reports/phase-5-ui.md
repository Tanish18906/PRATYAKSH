# Phase 5 report: ui
Developer: Anmol | Date: 2026-10-14

Phase 5 is code freeze and rehearsal. The UI agent ran the full `FRONTEND.md` §19 smoke checklist in a browser, live and offline. **No crash was found, so no frontend code was changed.** Only this report was added.

## Smoke results (Playwright, live backend `uvicorn :8000` + Vite `:5173`, 1600×1000)

Structural
- [x] `npm run build` ✓ (only the existing >500 kB chunk warning), `npm run lint` clean, tests phase3 8/8 and phase4 4/4
- [x] No external runtime resources: no `http(s)://` URL in `dist/index.html` or CSS, and no CDN or Google Fonts reference in the JS
- [x] No extra screens; five tabs: Origin match, Containment, Benchmark, Report, Audit

Scenario
- [x] Startup in live mode generates seed 42 A1 and does **not** show a trace before Export and trace
- [x] SIMULATED badge and the synthetic-Telegram notice are visible
- [x] Export and trace: export → trace → report → audit in about 0.4 s in the browser (the trace API itself takes about 40 ms)
- [x] A2 and A3: Generate clears the old trace, then Export and trace renders a graph and hypotheses with no error (A2 8 nodes, A3 7 nodes)

Investigation
- [x] Graph kinds rendered: artifact, system, endpoint, external; 8 inferred edges are dashed
- [x] Top 1 path = `art:E1 → sys:bi-warehouse → ep:ravi-menon ⇢ ext:telegram-leak-channel`
- [x] Origin match: E1, E4, E5, E6 candidates; E2 and E3 excluded with reasons (backend order kept)
- [x] Containment: chokepoints with cumulative coverage (#1 "Block outbound uploads from Ravi Menon's laptop", 81.4%)
- [x] Judge inject `act:meena-iyer` → new scenario `scn:INJ-42-meena-iyer-L40` → Export and trace → Meena is the Top 1 actor; whole flow 0.98 s

Privacy
- [x] Reveal blocked below 8 characters; successful reveal is audited, value cleared on close (verified in Phase 2, code unchanged since)
- [x] Offline: all 15 masked-preview reveal buttons disabled

Reporting
- [x] Report preview is an iframe with `sandbox=""` (scripts blocked), 7.6 kB backend HTML containing "Verify current legal timelines with counsel"; Download report button enabled
- [x] Audit shows `scenario_generate`, `telegram_export`, `trace`, `report_export`

Benchmark (full UI run: seeds 50–199, losses 0 / 0.2 / 0.4 / 0.6, A1–A3)
- [x] Progress bar shown while running (11% at 4 s); finished in about 40 s
- [x] Chart and table match `GET /api/benchmark/bench:0001` exactly: PUGMARK origin top-1 100 / 100 / 95.3 / 92%, B4 top-3 83.3% at every level, B3 0% (empty bars); mean rank PUGMARK 1.00 / 1.00 / 1.05 / 1.08, B3 4.67, B4 2.67, n = 150 per level; note shown verbatim

Offline (backend killed, page reloaded)
- [x] OFFLINE REPLAY badge appears and `demo.json` loads
- [x] Generate, Trace, Inject leak, Run benchmark and Export and trace are all disabled
- [x] Graph is interactive (Top 1 → Top 2 switches the 3 highlighted edges), report preview and download work, audit entries are shown
- [ ] **Benchmark tab is empty offline**: `frontend/public/demo.json` still has `benchmark: null`

## Needs a human before `final`
1. **Tanish:** regenerate `demo.json` with the final held-out benchmark (`python backend/scripts/make_demo_bundle.py`). Without it, the offline Benchmark tab says "No benchmark results available".
2. **Tanish:** merge `feat/ui` into `main` (main is still at `5e1b973`; none of the UI phases are merged), run `pytest -q` and `npm run build`, then tag `ok-4` / `final`.
3. **Both:** three timed offline rehearsals (wifi off), record the backup video, and prepare the Q&A sheet. `docs/DEMO_AND_PITCH.md` still does not exist, so the demo script must come from somewhere else.
4. Don't start a benchmark mid-demo: the UI is locked for about 40 s while it runs.

## Files changed
- `docs/reports/phase-5-ui.md` only.

STOPPED. Waiting for APPROVED PHASE 5.
