# Phase 5 — sim

Developer: Anmol
Branch: `feat/sim`
Status: simulator frozen and locally rehearsed; full submission rehearsal blocked by absent integration modules

## Freeze check

- No simulator source code changed in Phase 5. The Phase 4 simulator commit is `2648453`.
- Fetched `origin/main` remains at `9c1c854`, with only the initial docs commit; no phase tags exist in this checkout. The shared sketch, engine, API, frontend, demo bundle script, demo script, slides, and Q&A sheet are absent. `AGENTS.md` and `docs/QUESTIONS.md` are also absent.
- Generated `backend/data/` and Python cache directories remain untracked and are not included in simulator commits.

## Local rehearsal

Loaded the exact sketch reference snippet from `docs/01_DATA_CONTRACT.md` into memory, warmed the demo cache, and repeated the seed 42 / loss 0.4 / canary-on simulator path three times. Each run generated and validated the public scenario, found the mock Telegram attachment, checked three canary hits and the alert, and exercised reveal without printing raw values.

```text
sim rehearsal 1 valid in 1.002 s; 857 events
sim rehearsal 2 valid in 0.924 s; 857 events
sim rehearsal 3 valid in 0.931 s; 857 events
```

These are simulator-only timings. The full offline Telegram-to-graph demo, three real end-to-end rehearsals, backup video, benchmark chart check, and `final` tag require Tanish's integration work and the frontend. No full-demo success or final submission readiness is claimed.
