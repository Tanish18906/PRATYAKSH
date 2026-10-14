
# FRONTEND.md

# PUGMARK: Frontend Engineering Specification

Version: 1.0  
Owner: Anmol  
Stack: React, Vite, TypeScript, Tailwind CSS, Cytoscape.js, Recharts, Framer Motion  
Contract: `01_DATA_CONTRACT.md` v1.0

## 1. Objective

Build the PUGMARK single-page forensic investigation interface.

The frontend must support:

- SIMULATED Telegram discovery.
- Export and trace.
- Incident details.
- Fingerprint and origin results.
- Provenance graph.
- Ranked custody hypotheses.
- Containment recommendations.
- Masked previews and audited reveal.
- Report preview and HTML download.
- Judge-driven synthetic leak injection.
- Log-loss and canary controls.
- Synthetic benchmark results.
- Offline replay.

The frontend never performs leak attribution, scoring, or path reconstruction.

These operations belong to the Python backend.

Do not duplicate engine calculations in TypeScript.

## 2. Non-negotiable engineering rules

1. Copy types directly from `01_DATA_CONTRACT.md`.
2. Preserve snake_case field names.
3. Never create frontend-only substitutes for API data fields.
4. Never read ground truth.
5. Never expose raw source rows.
6. Display backend-masked values.
7. Always label simulated Telegram content SIMULATED.
8. Every displayed probability is relative likelihood.
9. All times remain UTC.
10. All code must run offline.
11. No CDN, Google Fonts request, or external icon dependency at runtime.
12. No database.
13. Do not add screens or endpoints.
14. Build only the assigned phase, test, report, and wait for approval.

## 3. Frontend structure

    frontend/
      package.json
      package-lock.json
      index.html
      vite.config.ts
      tsconfig.json
      tsconfig.app.json
      eslint.config.js
      postcss.config.js
      tailwind.config.js

      public/
        demo.json

      src/
        main.tsx
        App.tsx
        index.css

        types/
          contract.ts

        api/
          client.ts

        state/
          AppContext.tsx
          reducer.ts

        components/
          Header.tsx
          ScenarioControls.tsx
          TelegramChat.tsx
          IncidentPanel.tsx
          ProvenanceGraph.tsx
          HypothesisPanel.tsx
          OriginMatchTab.tsx
          ContainmentTab.tsx
          BenchmarkTab.tsx
          ReportTab.tsx
          AuditTab.tsx
          InjectDialog.tsx
          RevealDialog.tsx
          StatusBadge.tsx
          ErrorMessage.tsx

        utils/
          graph.ts
          benchmark.ts
          format.ts

The component filenames above describe source organization. They do not introduce new product screens.

Keep styling in Tailwind classes and a small set of CSS tokens.

Do not introduce Redux, Zustand, React Router, a component-framework dependency, or a layout plugin.

## 4. Component tree

    App
    |
    +-- Header
    |    +-- StatusBadge
    |
    +-- ScenarioControls
    |
    +-- InvestigationWorkspace
    |    |
    |    +-- IncidentPanel
    |    |    +-- TelegramChat
    |    |
    |    +-- ProvenanceGraph
    |    |
    |    +-- HypothesisPanel
    |
    +-- InvestigationTabs
    |    +-- OriginMatchTab
    |    +-- ContainmentTab
    |    +-- BenchmarkTab
    |    +-- ReportTab
    |    +-- AuditTab
    |
    +-- InjectDialog
    +-- RevealDialog
    +-- ErrorMessage

`InvestigationWorkspace` and `InvestigationTabs` may be layout sections inside `App.tsx`. They do not need dedicated component files.

## 5. Component props

Types must be imported from `src/types/contract.ts`.

### Header

Props:

- `offlineReplay: boolean`
- `simulated: boolean`

Displays PUGMARK, SIMULATED, OFFLINE REPLAY when applicable, and UTC.

### ScenarioControls

Props:

- `scenario: ScenarioSummary | null`
- `busy: boolean`
- `offlineReplay: boolean`
- `onGenerate: () => void`
- `onTrace: () => void`
- `onInject: () => void`
- `onBenchmark: () => void`

Controlled inputs:

- `archetype: Archetype`
- `seed: number`
- `log_loss: number`
- `canary_mode: boolean`

The `scale` submitted by the UI is `"demo"` for interactive scenarios.

### TelegramChat

Props:

