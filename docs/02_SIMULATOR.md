# PUGMARK: Simulator Spec

Owner: Anmol. Suggested agent: Codex. Module folder: `backend/app/sim/` and `backend/scripts/validate.py`.
Read first: `00_PROJECT_CONTEXT.md`, `01_DATA_CONTRACT.md`, `AGENTS.md`. Shapes come from the contract. This file says how to generate the data.

---

## 1. What the simulator does

It invents a fictional insurer (Nova Health), runs 30 days of its life as a stream of log events, plants one data leak with a known cause, loses some of the logs, and hands the engine only what an investigator would really have. It also writes the answer key (truth) to a separate private place that the engine never sees.

Outputs per scenario:
- `PublicScenario` (contract section 8): the only thing the engine reads.
- `ScenarioTruth` (contract section 8): the answer key, used only by tests and the benchmark.
- `PrivateStore`: things that must never reach the engine or the API: the case key, the base table, the row indices of the leaked file, and a function that renders leak rows (for the masked preview and for reveal).

Hard rule: nothing in `PublicScenario` may reveal the truth. Artifact IDs must not encode which artifact is the origin (see 6.4). Event IDs are sequential by time only.

---

## 2. Module layout

```
backend/app/sim/
  __init__.py
  names.py          bundled first/last name lists, city lists (no Faker per row)
  company.py        fixed locations, log sources, actors, access matrix, datasets
  base_table.py     base customers table + hash cache (numpy)
  styles.py         the 4 format styles and the render functions
  exports.py        make_artifact(): filter rows, build sketches, canaries
  background.py     30 days of normal events
  archetypes.py     A1..A5 planting functions
  lossy.py          seq assignment and event loss
  discovery.py      mock Telegram chat
  leakfile.py       leak sample derivation and row rendering
  inject.py         "judge picks an actor" scenario builder
  store.py          in-memory scenario registry + JSON persistence
  generator.py      generate_scenario() entry point
backend/scripts/validate.py
backend/tests/sim/   unit tests
```

---

## 3. Public functions (Tanish's API layer calls exactly these)

```python
@dataclass
class ScenarioBundle:
    public: dict            # PublicScenario as plain dict (contract section 8)
    truth: dict             # ScenarioTruth
    private: "PrivateStore"

def generate_scenario(archetype: str, seed: int, log_loss: float,
                      canary_mode: bool, scale: str) -> ScenarioBundle: ...

def inject_leak(base: ScenarioBundle, actor_id: str) -> ScenarioBundle: ...

def reveal_value(bundle: ScenarioBundle, row_index: int, field: str) -> str: ...   # unmasked, from the leak rows

def canary_alert(bundle: ScenarioBundle, canary_id: str) -> dict: ...              # {canary_id, export_id, ts, message}

def to_summary(bundle: ScenarioBundle) -> dict: ...                                # ScenarioSummary (contract section 12)

def get_bundle(scenario_id: str) -> ScenarioBundle | None: ...                     # store lookup
def warm_cache(scale: str) -> None: ...                                            # build the hash cache
```

Scenario id format: `scn:{archetype}-{seed}-L{loss_percent}` plus `-C` if canary mode plus `-b` if scale is `bench`. Example: `scn:A1-42-L40`, `scn:A1-42-L40-C`. Injected scenarios: `scn:INJ-{base_seed}-{actor_slug}-L{loss_percent}`.

---

## 4. Determinism

- Every random stream is `numpy.random.default_rng(seed_int)` where `seed_int = int.from_bytes(sha256(f"{label}|{seed}").digest()[:8], "big")`. Use a different `label` per concern: `"actors"`, `"background"`, `"archetype"`, `"loss"`, `"leak"`, `"telegram"`, `"ids"`.
- The company (base table, actors, access) is fixed by `COMPANY_SEED = 7` and does NOT change with the scenario seed. Only the incident changes with the scenario seed. This is what makes the hash cache reusable.
- Same arguments give byte-identical JSON. A test must check this.
- No `datetime.now()`, no `random` module, no `uuid4`, no set iteration order dependence (sort before output).

---

