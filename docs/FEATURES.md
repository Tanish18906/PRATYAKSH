
# FEATURES.md

# PUGMARK: Locked Feature Specification

Version: 1.0  
Contract: `01_DATA_CONTRACT.md` v1.0  
Project: INNOVATHON 2026  
Team: Tanish and Anmol  
Status: Scope frozen for coding agents

## 1. Scope

PUGMARK investigates synthetic data leaks across multiple systems.

It identifies plausible data origins and custody paths using privacy-preserving fingerprints and incomplete event logs.

It reports ranked hypotheses with supporting evidence.

PUGMARK does not determine criminal responsibility, detect real Telegram leaks, or perform production containment.

All data is synthetic.

All Telegram interactions are SIMULATED.

The following six feature groups contain the required features from `00_PROJECT_CONTEXT.md` section 16 and the superseding v1.1 changes.

No seventh feature group may be added without a scope review.

## 2. Feature ownership

Tanish:

- Shared sketch implementation.
- Tracing engine.
- Origin ranking.
- Custody path reconstruction.
- API.
- Privacy backend.
- Integration.

Anmol:

- Simulator.
- Archetypes.
- SIMULATED Telegram discovery.
- Frontend.
- Validator implementation.
- Benchmark and baselines.
- Chokepoint computation.
- Canary flow.

Shared contracts must be agreed before independent implementation.

`01_DATA_CONTRACT.md` is frozen after Phase 0.

Agents only edit files within their assigned modules.

## 3. Locked features

### F-01: Synthetic Incident Generation and Discovery

Tier: Must  
Owner: Anmol  
Phases: 1, 3  
Demo: Steps 1 and 2

Purpose:

Generate synthetic incidents and expose the leaked attachment through a SIMULATED Telegram chat.

Must include:

- Nova Health scenario.
- Deterministic seed.
- Archetype A1.
- Decoy exports.
- Lossy event logs.
- Separate private ground truth.
- SIMULATED Telegram discovery.
- Export and trace interaction.
- Public scenario validator.

Phase 3 Must additions:

- Archetype A2.
- Archetype A3.

Should additions:

- Judge-driven incident injection.
- Log-loss slider.
- Archetypes A4 and A5.

Stretch additions:

- Canary record generation and canary alert workflow.

Contract types:

- `PublicScenario`
- `ScenarioTruth`
- `ScenarioSummary`
- `Discovery`
- `TelegramMessage`
- `LeakSample`
- `Event`
- `Artifact`
- `CanaryEntry`
- `Archetype`

API:

- `POST /api/scenario/generate`
- `GET /api/scenario/{id}`
- `POST /api/leak/export`
- `POST /api/inject`
- `POST /api/canary/alert`

Acceptance criteria:

1. A1 seed 42 produces the specified Nova Health incident with the leak found at `ext:telegram-leak-channel`.
2. Repeating generation with identical parameters produces byte-identical public scenario JSON, and the validator rejects private ground truth in public data.
3. The SIMULATED Telegram attachment can be exported through the contracted endpoint without accessing Telegram or any external service.

### F-02: Privacy-Preserving Fingerprint and Origin Ranking

Tier: Must  
Owner: Tanish  
Phases: 1, 2, 3  
Demo: Steps 3 and 4

Purpose:

Match the leaked file against known export artifacts without sending source rows to the engine.

Must include:

- Shared normalization.
- HMAC-SHA256 bottom-k sketches.
- Per-scenario case key kept outside public scenario data.
- Identifier overlap estimation.
- Schema exclusions.
- Watermark exclusions.
- Containment scoring.
- Specificity scoring.
- Format similarity.
- Origin ranking.
- Candidate exclusion reasons.
- Origin match table.

Stretch additions:

- Canary-based origin pinning, when `canary_hits` are present.
- Joined-source leak analysis only if the core system is complete and its contract can be extended with approval.

Contract types:

- `Sketch`
- `FormatProfile`
- `Artifact`
- `LeakSample`
- `OriginCandidate`
- `TraceResult`

