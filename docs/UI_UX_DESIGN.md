
# UI_UX_DESIGN.md

# PUGMARK: UI and UX Design Specification

Version: 1.0  
Contract: `01_DATA_CONTRACT.md` v1.0  
Owner: Anmol  
Project: INNOVATHON 2026  
Interface: Single-page investigative dashboard  
Status: Implementation specification

## 1. Purpose

PUGMARK helps an investigator trace a leaked dataset through multiple internal systems using incomplete event logs.

The interface must answer five questions:

1. What data leaked, and where was it discovered?
2. Which known export most likely contained the leaked records?
3. Which custody paths could explain the leak?
4. What evidence supports or weakens each hypothesis?
5. What should investigators contain or investigate next?

The interface presents ranked hypotheses, not accusations or verified identities of perpetrators.

The core interaction begins in a SIMULATED Telegram chat. The investigator selects the attached CSV and clicks **Export and trace**. PUGMARK fingerprints the file, reconstructs candidate origins and paths, and displays the results.

All records, identities, Telegram messages, and scenarios are synthetic.

## 2. Interface rules

- One application page. No multi-page routing.
- Dark investigative theme.
- One primary accent colour: cyan-teal.
- Large, readable text for projector demonstrations.
- All times remain in UTC. Never convert time zones.
- All personal values remain masked except a value explicitly revealed through the approved reveal flow.
- SIMULATED must be visible wherever Telegram or synthetic incident activity is displayed.
- Probabilities are always labelled **Relative likelihood**.
- Benchmark results must always be labelled as synthetic-data results.
- Do not display private scenario truth or raw source records.
- No runtime network access beyond the local backend.
- No externally hosted fonts, images, icons, scripts, or stylesheets.
- Do not add new screens, API fields, or workflows.

The interface consumes the exact shapes defined in `01_DATA_CONTRACT.md`.

## 3. Information architecture

The application uses the single-page layout defined in `00_PROJECT_CONTEXT.md`, section 11.

The top bar contains scenario controls.

The investigation workspace contains:

- Left: Incident panel, including the SIMULATED Telegram discovery.
- Centre: Provenance graph.
- Right: Ranked hypotheses.

Tabs below the graph contain:

1. Origin match
2. Containment
3. Benchmark
4. Report
5. Audit

The judge injection interaction and reveal interaction use dialogs over the existing page.

No separate settings page, account page, onboarding page, or navigation system is required.

## 4. Main dashboard wireframe

Target: laptop viewport of approximately 1366 × 768 or larger.

    +--------------------------------------------------------------------+
    | PUGMARK                         SIMULATED               UTC         |
    +--------------------------------------------------------------------+
    | Archetype [A1 v] Seed [42] Loss [----40%----] Canary [ON]          |
    | [Generate] [Trace] [Inject leak (judge picks)] [Run benchmark]      |
    +--------------------------------------------------------------------+
    | INCIDENT       | PROVENANCE GRAPH             | HYPOTHESES         |
    |                |                              |                    |
    | Nova Health    |    [Dataset]                  | #1 Relative        |
    |                |        |                     | likelihood         |
    | SIMULATED      |    [Artifact]                 | [=======  ]        |
    | Telegram       |        |                     |                    |
    |                |    [Warehouse]               | Evidence           |
    | [Chat post]    |        |                     | - Observed         |
    | [CSV file]     |    [Endpoint]                 | - Inferred         |
    |                |        :                     |                    |
    | [Export        |   [External]                  | #2 Relative        |
    |  and trace]    |                              | likelihood         |
    |                | [Top 1] [Top 2] [Top 3]      |                    |
    | File details   |                              | #3 ...             |
    | Masked preview | Observed: solid              |                    |
    | [Reveal]       | Missing log: dashed amber    |                    |
    +----------------+------------------------------+--------------------+
    | [Origin match] [Containment] [Benchmark] [Report] [Audit]           |
    +--------------------------------------------------------------------+
    | TAB CONTENT                                                        |
    |                                                                    |
    +--------------------------------------------------------------------+

