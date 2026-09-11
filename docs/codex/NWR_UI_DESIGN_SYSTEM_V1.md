# NWR UI Design System V1

Written by the `ui/nwr-visual-redesign-v1-20260910` pass (directive
Phase 2). This documents the compact visual language the League Shell,
Home, and Universal Player Drawer redesigns (Phases 3-5) were built on.
Presentation-layer only -- extends, never redefines, the existing token
set in `desktop/packages/ui/src/styles.css` (`--gold`/`--violet`/
`--crimson`/`--cyan`/`--green`/`--muted`/`--line`/...). New tokens and
components live in `desktop/apps/redraft/src/redraft.css` under the
"NWR UI FOUNDATION V1" section, scoped to Redraft only -- Dynasty's own
rendering is untouched by this pass.

## Direction

A serious decision system, not a sportsbook/fantasy-gambling site,
generic SaaS admin, ESPN clone, or neon gamer dashboard. Dark-first
(inherited from the existing app -- already highly legible), restrained
49ers-adjacent gold/crimson accents used sparingly (also inherited, not
expanded). Color communicates status/urgency/recommendation/selection,
never decorative variety.

## Semantic state tokens

Each maps onto an already-existing base color -- no new palette was
invented:

| Token | Maps to | Meaning |
|---|---|---|
| `--nwr-recommended` / `-dim` | `--green` | This is the right call |
| `--nwr-alternative` / `-dim` | `--violet-bright` | A real next-best option |
| `--nwr-warning` / `-dim` | `--gold-bright` | Needs a decision, close call |
| `--nwr-unavailable` / `-dim` | crimson family | Blocked / cannot compute |
| `--nwr-stale` | `#dfc17f` | Data is real but aging |
| `--nwr-healthy` | `--green` | Data/board/source is current |
| `--nwr-close-call` | `#c9908a` | Real margin, but a small one |
| `--nwr-rostered` | `--violet-bright` | Owned on a roster |
| `--nwr-available` | `--cyan` | Free agent / open |

These are the vocabulary `DecisionExplain` (below) and the new shell
components style against -- never a bespoke one-off color per surface.

## Typography scale

Utility classes (not `font:` shorthand tokens, so line-height/family
are never silently dropped at a call site):

| Class | Use |
|---|---|
| `.nwr-text-recommendation-headline` | A DO-THIS headline inside a decision card |
| `.nwr-text-section-heading` | A section label above a group of cards (e.g. "NWR Actions") |
| `.nwr-text-meta` | Freshness/provenance/secondary metadata |
| `.nwr-text-body` | Prose inside an explanation block |

Existing page-level typography (`page-header h1`, `panel__header h2`,
`data-table` cell sizes) is unchanged -- this pass did not touch the
established page-title/section-heading/table-value scale already in
`@nwr/ui/styles.css`.

## Spacing rhythm

| Token | Value | Use |
|---|---|---|
| `--nwr-space-gutter` | `clamp(20px, 2.5vw, 38px)` | Page gutter (matches the existing `.workspace__content` padding) |
| `--nwr-space-card` | `16px` | Standard card padding |
| `--nwr-space-card-dense` | `10px` | Dense table/list row padding |
| `--nwr-space-section` | `22px` | Vertical rhythm between page sections |

## Surfaces / components

| Component | Class(es) | Used by |
|---|---|---|
| League identity (shell top-left) | `.nwr-shell-identity*` | `shell-identity.tsx` (`ShellIdentity`) |
| Freshness indicator (header, click-for-detail) | `.nwr-freshness*` | `shell-identity.tsx` (`FreshnessIndicator`) |
| This-week strip | `.nwr-this-week*` | Home |
| NWR Actions grid | `.nwr-action-grid` | Home |
| Decision explanation card | `.nwr-explain*` | `decision-explain.tsx` (`DecisionExplain`) -- Phase 6 pattern |
| Settled/zero-actions state | `.nwr-home-settled` | Home |
| Player drawer lede/ownership tag | `.player-drawer__lede`, `.player-drawer__ownership` | Universal Player Drawer |

Existing surfaces (`.panel`, `.data-table`, `.metric-card`,
`.status-badge`, `.button--*`) are unchanged and reused directly --
`DecisionExplain` and the shell components sit alongside them, not as a
second competing card/table system.

## Semantic states (StatusBadge tones, unchanged vocabulary)

`safe` / `review` / `blocked` / `offline` already existed
(`@nwr/ui`'s `StatusBadge`) and is reused as-is throughout the new
components -- this pass did not invent a second tone vocabulary.
`DecisionExplain`'s own `confidence` prop (`HIGH`/`NOMINAL`/`LOW`/
`UNAVAILABLE`) maps onto those same tones (`safe`/`safe`/`review`/
`offline`) so a decision card's confidence badge reads consistently
with every other status badge in the app.

## Button hierarchy

Unchanged from the existing system (`.button--primary/secondary/ghost/
danger` in `@nwr/ui/styles.css`) -- this pass did not add a new button
tier. `DecisionExplain`'s "Open" action is a plain text link (matching
the existing `.nwr-actions-list a` pattern used elsewhere), not a new
button variant, since it is a low-emphasis secondary navigation action,
not a primary command.

## Progressive disclosure

One shared pattern, used by both the redesigned Player Drawer and
`DecisionExplain`: a native `<details>` element styled via
`.player-drawer__section` (drawer) or `.nwr-explain__advanced`
(decision cards) -- collapsed by default, `▸`/`▾` marker, no JS state
needed. Primary layer = owner decision info; advanced layer =
model/provenance detail (raw ids, status-category enums, source
timestamps) -- never model names, hashes, or internal service
terminology in the primary layer.

## What this pass did NOT change

- `@nwr/ui/styles.css`'s existing token set, `.panel`/`.data-table`/
  `.metric-card` components, or button styles -- only additive new
  classes were introduced.
- Dynasty's rendering -- `AppShell`'s two new props
  (`sidebarIdentity`, `statusExtra`) are optional and unused by
  `DynastyApp.tsx`.
- Draft Room's own dense, power-tool visual language (`draft-room-v2.tsx`
  / the `.draft-room-v2-*` classes) -- explicitly out of this pass's
  Phase 7 scope (Shell + Home + Player Drawer only). See the audit
  entry in the freeze handoff for why this is flagged as a later-pass
  target, not silently left inconsistent.
