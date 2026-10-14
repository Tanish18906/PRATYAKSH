# Design system

Status: the visual language for the redesign. One theme only (light "paper"). Everything is offline: system fonts, inline SVG icons, no CDN.

## 1. Direction

PUGMARK is a forensic evidence board, not a cyber-security cockpit. Calm paper background, ink text, one accent colour, and four meaning colours that always mean the same thing. The graph is the only place that gets visual drama; everything else is quiet.

Why light: it reads on a projector, it photographs well for slides, and it avoids the neon dark dashboard look that every AI-generated security tool has.

Remove from the current UI: neon teal glow and outlines, monospace for everything, all-caps tracked micro-labels, cards nested in cards, equal visual weight for every panel.

## 2. Tokens (paste into the global CSS, then map into Tailwind)

```css
:root {
  /* surfaces */
  --bg: #F5F3EE;          /* paper */
  --surface: #FFFFFF;
  --surface-2: #FAF9F6;   /* tinted rows, zebra */
  --line: #E4E0D6;        /* card borders, dividers */
  --line-strong: #C9C4B6; /* inputs, secondary button borders */

  /* text */
  --ink: #1C2030;
  --ink-2: #4A5064;
  --ink-3: #5F6578;

  /* brand and meaning */
  --accent: #3D4FD9;      /* primary actions, selection, focus */
  --accent-tint: #ECEEFC;
  --observed: #2E5E9E;    /* logged steps */
  --inferred: #C77700;    /* inferred steps (lines, fills) */
  --inferred-text: #8A5200;
  --inferred-tint: #FFF3DD;
  --leak: #C8321F;        /* leak location, danger */
  --leak-tint: #FDECE9;
  --ok: #1F7A4D;         /* fingerprint match, canary confirmed */
  --ok-tint: #E6F4EC;

  /* shape */
  --radius: 12px;
  --radius-sm: 8px;
  --shadow-pop: 0 8px 24px rgba(28, 32, 48, 0.12);   /* popover, dialog, drawer only */
}
```

Tailwind mapping (extend, do not replace): `colors: { bg: 'var(--bg)', surface: 'var(--surface)', line: 'var(--line)', ink: 'var(--ink)', 'ink-2': 'var(--ink-2)', 'ink-3': 'var(--ink-3)', accent: 'var(--accent)', observed: 'var(--observed)', inferred: 'var(--inferred)', leak: 'var(--leak)', ok: 'var(--ok)' }`.

Meaning is fixed. Never use a meaning colour for decoration.

| Colour | Always means |
|---|---|
| Indigo | an action or the current selection |
| Blue | a step that appears in the logs (observed) |
| Amber | a step we inferred; also the "Simulated data" chip |
| Red | where the data leaked to; danger |
| Green | fingerprint match, confirmed, the winning source |

Checked contrast: ink 16.2 on white, ink-2 8.0, ink-3 5.8 (5.2 on paper), accent 6.3, observed 6.5, inferred-text 6.4, leak 5.3 (4.8 on paper), ok 5.3 (4.8 on paper). The amber line is 3.5 on white, enough for graphics. Use `--inferred-text` for any amber text, never `--inferred`.

## 3. Typography

System fonts only, so the app works offline and looks native:

```css
font-family: ui-sans-serif, system-ui, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
--mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
```

| Role | Size / weight / line height |
|---|---|
| Answer banner sentence | 20 / 600 / 28 |
| Section title | 14 / 600 / 20 |
| Body | 14 / 400 / 20 |
| Secondary, labels | 13 / 400 / 18, ink-3 |
| Timestamps, chips, legend | 12 / 500 / 16 |
| Big numbers (likelihood, records) | 24 / 600, `font-variant-numeric: tabular-nums` |

Monospace is for ids, hashes and file names inside Details only. Letter spacing 0 everywhere. No all-caps except the two status chips.

## 4. Spacing, shape, elevation

- 4px base unit. Use 8, 12, 16, 24, 32. Card padding 16. Gap between cards 16.
- Radius 12 for cards, 8 for buttons and inputs, 999 for chips.
- Cards have a border and no shadow. Shadow is only for things that float: popover, dialog, drawer.
- Two levels of containment at most: page, then card. Use dividers inside cards.

## 5. Components in one line each

- Primary button: indigo, white text, 40px. Secondary: white, `--line-strong` border. Text button: indigo text.
- Chip: tint background, matching text, 24px high.
- Input: white, `--line-strong` border, 40px high, 2px indigo focus ring with 2px offset.
- Selected row: `--accent-tint` background and a 3px indigo left border.
- Status dot: 8px circle in a meaning colour next to a label.

## 6. Motion

- Easing `cubic-bezier(0.2, 0, 0, 1)`; durations 150ms (hover), 250ms (panels), 600 to 2400ms for the trace reveal (see below).
- Trace reveal order: stage dots, fingerprint bars fill (400ms), banner text fades in, graph edges draw in time order (120ms each), the dashed edge pulses once.
- Animate opacity and transform only. Total reveal under 3 seconds.
- `prefers-reduced-motion`: no reveal, no shimmer, state changes are instant.

## 7. Icons

Inline SVG, 16 or 20px, 1.5px stroke, `currentColor`. A small local `Icon` component with: document, server, laptop, send (paper plane), shield, alert, check, x, chevron, download, fit. No icon library, no emoji, no CDN.

## 8. Do and don't

| Do | Don't |
|---|---|
| One hero (the answer banner) per screen | Give every panel the same weight |
| Names and plain sentences | Show ids, hashes or rule codes in primary views |
| Solid versus dashed plus a label | Rely on colour alone |
| Whole percentages with "relative likelihood" | Show 87.9% or call it confidence |
| Quiet borders, generous space | Glows, gradients, neon, drop shadows on cards |
| Empty states with one sentence | Blank panels or raw JSON |
| Keep the page inside the viewport | Horizontal scroll |