Desktop layout proportions:

- Incident: approximately 24%.
- Graph: approximately 48%.
- Hypotheses: approximately 28%.

The graph gets the largest working area.

Use a minimum practical graph height of 390px. Permit panel scrolling if content exceeds the viewport.

On narrow screens, stack Incident, Graph, Hypotheses, and tabs vertically. Do not invent mobile-specific screens.

## 5. Investigation flow

### 5.1 Initial state

On startup:

1. Call `GET /api/health`.
2. If it responds successfully within two seconds, enter live mode.
3. Load or generate the seed 42 A1 demonstration scenario.
4. Display the scenario's `Discovery` in the Incident panel.
5. Do not automatically claim a trace has been completed.
6. Wait for the investigator to click Export and trace.

If the backend is unavailable, load `public/demo.json` and enter Offline Replay mode.

### 5.2 SIMULATED Telegram discovery

The SIMULATED Telegram channel is a presentation of `Discovery`.

The chat displays:

- `Discovery.channel.name`
- `Discovery.channel.handle`
- `Discovery.channel.members`
- `Discovery.messages`
- Each message's `sender`, `text`, `ts`, and optional `attachment`
- The leak attachment identified by `Discovery.leak_message_id`

Never connect to Telegram.

#### Wireframe

    +--------------------------------+
    | SIMULATED TELEGRAM             |
    | Channel: [name]                |
    | [handle]  Members: [count]     |
    +--------------------------------+
    | @synthetic_handle             |
    | 2026-10-12 08:30 UTC           |
    |                                |
    | [Synthetic message text]       |
    |                                |
    | +----------------------------+ |
    | | CSV                        | |
    | | nova_customers_cg.csv      | |
    | | Rows: 48,212              | |
    | | Size: [attachment size]   | |
    | +----------------------------+ |
    |                                |
    | [Export and trace]             |
    +--------------------------------+
    | Synthetic scenario. No real   |
    | Telegram connection.          |
    +--------------------------------+

The interface must not display a Telegram logo or text suggesting official Telegram integration.

Clicking Export and trace:

1. Finds the attachment message using `leak_message_id`.
2. Calls `POST /api/leak/export` with `scenario_id` and `message_id`.
3. Receives the masked `LeakSample` and file metadata.
4. Calls `POST /api/trace` with `scenario_id`.
5. Displays the returned `TraceResult`.
6. Opens Origin match by default.

Do not invent a direct raw-file upload endpoint.

The export action must not expose the original leaked rows.

### 5.3 Incident panel

The Incident panel shows the currently investigated leak.

#### Wireframe

    +--------------------------------+
    | INCIDENT                       |
    | Nova Health                    |
    | SIMULATED                      |
    +--------------------------------+
    | Discovery                      |
    | Mock Telegram channel          |
    |                                |
    | File                           |
    | nova_customers_cg.csv          |
    |                                |
    | Found                          |
    | 2026-10-12 08:30 UTC           |
    |                                |
    | Records                        |
    | 48,212                         |
    |                                |
    | Columns                        |
    | [full_name] [phone]            |
    | [policy_no]                    |
    |                                |
    | Newest record                  |
    | [watermark timestamp] UTC      |
    |                                |
    | FORMAT FINGERPRINT             |
    | [delimiter] [phone style]      |
    | [encoding] [line ending]       |
    |                                |
    | MASKED PREVIEW                 |
    | R. M.   +91-98******21        |
    | NH**********17                 |
    |                                |
    | [Reveal]                       |
    +--------------------------------+

Source: `ScenarioSummary.leak_sample` or the response from `/api/leak/export`.

Display the available `FormatProfile` properties only. Do not generate inferred format properties.

Preview shows a maximum of five rows, directly from `masked_preview`.

No personal identifier may be unmasked by default.

### 5.4 Provenance graph

The centre panel visualizes `TraceResult.graph`.

It must show:

- Actors
- Systems
- Datasets
- Artifacts
- Endpoints
- External locations
- Observed custody edges
- Inferred edges representing missing logs

