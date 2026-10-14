# Phase 0 — sim

Developer: Anmol
Branch: `feat/sim`
Status: ready for module review

## Delivered

- Created the `backend/app/sim/` package layout from `docs/02_SIMULATOR.md` section 2. Modules scheduled for later phases contain docstrings only.
- Added bundled synthetic first and last names and state-specific city choices in `names.py`.
- Added the four format profiles, deterministic value rendering, and CSV rendering in `styles.py`.
- Added render-rule tests for profiles, phones, dates, names, email casing, quoting, line endings, encoding, and null tokens.

## Checks run

From `backend/`:

```text
> C:\Users\anmol\AppData\Local\Programs\Python\Python314\python.exe -m unittest discover -s tests/sim -v
Ran 4 tests in 0.001s
OK

> C:\Users\anmol\AppData\Local\Programs\Python\Python314\python.exe -m pytest -q -p no:cacheprovider
4 passed in 0.04s
```

## Open project setup items

- `AGENTS.md` is absent, so its section 7 report template was unavailable; this is a short gate report instead.
- `docs/QUESTIONS.md` is absent and is outside the sim edit scope. Tanish's API/setup session should add it and record the missing `AGENTS.md` there.
- The repository-wide Phase 0 gate also needs the other modules and setup files. No Phase 1 simulator work was started.