- `discovery: Discovery`
- `scenario_id: string`
- `busy: boolean`
- `offlineReplay: boolean`
- `onExportAndTrace: (message_id: number) => void`

The component locates the message identified by `leak_message_id`.

Only messages with attachments display an attachment card.

The export action must use the actual message ID.

### IncidentPanel

Props:

- `scenario: ScenarioSummary | null`
- `leakSample: LeakSample | null`
- `hasTraced: boolean`
- `offlineReplay: boolean`
- `onReveal: (row_index: number, field: string) => void`
- `onExportAndTrace: (message_id: number) => void`

Consumes:

- `ScenarioSummary`
- `LeakSample`
- `FormatProfile`
- `Discovery`

All preview values come from `masked_preview`.

### ProvenanceGraph

Props:

- `graph: Graph | null`
- `hypotheses: Hypothesis[]`
- `selectedPathId: string | null`
- `onSelectPath: (path_id: string) => void`

Consumes:

- `Graph`
- `Hypothesis`
- `Hop`

The graph itself does not fetch API data.

### HypothesisPanel

Props:

- `hypotheses: Hypothesis[]`
- `selectedPathId: string | null`
- `onSelectPath: (path_id: string) => void`

Consumes:

- `Hypothesis`
- `Evidence`
- `Hop`

Do not recompute `probability` or `score`.

### OriginMatchTab

Props:

- `candidates: OriginCandidate[]`

Consumes:

- `OriginCandidate`

Displays every candidate, including excluded candidates.

### ContainmentTab

Props:

- `chokepoints: Chokepoint[]`
- `recommendedEvidence: EvidenceRequest[]`
- `originPinned: boolean`
- `canaryHits: string[]`
- `offlineReplay: boolean`
- `onCanaryAlert: (canary_id: string) => void`

Consumes:

- `Chokepoint`
- `EvidenceRequest`
- `LeakSample.canary_hits`

### BenchmarkTab

Props:

- `benchmark: BenchmarkResult | null`
- `busy: boolean`
- `offlineReplay: boolean`
- `onRun: () => void`

Consumes:

- `BenchmarkResult`
- `MethodStats`

### ReportTab

Props:

- `trace_id: string | null`
- `reportHtml: string | null`
- `busy: boolean`
- `offlineReplay: boolean`
- `onDownload: () => void`

HTML originates from the backend or `DemoBundle.report_html`.

Render safely without executing report scripts.

### AuditTab

Props:

- `entries: AuditEntry[]`

Consumes:

- `AuditEntry`

### InjectDialog

Props:

- `open: boolean`
- `actors: Actor[]`
- `busy: boolean`
- `onConfirm: (actor: string) => void`
- `onCancel: () => void`

### RevealDialog

Props:

- `open: boolean`
- `busy: boolean`
- `onConfirm: (reason: string) => void`
- `onCancel: () => void`
- `revealedValue: string | null`

A successful reveal is transient.

Clear `revealedValue` when the dialog closes.

### StatusBadge

Props:

- `label: string`
- `kind: "simulated" | "offline" | "status"`

These are component presentation variants, not backend enums.

### ErrorMessage

Props:

- `message: string | null`
- `onDismiss: () => void`

Use the microcopy defined in `UI_UX_DESIGN.md`.

## 6. Contract types

File:

`src/types/contract.ts`

This must be a direct TypeScript copy of the public interfaces and enums from `01_DATA_CONTRACT.md`.

No renaming.

No camelCase translation.

No alternate field shapes.

Required enums/types:

- `LocationKind`
- `ActorKind`
- `Role`
- `Action`
- `Archetype`
- `Scale`
- `HopKind`
- `Verdict`
- `ExclusionRule`
- `ChokeItemType`

Required interfaces:

- `Location`
- `LogSource`
- `Actor`
- `Dataset`
- `Event`
- `EventMeta`
- `Sketch`
- `FormatProfile`
- `Artifact`
- `LeakSample`
- `TelegramMessage`
- `Discovery`
- `CanaryEntry`
- `PublicScenario`
- `ScenarioTruth`
- `TraceResult`
- `OriginCandidate`
- `Hop`
- `Evidence`
- `Hypothesis`
- `Chokepoint`
- `EvidenceRequest`
- `Graph`
- `AuditEntry`
- `ApiError`
- `ScenarioSummary`
- `MethodStats`
- `BenchmarkResult`
- `DemoBundle`

