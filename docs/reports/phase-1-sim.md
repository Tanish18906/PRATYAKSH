# Phase 1 — sim

Developer: Anmol
Branch: `feat/sim`
Status: simulator implementation complete; real shared-module gate deferred at Anmol's direction

## Delivered

- A1 scenario generation with the fixed Nova Health company, 30 days of background events, standing exports, the insider download, near misses, lossy logs, and separate truth.
- Vectorized synthetic customer table and reusable keyed-hash `.npy` cache. The simulator imports `h64` and `normalize` from Tanish's `app.common.sketch` and has no copy of them.
- Leak sample, masked preview, on-demand reveal, simulated Telegram discovery, summary and in-memory bundle lookup. Public and truth JSON are persisted separately under `backend/data/scenarios/`.
- Public-scenario and trace validators with the required CLI, plus seed 42, loss, privacy, style and validator tests.

## Checks run

From `backend/` with Python 3.14:

```text
& 'C:\Users\anmol\AppData\Local\Programs\Python\Python314\python.exe' -m pytest -q -p no:cacheprovider tests/sim/test_loss.py tests/sim/test_validate.py tests/sim/test_styles.py
10 passed in 0.31s

& 'C:\Users\anmol\AppData\Local\Programs\Python\Python314\python.exe' scripts/validate.py scenario data/scenarios/scn_A1-42-L40/public.json
VALID

& 'C:\Users\anmol\AppData\Local\Programs\Python\Python314\python.exe' -m pytest -q -p no:cacheprovider tests/sim
3 failed, 10 passed in 0.55s
All three failures: ModuleNotFoundError: No module named 'app.common'.
```

For a provisional end-to-end check, I loaded the exact `sketch.py` reference snippet from `docs/01_DATA_CONTRACT.md` into an in-memory `app.common.sketch` module (no repository file or simulator fallback added), then ran `pytest -q -s -p no:cacheprovider tests/sim`:

```text
seed 42 generation after cache: 1.191s
bench generation after cache: 0.079s
13 passed in 3.95s
```

The generated seed 42 / loss 0.4 scenario has 23 actors, 6 artifacts, 857 surviving events, 47,679 E1 rows and 47,011 leaked rows. The validator passes; the Ravi download is retained, while loss 0.6 drops it. These counts satisfy the acceptance ranges in `docs/02_SIMULATOR.md` section 14. The scenario produces 1,443 events before log loss, below the spec's approximate 2,000–3,500 figure; background activity follows the explicit per-role daily rates, so this estimate needs reconciliation when the simulator spec is next revised.

## Pending for the real gate

- `backend/app/common/sketch.py` is absent from this checkout and from fetched `origin/main` (`9c1c854`). Anmol directed that its integration check be done later when Tanish's work arrives.
- Tanish's H1–H8 fixture JSON is also absent, so the fixture validator run is pending.
- `AGENTS.md`, `docs/QUESTIONS.md`, and the repository `.gitignore` are absent. Generated `backend/data/` files are local outputs and are excluded from this commit; the setup owner should ignore them in Git.

The simulator spec's reusable fixed company key takes precedence over the contract's earlier per-scenario-key sentence. The illustrative seed 42 counts in the story are more specific than the acceptance ranges and differ from this deterministic table; the generated counts satisfy the stated gate. No Phase 2 work was started.