## 5. The company (fixed)

### 5.1 Locations and log sources

| id | kind | log_source | monitored | egress_capable |
|---|---|---|---|---|
| sys:customer-db | system | src:customer-db | true | false |
| sys:claims-api | system | src:claims-api | true | false |
| sys:crm | system | src:crm | true | false |
| sys:bi-warehouse | system | src:bi-warehouse | true | false |
| sys:notebook-server | system | src:notebook-server | true | false |
| sys:partner-sftp | system | src:partner-sftp | true | true |
| sys:object-store | system | src:object-store | true | true |
| sys:ticketing | system | src:ticketing | true | false |
| sys:email-gateway | system | src:email-gateway | true | true |
| ep:<user-slug> (one per user) | endpoint | null | false | true |
| ext:telegram-leak-channel | external | null | false | false |
| ext:file-share-site | external | null | false | false |
| ext:personal-cloud-drive | external | null | false | false |
| ext:unknown-host | external | null | false | false |
| ext:vendor-nimbus | external | null | false | false |

`owner_actor` is set on endpoints only. Every `LogSource.location` points at its system.

Rule for the `source` field of an event: `source = log_source(from_loc)` if `from_loc` is a logged system, else `log_source(to_loc)` if `to_loc` is a logged system, else the event is NOT generated at all (nobody logs it). This is why laptop uploads never appear.

### 5.2 Actors

20 users + 3 service accounts (+ `act:anonymous` only in A4).

Named (always present, fixed ids):

| id | name | role | team |
|---|---|---|---|
| act:ravi-menon | Ravi Menon | analyst | Data & BI |
| act:meena-iyer | Meena Iyer | bi-admin | Data & BI |
| act:arjun-das | Arjun Das | contractor | External |
| act:kavya-rao | Kavya Rao | marketing | Growth |
| act:etl-nightly | etl-nightly | service | Platform |
| act:partner-api-key-7 | partner-api-key-7 | service | Partners |
| act:backup-svc | backup-svc | service | Platform |

Generated users (16, names from `names.py`, ids are slugs `act:first-last`): 4 analysts, 4 engineers, 2 marketing, 4 support, 1 contractor, 1 bi-admin. All names are synthetic. Do not use any real person's name.

Access (Location ids the actor can read or write). Every user also has their own `ep:<slug>`.

| role | access |
|---|---|
| analyst | sys:bi-warehouse, sys:notebook-server |
| bi-admin | sys:bi-warehouse, sys:notebook-server, sys:object-store |
| engineer | sys:customer-db, sys:claims-api, sys:bi-warehouse, sys:object-store, sys:ticketing |
| marketing | sys:crm, sys:email-gateway, sys:partner-sftp |
| support | sys:ticketing, sys:crm, sys:claims-api |
| contractor | sys:customer-db, sys:notebook-server |
| act:etl-nightly | sys:customer-db, sys:bi-warehouse |
| act:partner-api-key-7 | sys:bi-warehouse, sys:partner-sftp, sys:crm |
| act:backup-svc | sys:customer-db, sys:object-store |

### 5.3 Datasets

| id | system | columns | identifier_columns |
|---|---|---|---|
| ds:customers | sys:customer-db | customer_id, full_name, email, phone, dob, city, state, signup_date, created_at, policy_no, premium_tier | customer_id, email, phone, policy_no |
| ds:claims | sys:claims-api | claim_id, customer_id, amount, diagnosis_code, claim_date | customer_id |
| ds:marketing-leads | sys:crm | lead_id, full_name, email, city | email |

`ds:customers` also exists as a warehouse copy on `sys:bi-warehouse` (same dataset id, analysts query it there).
`arrivals_per_hour` of `ds:customers` = overall new-record rate in the last 30 days before `found_ts`.

### 5.4 The base table (`ds:customers`)

| | demo scale | bench scale |
|---|---|---|
| total rows N | 310,000 | 31,000 |
| rows matching the story filter (state CG and created_at >= 2025-01-01) | about 48,800 | about 4,880 |