API:

- `POST /api/leak/export`
- `POST /api/trace`

Acceptance criteria:

1. Known sketch normalization vectors and identical/disjoint set tests pass.
2. The origin result contains every artifact exactly once, including excluded candidates with contract-defined reasons.
3. The seed 42 investigation ranks the intended E1 export appropriately without reading private `ScenarioTruth` or raw source rows.

### F-03: Custody Path Reconstruction and Evidence

Tier: Must  
Owner: Tanish  
Phases: 2, 3  
Demo: Steps 4 and 5

Frontend rendering responsibility: Anmol.

Purpose:

Reconstruct plausible leak paths when some transfer logs are missing.

Must include:

- Observed custody hops.
- Explicit inferred hops.
- Maximum two inferred hops per path.
- Path depth limit of six.
- Temporal and access constraints.
- Actor anomaly scoring.
- Path ranking.
- Relative likelihood normalization.
- Actor and location ranking.
- Supporting evidence cards.
- Provenance graph.
- Top-three path switching.
- Dashed amber inferred edges.
- Selected-path highlighting.

Should addition:

- Sequence-gap loss estimation.

Stretch addition:

- Recommended missing evidence based on expected informativeness.

Contract types:

- `Event`
- `Hop`
- `Evidence`
- `Hypothesis`
- `Graph`
- `TraceResult`
- `EvidenceRequest`

API:

- `POST /api/trace`

Acceptance criteria:

1. Every produced path is contiguous, respects time ordering, and contains no more than two inferred hops.
2. Seed 42 produces an evidence-backed path that can represent the missing transfer toward the SIMULATED Telegram destination.
3. The frontend highlights selected hypotheses and always distinguishes observed hops from inferred hops.

### F-04: Privacy Controls, Reporting and Offline Replay

Tier: Must  
Owner: Tanish  
Phases: 2, 3, 5  
Demo: Steps 3, 6 and 8

Frontend and replay responsibility: Anmol.

Purpose:

Keep investigations privacy-conscious, auditable, understandable, and demonstrable without internet or a running backend.

Must include:

- Backend masking.
- Masked preview data.
- Reveal with reason.
- Reveal audit entry.
- Trace and report audit entries.
- Audit log view.
- Auto-drafted incident report.
- HTML report download.
- Offline replay with `DemoBundle`.
- SIMULATED and OFFLINE REPLAY labels.
- Clear uncertainty labels.

Stretch addition:

- Optional LLM narrative phrasing with a three-second timeout and template fallback.

Contract types:

- `LeakSample`
- `AuditEntry`
- `ApiError`
- `DemoBundle`
- `TraceResult`

API:

- `POST /api/reveal`
- `GET /api/audit`
- `GET /api/report/{trace_id}`
- `GET /api/health`

Acceptance criteria:

1. Ordinary API responses contain masked personal values, and reveal requires a reason of at least eight characters with an audit record.
2. The incident report contains observed and inferred evidence, containment recommendations, and "Verify current legal timelines with counsel." It states no specific deadline.
3. With the backend unavailable, the frontend loads the valid seed 42 DemoBundle and supports investigation browsing without real API operations.

### F-05: Containment and Investigation Guidance

Tier: Should  
Owner: Anmol  
Phase: 3  
Demo: Step 6

Engine integration responsibility: Tanish.

Purpose:

Help investigators decide which permissions, keys, or channels deserve containment and which missing evidence should be recovered.

Must include within this feature:

- Chokepoint ranking.
- Greedy second containment recommendation.
- Cumulative coverage display.
- Plain-English containment actions.
- Clear advisory-only presentation.

Stretch addition:

- "Which missing log helps most" recommendation.

Contract types:

- `Chokepoint`
- `EvidenceRequest`
- `Hypothesis`
- `TraceResult`

API:

- `POST /api/trace`

Acceptance criteria:

1. Chokepoint recommendations are derived from candidate-path marginals, not hardcoded for seed 42.
2. Two recommended actions display their contract-provided cumulative coverage without implying that permissions were actually revoked.
3. If no chokepoint or evidence recommendation exists, the UI displays the defined empty state without inventing one.

### F-06: Synthetic Benchmark and Baseline Evaluation

Tier: Should  
Owner: Anmol  
Phases: 3, 4, 5  
Demo: Step 7

Purpose:

Evaluate the tracing approach against simple baselines across different levels of missing logs.

Must include:

- Synthetic benchmark generator.
- Origin top1 and top3.
- Actor top1 and top3.
- Mean rank.
- Multiple log-loss levels.
- Naive baseline comparisons.
- Benchmark API.
- Benchmark chart.
- Benchmark notes explaining synthetic-data limitations.
- Weight tuning restricted to the specified training seeds.
- Reporting results from held-out seeds.
- Hand-written H1 to H7 scenario testing.

Baselines:

Origin:

- `B3_largest_export`
- `B4_most_recent_export`

Actor:

- `B1_last_accessor`
- `B2_biggest_exporter`

PUGMARK is compared with the appropriate baseline methods.

Contract types:

- `BenchmarkResult`
- `MethodStats`
- `Archetype`

API:

- `POST /api/benchmark/run`
- `GET /api/benchmark/{id}`

Acceptance criteria:

1. Benchmark statistics are produced by actual runs and never hardcoded into the UI.
2. The benchmark separates tuning seeds 0 to 49 from reported seeds 50 to 199 and compares top1 and top3 across configured loss levels.
3. The UI displays the required synthetic-data note and never claims real-world accuracy or calibrated probabilities.

## 4. Feature dependencies

Use this dependency order:

    Frozen Data Contract
           |
           +--> F-01 Simulator and Validator
           |        |
           |        v
           |     F-02 Fingerprints and Origins
           |        |
           |        v
           |     F-03 Paths and Evidence
           |        |
           |        +------> F-05 Chokepoints
           |        |
           |        +------> F-06 Benchmark
           |        |
           |        v
           +------> F-04 Report and Replay

Independent work:

- Anmol may build the frontend shell using a contract-valid sample bundle before the engine exists.
- Tanish may build and test the engine against contract-valid fixture input before the simulator exists.
- The simulator must import the shared sketch implementation owned by Tanish.
- The benchmark must never expose private truth to the tracing engine.

Integration boundary:

- `PublicScenario` enters the engine.
- `TraceResult` leaves the engine.
- `ScenarioTruth` is available only to tests and benchmarks.
- The frontend receives only contracted public API responses.

## 5. Phase gates

### Phase 0: Contract and scaffold

Deliver:

- Documentation.
- Project scaffold.
- Frozen `01_DATA_CONTRACT.md`.
- Shared type definitions.
- Contract-valid sample data.

Done when both developers confirm identical data shapes.

No feature implementation beyond the scaffold.

### Phase 1: First functional foundation

Deliver:

- F-01 A1 simulator.
- Public scenario validator.
- Shared sketch implementation.
- F-02 origin ranking foundation.
- Frontend shell on sample JSON.

Done when A1 produces a valid scenario and the UI renders contract-valid sample content.

### Phase 2: Seed 42 end-to-end

Deliver:

- F-02 origin ranking.
- F-03 path search and ranking.
- API wiring.
- Graph rendering.
- First real seed 42 trace.

Done when the simulator, engine, API, and frontend complete the same investigation without hardcoded conclusions.

### Phase 3: Investigation functionality

Deliver:

- F-01 A2 and A3.
- Judge injection.
- Log-loss slider.
- F-04 masking, reveal, audit, report, replay.
- F-05 containment.
- Canary flow if available.
- SIMULATED Telegram workflow completion.

Done when the principal investigation interactions work, errors are handled, and offline replay is available.

### Phase 4: Evaluation

Deliver:

- F-06 benchmark and baselines.
- Held-out benchmark results.
- H1 to H7 test execution.
- Weight tuning on allowed seeds.
- Benchmark charts.