`ScenarioTruth` may appear in the shared type-copy file to mirror the contract, but frontend components and API functions must never import or consume it.

Every top-level scenario, trace, and demo bundle must use:

`contract_version: "1.0"`

Validate this version when loading live or replay data.

The frontend must reject incompatible contract versions instead of silently interpreting them.

## 7. Typed API client

File:

`src/api/client.ts`

Base URL:

`/api`

For development, configure Vite to proxy `/api` requests to the locally running FastAPI server.

The API client must:

- Use `fetch`.
- Serialize request bodies as JSON.
- Preserve snake_case.
- Parse JSON responses for JSON endpoints.
- Return text for HTML reports.
- Throw normalized errors based on `ApiError`.
- Handle network timeouts.
- Not retry mutation requests automatically.
- Never use an external hostname.

### Endpoint functions

Implement one function for every endpoint in section 12 of `01_DATA_CONTRACT.md`.

#### 1. Health

`getHealth(signal?: AbortSignal)`

Method:

`GET /api/health`

Returns:

`{ status: "ok"; contract_version: "1.0"; engine_version: string }`

Startup timeout: 2 seconds.

#### 2. Generate scenario

`generateScenario(request)`

Method:

`POST /api/scenario/generate`

Request:

    {
      archetype: Archetype;
      seed: number;
      log_loss: number;
      canary_mode: boolean;
      scale: Scale;
    }

Returns:

`ScenarioSummary`

Respect the API's `log_loss` range of 0 to 0.8. The visible dashboard slider uses 0 to 0.6.

#### 3. Get scenario

`getScenario(id: string, full?: false)`

Method:

`GET /api/scenario/{id}`

Returns:

`ScenarioSummary`

`getScenario(id: string, full: true)`

Method:

`GET /api/scenario/{id}?full=true`

Returns:

`PublicScenario`

This overload uses the same endpoint.

The UI must never request or infer private `ScenarioTruth`.

#### 4. Export leaked file

`exportLeak(request)`

Method:

`POST /api/leak/export`

Request:

    {
      scenario_id: string;
      message_id: number;
    }

Returns:

    {
      leak_sample: LeakSample;
      file: {
        name: string;
        size_bytes: number;
      };
    }

This does not call Telegram.

#### 5. Trace

`traceScenario(request)`

Method:

`POST /api/trace`

Request:

    {
      scenario_id: string;
      top_k?: number;
    }

Returns:

`TraceResult`

#### 6. Inject

`injectLeak(request)`

Method:

`POST /api/inject`

Request:

    {
      base_scenario_id: string;
      actor: string;
    }

Returns:

`ScenarioSummary`

#### 7. Canary alert

`sendCanaryAlert(request)`

Method:

`POST /api/canary/alert`

Request:

    {
      scenario_id: string;
      canary_id: string;
    }

Returns:

    {
      alert: {
        canary_id: string;
        export_id: string;
        ts: string;
        message: string;
      };
      trace: TraceResult;
    }

#### 8. Reveal

`revealValue(request)`

Method:

`POST /api/reveal`

Request:

    {
      scenario_id: string;
      object: "leak_sample";
      row_index: number;
      field: string;
      reason: string;
    }

Returns:

    {
      value: string;
      audit_id: string;
    }

Validate `reason.trim().length >= 8` before submission.

The backend remains authoritative for access and audit recording.

#### 9. Audit

`getAudit(scenario_id?: string)`

Method:

`GET /api/audit`

Optional query:

`scenario_id`

Returns:

`{ entries: AuditEntry[] }`

#### 10. Start benchmark

`runBenchmark(request)`

Method:

`POST /api/benchmark/run`

Request:

    {
      seed_range: [number, number];
      loss_levels: number[];
      archetypes: Archetype[];
    }

Returns:

`{ benchmark_id: string }`

This request is asynchronous. Do not wait for benchmark completion in the initial response.

#### 11. Get benchmark

`getBenchmark(id: string)`

Method:

`GET /api/benchmark/{id}`

Returns:

`BenchmarkResult`

#### 12. Get report

`getReport(trace_id: string)`

Method:

`GET /api/report/{trace_id}`

Returns:

`string`

Content type:

`text/html`

Do not call `.json()` on this response.

### API error handling

Normalized error codes:

- `bad_request`
- `not_found`
- `reason_required`
- `engine_error`
- `not_ready`

