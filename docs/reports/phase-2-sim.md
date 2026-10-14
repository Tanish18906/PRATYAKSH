# Phase 2 — sim

Developer: Anmol
Branch: `feat/sim`
Status: simulator inputs ready; cross-module gate pending Tanish's shared and engine work

## Delivered

- Added seed 42 checks at log loss 0.0, 0.2, and 0.4 for the public contract, origin, exclusions, Ravi download, and the later nightly exports. These are the simulator inputs for the Phase 2 engine trace gate.
- Measured warm-cache generation against the simulator targets. Demo took 0.879 s and bench took 0.075 s, below their 3 s and 0.3 s limits; no speed change was needed.

## Checks run

From `backend/` with Python 3.14:

```text
python -m pytest -q -p no:cacheprovider tests/sim
6 failed, 10 passed in 0.53s
All six failures: ModuleNotFoundError: No module named 'app.common'.
```

For a provisional check only, I loaded the exact `sketch.py` reference snippet from `docs/01_DATA_CONTRACT.md` into an in-memory `app.common.sketch` module, then ran `pytest -q -s -p no:cacheprovider tests/sim`:

```text
seed 42 generation after cache: 0.879s
bench generation after cache: 0.075s
16 passed in 5.77s
```

## Pending for the real gate

- `backend/app/common/sketch.py`, the engine, and H1–H8 fixtures are absent from this checkout. Fetched `origin/main` and `git ls-remote --heads origin` show only `main` at `9c1c854`. Anmol previously directed that shared sketch integration wait for Tanish's work.
- The Phase 2 `trace()` assertions, full backend `pytest -q`, offline UI walkthrough, and under-3-second trace timing require those modules and their owners. They were not run or claimed here.
- `AGENTS.md` and `docs/QUESTIONS.md` remain absent; this report records the integration dependency. No Phase 3 work was started.