Done when results are backed by actual synthetic runs and reported limitations are visible.

### Phase 5: Freeze and presentation

Deliver:

- Code freeze.
- End-to-end smoke tests.
- Three rehearsals.
- Backup video.
- Verified offline replay.

Done when the team has one working, reproducible demonstration.

No new feature work after code freeze.

## 6. Demo order

Use the following story:

1. Show the SIMULATED Telegram chat containing the synthetic leaked CSV.
2. Click Export and trace.
3. Display the masked incident details and fingerprint.
4. Show matching and excluded export candidates.
5. Show the provenance graph, ranked hypotheses, missing hop, and evidence.
6. Show containment recommendations, report, and audit.
7. Demonstrate a judge-selected synthetic leak or benchmark if ready.
8. Demonstrate offline replay if necessary.

Never display synthetic ground truth as an engine conclusion.

The demo explains hypotheses, not guilt.

## 7. Cut order

Cut from the bottom of this list first.

1. Joined-source leak analysis.
2. Optional LLM narrative phrasing.
3. A4 and A5 archetypes.
4. Extra visual polish beyond readable graph and path highlighting.
5. "Which missing log helps most" card.
6. Canary alert demonstration.
7. Sequence-gap loss estimation.
8. Full benchmark chart if benchmark execution is not reliable.
9. Judge-driven injection.
10. Interactive log-loss slider.
11. Second chokepoint recommendation.

After these cuts, protect the Must-tier workflow.

Do not cut:

- Seed 42 A1.
- Ground-truth separation.
- Contract validation.
- Fingerprint and origin ranking.
- Path search and inferred missing hops.
- Ranked evidence-backed hypotheses.
- Basic graph with observed and inferred edges.
- Masked values.
- Audited reveal.
- Incident report.
- Offline replay.

A2 and A3 remain required by the project scope, but their implementation may be deferred behind a fully working seed 42 investigation if the team is at risk of missing the demonstration deadline. This is a schedule contingency, not a claim that the locked Must scope has been completed.

## 8. Non-goals

Do not build:

- Real Telegram integration.
- Website or dark-web crawling.
- Production leak surveillance.
- Authentication or user accounts.
- Hosted deployment.
- Databases.
- Real personal-data processing.
- Automated production containment.
- A trained ML model.
- Additional API endpoints.
- Additional frontend screens.
- Unapproved contract changes.

Never claim:

- Calibrated probabilities.
- Guaranteed attribution.
- Zero privacy exposure.
- Real-world benchmark accuracy.
- A legal reporting deadline.
- Real Telegram monitoring.
- Production incident-response readiness.

## 9. Agent completion report

After each phase, agents must report:

- Phase completed.
- Features implemented.
- Files modified.
- Tests run.
- Exact test outcomes.
- Outstanding work.
- Contract discrepancies.
- Any scoped feature cut.
- Integration risks.

Wait for human approval before starting another phase.

Approval format:

`APPROVED PHASE N`

## 10. Final acceptance

A successful hackathon demonstration requires:

- [ ] The seed 42 synthetic incident is reproducible.
- [ ] Mock Telegram discovery is clearly SIMULATED.
- [ ] Export and trace follows the contracted API.
- [ ] The engine uses public scenario information only.
- [ ] Origin candidates include evidence and exclusion reasons.
- [ ] Custody paths visibly distinguish missing logs.
- [ ] Hypotheses are ranked as relative likelihoods.
- [ ] Masking is enforced.
- [ ] Reveals require an audited reason.
- [ ] A report can be generated.
- [ ] Offline replay functions.
- [ ] The application runs without internet access.
- [ ] Actual benchmark numbers are used if presented.
- [ ] No unimplemented capability is presented as complete.

## 11. Question requiring contract clarification

QUESTION: `01_DATA_CONTRACT.md` section 8 lists `rows` among forbidden public-scenario keys, but section 4 requires `Event.rows` as a numeric event count. Confirm that validation should reject raw-record containers without rejecting the contracted `Event.rows` count field.