Use the HTTP status and the returned `ApiError.error`.

For non-JSON network failures, display the appropriate generic network error.

For a timeout, abort the request using `AbortController`.

Use two seconds specifically for the startup health probe. Other request timeout values should remain reasonable for the operation.

Do not silently treat an engine error as a successful empty result.

## 8. State management

Use one React context and one `useReducer`.

Do not introduce an external state manager.

The context stores:

- Current scenario controls.
- Current `ScenarioSummary`.
- Current `LeakSample`.
- Current `TraceResult`.
- Current `BenchmarkResult`.
- Current audit entries.
- Current report HTML.
- Current selected hypothesis.
- Current selected tab.
- Current loading/error state.
- Whether the app is in Offline Replay mode.
- Current reveal dialog and transient revealed value.
- Current inject dialog state.

These are frontend state variables, not new API schema fields.

### Main state transitions

Initial:

`STARTUP -> HEALTH_CHECK`

Success:

`HEALTH_CHECK -> LIVE_MODE`

Failure or timeout:

`HEALTH_CHECK -> OFFLINE_REPLAY`

Scenario creation:

`GENERATE_REQUEST -> SCENARIO_READY`

Export:

`EXPORT_REQUEST -> LEAK_READY`

Trace:

`TRACE_REQUEST -> TRACE_READY`

Error:

`REQUEST -> ERROR`

The reducer must preserve the most recent valid data unless switching to a newly generated scenario.

When switching scenario IDs:

- Clear the previous trace.
- Clear the previous report.
- Clear the selected path.
- Clear the previous benchmark selection if it no longer applies.
- Keep the current scenario controls.
- Load the new scenario's discovery.

Do not display an old trace alongside a new scenario.

## 9. Action data flows

### 9.1 Generate

1. Read current controls.
2. Call `generateScenario`.
3. Store the returned `ScenarioSummary`.
4. Display `Discovery` in TelegramChat.
5. Clear old trace data.
6. Await Export and trace.

### 9.2 Export and trace

1. Read `scenario.id`.
2. Read `discovery.leak_message_id`.
3. Call `exportLeak`.
4. Store returned `leak_sample`.
5. Call `traceScenario`.
6. Store returned `TraceResult`.
7. Set selected path to the first hypothesis, if any.
8. Open Origin match.
9. Refresh audit entries.

These requests are sequential.

### 9.3 Trace button

1. Require a current scenario.
2. Call `traceScenario`.
3. Replace the active trace.
4. Refresh graph and hypotheses.
5. Refresh audit entries.

The button must not invent a file upload.

### 9.4 Select hypothesis

1. Receive `path_id`.
2. Find matching `Hypothesis`.
3. Highlight edges and nodes belonging to the path.
4. Update the active hypothesis card.
5. Do not call the backend.

### 9.5 Reveal

1. Open dialog with selected preview cell.
2. Request a reason.
3. Validate at least eight characters.
4. Call `revealValue`.
5. Temporarily show the returned `value`.
6. Refresh audit entries.
7. Clear the unmasked value on dialog close.

No browser persistence.

### 9.6 Judge inject

1. Open actor selector.
2. Select a real `Actor.id` from the current scenario.
3. Call `injectLeak`.
4. Replace the current scenario.
5. Display the new simulated Telegram discovery.
6. Clear old trace state.
7. Allow Export and trace.
8. Refresh audit entries.

### 9.7 Canary alert

1. Select a returned `canary_id`.
2. Call `sendCanaryAlert`.
3. Show the simulated alert message.
4. Set returned `trace` as active.
5. Update the graph and origin ranking.
6. Refresh audit entries.

### 9.8 Benchmark

1. Call `runBenchmark`.
2. Store `benchmark_id`.
3. Poll `getBenchmark`.
4. Display `status` and `progress`.
5. Stop polling on `"done"` or `"failed"`.
6. Render charts only from returned statistics.
7. Refresh audit entries.

### 9.9 Report

1. Require `trace.trace_id`.
2. Call `getReport`.
3. Store HTML.
4. Display safe preview.
5. Let Download report save that HTML.
6. Refresh audit entries after the report request.

## 10. Graph rendering

File:

`src/utils/graph.ts`

Graph input:

`TraceResult.graph`

### Node conversion

For every item in `graph.nodes`, create one Cytoscape node.

Cytoscape data should retain:

- `id`
- `kind`
- `label`

These values come from `Graph.nodes`.

Never change canonical IDs.

### Edge conversion

For every item in `graph.edges`, create one Cytoscape edge.

Map:

- `id` -> element ID
- `from` -> Cytoscape `source`
- `to` -> Cytoscape `target`
- `kind` -> edge kind
- `ts` -> timestamp
- `event_id` -> event reference
- `path_ids` -> participating hypotheses
- `label` -> visible label

`source` and `target` are Cytoscape's presentation keys. They do not modify the API contract's `from` and `to` fields.

### Layout

Default:

`breadthfirst`

Configure:

- Directed layout.
- Adequate node separation.
- Padding around the graph.
- No continuous physics simulation.

Use `cose` only if necessary.

Do not install Cytoscape layout extensions.

### Style

Use the exact kind-based visual treatment defined in `UI_UX_DESIGN.md`.

Observed edges:

- Solid.

Inferred edges:

- Dashed amber.

Selected-path nodes and edges:

- Higher opacity.
- Thicker outline or line.
- Remaining graph elements de-emphasized.

### Highlighting

When `selectedPathId` changes:

1. Clear previous selected-path classes.
2. Find edges whose `path_ids` includes the chosen `path_id`.
3. Highlight those edges.
4. Highlight their endpoint nodes.
5. Preserve inferred-edge status.
6. Use the corresponding `Hypothesis.hops` to expose selected-hop details.

Do not compare labels to identify paths.

Use IDs.

### Moving-dash animation

Keep the underlying graph edges unchanged.

Use a lightweight derived visual overlay or selected-edge dash treatment to indicate movement along the chosen path.

The visual overlay must not be serialized into `TraceResult`.

Use one animation loop, not one independent loop per edge.

Target approximately 20 frames per second at most.

Stop or pause when:

- The component unmounts.
- The selected path changes.
- The document becomes hidden.
- Reduced motion is requested.

Destroy the Cytoscape instance on component cleanup.

Avoid rebuilding the entire graph whenever only the selected path changes.

### Missing-log labels

Prefer the contracted `Graph.edges[].label`.

For the selected hypothesis, correlate `Hop` with graph edges using:

- `event_id` for observed hops where present.
- `from_loc`, `to_loc`, and `kind` for inferred hops.

Where an inferred matching hop has `est_loss`, show the estimate.

If unavailable, say the log is missing without inventing a percentage.

## 11. Benchmark chart implementation

File:

`src/utils/benchmark.ts`

Input:

`BenchmarkResult`

Chart library:

Recharts.

### Origin methods

- `pugmark`
- `B3_largest_export`
- `B4_most_recent_export`

### Actor methods

- `pugmark`
- `B1_last_accessor`
- `B2_biggest_exporter`

### Data transformation

For each loss level in `BenchmarkResult.loss_levels`:

1. Find the corresponding method statistics by the string form of the loss level used by the backend.
2. Read `top1`.
3. Read `top3`.
4. Read `mean_rank`.
5. Read `n`.

The transformation must not recalculate accuracy.

Render:

- Loss level on the X-axis.
- Percentage accuracy on the Y-axis.
- Top1 and top3 as distinct metric groups.
- Method names as grouped series.
- A clear legend.
- Sample count.
- Mean rank where applicable.

Use two views inside the same tab, Origin and Actor.

If `BenchmarkResult.status` is `"running"`, show a progress indicator instead of final charts.

If `"failed"`, show the error state.

If no benchmark exists, show the empty state.

Display `BenchmarkResult.note` verbatim:

`Synthetic data. Numbers measure the engine on our simulator, not real-world accuracy.`

No placeholder accuracy values in the rendered final UI.

## 12. Offline replay

File:

`frontend/public/demo.json`

Exact type:

`DemoBundle`

Generated by:

`backend/scripts/make_demo_bundle.py`

Seed:

42

Archetype:

A1

Scale:

`"demo"`

Log loss:

0.4

Canary mode:

true

### Startup logic

1. Create an `AbortController`.
2. Request `GET /api/health`.
3. Abort after 2 seconds if unresolved.
4. On failure, request `/demo.json`.
5. Parse as `DemoBundle`.
6. Require `contract_version === "1.0"`.
7. Store scenario, trace, audit, benchmark, and report HTML.
8. Set Offline Replay mode.
9. Display OFFLINE REPLAY and SIMULATED.