Generation (vectorised numpy, no per-row Python loops, no Faker):
- `created_at`: 45 percent of rows uniform in [2025-01-01, 2026-10-26T00:00:00Z), 55 percent uniform in [2019-01-01, 2024-12-31T23:59:59Z], seconds resolution. Sort ascending. Row order = created_at order.
- `state`: CG 35 percent, otherwise MH, KA, MP, OD, DL, TN, GJ, UP. Cities depend on state (CG: Raipur, Bhilai, Durg, Bilaspur, Korba, Rajnandgaon).
- `customer_id`: `C{index:07d}` in row order.
- `email`: `{first}.{last}{index}@{example.com|example.org|example.net}` (unique).
- `phone`: `6_000_000_000 + (index * 7919 + 12345) % 4_000_000_000` (unique 10 digits, all start 6 to 9).
- `policy_no`: `NH-{created_year}-{index:06d}` (unique).
- `full_name`: first and last name drawn from the bundled lists. Duplicates allowed.
- `dob`: uniform 1950-01-01 to 2004-12-31. `premium_tier`: basic 50, silver 35, gold 15 percent.
- `signup_date` = date part of `created_at`.

Hash cache: for each identifier column compute `h64(case_key, normalize(col, value))` for every row ONCE and store as `numpy.uint64` arrays in `backend/data/cache/{scale}_{column}.npy` (plus a small JSON with `COMPANY_SEED`, N, a checksum). Normalization is invariant to formatting, so any export or leak sketch is just "take the subset of cached hashes, `np.unique`, take the smallest 512". Never recompute HMACs per scenario. Building the demo cache once may take up to about 20 seconds; bench cache about 2 seconds. `warm_cache()` builds it; the API calls it at startup in a background thread.

`case_key = sha256(f"pugmark-case-{COMPANY_SEED}-{scale}")` as bytes (contract section 6).

### 5.5 Format styles (`styles.py`)

| style | delimiter | quoting | header_case | line_ending | encoding | null_token | phone | email | full_name | dates (`signup_date`, `dob`) | created_at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ETL | `,` | minimal | snake | LF | utf-8 | `""` | e164_dash | lower | title | iso | iso |
| CONTRACTOR | `,` | all | title | CRLF | utf-8-bom | NULL | digits10 | mixed | upper | dmy_slash | iso |
| MARKETING | `;` | minimal | title | LF | utf-8 | N/A | intl_spaced | lower | title | mdy_dash_yy | iso |
| NOTEBOOK | `,` | minimal | camel | LF | utf-8 | `""` | digits10 | lower | lower | iso | iso |

Render rules: `e164_dash` = `+91-9876543221`; `digits10` = `9876543221`; `intl_spaced` = `+91 98765 43221`; `iso` date = `2026-10-08`; `dmy_slash` = `08/10/2026`; `mdy_dash_yy` = `10-08-26`; `created_at` is always `2026-10-08T17:42:09Z`; `mixed` email = first letter upper-cased on a random 50 percent of rows (seeded by row index).
`FormatProfile.columns` only lists columns present in the file. Phone gets `style`, email gets `case`, full_name gets `case`, `signup_date` and `dob` get `style`, `created_at` gets `style: "iso"`.
`LeakSample.columns` and `Artifact.columns` always use canonical snake_case names. The header style is only recorded in `header_case`.

---

## 6. Exports, artifacts, canaries

### 6.1 `make_artifact(...)`

Inputs: id, dataset, created_by, created_ts, location, predicate, columns, style, canary_mode.
- Row set = base rows with `created_at <= created_ts` AND `predicate`.
- `row_count`, `columns`, `format_profile` from the style restricted to `columns`.
- `sketches`: for each identifier column in `columns`, `make_sketch` over the cached hashes of the row set (plus canary hashes, 6.3).
- `newest_record_ts` = max `created_at` in the row set (real rows only).
- `arrivals_per_hour` = (rows matching the predicate with `created_at` in `(created_ts - 30 days, created_ts]`) / 720.
- `filter_desc`: human string, for example `state = 'CG' AND created_at >= '2025-01-01'`.

### 6.2 Standing exports in every scenario

