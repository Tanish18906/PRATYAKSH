# Phase 3 — sim

Developer: Anmol
Branch: `feat/sim`
Status: simulator Phase 3 implementation complete; real cross-module gate pending Tanish's work

## Delivered

- A2 compromised API key and A3 vendor SFTP paths, each with standing exports, planted evidence, private truth, and valid public scenarios. A3 leak columns are restricted to the vendor export's columns.
- Actor-selected `inject_leak` for all 23 actors, including grant events for users without warehouse access and the backup service's A5 route. Injection preserves loss, canary mode, and scale.
- Canary rows and hashes on every artifact, leak canary hits, on-demand reveal of synthetic canary rows, and `canary_alert`.
- Optional A4 public bucket and A5 backup copy archetypes. For A5 injection, truth includes both the selected backup service and the user who downloads the snapshot.

## Checks run

From `backend/` with Python 3.14, loading the exact `sketch.py` reference snippet from `docs/01_DATA_CONTRACT.md` into an in-memory `app.common.sketch` module for provisional checks only:

```text
pytest -q -s -p no:cacheprovider tests/sim
seed 42 generation after cache: 0.916s
bench generation after cache: 0.080s
28 passed in 10.37s
```

Also generated 10 bench scenarios per archetype (A1–A5) with loss 0.4 and alternating canary mode. All 50 passed the public validator, leak-column containment, canary ownership, and upload-time checks. Slowest generation per archetype was 0.131 s or less. A seed 42 demo scenario with canaries produced three leak canary hits; injected demo scenarios for Ravi, Kavya, and the backup service validated in 0.909 s, 0.871 s, and 1.663 s respectively.

The normal suite remains blocked by the shared module:

```text
python -m pytest -q --tb=no -p no:cacheprovider tests/sim
18 failed, 10 passed in 0.34s
All failures: ModuleNotFoundError: No module named 'app.common'.
```

## Pending for the real gate

- `backend/app/common/sketch.py`, engine, API, fixtures, and frontend are absent from this checkout; fetched `origin/main` still contains only the initial docs commit (`9c1c854`). Anmol directed that shared sketch integration wait for Tanish's work.
- Therefore real A2/A3 `trace()` results, Phase 3 API tests, and offline replay could not run here. The provisional in-memory sketch check is not a substitute for that gate.
- `AGENTS.md` and `docs/QUESTIONS.md` remain absent; this report records the dependency. No Phase 4 work was started.
