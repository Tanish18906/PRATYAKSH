# Phase 3 report: ui
Developer: Anmol | Date: 2026-10-14

## Done
- Reused the existing containment and evidence cards. Corrected cumulative-coverage wording, removed the unsupported 100% confidence claim, retained backend ordering and values, and enlarged the card text.
- Judge injection includes all returned actors, including services. Added dialog semantics, initial focus, Tab containment, Escape, focus restoration, and in-dialog errors. Failed injection preserves the current scenario; successful injection clears previous investigation data.
- Canary alert remains available after origin pinning, is disabled while busy/offline, and displays the actual returned message, identifiers, and UTC time. The returned trace updates the graph and report.
- All successful trace flows refresh report HTML and then audit entries, including report_export. A new trace clears stale report HTML; report failures show normalized errors. Preview uses an empty iframe sandbox; existing exact-HTML Blob download is retained.
- Log-loss and canary controls retain the existing generate integration. Added accessible labels, toggle state, exact button wording, and disabled scenario-dependent actions without a scenario.
- Offline replay retains the existing generated demo.json. Backend actions, including Telegram export and canary alert, are disabled. Masked preview cells now expose keyboard-accessible Reveal buttons; a late reveal response after dialog closure is discarded.
- Enlarged graph node labels from 12px to 16px and edge labels from 10px to 14px, with wrapping. Graph construction, path-selection dependencies, and animation overlays are unchanged. Added 40px control targets and visible focus outlines.
- Live HTTP checks cover A1/A2/A3 public responses, report/audit, changed loss settings, canary alert, and three injections. No backend source, contract, contract.ts, dependencies, or demo bundle changes.

## Files created or changed
- frontend/src/App.tsx
- frontend/src/components/ContainmentTab.tsx
- frontend/src/components/IncidentPanel.tsx
- frontend/src/components/InjectDialog.tsx
- frontend/src/components/ReportTab.tsx
- frontend/src/components/ScenarioControls.tsx
- frontend/src/components/TelegramChat.tsx
- frontend/src/index.css
- frontend/src/state/AppContext.tsx
- frontend/src/state/reducer.ts
- frontend/src/utils/graph.ts
- frontend/tests/phase3.test.tsx
- docs/reports/phase-3-ui.md

## Commands run and real output
From frontend/:
```text
$ npm run build
> pugmark-frontend@1.0.0 build
> tsc -p tsconfig.app.json && vite build
vite v5.4.21 building for production...
✓ 851 modules transformed.
dist/index.html                     0.54 kB │ gzip:   0.35 kB
dist/assets/index-BY_oIaqi.css     20.93 kB │ gzip:   4.63 kB
dist/assets/index-ClG7-Hf2.js   1,032.12 kB │ gzip: 308.97 kB
(!) Some chunks are larger than 500 kB after minification.
✓ built in 3.37s

$ npm run lint
> pugmark-frontend@1.0.0 lint
> eslint .
```
Both exited 0. The existing chunk-size warning remains. The sandbox launcher also printed `Failed to create stream fd: Operation not permitted` three times before each command; neither command failed.

Regression command (uses the already-installed Vite/esbuild toolchain and Node test runner):
```sh
node --input-type=module -e 'import { buildSync } from "esbuild"; buildSync({entryPoints:["tests/phase3.test.tsx"],bundle:true,platform:"node",outfile:"/tmp/pugmark-phase3-tests.cjs"}); await import("/tmp/pugmark-phase3-tests.cjs");'
```
Actual final test summary:
```text
1..8
# tests 8
# suites 0
# pass 8
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 35.462661
```
The initial six tests failed before implementation. Two additional offline/accessibility tests were observed failing before their fixes. Tests exercise the reducer and actual React component markup; they do not execute browser layout or keyboard events.

Live HTTP smoke command (temporary verification script, not a repository deliverable):
```text
$ python3 /tmp/pugmark_phase3_api.py
health: ok
A1: public summary + export + 5 hypotheses + report/audit PASS; trace 39.7 ms
A2: public summary + export + 5 hypotheses + report/audit PASS; trace 13.3 ms
A3: public summary + export + 5 hypotheses + report/audit PASS; trace 10.8 ms
controls: log_loss=0.0, canary=false preserved; events=1443 PASS
controls: log_loss=0.6, canary=false preserved; events=574 PASS
canary: returned alert and pinned trace PASS
inject act:ravi-menon: new scenario PASS; top3=True; inject/export/trace/report/audit 0.398s
inject act:meena-iyer: new scenario PASS; top3=True; inject/export/trace/report/audit 0.381s
inject act:partner-api-key-7: new scenario PASS; top3=False; inject/export/trace/report/audit 0.341s
judge smoke: 2/3 selected actors in top 3
reveal: short reason rejected PASS (no raw values requested)

$ git diff --check
```
HTTP script and diff check exited 0. Socket-restricted sandbox initially blocked the HTTP script; the approved external run produced the results above. Response checks reject private keys and verify graph references, hypothesis order, and the report's counsel notice.

## Gate checks
- [x] Build, TypeScript and lint: pass.
- [x] Frontend regression tests: 8/8 pass.
- [x] Short reveal reason rejected: HTTP pass; late-response privacy regression passes.
- [x] Backend report HTML and report_export audit entry: HTTP pass.
- [x] Judge injection switches scenario: HTTP and reducer checks pass. Two of three selected actors in top three; all operations under five seconds.
- [x] Log-loss and canary settings reflected in generated scenarios: HTTP pass.
- [x] Canary endpoint ready and returns alert plus pinned trace: HTTP pass.
- [x] Offline mutation controls: rendered-markup checks pass.
- [ ] Successful reveal/audit interaction, downloaded-file review, keyboard behavior, projector readability, A2/A3 browser rendering, and offline startup/all-tab browser review: delegated to the user by explicit instruction.

## Not done / cut
- No Phase 4 work or benchmark run.
- No new browser testing after the user instructed: "Don't use Browser UI Tools, Just build the frontend. I'll review the Ui on my own". Earlier browser observations diagnosed the original gaps and do not verify the final changes.
- Preserved the existing generated demo bundle rather than regenerate it or alter backend scripts.

## Contract or spec discrepancies
- Existing missing docs/DEMO_AND_PITCH.md remains unchanged and was already recorded in Phase 2.
- No new contract changes or discrepancies. Alert state derives its type from the existing API client response.

## Risks for integration
- Final visual layout, label overlap at fitted zoom, dialog keyboard interactions, offline startup and browser download remain for human review. Build and server-rendered tests do not establish these behaviors.
- The service-account injection did not place that account in the top three; the two-of-three smoke threshold passed. Results are ranked hypotheses, not guaranteed attribution.
- Existing >500 kB bundle warning remains. Earlier .playwright-mcp artifacts and unrelated untracked backend files are excluded from the commit.

STOPPED. Waiting for APPROVED PHASE 3.