- Nightly ETL: `act:etl-nightly`, 02:10Z, `ds:customers` from `sys:customer-db` to `sys:bi-warehouse`, predicate `state = 'CG' AND created_at >= 2025-01-01`, all 11 columns, style ETL. An `export` event is generated for each night from the origin night up to and including the found day (3 to 4 nights). Earlier nights only get a `query` event (rows = filter size) at 02:09Z and no artifact (retired).
- Contractor full export: `act:arjun-das` (or the generated contractor), about 9 days before found, `ds:customers` to `sys:notebook-server`, no predicate, all columns, style CONTRACTOR.
- Marketing export: `act:kavya-rao` (or another marketing user), about 6 days before found, `ds:marketing-leads` from `sys:crm` to `sys:crm`, columns full_name, email, city, style MARKETING. Its rows are a seeded 20 percent sample of the base rows.

### 6.3 Canaries (when `canary_mode` is true)

For each artifact, add 3 fake rows: `n` in 1..3.
- email `canary.{artslug}.{n}@example.net`, phone `500{artnum:03d}{n:04d}` (starts with 5, cannot collide), policy_no `CAN-{artslug}-{n}`, customer_id `CAN{artslug}{n}`.
- `artslug` = the artifact id with `art:` removed.
- Their `created_at` equals the artifact's `newest_record_ts` (so they do not move the watermark).
- Add their hashes to the sketches (and +3 to `row_count` and `distinct`). `canary_ids = ["can:{artslug}-1", ...]`.
- `canary_registry` entries hold the full 16-hex hash of each canary's normalized value per identifier column.

### 6.4 Artifact ids (important)

- For `seed == 42`, archetype A1, scale demo: use the fixed ids in contract Appendix A: E1 (origin), E2 (contractor), E3 (marketing), E4 to E6 (later nightly runs).
- For every other scenario: assign `art:E{n}` with `n` from a seeded random permutation of 1..number_of_artifacts, so that the id carries no information about which artifact is the origin and not even its time order.

---

## 7. Background events (30 days before `found_ts`, up to `found_ts`)

Weekday rates. Weekends: users at 20 percent of the rate, service accounts unchanged. Times are UTC, uniform within the hour window. Rows are log-normal: `rows = max(1, round(exp(N(ln_median, sigma))))`.

| actor | events per weekday | action | object / from_loc | median rows | sigma | hours |
|---|---|---|---|---|---|---|
| analyst | 3 | query | ds:customers @ sys:bi-warehouse | 300 | 0.6 | 8 to 18 |
| bi-admin | 3 | read | ds:customers @ sys:bi-warehouse | 60 | 0.5 | 8 to 18 |
| engineer | 3 + 1 | query / api_call | ds:customers @ sys:customer-db (20, 0.8) / ds:claims @ sys:claims-api (100, 0.7) | | | 8 to 19 |
| marketing | 1 | query | ds:marketing-leads @ sys:crm | 2000 | 0.5 | 9 to 17 |
| support | 4 | read | ds:claims @ sys:claims-api | 5 | 0.5 | 9 to 18 |
| contractor | 2 | query | ds:customers @ sys:customer-db | 50 | 0.7 | 9 to 16 |
| act:etl-nightly | 1 per night | query | ds:customers @ sys:customer-db, rows = filter size | | | 02:09 |
| act:partner-api-key-7 | 2 per day | api_call | ds:marketing-leads @ sys:crm, rows 0 | | | all day |
| act:backup-svc | 1 per night | read | ds:customers @ sys:customer-db, rows = N | | | 03:00 |

Also: one `permission_change` per bi-admin every 10 days on average (grant or revoke on a random in-scope user, scope `sys:bi-warehouse`). Add 1 or 2 near-miss events in every scenario (a different user reads a few hundred rows of the origin artifact; the partner key lists the origin artifact with rows 0).

Do NOT generate background `download`, `export` or `copy` events other than the standing exports above. (Those need artifacts in the catalog.)

Expected total: about 2,000 to 3,500 events at demo scale before loss.

---

## 8. Archetypes

