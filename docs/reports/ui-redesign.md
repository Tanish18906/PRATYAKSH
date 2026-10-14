# UI redesign report

Branch: `feat/ui-redesign` (from `feat/ui` at 81f3c50) | Rollback tag: `ui-pre-redesign` | Date: 2026-10-14
Specs: `docs/ui-REDESIGN/UI_REDESIGN_BRIEF.md`, `UX_FLOW.md`, `UI_LAYOUT.md`, `DESIGN_SYSTEM.md`.
Front end only. No change to the API, the contract, `contract.ts`, the engine text, `demo.json` or any backend file. No new dependency.

## Tier reached

All four tiers. The 16:00 time box was waived by the human for this run.

| Tier | Status |
|---|---|
| 0 | Done. No horizontal or page scroll at 1280x720, 1366x768 and 1920x1080. Graph fits on load, on route change and on resize (ResizeObserver). `displayName` and `prettyIds` in `src/utils/names.ts`. |
| 1 | Done. Tokens in `index.css` and `tailwind.config.js` (hex mirror for Cytoscape and Recharts in `utils/tokens.ts`). Header with tabs, two chips and a Scenario drawer holding every simulator control. Answer banner. Right rail: routes, "Why we think so" with three bullets and Details, Where to cut, What to collect next. One-surface Telegram card. |
| 2 | Done. Preset left-to-right layout (`computePositions` in `utils/graph.ts`), node cards with inline SVG icons, pill edge labels, legend, route tabs above the graph, Fit button, Route as text. |
| 3 | Done. Edges draw in time order (120 ms each), the inferred edge on the route pulses once, fingerprint bars fill (400 ms), stage indicator, restyled Origin match, Report, Audit and Benchmark. All motion is off under `prefers-reduced-motion`. |

## Evidence for the seven checks

### 1. Build and lint

```
$ cd frontend && npm run build
✓ built in 6.52s
$ npm run lint
> eslint .
(no output: 0 problems)
```

Tests (bundled with esbuild and run with `node --test`, as in `phase-3-ui.md`):

```
tests/phase3.test.tsx    # pass 8  # fail 0
tests/phase4.test.tsx    # pass 4  # fail 0
tests/redesign.test.tsx  # pass 6  # fail 0   (new: names, answer sentences, preset layout, no ids on cards, layout fits the canvas at zoom 1)
```

### 2. Viewports

Measured in Chromium with `scrollWidth > innerWidth` and `scrollHeight > innerHeight` on the Investigation tab after a trace:

| Viewport | Horizontal scroll | Page scroll |
|---|---|---|
| 1920x1080 | false | false |
| 1366x768 | false | false |
| 1280x720 | false | false |

Screenshots (offline replay, after load): `docs/reports/ui-redesign-1920x1080.png`, `docs/reports/ui-redesign-1366x768.png`.

### 3. Demo steps, backend OFF and ON

Backend OFF (health returns 500): the app loads `demo.json`, shows the Offline replay chip, and the full route, banner, rail and tabs render. Route switching, the node popover, Route as text, the drawer, Origin match, Report and Audit all work. Export and trace, reveal, inject and benchmark are disabled with an explanation, as before.

Backend ON (`uvicorn app.main:app --port 8000`, health ok):
1. Open app: banner shows "Open the Telegram post and press Export and trace."
2. Export and trace: banner fills with "Export E1, created by etl-nightly on 9 Oct, 02:10 UTC", "100% of identifiers match", "Ravi Menon: Bi Warehouse, then Ravi Menon laptop, then Telegram Leak Channel", "81% relative likelihood".
3. Click route #2: graph re-lays out with the new route on the centre line, and the rail and tabs follow.
4. Action cards: "Where to cut" and "What to collect next" scroll into view.
5. Scenario drawer, then Inject leak (Meena Iyer), then Export and trace: the new trace ranks Meena Iyer first at 77%.
6. Run benchmark: finished in about 35 s; charts and the mean-rank table render.

Reveal and canary alert were also run live (see check 7).

### 4. No internal ids in primary views

`document.body.innerText.match(/\b(art|act|sys|ep|ch|ds|hyp):[\w-]+/g)` returned `null` in every case below, with Details closed:
- Investigation: offline at 1920 and 1366, live after the first trace, and live after inject and trace.
- Origin match: offline.

### 5. Colours from tokens

```
$ grep -rn "teal\|cyan\|shadow-\[0_0" frontend/src
(empty)
$ grep -rnE "#[0-9A-Fa-f]{6}\b" frontend/src | grep -v "utils/tokens.ts\|index.css"
(empty)
```

The only literal colour outside the token files is the dialog overlay `rgba(28,32,48,0.3)`, which is the ink token at 30%. There are no emoji in `frontend/src`.

### 6. Keyboard

The Tab order runs: header tabs, Scenario, Export and trace, Masked sample, Where to cut, What to collect next, route tabs, Fit, Route as text, route rows, Details, cut and request lists, Simulate canary alert. Arrow keys move between header tabs, route tabs and route rows, and the rows and tabs stay in sync.

Escape behaviour:
- **Scenario drawer:** Esc closes it and focus returns to the Scenario button. Clicking the overlay also closes it.
- **Inject dialog:** focus opens on the actor picker.
- **Reveal dialog:** Esc closes it, including after a value has been revealed. That case was a pre-existing bug, now fixed (see deviations).

### 7. Reveal

The Reveal button stays disabled while the reason is under 8 characters, and a live counter reads "N characters, 8 minimum". A live reveal wrote this audit entry to `backend/data/audit.jsonl`:

