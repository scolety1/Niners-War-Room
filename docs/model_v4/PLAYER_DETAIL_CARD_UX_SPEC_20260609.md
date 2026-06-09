# Player Detail Card UX Spec - 2026-06-09

## UX Goal

Give every major page a consistent way to inspect a player without turning the main table into an audit cockpit. The card should answer:

- Who is this player?
- Why is this row on this page?
- What private/source-safe model context exists?
- What source/trust risks should a human review?
- Which context is display-only or comparison-only?
- What receipts are available if the user wants to audit the row?

## Layout

### Header

Show:

- Player
- Position
- Team
- Age
- Roster/pool status badges
- Trust badge
- Source type badge

Missing fields show `-`, `Unknown`, or a page-specific pending label. Do not hide missing source state.

### Section 1: Why This Row Appears Here

This is page-specific and should be plain English.

Rankings examples:

- `Ranked by admitted private NWR Dynasty Score.`
- `No private score is available; shown for source repair review.`

Draft Prep examples:

- `Shown in the scouting prep pool for the selected pick window.`
- `Legal pool is pending dropped/released veteran data.`
- `Manual watchlist row; no exact baseline.`

Live Draft Room examples:

- `Available in the mock/scouting pool.`
- `Already marked drafted at <pick>.`
- `Hidden when Hide Drafted is enabled.`

Roster Decisions future examples:

- `Shown because roster pressure or forced-drop context requires review.`

If unavailable, show:

`Explanation not available from current source rows.`

### Section 2: NWR / Private Model Context

Show source-safe score/rank context only:

- Rankings: NWR Dynasty Score, NWR rank, confidence cap/status.
- Draft Prep: NWR Draft Value, Rookie Score, Dynasty Score as context if present.
- Live Draft Room: scouting/mock score display and draft-state context, with original source row available for receipts.
- Roster Decisions: relevant private model and replacement context when later wired.

Never mix public/market/league/prior-history/RotoWire projection/ranking/legacy fields into private value.

### Section 3: Page-Specific Context

Rankings:

- Market Rank display-only.
- League Rank display-only.
- NWR vs Market / NWR vs League if both NWR rank and comparison rank exist.
- Outcome status: `Outcome percentage model in development` until a real private model exists.

Draft Prep:

- Pick window.
- Fit band.
- Legal draft status.
- Prospect talent context.
- Landing spot.
- Draft capital.
- Role path.
- Prior user/history tags as display-only context.
- `2026 5.04`: `No Baseline`, `Manual Watchlist`, `No exact equivalence`.

Live Draft Room:

- Drafted status.
- Drafted pick.
- Current selected pick.
- Best remaining context.
- Legal pool pending status.
- Session/local mock state note.

Future Roster Decisions:

- Roster pressure context.
- Forced-drop rule context.
- Owner/team status.
- Replacement or cut-cost context.

### Section 4: Trust, Warnings, Data Needed

Show:

- Trust status.
- Warning count.
- Human-readable warning messages.
- Human-readable data-needed messages.

Rules:

- Translate raw warning flags before showing them in the main card body.
- Keep raw flags in receipts.
- Do not use `Needs Data` as a blanket trust label for valid scored rows.
- Severe identity/current-team/source conflicts must remain visible.

### Section 5: Source Receipts

Collapsed by default.

Include:

- Source path.
- Source column.
- Upstream source path/column if present.
- Model version.
- Lineage class.
- Allowed use.
- Blocked use.
- Raw warning flags.
- Raw source repair notes.

The label should be boring and clear, for example:

`Advanced source receipts`

### Section 6: Legacy / Display-Only Disclosures

Show only when relevant:

- Legacy active-pack scores are comparison-only.
- Market rank and league rank are display-only.
- Prior draft history and spreadsheet highlights are context-only.
- RotoWire is source/status/context only and cannot affect private score unless an existing admitted Model v4 component explicitly allows a source-safe field.
- Dropped-player status can confirm legal draftability later, but cannot alter private score.

### Section 7: User Notes / Tags

Future optional section.

Rules:

- User notes are manual context only.
- Notes cannot change private score, rank, fit band, or draft state.
- Notes should not create final recommendations.

## Interaction Pattern

Recommended first implementation:

- Shared Streamlit component rendered inside a collapsed or expanded expander, depending on page context.
- Rankings can keep one selected player detail expanded by default.
- Draft Prep can show detail for a selected scouting row or a row selected from a table/filter.
- Live Draft Room can show detail for selected available/drafted player near Best Remaining/Pick Controls.
- Roster Decisions can later use the same component with roster-pressure fields.

Do not implement a custom drawer until the table-selection pattern is stable.

## Tone Rules

Allowed language:

- Review
- Context
- In Range
- Likely Gone
- Value If Falls
- Possible Reach
- Expensive vs NWR
- Favorite At Cost
- Must Review At Cost
- Needs Scouting
- Source Limited
- Manual Watchlist
- No Baseline
- Scouting Only
- Legal Pool Pending
- Mark Drafted
- Undo
- Save Mock
- Load Mock

Forbidden final-action language:

- Draft this player
- Target
- Buy
- Sell
- Cut
- Defer
- Trade for
- Start/sit command language

## Design Verdict

Use a shared player card, but keep page-specific context in extension sections. Start with a reusable component and adapter helpers, then wire one page at a time.