All archetypes put the leaked file in `ext:telegram-leak-channel` (mock). Parameters in `[a, b]` are drawn from the `"archetype"` stream. For seed 42 / A1 / demo the values in the third column are fixed.

Common timing: `found_ts = 2026-10-12T08:30:00Z + offset` where offset is 0 for seed 42, otherwise a seeded value in 0 to 10 days plus 0 to 600 minutes. Telegram post time = upload time + 30 minutes.

### A1 Insider via laptop (MUST)

| step | detail | seed 42 |
|---|---|---|
| origin | nightly ETL artifact, `k` nights before found day, `k` in {2, 3} | Oct 9 (k = 3), id art:E1 |
| insider | random user whose role is analyst, bi-admin or engineer | act:ravi-menon |
| download | `download` of the origin artifact, `sys:bi-warehouse` to the insider's endpoint, same day as origin, 17:00 to 23:00 UTC, rows = artifact rows | 2026-10-09T21:40:00Z |
| upload | endpoint to `ext:telegram-leak-channel`, 12 to 30 hours after download. NEVER generated as an event (unlogged). Recorded in truth only. | 2026-10-10T22:00:00Z |
| near misses | bi-admin `read` of the origin artifact (50 rows); partner key `api_call` listing (0 rows) | Meena 2026-10-09T09:15Z; partner key 2026-10-09T10:30Z |

### A2 Compromised API key (MUST)

- Origin: nightly ETL artifact, `k` in {1, 2}.
- Key: `act:partner-api-key-7` (or the generated service account).
- Event: `api_call`, object = origin artifact, `from_loc = sys:bi-warehouse`, `to_loc = ext:unknown-host`, `meta.client_ip` = an address in 203.0.113.0/24 (documentation range) that differs from the key's usual IP (background `api_call` events carry `client_ip` 198.51.100.10). rows = artifact rows. 01:00 to 05:00 UTC.
- Then `ext:unknown-host` to `ext:telegram-leak-channel`: unlogged (truth only).
- The theft of the key is not an event.

### A3 Vendor SFTP (MUST)

- Origin: an export of `ds:customers` (columns full_name, email, phone, city, created_at, style MARKETING) made by a marketing user, from `sys:customer-db` to `sys:partner-sftp`. The marketing role does not normally have `sys:customer-db` access, so 3 days earlier a `permission_change` event grants that user `sys:customer-db` (this is a visible privilege signal).
- Event: `send`, object = artifact, `from_loc = sys:partner-sftp`, `to_loc = ext:vendor-nimbus`, rows = artifact rows.
- Vendor to Telegram: unlogged, outside the company.
- Truth: `true_actors` = [the user who sent it]. The chain of custody leaves the company at `ext:vendor-nimbus`; a correct engine ends with an inferred hop beyond that point. The report must say so.

### A4 Public bucket (SHOULD)

- Origin: nightly ETL artifact copied by an engineer (`copy`, `sys:bi-warehouse` to `sys:object-store`).
- `permission_change` by the same engineer: grantee `act:anonymous`, scope `sys:object-store`, change grant.
- Anonymous access to the bucket is unlogged. Final hop: `sys:object-store` to Telegram, unlogged.
- `true_actors` = [the engineer].

### A5 Backup copy (SHOULD)

- Origin: `act:backup-svc` copies a full snapshot of `ds:customers` (all columns, style ETL, no predicate) from `sys:customer-db` to `sys:object-store` (`copy`, creates an artifact).
- Two or more users with `sys:object-store` access read it; one `download`s it to their endpoint; endpoint to Telegram unlogged.
- At least two readers have equal anomaly so the engine must show uncertainty (hand-written test H2 mirrors this).

### Leak derivation (all archetypes)

