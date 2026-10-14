# UI redesign brief (for the UI agent)

Read first: `AGENTS.md`, then `docs/UX_FLOW.md`, `docs/UI_LAYOUT.md`, `docs/DESIGN_SYSTEM.md`. This brief wins over them on scope and timing.

## Scope rules

- Front end only: `frontend/`. One agent, one branch `feat/ui-redesign`. Nobody else edits `frontend/` while this runs.
- No change to the API, the contract, `contract.ts` field names, the engine text, `demo.json` or any backend file.
- Everything keeps working: Export and trace, hypothesis switching, origin table, reveal, audit, report, benchmark tab, offline replay, scenario controls, inject, canary.
- Offline: no CDN, no web fonts, no new dependency (if one is unavoidable, one line in `docs/DECISIONS.md` first).
- Derived views are allowed (the answer banner is built from the top hypothesis, the first origin ranking entry, the chokepoint and the evidence request). New data is not.
- Keep existing `data-testid` attributes and test files passing.

## Time box: hard stop 16:00

| Tier | Work | Target | Must |
|---|---|---|---|
| 0 | Fix horizontal overflow (fit 1280 to 1920). Graph fits in view on load and on hypothesis change. Hide ids behind `displayName` and `prettyIds`. | by 15:50 | yes, always |
| 1 | Design tokens and theme (`DESIGN_SYSTEM.md`). Header cleanup: tabs plus two chips plus a Scenario drawer holding all simulator controls. Answer banner. Right rail with three bullets and Details. One-surface Telegram card. | by 15:55 | yes |
| 2 | Graph: preset left-to-right layout, node cards with icons, pill edge labels, legend, hypothesis tabs above the graph. Action cards (cut, collect). | by 16:00 | if time |
| 3 | Trace reveal animation, stage indicator, polish of Origin match, Report, Audit and Benchmark tabs. | only if Tier 2 is done early | no |

If Tier 1 is not done by 15:55, stop and keep Tier 0 only. If anything is half-finished at 16:00, finish the smallest working state, do not start another change.

## Rollback

Before starting, the human tags the current UI: `git tag ui-pre-redesign`. If the redesign breaks any demo step, the human runs `git checkout ui-pre-redesign -- frontend` and the project is back to the old UI in one command.

## Acceptance checklist (show real evidence for each)

1. `cd frontend && npm run build` passes, and `npm run lint` if it exists.
2. At 1920x1080 and 1366x768: no horizontal scroll, no page scroll on Investigation, the whole graph visible. Attach one screenshot of each to the report.
3. Demo steps 1 to 5 run end to end with the backend OFF (offline replay) and again with it ON.
4. No internal ids in the primary views. In the browser console, after a trace, on the Investigation and Origin match tabs (with Details closed):
   `document.body.innerText.match(/\b(art|act|sys|ep|ch|ds|hyp):[\w-]+/g)` must be `null`.
5. Every text colour comes from the tokens; no neon teal remains (`grep -rn "teal\|cyan\|shadow-\[0_0" frontend/src` is empty or justified).
6. Keyboard: Tab reaches the tabs, hypothesis rows, the Scenario button and the dialogs; Esc closes the drawer and dialogs.
7. Reveal still needs a reason of at least 8 characters and still writes an audit entry.

## Report

Write `docs/reports/ui-redesign.md`: what tier was reached, the evidence for the seven checks, what was not done, any deviation from the docs. Then print `STOPPED. Waiting for human.` and do nothing else.