#### Wireframe

    +------------------------------------------------+
    | PROVENANCE GRAPH                               |
    | [Top 1] [Top 2] [Top 3]                       |
    +------------------------------------------------+
    |                                                |
    |               [ds:customers]                   |
    |                      |                         |
    |                  [art:E1]                      |
    |                      |                         |
    |              [sys:bi-warehouse]                |
    |                      |                         |
    |                [ep:ravi-menon]                 |
    |                      :                         |
    |                      :  Missing log            |
    |                      v                         |
    |        [ext:telegram-leak-channel]             |
    |                                                |
    +------------------------------------------------+
    | Solid = observed    Dashed amber = inferred    |
    | Selected path = highlighted                    |
    +------------------------------------------------+

The ASCII drawing is illustrative. Node positions come from Cytoscape.js.

Use built-in `breadthfirst` for the initial path-focused layout.

Use built-in `cose` only when breadthfirst positioning creates unacceptable overlap.

No layout plugin is permitted.

#### Node design

| Kind | Shape | Fill | Border |
|---|---|---|---|
| actor | ellipse | #6489C6 | #9DB9EA |
| system | round-rectangle | #486C79 | #91B2BD |
| endpoint | diamond | #8576AF | #C3B6EB |
| external | triangle | #AC685B | #E9A99D |
| dataset | hexagon | #417F73 | #89CABB |
| artifact | rectangle | #99834D | #DDCB92 |

These are graph-category colours, not additional application accent colours.

Every node also has a shape difference and a visible label.

Node labels must come from `Graph.nodes[].label`.

Use only masked labels supplied by the backend.

#### Edge design

Observed:

- Solid line.
- Neutral slate.
- Normal width: 2px.
- Include the `Graph.edges[].label` where readable.
- No missing-log marker.

Inferred:

- Dashed amber line.
- Default colour: `#F5B95C`.
- Width: 2.5px.
- Label: the supplied edge label.
- Indicate that a log is missing.
- Where a corresponding selected `Hop.est_loss` is available, show the estimated loss in the edge details or tooltip.

Example inferred-edge wording:

`Log missing. Estimated loss: 40%.`

Never silently turn inferred edges into observed edges.

#### Selected hypothesis

Selecting a hypothesis:

1. Read its `path_id`.
2. Find graph edges whose `path_ids` include that value.
3. De-emphasize unrelated graph elements.
4. Highlight selected path edges.
5. Preserve amber styling for inferred hops.
6. Highlight participating nodes.
7. Display the relevant evidence in the hypotheses panel.

Top-path moving-dash effect:

- Draw a visual highlight over the selected path.
- Animate dash offset along the path.
- Keep the underlying observed or inferred edge styling distinguishable.
- Do not change the backend graph.
- Do not introduce extra layout or animation plugins.
- Pause the animation when the graph is not visible.

Hover:

- Slightly increase border thickness.
- Emphasize connected edges.
- Show label and kind.

Selected node:

- Bright accent outline.
- Emphasize connected elements.
- Do not open an additional information screen.

Reduced-motion preference:

- Disable moving dashes.
- Retain static highlighting.

### 5.5 Ranked hypotheses

Source: `TraceResult.hypotheses`.

Display hypotheses in their existing contract order. Never rerank on the frontend.

#### Wireframe

    +--------------------------------+
    | RANKED HYPOTHESES              |
    | Relative likelihood            |
    +--------------------------------+
    | #1                             |
    | [===========       ] [X]%      |
    |                                |
    | [summary_text]                 |
    |                                |
    | Evidence                       |
    | OBSERVED   [evidence text]     |
    | INFERRED   [evidence text]     |
    | ANOMALY    [evidence text]     |
    |                                |
    | [Select path]                  |
    +--------------------------------+
    | #2                             |
    | [========            ] [X]%    |
    | [summary_text]                 |
    +--------------------------------+
    | #3 ...                         |
    +--------------------------------+

Each card displays:

- `rank`
- `path_id`
- `origin_artifact`
- `probability`
- `summary_text`
- `evidence`
- Relevant observed and inferred hops