From the final artifact on the true path:
- `ratio` r drawn from {1.0 with 60 percent, 0.98 with 15 percent, 0.5 with 15 percent, 0.1 with 10 percent}. Row subset: seeded random sample of that fraction, always keeping the 5 newest rows. For seed 42: dedupe-like removal of about 1.4 percent of rows (keep the 5 newest), giving about 48,200 rows at demo scale.
- Columns: keep a seeded subset that always contains at least one identifier column and `created_at`. Seed 42: full_name, phone, policy_no, created_at.
- Laundering: with 25 percent probability the file passed through a notebook, so the leak style becomes NOTEBOOK instead of the artifact's style. Seed 42: no laundering.
- Canaries: if the artifact has canaries, all 3 are in the leak when r = 1.0, and each is kept with 90 percent probability otherwise.
- `newest_record_ts` = max `created_at` of the kept real rows (canaries excluded).
- `row_count`, `sketches` (identifier columns present), `format_profile`, `canary_hits` (computed by hashing the leak's canary rows with the case key and matching the registry), `file_name` (`nova_customers_cg.csv` for seed 42, otherwise `nova_{dataset}_{n}.csv`), `masked_preview` (first 5 leak rows in leak order, masked per contract section 10).
- Leak row order: ascending `created_at`. `row_index` in reveal is the position in this order.
- Do not write the leak CSV to disk. Render rows on demand with `render_leak_row(private, i)`.

---

## 9. Loss model (`lossy.py`)

1. Generate ALL events (including planted ones) with timestamps.
2. Sort by ts. Assign `seq` per `source` in that order (1, 2, 3, ...).
3. Loss: for each source `s`, `p_s = clip(log_loss + jitter_s, 0, 0.9)` with `jitter_s` uniform in [-0.05, 0.05] from the `"loss"` stream (no jitter when `log_loss == 0`). Each event is dropped independently with probability `p_s`.
4. Forced critical drop: when `log_loss > 0`, with probability 0.5 (decided once per scenario from the `"loss"` stream) the planted event just before the unlogged final hop is dropped regardless of `p_s`: the A1 download, the A2 `api_call`, the A3 `send`, the A4 `permission_change`, the A5 download. This guarantees the benchmark contains hard cases.
5. Seed 42 / A1 / demo exception: Ravi's download is NEVER dropped when `log_loss <= 0.4` and ALWAYS dropped when `log_loss >= 0.6`. (Demo reliability, and a visible degradation story.)
6. Keep `seq` unchanged for surviving events. Record dropped ids in the truth as `dropped_event_ids`.
7. Artifacts are never lost (contract assumption A-1).

Events with no logging source (laptop uploads) are not generated (section 5.1), so they are not "dropped"; in truth their `event_id` is `null` and `dropped` is `false`.

---

## 10. Mock Telegram chat (`discovery.py`)

- `platform = "telegram-mock"`. Channel: name `"Dump Zone India (demo)"`, handle `"@dumpzone_demo"`, members seeded 1,200 to 9,000.
- 7 to 10 messages in the 6 hours around the post time, from synthetic handles (`@fr3sh_dumps`, `@admin_dz`, `@buyer_0xA`, ...). Short, tame text. One message carries the attachment:
  - text: `fresh insurance customers, CG region, ~{rows_k}k rows. csv attached. dm for the rest`
  - `attachment = {file_name, size_bytes: row_count * 62, rows_hint: row_count}`
- Other messages: greetings, "legit?", "checking", emojis as words. No real brands or people. No instructions on misuse.
- `leak_message_id` = id of the attachment message. `leak_sample.found_at = "ext:telegram-leak-channel"`.
- Everything is labelled SIMULATED in the UI (frontend job). The data in the attachment is synthetic.

---

## 11. Inject ("judge picks the leaker")

`inject_leak(base, actor_id)`:
- Same company and scale. New seed = first 4 bytes of `sha256(f"{base.seed}|{actor_id}")` as int.
- Archetype choice: service account whose id contains `api-key` or `etl` => A2 (key misuse); `act:backup-svc` => A5; a user with `sys:bi-warehouse` access => A1; a user with `sys:partner-sftp` or `sys:email-gateway` access (no warehouse) => A3; anyone else => A1 preceded by a `permission_change` grant of `sys:bi-warehouse` to that user 1 to 3 days earlier (this is a privilege escalation signal the engine can use).
- Force the leaker to be `actor_id`. Keep `log_loss`, `canary_mode`, `scale` of the base.
- Must finish in under 1 second at bench scale and under 3 seconds at demo scale (cache is warm).

---

## 12. Canary alert

`canary_alert(bundle, canary_id)` returns `{canary_id, export_id, ts, message}` where `ts = found_ts` and message is for example `Phishing email received at canary address canary.E1.1@example.net`. Error if canary mode is off or the id does not exist. The API then calls the engine.

---

## 13. Truth and private store

`ScenarioTruth` (contract section 8) is written to `backend/data/scenarios/{id}/truth.json`. `PrivateStore` is in memory only (it can be rebuilt from the seed). The API NEVER serialises `truth` or `private`. The engine function signature accepts only the public dict.

---

## 14. Seed 42 acceptance checks (`tests/sim/test_seed42.py`)

`generate_scenario("A1", 42, 0.4, False, "demo")` must satisfy:
1. Validator passes.
2. Artifacts `art:E1` to `art:E6` exist with the creators, times and styles in contract Appendix A. E1 `row_count` between 47,000 and 51,000. E4, E5, E6 `row_count` > E1 `row_count`.
3. E1 `newest_record_ts` is within 90 minutes before E1 `created_ts`.
4. Leak: `found_at = ext:telegram-leak-channel`, `found_ts = 2026-10-12T08:30:00Z`, columns exactly [full_name, phone, policy_no, created_at], `row_count` between 45,000 and 49,500, leak `newest_record_ts` equals E1 `newest_record_ts` (within the 5-newest rule), `format_profile` equals the ETL style.
5. Containment of the leak's phone sketch in E1's phone sketch is at least 0.95 using the shared `containment()`. E2 `created_ts < leak.newest_record_ts`. E3 columns do not include `phone`.
6. Truth: origin `art:E1`, true actors [`act:ravi-menon`], the download event exists in the public events (loss 0.4), the upload is the last hop with `event_id` null.
7. With `log_loss = 0.6` the Ravi download event is missing from public events and its id is in `dropped_event_ids`.
8. Determinism: two calls produce identical JSON.
9. No forbidden keys in the public dict.
10. Generation time after warm cache: under 3 seconds (demo), under 0.3 seconds (bench).

---

## 15. Other tests Anmol's agent writes

- Loss: over 200 bench scenarios at `log_loss = 0.4`, the mean fraction of dropped (non-forced) events is within 0.05 of 0.4.
- Forced drop happens in about 50 percent of scenarios (between 40 and 60 percent over 200).
- Canary: with canary mode on, leak `canary_hits` is non-empty in every scenario with r = 1.0.
- Id privacy: across 200 scenarios the true origin artifact id is not correlated with `E1` (fewer than 20 percent are `art:E1` outside seed 42).
- Inject: injecting each of the 23 actors yields a valid scenario whose `truth.true_actors` contains that actor (except A3 where it contains the sender).
- Rendering: `render_leak_row` output re-normalised and hashed gives the same hashes as the sketch inputs (spot check 200 rows).
- Reveal returns unmasked values that, once masked, equal `masked_preview`.

---

## 16. Validator (`backend/scripts/validate.py`)

As specified in contract section 14. Phase 1 must include it and a pytest that runs it on a generated scenario and on the hand-written fixtures from Tanish.

---

## 17. Do not

- Do not import anything from `app/engine`.
- Do not put ground truth, base-table rows or the case key in the public dict.
- Do not use Faker for the big table. Do not use real names, real companies or real phone/email patterns outside `example.*`.
- Do not generate background events of types that need catalog entries (section 7).
- Do not change contract shapes. Ask Tanish.

---

## 18. Deliverables by phase

- Phase 1: A1 only. `generate_scenario`, `validate.py`, hash cache, styles, background events, loss model, seed 42 acceptance checks passing, Telegram discovery, `to_summary`, `reveal_value`.
- Phase 2: support Tanish's integration; fix generator bugs found by the engine; speed work if generation is slow.
- Phase 3: A2, A3, `inject_leak`, canary mode and `canary_alert`; A4 and A5 if time.
- Phase 4: benchmark support (bench scale speed, multiprocessing safety), help with baselines.
