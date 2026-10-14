# UI layout and components

Status: wins over older layout notes. Pure front-end change in `frontend/`. No change to the API, the contract types, the data or the offline rule (no CDN, no web fonts).

Viewports: **1920x1080** (projector, primary) and **1366x768** (laptop). No horizontal scroll at any width of 1280 or more. No page scroll on the Investigation screen: panels scroll inside themselves. The current UI overflows horizontally at 1920 (the header buttons, the time zone control and the right panel are cut off). Fixing that is the first job.

---

## 1. Page frame

**Header, 56px, white, 1px bottom line.**
- Left: logo mark, wordmark "PUGMARK", then the case name in muted text ("Nova Health, case A1-42").
- Centre: tabs **Investigation | Origin match | Report | Audit | Benchmark**.
- Right: chip "Simulated data", chip "Offline replay" (only when offline), button "Scenario" (opens the drawer).

**Body grid** on the paper background, 16px gap and padding:
- width 1600 and up: `320px | 1fr | 380px`
- width 1280 to 1599: `288px | 1fr | 340px`
- the centre column is a stack: answer banner on top, graph filling the rest.

Footer line inside the body bottom, 12px muted: "Simulated data. Rankings are relative likelihoods, not a finding of responsibility."

---

## 2. Regions

### Left rail: the post
1. **Telegram card** (one surface, no cards inside cards). Channel header (avatar, name, subscribers, a small "Simulated channel, no real Telegram connection" caption), the message list, and the message with the file. The file row shows file name, size and row count. The **Export and trace** button sits directly under the file row, full width, primary style. The message list scrolls inside the card; the card is max 55% of the rail height.
2. **Incident facts card.** A two column key/value list: Found (9 Oct style date, UTC), Leaked records, Columns, Company. Values 16px semibold, labels 12px muted. Nothing else.

### Centre: the answer and the route
1. **Answer banner**, full width, white card, 16px padding.
   - Row 1, small label "Most likely source", then one sentence at 20px semibold: "Export E1, the customer export made by the nightly ETL on 9 Oct, 02:10". Right side: a green chip "100% of identifiers match".
   - Row 2, small label "Most likely route", then one sentence: "Ravi Menon: BI warehouse, then his laptop, then the Telegram channel". Right side: "88% relative likelihood" with a thin bar.
   - Row 3, two small text buttons with icons: "Where to cut" and "What to collect next". Each scrolls to its card in the right rail.
   - Before a trace, the banner shows only the empty-state sentence.
2. **Stage indicator** (4 dots, labels below, 12px), above the graph, left aligned.
3. **Hypothesis tabs**, above the graph, right aligned: `#1  88%`, `#2  7%`, `#3  3%`. Replaces the old "Highlight Top 1 / 2 / 3" and "Reset view" buttons. A small "Fit" icon button resets the view.
4. **Graph canvas**, fills the remaining height, white card with a faint dot grid. Legend inside, bottom left. Collapsible "Route as text" bar at the bottom.

### Right rail: who, why, what to do
1. **Hypothesis list**, three compact rows: rank, name, one-line route, likelihood bar. The selected row has an indigo left border and a tinted background.
2. **Why we think so** for the selected hypothesis: three bullets, each with a coloured dot and a time stamp on the right.
   - green dot, "Fingerprint": "100% of leaked identifiers appear in Export E1."
   - blue dot, "Observed": "Ravi Menon downloaded it from the BI warehouse, 9 Oct 21:40 UTC."
   - amber dot, "Inferred": "A move to the Telegram channel is inferred because no log was found."
   A "Details" disclosure under the bullets shows ids, hashes and the full engine text in monospace.
3. **Where to cut** card (chokepoint): one sentence and one number, "Blocking the BI warehouse download path would stop 85% of likely routes."
4. **What to collect next** card (evidence request): one sentence, the log name and the likelihood that would change.
5. Origin match table lives on its own tab, not in this rail.

---

## 3. Graph specification