The UI may present `score_parts` in the same card as a compact technical detail section.

Evidence labels use the exact `Evidence.kind` values:

- observed
- inferred
- anomaly
- fingerprint

Show timestamp as UTC when non-null.

Use "Time unavailable" for null timestamps.

All bars use `Hypothesis.probability`.

Display percentages as relative likelihood values, not certainty or calibrated risk.

Show the first three hypotheses in the graph path selector. The ranked list may contain the full `top_k` result.

### 5.6 Origin match tab

Source: `TraceResult.origin_candidates`.

#### Wireframe

    +--------------------------------------------------------+
    | ORIGIN MATCH                                           |
    +--------------------------------------------------------+
    | Artifact | Verdict | Containment | Format | Watermark |
    |--------------------------------------------------------|
    | art:E1   | Candidate| [X]        | [X]    | [X]       |
    | art:E2   | Excluded | [X]        | [X]    | [X]       |
    | art:E3   | Excluded | [X]        | [X]    | [X]       |
    | art:E4   | Candidate| [X]        | [X]    | [X]       |
    +--------------------------------------------------------+
    | Selected artifact                                      |
    | Origin fit: [X]                                        |
    | Specificity: [X]                                       |
    | Exclusion reason: [rule or none]                       |
    | Notes: [contract notes]                                |
    +--------------------------------------------------------+

Columns:

- `artifact_id`
- `verdict`
- `containment`
- `specificity`
- `format_sim`
- `watermark_term`
- `origin_fit`
- `exclusion_rule`

Keep the contract's sorting order.

Excluded candidates remain visible.

Use `N/A` for null fields. Do not display null values as zero.

Show exact exclusion enum values or a readable label beside them. Preserve the original enum in data and logic.

The fingerprint result must not be presented as proof of a perpetrator.

### 5.7 Containment tab

Source:

- `TraceResult.chokepoints`
- `TraceResult.recommended_evidence`

#### Wireframe

    +----------------------------------------------------+
    | CONTAINMENT                                        |
    +----------------------------------------------------+
    | CHOKEPOINT RECOMMENDATIONS                         |
    |                                                    |
    | 1. [action_text]                                   |
    |    Path coverage: [X]%                            |
    |                                                    |
    | 2. [action_text]                                   |
    |    Cumulative coverage: [X]%                      |
    +----------------------------------------------------+
    | EVIDENCE TO COLLECT                                |
    |                                                    |
    | [request_text]                                     |
    | Relative path mass: [X]                           |
    +----------------------------------------------------+

Recommendations are advisory.

The interface must not imply that PUGMARK has revoked permissions, blocked users, or changed infrastructure.

The evidence request card appears only when `recommended_evidence` is non-empty.

Use `cumulative_coverage` for cumulative containment claims.

Never invent a percentage.

### 5.8 Benchmark tab

Source: `BenchmarkResult`.

#### Wireframe

    +-----------------------------------------------------+
    | BENCHMARK                                           |
    | [Run benchmark]                                     |
    +-----------------------------------------------------+
    | [Origin] [Actor]                                    |
    |                                                     |
    | TOP-1 / TOP-3 ACCURACY                             |
    |                                                     |
    | 100 |                                               |
    |  75 |     ||  ||   ||                               |
    |  50 |     ||  ||   ||                               |
    |  25 |     ||  ||   ||                               |
    |   0 +-----------------------------------            |
    |        0%   20%   40%   60% log loss                |
    |                                                     |
    | Legend: PUGMARK / baseline methods                 |
    |                                                     |
    | Mean rank: [X]                                     |
    | Samples: [n]                                       |
    +-----------------------------------------------------+
    | Synthetic data. Numbers measure the engine on our  |
    | simulator, not real-world accuracy.                 |
    +-----------------------------------------------------+

Use grouped Recharts bars.

Two views within the Benchmark tab:

- Origin ranking
- Actor ranking

Origin methods:

- `pugmark`
- `B3_largest_export`
- `B4_most_recent_export`

