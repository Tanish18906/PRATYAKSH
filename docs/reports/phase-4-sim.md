# Phase 4 — sim

Developer: Anmol
Branch: `feat/sim`
Status: simulator benchmark inputs ready; full benchmark gate depends on Tanish's engine and API

## Delivered

- Serialized cold hash-cache builds across threads and processes, and published cache metadata only after all four `.npy` arrays were written. A partial metadata file now triggers a rebuild.
- Added a concurrent cold-cache test for two independent benchmark workers. It runs when Tanish's shared `app.common.sketch` exists on disk.
- Checked the 200-seed bench input set and A1 artifact-ID privacy. No benchmark scoring code was added outside the sim ownership boundary.

## Checks run

The shared sketch is still absent, so provisional checks loaded the exact contract reference snippet into memory without adding a repository module:

```text
Two separate cold bench workers completed successfully with the same email hash;
a third worker reloaded the cache with the same value. Total: 1.413 s.

200 bench scenarios, seeds 0–199, archetypes A1/A2/A3 by seed mod 3,
loss 0.4: all public scenarios valid. Generation median 0.078 s,
p95 0.088 s, maximum 0.197 s.

200 A1 bench scenarios: art:E1 was the origin in 34/200 (17%),
below the spec's 20% threshold.

pytest -q -s -p no:cacheprovider tests/sim
seed 42 demo generation after cache: 0.925 s
bench generation after cache: 0.069 s
28 passed, 1 skipped in 10.39 s
```

The normal suite still cannot import the shared sketch:

```text
python -m pytest -q --tb=no -p no:cacheprovider tests/sim
18 failed, 10 passed, 1 skipped in 0.39 s
All failures: ModuleNotFoundError: No module named 'app.common'.
```

## Pending for the real gate

- `backend/app/common/sketch.py`, the engine, API, benchmark runner, and UI remain absent from this checkout. Real cross-process testing with the shared sketch, benchmark metrics and sanity gates, and chart verification require those modules and their owners.
- `AGENTS.md` and `docs/QUESTIONS.md` remain absent. Anmol previously directed that shared sketch integration wait for Tanish's work. No Phase 5 work was started.
