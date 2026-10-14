# UX flow: from a Telegram post to a ranked route

Status: wins over `docs/UI_UX_DESIGN.md`, `docs/FRONTEND.md` and `docs/FEATURES.md` wherever they conflict. The contract, the API and the data do not change. This is a re-skin and a re-ordering of what is already built.

---

## 1. Who looks at this and what they need

The viewer is a judge or a security investigator. They have three minutes and no training. The question in their head is: where did this file come from, who moved it, and what do I do now?

The screen must answer in exactly this order, in plain words:
1. Source: which export the leaked file came from.
2. Route: who most likely moved it and through which systems.
3. Action: where to cut the chain, and what to collect next.

If the answer is not readable in five seconds without scrolling, the screen has failed.

---

## 2. The story in four stages (the UI mirrors the demo)

| Stage | What the user sees | Action |
|---|---|---|
| 1 Discover | A Telegram channel post with a CSV attached | Press **Export and trace** |
| 2 Match | The leaked file's fingerprint matched to company exports; one wins, decoys are excluded with a reason | none (animated) |
| 3 Trace | The route drawn on the graph; observed steps solid, inferred steps dashed | Click a hypothesis |
| 4 Act | Where to cut, what to collect next, the incident report | Open Report |

A slim stage indicator (four labelled dots) sits above the graph and shows how far the trace has progressed. It is a progress indicator, not navigation.

---

## 3. Information hierarchy

- **Level 1, always visible:** the answer banner (source, route, likelihood), the graph, the selected hypothesis in one sentence.
- **Level 2, one click:** the evidence list, the origin match table, the chokepoint card, the evidence-to-collect card, the report.
- **Level 3, behind a "Details" disclosure:** internal ids, hashes, config values, the raw audit log.

Rule: on first view, no column shows more than seven distinct pieces of information. Everything else is one click away.

---

## 4. Screens and states

Tabs: **Investigation** (default), **Origin match**, **Report**, **Audit**, **Benchmark**. Simulator controls live in a **Scenario** drawer, closed by default.

States of the Investigation screen:

| Region | Before trace | Tracing (under 3 s) | Done | API down |
|---|---|---|---|---|
| Answer banner | "Open the Telegram post and press Export and trace." | skeleton lines | source, route, likelihood | same as done, from the bundled demo |
| Graph | faint empty grid with a one-line hint | skeleton nodes, then edges draw in order | full route, fitted to view | same |
| Right rail | hint text | skeleton rows | hypotheses, evidence, actions | same |
| Header chips | Simulated data | same | same | Simulated data + Offline replay |

Errors are inline and calm: one line, one retry button. No stack traces, no raw JSON, no toast stacks.

---

## 5. Interactions

- **Export and trace:** the only primary button on the screen. It lives inside the Telegram post, because that is where the story starts.
- **Hypothesis selection:** click a tab above the graph, a row in the right rail, or a path on the graph. All three stay in sync. Arrow keys move between hypotheses.
- **Node click:** a small popover with time, rows moved, and whether the step is observed or inferred.
- **Reveal:** values are masked. A "Reveal" button opens a dialog that needs a reason of at least 8 characters, then writes an audit entry. Never reveal automatically.
- **Scenario drawer:** archetype, seed, log loss, canary mode, Generate, Inject leak, Run benchmark. Judges open it for the inject moment. It slides in from the right and closes with Esc.
- **Offline:** if the API is unreachable, switch silently to the bundled demo and show the "Offline replay" chip. No error spam.

---

## 6. Copy rules

- **No internal ids in primary views.** Never show `art:`, `act:`, `sys:`, `ep:`, `ch:`, `ds:` or `hyp:` strings. Show names: "Export E1", "Ravi Menon", "BI warehouse", "Ravi's laptop", "Telegram channel". Ids appear only inside Details, in monospace. A single `displayName(id)` helper does the mapping, with a fallback that strips the prefix and title-cases.
- Likelihood is a whole percent plus the words "relative likelihood". Never "confidence", "certainty", "calibrated" or "zero exposure".
- Every inferred step says why: "No log found for this step."
- Sentence case. No all-caps labels except the two status chips. No emoji, no exclamation marks.
- Dates read "9 Oct, 21:40 UTC". Company time is UTC.
- Persistent small footer line: "Simulated data. Rankings are relative likelihoods, not a finding of responsibility."
- The engine's narrative text contains ids such as `art:E1`. Until the engine text is changed, the UI runs `prettyIds(text)` over it before display.

---

## 7. Demo choreography (3 minutes)

| Time | User action | Screen does | Line to say |
|---|---|---|---|
| 0:00 | Open the app | Banner shows the empty-state hint; Telegram post visible | "A customer file just appeared on a Telegram channel." |
| 0:20 | Press Export and trace | Stage dots advance; fingerprint match bars fill | "We never read the data. We match its fingerprint." |
| 0:45 | Watch the banner | Banner fills: source Export E1, 100% of identifiers match; two decoys excluded with reasons | "Only one company export contains all of it." |
| 1:10 | Look at the graph | Route draws in time order; the last step is dashed | "The last step has no log. We infer it and say so." |
| 1:40 | Click hypothesis #2 | Graph and right rail switch together | "Here is the next most likely route." |
| 2:00 | Open the two action cards | Cut point and next evidence to collect | "Block this to cut most likely routes. Collect this log next." |
| 2:20 | Open Scenario drawer, inject another actor | A new trace runs live | "Pick anyone. It traces again in under a second." |
| 2:45 | Show Benchmark tab | Real numbers and the limits note | "Measured on 150 simulated incidents. Here is where it fails." |

---

## 8. Accessibility

- Text contrast at least 4.5:1, graphics at least 3:1 (the palette in `DESIGN_SYSTEM.md` is checked).
- Never colour alone: observed is solid, inferred is dashed and labelled.
- Visible focus ring on every interactive element; tabs, drawer and dialogs work from the keyboard; Esc closes the drawer and dialogs.
- The graph has a text alternative: a collapsible "Route as text" list under it.
- Respect `prefers-reduced-motion`: no animated reveal, instant state changes.
- Minimum body text 13px; touch and click targets at least 36px.