Actor methods:

- `pugmark`
- `B1_last_accessor`
- `B2_biggest_exporter`

For each loss level, display top1 and top3 with readable series labels. Separate top1 and top3 groups clearly rather than placing six overlapping bars.

Show `mean_rank` and `n` from the result.

Do not create benchmark numbers in the frontend.

For `status: "running"`, show `progress`.

For `status: "failed"`, show an error and no fabricated charts.

Use `BenchmarkResult.note` verbatim.

### 5.9 Report tab

Source: `GET /api/report/{trace_id}` and `DemoBundle.report_html` in offline replay.

#### Wireframe

    +------------------------------------------------------+
    | INCIDENT REPORT                                      |
    | [Download report]                                    |
    +------------------------------------------------------+
    | Incident summary                                     |
    | How the leak was discovered                          |
    | Scope                                                |
    | Probable origin                                      |
    | Probable custody path                                |
    | Observed and inferred evidence                       |
    | Evidence gaps                                        |
    | Recommended containment                              |
    | Notification checklist                               |
    | Audit trail                                          |
    +------------------------------------------------------+
    | Verify current legal timelines with counsel.        |
    +------------------------------------------------------+

The report preview renders the backend's HTML safely.

Do not rewrite report conclusions in the frontend.

Report language must distinguish observed and inferred evidence.

Reports must refer to reporting breaches to the Data Protection Board and notifying affected people as the rules require.

Never display a legal reporting deadline.

Show:

`Verify current legal timelines with counsel.`

The download action saves the returned HTML. No PDF export implementation is required.

### 5.10 Audit tab

Source: `GET /api/audit`.

#### Wireframe

    +------------------------------------------------------+
    | AUDIT LOG                                            |
    +------------------------------------------------------+
    | UTC TIME     ACTION        OBJECT        REASON       |
    |------------------------------------------------------|
    | [ts]        trace         [object]      -            |
    | [ts]        reveal        [object]      [reason]     |
    | [ts]        inject        [object]      -            |
    | [ts]        report_export [object]      -            |
    +------------------------------------------------------+

Display:

- `id`
- `ts`
- `who`
- `action`
- `scenario_id`
- `object_id`
- `field`
- `reason`

Use the exact audit action enum.

Never display revealed values in the audit log.

No audit-entry editing or deletion controls.

### 5.11 Judge injection dialog

Opened from `Inject leak (judge picks)`.

#### Wireframe

    +----------------------------------------+
    | INJECT A SIMULATED LEAK                |
    |                                        |
    | Choose an actor                        |
    | [Actor selector                  v]    |
    |                                        |
    | A new synthetic leak scenario will    |
    | be generated using this actor.         |
    |                                        |
    | [Cancel]        [Inject leak]          |
    +----------------------------------------+

Actor options come from `ScenarioSummary.actors`.

Submit:

`POST /api/inject`

Body:

- `base_scenario_id`
- `actor`

On success, replace the active scenario with the returned `ScenarioSummary`.

Show the new simulated Telegram discovery. Do not reuse stale trace results.

The investigator can run Export and trace against the new scenario.

### 5.12 Reveal dialog

#### Wireframe

    +----------------------------------------+
    | REVEAL MASKED VALUE                    |
    |                                        |
    | This action will be recorded.          |
    |                                        |
    | Reason for reveal                      |
    | [                                ]      |
    |                                        |
    | Minimum 8 characters                   |
    |                                        |
    | [Cancel]          [Reveal value]       |
    +----------------------------------------+

Request:

`POST /api/reveal`

Exact request fields:

- `scenario_id`
- `object`
- `row_index`
- `field`
- `reason`

`object` must be `"leak_sample"`.

On success, show the returned `value` only in the active reveal dialog or controlled result area. The rest of the UI stays masked.

Do not store the revealed value in persistent state, browser storage, or replay data.

Do not include it in analytics or error logs.

Refresh the audit tab from the backend after a successful reveal.

The reveal dialog is unavailable during offline replay.

### 5.13 Canary demonstration