The demo JSON is served locally by Vite.

No internet connection is required.

### Replay behavior by component

| Component | Behavior |
|---|---|
| Header | Shows OFFLINE REPLAY and SIMULATED |
| ScenarioControls | Shows scenario values; backend actions disabled |
| TelegramChat | Renders `scenario.discovery`; export action disabled |
| IncidentPanel | Shows masked `scenario.leak_sample` |
| ProvenanceGraph | Fully interactive using bundle trace |
| HypothesisPanel | Interactive local path selection |
| OriginMatchTab | Displays bundled origin candidates |
| ContainmentTab | Displays bundled recommendations |
| BenchmarkTab | Displays benchmark if non-null; Run disabled |
| ReportTab | Displays `report_html`; local HTML download allowed |
| AuditTab | Displays bundled audit entries |
| InjectDialog | Unavailable |
| RevealDialog | Unavailable |

Offline replay is not represented as a live engine result.

If `/demo.json` is unavailable or invalid, display the specified replay error rather than showing fabricated content.

## 13. Mock-data development plan

Frontend work must start before the engine API is complete.

Use a `DemoBundle` fixture with exact contract shapes.

Phase 1 approach:

1. Copy contract interfaces.
2. Build the page shell.
3. Create valid sample `ScenarioSummary`.
4. Create valid sample `TraceResult`.
5. Render each component from that data.
6. Keep placeholder numeric scores clearly marked as development-only values.
7. Remove development-only placeholders from the final demonstration.
8. Replace the fixture with the generated `demo.json` once the real engine is available.

The sample fixture must use the exact field and enum names.

Never create new response fields to make UI development easier.

Do not modify the contract.

Once the backend is integrated, actual generated results replace sample values.

## 14. Privacy behavior

All personal values returned by ordinary APIs are masked.

Do not attempt to reconstruct full values in TypeScript.

`LeakSample.masked_preview` is the only preview source.

The frontend must not:

- Save revealed values in localStorage.
- Write them to console logs.
- Include them in browser error messages.
- Include them in reports generated on the client.
- Display them in graph labels.
- Expose private `ScenarioTruth`.
- Read private simulator source rows.

Revealed data must only appear after a successful `/api/reveal` response and only for the selected value.

Clear it when the dialog closes.

Audit entries contain the reason, not the raw revealed value.

## 15. Report rendering

`GET /api/report/{trace_id}` returns HTML.

Use a sandboxed iframe for preview.

Do not permit scripts inside report HTML to execute.

Do not inject the report into the application's main DOM with unrestricted `innerHTML`.

For download:

1. Use the exact returned HTML string.
2. Create a local HTML Blob.
3. Trigger a browser download.
4. Release the generated object URL.

Do not implement PDF export.

The report's content belongs to the backend.

The frontend must not create invented legal statements.

## 16. UTC formatting

All timestamps already contain `Z`.

Display UTC explicitly.

Do not apply `toLocaleString()` with the browser's local timezone.

Use `Intl.DateTimeFormat` with `timeZone: "UTC"` or deterministic UTC formatting functions.

Null timestamps display:

`Time unavailable`

Do not use relative times such as "two hours ago" when they could confuse the fixed synthetic incident timeline.

## 17. Build and run

Frontend setup from `frontend/`:

    npm install

Start development server:

    npm run dev

Expected local frontend:

    http://localhost:5173

Production build:

    npm run build

Lint:

    npm run lint

If these scripts are missing from the scaffold, configure them in `package.json`.

Required behavior:

- `dev` launches Vite.
- `build` performs TypeScript checking and Vite production build.
- `lint` runs ESLint against the frontend source.

Run generated build locally to verify that its assets are bundled.

No CDN assets.

No remote fonts.

No runtime hosted dependencies.

## 18. Frontend phases

### Phase 1: Shell and fixture UI

Build:

- Vite React TypeScript scaffold.
- Tailwind.
- Contract types.
- Basic single-page layout.
- Header and controls.
- SIMULATED Telegram chat.
- Incident card.
- Initial graph rendering.
- Hypothesis cards.
- All five tab containers.
- Static development sample using exact contract shapes.

Done when:

- The app builds without TypeScript errors.
- Mock Telegram discovery is visible.
- Graph renders fixture nodes and edges.
- The interface works without the backend.
- No incorrect API fields are used.
- SIMULATED is visible.