- **Library:** Cytoscape.js, already installed. No new layout plugin.
- **Layout:** `preset`, computed in code, left to right by time. x = hop index times 240px, y = lane times 120px. The selected hypothesis sits on one straight horizontal line; other hypotheses branch to lanes above and below.
- **Fit:** call `fit` with 48px padding on load, on hypothesis change and on resize. Everything visible without scrolling or zooming. Mouse wheel zoom allowed, min zoom 0.5.
- **Nodes:** rounded rectangle cards, 168x56. Icon on the left (document for exports and datasets, server for systems, laptop for personal devices, paper plane for the Telegram channel), name 14px semibold on the first line, time 12px muted on the second. Border 1px, fill white. The leak location has a red border and a red icon. The origin export has a green border.
- **Edges:** 2px, arrow head, curve style `bezier`.
  - observed: solid, `--observed` blue.
  - inferred: dashed (6 4), `--inferred` amber, with a pill label "inferred, no log found".
  - edge labels are short verbs ("exported", "downloaded", "sent") in a white pill with 4px padding so they never collide with lines.
  - non-selected hypotheses: 25% opacity.
- **Legend:** three entries, bottom left: Observed (solid blue), Inferred (dashed amber), Leak location (red).
- **Hover:** tooltip with time, rows moved, evidence type. **Click** a node: popover with the same plus the actor name.
- **Reveal animation:** edges draw in time order, 120ms each, the dashed edge pulses once at the end. Disabled under reduced motion.
- Never print an id as a node label. Use `displayName`.

---

## 4. Other components

| Component | Spec |
|---|---|
| Primary button | indigo fill, white text, 40px high, 8px radius, 14px semibold. Hover darkens 8%. Disabled 50% opacity. |
| Secondary button | white fill, 1px line-strong border, ink text. |
| Text button | indigo text, no border, underline on hover. |
| Chip | 24px high, 12px text, 999px radius, tinted background and matching text. "Simulated data" amber tint, "Offline replay" ink tint, match chips green tint. |
| Card | white, 1px `--line` border, 12px radius, no shadow by default. Never nest a card inside a card; use a divider line instead. |
| Tabs (header) | text only, 14px, selected has a 2px indigo underline. |
| Likelihood bar | 6px high, rounded, indigo fill on a `--line` track. |
| Scenario drawer | 360px wide, slides from the right with a dim overlay; fields: archetype select, seed number, log loss slider (0, 20, 40, 60) with the value shown, canary switch, buttons Generate, Inject leak, Run benchmark. Closes on Esc and on overlay click. |
| Reveal dialog | centred, 420px, shows what will be revealed, a required reason field (min 8 chars) with a live counter, Cancel and Reveal buttons. |
| Skeleton | `--line` rectangles with a slow shimmer; static under reduced motion. |
| Empty state | one icon, one sentence, at most one action. |

---

## 5. Origin match, Report, Audit, Benchmark tabs

- **Origin match:** a clean table. Columns: Export, Made by, Date, Match, Verdict. The winner row is highlighted green with a tick; excluded rows show a grey "Excluded: " reason in words ("Older than the newest record in the leak", "Different columns"), never the rule code. Rule codes go into Details.
- **Report:** a paper-style preview on the left (white page on the paper background), "Download" and "Copy summary" on the right.
- **Audit:** a simple list, newest first: time, action, who, reason. A small line "Log is append-only" under the title.
- **Benchmark:** grouped bars by log loss (PUGMARK versus the best baseline), a table below, and a visible note "Simulated incidents. At loss above 0, half the scenarios deliberately drop the key event." Colours from the design tokens, labels on bars, no legend hunting.

---

## 6. What changes from today

| Today | New |
|---|---|
| Eight controls and a time zone control in the header | Tabs and two chips in the header; controls inside the Scenario drawer |
| Three equal panels | One answer banner as the hero, graph second, detail third |
| "Highlight Top 1 / 2 / 3" buttons | Hypothesis tabs above the graph, synced with the right rail |
| A paragraph per hypothesis | Three bullets plus Details |
| Ids everywhere (`art:E1`, `act:ravi-menon`, `hyp:1`) | Names; ids only in Details |
| Cards inside cards in the Telegram view | One surface |
| Graph cut off, labels overlap | Fitted preset layout, pill labels |
| Page wider than the screen | Fits 1280 to 1920 wide |
| Neon teal borders, monospace everywhere | See `DESIGN_SYSTEM.md` |

---

## 7. Responsive

- 1280 to 1599: narrower rails (above). The graph keeps at least 600px of width.
- Below 1280: the right rail moves under the graph and the page scrolls. Not a priority; do not spend time here.