Canary controls remain within the existing scenario and Containment workflows.

When canary mode is enabled:

- Show whether `LeakSample.canary_hits` contains entries.
- Show `TraceResult.origin_pinned`.
- A canary alert demonstration can call `POST /api/canary/alert` using a valid `canary_id`.
- Show the returned alert and trace.
- Clearly label the activity SIMULATED.

If the backend has not implemented canaries, disable the control rather than fabricate results.

## 6. Visual design system

### 6.1 Colour tokens

| Token | Hex | Purpose |
|---|---|---|
| background | #091119 | Application background |
| surface | #121D27 | Main panels |
| surface-raised | #192733 | Dialogs and cards |
| surface-hover | #233442 | Hover state |
| border | #344754 | Dividers and borders |
| text-primary | #F2F7FA | Main content |
| text-secondary | #B9C8D2 | Secondary information |
| text-muted | #95AAB8 | Tertiary labels |
| accent | #5EEAD4 | Primary interactive accent |
| accent-dark | #164F4C | Accent backgrounds |
| inferred | #F5B95C | Inferred evidence and missing logs |
| danger | #F28B82 | Errors and failed operations |
| success | #7FD6AA | Completed operations |
| focus | #A8FFF0 | Keyboard focus outline |

Cyan-teal is the only primary accent. Amber, red, and green communicate evidence or system status.

Never use category colours as decorative buttons.

### 6.2 Typography

Use system fonts.

Body:

`system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`

Numeric and technical content:

`ui-monospace, SFMono-Regular, Consolas, monospace`

| Role | Size | Weight |
|---|---|---|
| Application title | 28px | 700 |
| Main numerical value | 30px | 700 |
| Panel heading | 20px | 650 |
| Section heading | 18px | 650 |
| Body | 16px | 400 |
| Button | 16px | 600 |
| Table content | 15px | 400 |
| Secondary label | 14px | 500 |
| Graph label | 13px minimum | 600 |

Use line height 1.4 to 1.55.

Do not reduce essential information below 14px outside graph labels.

### 6.3 Spacing

Base spacing unit: 4px.

| Token | Value |
|---|---|
| xs | 4px |
| sm | 8px |
| md | 12px |
| lg | 16px |
| xl | 24px |
| 2xl | 32px |

Panel padding: 16px.

Main section gaps: 12px.

Card corner radius: 10px.

Panel corner radius: 12px.

Button minimum height: 40px.

The layout should remain readable when projected.

## 7. Motion specification

Use Framer Motion only for simple React component transitions.

| Interaction | Motion | Duration |
|---|---|---|
| Panel first appearance | Fade and 6px upward movement | 180ms |
| Hypothesis selection | Border and background transition | 150ms |
| Dialog opening | Fade and small scale transition | 160ms |
| Tab content change | Short fade | 120ms |
| Graph top-path animation | Continuous moving dash | Lightweight loop |
| Loading status | Small pulse | 600ms cycle |
| Benchmark bars | Simple entry transition | 300ms |

Do not animate the entire graph layout continuously.

Do not add particle systems, background animations, elaborate transitions, or external animation libraries.

Honor `prefers-reduced-motion`.

Motion must never delay data visibility.

## 8. UI states

### Empty

No active scenario:

`No incident loaded. Generate a synthetic scenario to begin.`

No trace:

`No trace available. Export the simulated leak and run a trace.`

No hypotheses:

`No supported leak path was found. Review the origin candidates and evidence gaps.`

No origin candidates:

`No known export matches the leaked dataset.`

No audit entries:

`No audit events recorded yet.`

No benchmark:

`No benchmark results available. Run the synthetic benchmark.`

No chokepoints:

`No containment recommendation is available for this trace.`

### Loading

Show action-specific status:

- Generating synthetic scenario...
- Exporting simulated leak...
- Tracing possible custody paths...
- Loading investigation...
- Running synthetic benchmark...
- Loading incident report...
- Recording reveal...

Disable duplicate submissions while an action is pending.

### Error