Stop and report. Wait for phase approval.

### Phase 2: Real tracing integration

Build:

- Typed API client.
- Generate scenario.
- Export and trace.
- TraceResult integration.
- Ranked hypothesis selection.
- Origin-match table.
- Real graph edges and styling.
- Path highlighting and movement.
- Error handling.

Done when:

- Seed 42 A1 can complete Export and trace.
- UI displays real engine output.
- Graph path selection works.
- Observed and inferred edges remain visually distinct.
- Origin candidates include exclusion reasons.
- No values are hardcoded to make seed 42 look correct.

Stop and report. Wait for phase approval.

### Phase 3: Investigation controls

Build:

- Reveal dialog.
- Audit tab.
- Containment tab.
- Report preview and HTML download.
- Judge injection dialog.
- Log-loss slider integration.
- A2 and A3 compatibility.
- Canary UI if backend is ready.
- Offline replay.
- Usability and projector-readability improvements.

Done when:

- Reveal without an adequate reason is blocked.
- Successful reveal appears in audit.
- Report uses real backend HTML.
- Judge injection switches scenario.
- Log-loss control affects newly generated scenarios.
- Offline replay loads `demo.json` in under the normal startup fallback path.
- A2 and A3 results render without UI changes.

Stop and report. Wait for phase approval.

### Phase 4: Benchmark and verification

Build:

- Benchmark API integration.
- Benchmark progress.
- Origin and actor charts.
- Baseline comparison.
- Synthetic-data notice.
- Empty, loading and failed benchmark states.
- Final UI smoke testing.

Done when:

- A real benchmark result renders.
- Top1 and top3 come from `MethodStats`.
- No benchmark value is invented.
- Charts clearly separate PUGMARK and baseline methods.
- App builds and lints successfully.
- All major UI workflows pass the smoke checklist.

Stop and report. Wait for phase approval.

## 19. Smoke-test checklist

The frontend agent must run these checks before reporting each phase.

### Structural

- [ ] `npm run build` succeeds.
- [ ] `npm run lint` succeeds.
- [ ] No TypeScript errors.
- [ ] No external runtime resource requests.
- [ ] No extra routes or screens.
- [ ] All API fields match the contract.

### Scenario

- [ ] Generate updates the scenario.
- [ ] SIMULATED Telegram chat displays.
- [ ] Attachment comes from `leak_message_id`.
- [ ] Export and trace calls the correct endpoints.
- [ ] New scenario clears old trace.

### Investigation

- [ ] Incident displays the correct masked sample.
- [ ] Graph renders all node kinds.
- [ ] Observed and inferred edges are distinct.
- [ ] Top-three path selection works.
- [ ] Hypothesis ranking matches backend order.
- [ ] Excluded origins remain visible.
- [ ] Relative likelihood is labelled correctly.

### Privacy

- [ ] Reveal requires at least eight characters.
- [ ] Successful reveal refreshes audit.
- [ ] Revealed values disappear after closing.
- [ ] No raw personal value appears in console output.
- [ ] Offline replay does not allow reveal.

### Reporting

- [ ] Report preview renders safely.
- [ ] HTML download works.
- [ ] Report does not state legal deadlines.
- [ ] Report contains the legal-timeline verification note.

### Benchmark

- [ ] Running state shows progress.
- [ ] Failed state does not show fake bars.
- [ ] Chart uses returned metrics.
- [ ] Synthetic-data note is visible.

### Offline

- [ ] Health failure triggers replay after approximately two seconds.
- [ ] Graph and tabs remain interactive.
- [ ] Mutating controls are disabled.
- [ ] Report preview works from bundle.
- [ ] No backend or internet connection is needed.

## 20. Handoff requirements

After each phase, the frontend agent reports:

1. Files created or changed.
2. Components completed.
3. API endpoints integrated.
4. Commands run and real results.
5. Features incomplete.
6. Contract questions or blockers.
7. Confirmation that no unrelated backend files were changed.

The agent must stop after the assigned phase and wait for:

`APPROVED PHASE N`

Do not start the next phase automatically.

## 21. Questions and blockers

QUESTION: The public scenario validator in `01_DATA_CONTRACT.md` section 8 forbids any key named `rows`, while the required `Event` schema contains a numeric `rows` field. Should the forbidden-key validation apply only to raw-row containers rather than the defined event count field? The frontend preserves `Event.rows` exactly as contracted.