```
{'action': 'reveal', 'field': 'email', 'reason': 'Verify customer before notice', 'object_id': 'leak:A1-2155209066#0'}
```

## Deviations from the docs

1. **Graph geometry and rendering (round 2, after "blurry, text too small" feedback).** Node cards and edge labels are now HTML on top of the Cytoscape canvas; Cytoscape draws only the lines and handles clicks, hover, pan and wheel zoom. The layout stretches to the canvas instead of using the spec's fixed 168 px cards on a 240 px grid: cards are 120 to 212 px wide, gaps 64 to 140 px and lanes 66 to 120 px. Fit never zooms above 1. The result is that the graph is drawn at zoom exactly 1 at both 1920x1080 and 1366x768 (measured: card transform `scale(1)`). Before, the canvas labels were zoomed to about 0.7 and resampled, which is what made them blurry and small. Cards on the selected route are 64 px tall with a 14 px name (13 px on narrow cards) and a 12 px time; cards on other routes are 48 px, at 60% opacity, and show "Route #n · p%" instead of a time. Edge labels sit just above the line so the dashed inferred line stays visible. Off-route edges are at 30% opacity (spec 25%).
2. **Rail widths at 1280–1599.** The rails are 264 | 1fr | 320 (spec 288 | 1fr | 340) to give the graph more width at 1366. At 1600 and above the spec values (320 | 1fr | 380) are used. Graph fit padding is 20 px (spec 48), because the layout already fills the canvas.
3. **Origin match has no "Made by" or "Date" columns.** `TraceResult` and `ScenarioSummary` carry neither for non-winning exports. The winner's maker and date are in the answer banner, and raw scores and rule codes are under Details.
4. **The Containment tab is gone.** It is not in the spec's tab list. Its content (cut point, evidence request, canary check and the Simulate canary alert button) moved into the right rail. The `ContainmentTab` component is reused and its phase-3 test still passes. In `reducer.ts`, `ActiveTab` became `investigation | origin | report | audit | benchmark`.
5. **Three routes in the rail and the tabs.** The spec shows three, and the engine returns five. Routes #4 and #5 stay in the graph, faded.
6. **Inject does not trace on its own.** It creates the new scenario, and the judge then presses Export and trace on the new post. UX_FLOW section 7 says "A new trace runs live"; the state logic was left unchanged.
7. **Export and trace is disabled during offline replay.** An existing phase-3 test requires this. The bundled trace is already on screen.
8. **The benchmark note is the backend's text, shown verbatim.** An existing phase-4 test requires it, so the spec's fixed sentence is not used.
9. **Location names are shown as the backend sends them**, for example "Bi Warehouse" rather than the spec's "BI warehouse". Renaming them would make the UI disagree with the engine's text.
10. **Bug fix.** Before, after a reveal succeeded, focus fell to `<body>` and Esc no longer closed the dialog. Focus now moves back into the dialog.
11. **Clicking a node still selects the best route through it** (existing behaviour) and now also opens the popover. Hovering an edge shows a tooltip.
12. **Dead helpers removed.** `formatUtcTime`, `formatUtcShort` and `formatProbability` were deleted from `utils/format.ts` because nothing uses them any more.

## Round 2: typography

- **Rail text.** Body text in the right rail ("Why we think so", where to cut, what to collect next) is now 14 px with a 21 px line height. It was 13/18; the ui-ux-pro-max guidance asks for at least 1.5.
- **Line breaks.** `text-wrap: pretty` on paragraphs and `balance` on headings, for tidier line breaks.
- **Incident facts.** "Found" and "Company" take a full row, so the date no longer breaks across two lines at 1366.
- **Fixed in this round:**
  - A tapped node's popover was cleared when the tap also switched the route. It now appears above the card's new position.
  - The graph label pills briefly used a fade animation that animated `transform` and overrode their position. They now use an opacity-only fade.

## Not done or not checked

- **Narrow screens.** Below 1280 px the grid collapses to one column and the page scrolls. This was not tested, as the spec allows.
- **Error retry.** Errors show one line with Dismiss. There is no Retry button, because the handlers have no generic retry.
- **Trace speed.** Live trace time was not measured.
- **Reduced motion.** It is implemented through CSS and a check in the graph, but was not tested with the OS setting turned on.
- **Device scaling.** Crispness was checked at device pixel ratio 1 only. The HTML cards are rendered by the browser at any ratio, but a 125% or 150% display was not tried.
- **Commits.** Nothing is committed yet.
- **Ownership.** `AGENTS.md` lists `ui` as Anmol's module. This run was done in Tanish's session at the human's request, on `feat/ui-redesign`.

## Files

Changed:
- `frontend/index.html`, `tailwind.config.js`, `src/index.css`, `src/App.tsx`
- `src/state/reducer.ts`, `src/state/AppContext.tsx` (tab ids only)
- `src/utils/format.ts`, `src/utils/graph.ts`
- `src/components/`: `AuditTab`, `BenchmarkTab`, `ContainmentTab`, `ErrorMessage`, `Header`, `HypothesisPanel`, `IncidentPanel`, `InjectDialog`, `OriginMatchTab`, `ProvenanceGraph`, `ReportTab`, `RevealDialog`, `ScenarioControls`, `StatusBadge`, `TelegramChat`

New:
- `src/components/AnswerBanner.tsx`, `src/components/Icon.tsx`
- `src/utils/answer.ts`, `icons.ts`, `names.ts`, `tokens.ts`
- `tests/redesign.test.tsx`
- `docs/reports/ui-redesign-1920x1080.png`, `docs/reports/ui-redesign-1366x768.png`

Rollback: `git checkout ui-pre-redesign -- frontend`