Keep the current valid screen and display a concise error near the affected action.

Do not delete existing successful results because a later operation fails.

### Offline replay

Persistent badge:

`OFFLINE REPLAY`

Adjacent explanation:

`Showing precomputed synthetic demonstration data.`

Use `DemoBundle`.

Actions requiring backend mutations remain disabled.

Local selections, graph navigation, tabs, and report preview remain usable.

### SIMULATED

Persistent badge:

`SIMULATED`

Show it near the project header and inside the mock Telegram interface.

Guardian-style live threat monitoring is not part of this project.

### Masked

Display the backend-provided masked values. Do not guess or reconstruct missing characters.

### Reveal

Require a reason of at least eight characters.

No reveal without successful backend audit recording.

## 9. Exact microcopy

### 9.1 Buttons and controls

| Element | Exact text |
|---|---|
| Scenario selector label | Archetype |
| Seed input label | Seed |
| Loss slider label | Log loss |
| Canary toggle label | Canary mode |
| Generate button | Generate |
| Trace button | Trace |
| Judge injection button | Inject leak (judge picks) |
| Benchmark button | Run benchmark |
| Mock attachment action | Export and trace |
| Reveal button | Reveal |
| Reveal confirmation | Reveal value |
| Dialog cancel | Cancel |
| Injection confirmation | Inject leak |
| Report download | Download report |
| First path | Top 1 |
| Second path | Top 2 |
| Third path | Top 3 |
| Hypothesis selection | Select path |
| Origin tab | Origin match |
| Containment tab | Containment |
| Benchmark tab | Benchmark |
| Report tab | Report |
| Audit tab | Audit |
| Benchmark view | Origin |
| Benchmark view | Actor |
| Canary action | Simulate canary alert |

### 9.2 Labels

| Element | Exact text |
|---|---|
| Application | PUGMARK |
| Mode indicator | SIMULATED |
| Offline mode | OFFLINE REPLAY |
| Incident heading | Incident |
| Discovery heading | Discovery |
| Telegram heading | SIMULATED TELEGRAM |
| File heading | File |
| Found timestamp | Found |
| Row count | Records |
| Column list | Columns |
| Watermark | Newest record |
| Format section | Format fingerprint |
| Sample rows | Masked preview |
| Graph | Provenance graph |
| Hypotheses | Ranked hypotheses |
| Probability | Relative likelihood |
| Evidence | Evidence |
| Observed kind | Observed |
| Inferred kind | Inferred |
| Anomaly kind | Anomaly |
| Fingerprint kind | Fingerprint |
| Origin score | Origin fit |
| Containment score | Containment |
| Specificity | Specificity |
| Format match | Format similarity |
| Watermark score | Watermark term |
| Chokepoint heading | Chokepoint recommendations |
| Coverage | Cumulative coverage |
| Missing evidence | Evidence to collect |
| Report heading | Incident report |
| Audit heading | Audit log |
| Reveal reason | Reason for reveal |
| UTC indicator | UTC |
| Missing timestamp | Time unavailable |
| Missing metric | N/A |
| Completed benchmark | Synthetic benchmark complete |

### 9.3 Tooltips

| Element | Exact text |
|---|---|
| Relative likelihood | A score normalized across candidate paths. It is not a calibrated probability. |
| Observed edge | Transfer supported by an available event record. |
| Inferred edge | Possible transfer inferred because relevant logs are missing. |
| Origin fit | Relative match between leaked-file fingerprints and known exports. |
| Watermark | The newest record timestamp used to evaluate export timing. |
| Chokepoint | A suggested containment action covering plausible leak paths. |
| Reveal | Requires a reason and creates an audit entry. |
| Log loss | Percentage of simulated event records removed. |
| Canary mode | Adds synthetic identifiers used to trace a leaked export. |
| Inject leak | Creates a new synthetic scenario through the selected actor. |
| Benchmark | Tests PUGMARK on generated scenarios with known synthetic ground truth. |
| Offline replay | Precomputed results are shown because the backend is unavailable. |

### 9.4 Errors

| Condition | Exact text |
|---|---|
| `bad_request` | Invalid request. Check the selected inputs. |
| `not_found` | The requested scenario or result was not found. |
| `reason_required` | Enter a reason of at least 8 characters. |
| `engine_error` | The tracing engine could not complete this operation. |
| `not_ready` | This result is not ready yet. Try again shortly. |
| Network error | Cannot connect to the local backend. |
| Offline start | Backend unavailable. Showing offline replay. |
| Missing replay bundle | Offline replay data is unavailable. |
| Missing attachment | The simulated leak attachment could not be found. |
| Benchmark failure | Synthetic benchmark failed. No results were recorded. |
| Reveal failure | The value could not be revealed. |
| Report failure | The incident report could not be loaded. |
| Empty actor selection | Select an actor to create a simulated leak. |

### 9.5 Permanent notices

Mock Telegram:

`Synthetic scenario. No real Telegram connection.`

Benchmark:

`Synthetic data. Numbers measure the engine on our simulator, not real-world accuracy.`

Rankings:

`Rankings express relative likelihood, not a finding of responsibility.`

Privacy:

`Masked data reduces exposure. It does not eliminate all privacy risk.`

Incident report:

`Verify current legal timelines with counsel.`

## 10. Accessibility

- Maintain at least 4.5:1 contrast for normal body text where applicable.
- Focus states use a visible 2px outline.
- Keyboard users must access tabs, buttons, selectors and dialogs.
- Dialog focus remains inside the active dialog.
- Escape closes dialogs without submitting.
- Use semantic buttons and table headings.
- Show text labels alongside status colours.
- Do not rely on red, amber, green, or node colour alone.
- Every graph node must have a readable label and distinct shape.
- Include a legend for observed and inferred edges.
- Use visible loading text, not spinner-only loading.
- Respect reduced-motion preferences.
- Do not animate values in a way that obscures their actual result.

## 11. Performance and scope controls

Frontend priorities:

1. Accurate data presentation.
2. Mock Telegram export and trace flow.
3. Working graph and ranked hypotheses.
4. Masking, reveal, audit and report.
5. Secondary controls and benchmark.
6. Visual polish.

Use local system fonts.

Use built-in Cytoscape layouts.

Avoid SVG particle effects or large icon libraries.

Do not implement additional pages.

Preserve current investigation data when switching tabs.

Do not invent missing backend data.

## 12. Design acceptance checklist

- [ ] Single-page layout matches section 11 of project context.
- [ ] SIMULATED Telegram chat renders from `Discovery`.
- [ ] Export and trace uses the contracted local API flow.
- [ ] Incident data displays masked values.
- [ ] Graph renders every contracted node kind.
- [ ] Observed and inferred edges are visually distinct.
- [ ] Selecting a top-three hypothesis highlights its path.
- [ ] Selected path has a lightweight moving-dash effect.
- [ ] Hypothesis cards display relative likelihood and evidence.
- [ ] Origin table includes exclusion reasons.
- [ ] Containment card uses actual returned chokepoints.
- [ ] Benchmark shows actual synthetic results only.
- [ ] Reveal requires a reason and produces an audit entry.
- [ ] Report renders without adding legal deadlines.
- [ ] Judge injection creates a new synthetic scenario.
- [ ] Offline replay works without the backend.
- [ ] No runtime external network resources are required.
- [ ] UI remains readable on the presentation laptop.

## 13. Questions and contract issues

QUESTION: `00_PROJECT_CONTEXT.md` section 4.4 uses `2026-10-08 23:12` as the newest record time, while `01_DATA_CONTRACT.md` Appendix B specifies `2026-10-08T17:42:00Z` for the same seed 42 leak. The frontend will display the API-provided `newest_record_ts` without overriding it. Which seed 42 fixture is authoritative?

QUESTION: The context's Must tier says "Leak upload", but the frozen API provides `POST /api/leak/export` for the SIMULATED Telegram attachment and no general upload endpoint. This document implements the v1.1 Telegram export flow only. Is that the intended final interpretation?
