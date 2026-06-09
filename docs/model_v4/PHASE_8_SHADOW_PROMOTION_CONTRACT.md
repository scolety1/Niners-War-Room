# Phase 8 Shadow App Promotion Contract

Created: 2026-05-16

This contract defines how Model v4 may appear in the app before it is allowed to
replace any active ranking, roster-decision, draft, trade, or readiness surface.
Phase 8 promotes visibility only. It does not promote trust.

## Source Decision

Phase 8 follows `PHASE_7D_APP_PROMOTION_READINESS_DECISION.md`.

Phase 7D verdict:

- v4 is ready for app-promotion planning
- v4 is not ready for active app promotion
- v4 must remain review-only
- active My Team, War Board, Rankings, Draft Board, League Targets, and Trade Lab
  must remain unchanged
- no roster, draft, final-money, or decision-ready gate may unlock from display
  work alone

## Promotion States

| State | Meaning | Allowed in Phase 8? | Gate impact |
| --- | --- | ---: | --- |
| `review_only_shadow` | V4 is visible beside active outputs for inspection only. | yes | none |
| `roster_decision_shadow` | V4 is joined to Niners roster context but cannot recommend final actions. | yes | none |
| `active_roster_decision_candidate` | V4 is considered for live roster decisions after shadow review. | no | requires later gate |
| `active_model` | V4 replaces active model outputs. | no | requires later gate |

Every Phase 8 surface must show review-only language and must avoid wording that
implies live recommendation status.

## Global Guardrails

| Guardrail | Requirement |
| --- | --- |
| Active War Board | Must continue reading the same active data source and sort logic as before Phase 8. |
| Active My Team | Must continue reading the same active data source and action labels as before Phase 8. |
| Active Rankings/Draft Board | Must not read v4 preview outputs unless explicitly inside a v4 shadow section. |
| Readiness gates | Must not change because v4 appears in the UI. |
| Formula config | Must not change in Phase 8. |
| Source limitations | Must remain visible on every v4 surface. |
| Receipts | Must be available before a v4 row can be interpreted. |
| Legacy labels | Must not be displayed as trusted v4 decisions. |

## Canonical V4 Review Data

Phase 8 shadow surfaces may read these review-only artifacts:

| Artifact | Use |
| --- | --- |
| `local_exports/model_v4/review_only_latest/v4_preview_outputs.csv` | V4 preview player values, ranks, confidence, warnings, and unavailable sections. |
| `local_exports/model_v4/review_only_latest/normalized_component_rows.csv` | Component normalized values and contribution rows. |
| `local_exports/model_v4/review_only_latest/receipt_rows.csv` | Receipt drilldown rows. |
| `local_exports/model_v4/review_only_latest/source_coverage_rows.csv` | Source status and missing evidence rows. |
| `local_exports/model_v4/review_only_latest/warning_rows.csv` | Warning rows for shadow UI summaries. |
| `docs/model_v4/PHASE_7C_SANITY_FIXTURE_RESULTS.csv` | Latest sanity fixture status until a Phase 8 rerun exists. |
| `docs/model_v4/PHASE_7C_NAMED_PLAYER_REVIEW.csv` | Latest named-player review until a Phase 8 rerun exists. |
| `docs/model_v4/PHASE_7C_MOVEMENT_AUDIT.csv` | Latest movement context until Phase 8 comparison output exists. |

No Phase 8 surface may write to active data-pack outputs, active rankings,
active My Team tables, active draft state, or readiness-gate state.

## Shadow Surfaces

### V4 Shadow War Board

Purpose:

Show the v4 Dynasty Asset Value board in the app so it can be inspected without
replacing the active War Board.

Data source:

- `v4_preview_outputs.csv`
- `receipt_rows.csv`
- `source_coverage_rows.csv`
- `warning_rows.csv`

Required columns:

- V4 overall rank
- V4 position rank
- player
- position
- NFL team
- lifecycle
- Dynasty Asset Value
- confidence label
- review warnings
- unavailable sections

Warnings shown:

- review-only shadow status
- missing evidence
- source-limited young player
- unavailable route metrics
- proxy-only snap/usage role
- estimated first-down projection
- weak or blocked confidence

Receipt requirements:

- selected-player compact receipt
- top positive component drivers
- top negative or caution component drivers
- missing/proxy evidence list
- full receipt rows behind Advanced

Forbidden changes:

- no replacement of active War Board rows
- no overwrite of active overall rank or position rank
- no use of v4 rank for active action queue
- no readiness-gate unlock

### V4 Shadow My Team

Purpose:

Show how v4 evaluates the Niners roster while preserving current My Team output.

Data source:

- `v4_preview_outputs.csv`
- official Niners roster/rank lock
- `receipt_rows.csv`
- `source_coverage_rows.csv`
- `warning_rows.csv`

Required columns:

- player
- position
- NFL team
- roster rank
- league rank
- Roster's League-Rank Top Five status
- V4 Dynasty Asset Value
- confidence label
- review warnings
- unavailable sections

Warnings shown:

- review-only shadow status
- rule context is separate from Dynasty Asset Value
- weak/blocked young-player evidence
- missing projection or missing production
- unavailable route metrics
- proxy-only snap evidence

Receipt requirements:

- compact player receipt for every Niners row
- separate rule-context section for league-rank top five
- separate football-value section for v4 components
- confidence explanation
- source limitations and unavailable sections

Forbidden changes:

- no replacement of active My Team sections
- no trusted Core/Bubble/Shop/Release labels from v4
- no forced-release recommendation swap
- no roster-ready gate unlock

### V4 Shadow Receipts

Purpose:

Make v4 values explainable before any promotion decision.

Data source:

- `receipt_rows.csv`
- `normalized_component_rows.csv`
- `source_coverage_rows.csv`

Required sections:

- production
- first-down scoring fit
- usage/opportunity
- snap/proxy role
- projection
- age/dropoff
- young-player prior
- confidence
- market context when available
- league-rank rule context when rostered

Required fields per section:

- raw fields used
- normalized score
- weight
- contribution
- source status
- warning
- unavailable reason

Warnings shown:

- route metrics unavailable
- snap share is only a proxy
- missing first-down projections
- estimated first-down projections are not direct
- local baseline projection is not independent forecast evidence
- incoming rookie or young player has insufficient sourced prior

Forbidden changes:

- no score calculation in the UI
- no hidden fallback values displayed as evidence
- no market or league-rank contribution to Dynasty Asset Value

### V4 Old-vs-New Comparison

Purpose:

Show how v4 differs from the current active model so promotion risk can be
reviewed row by row.

Data source:

- active app ranking outputs
- `v4_preview_outputs.csv`
- latest movement audit CSV

Required columns:

- active overall rank
- v4 shadow rank
- active value
- V4 Dynasty Asset Value
- active confidence
- v4 confidence
- active warning
- v4 warning
- movement direction
- movement size
- movement reason when available

Warnings shown:

- v4 values are review-only
- large unexplained movement needs review
- active model remains the live model

Receipt requirements:

- ability to inspect v4 receipt for movement rows
- movement reason or `unknown movement` flag
- source limitation summary

Forbidden changes:

- no active rank replacement
- no sorting active pages by v4 values
- no use of v4 movement to alter trade or roster recommendations

### V4 Promotion Blockers

Purpose:

Show what must be resolved before v4 can become an active roster-decision
candidate.

Data source:

- `PHASE_7D_APP_PROMOTION_READINESS_DECISION.md`
- sanity fixture results
- named-player review
- source coverage rows
- warning rows
- movement audit

Required blocker groups:

- data blocker
- formula blocker
- confidence blocker
- source limitation
- UI blocker
- accepted limitation

Known blockers and limitations:

| Blocker | Type | Blocks shadow display? | Blocks active promotion? | Next action |
| --- | --- | ---: | ---: | --- |
| Caleb Williams missing from current v4 QB-control preview | data blocker | no | yes for QB-control completeness | Add or document before active promotion. |
| Luther Burden source-limited/blocked | source limitation | no | yes for trusted young-player decision | Keep warning visible; source rookie/prospect evidence before trust. |
| Kaleb Johnson source-limited/blocked | source limitation | no | yes for trusted young-player decision | Keep warning visible; source rookie/prospect/NFL evidence before trust. |
| Keenan Allen weak confidence | confidence limitation | no | maybe | Keep weak-confidence label visible. |
| Route metrics unavailable | accepted source limitation | no | no if visible | Keep quarantined; do not fake route evidence. |
| V4 shadow app review not accepted | UI/process blocker | no | yes | Complete Phase 8 shadow review first. |

Receipt requirements:

- blocker rows should link or point to affected player receipt when applicable
- each blocker should include why it matters and exact next action

Forbidden changes:

- no clearing blockers without evidence
- no readiness-gate changes
- no decision-ready label changes

## Phase 8B-8F Implementation Tasks

### Phase 8B: V4 Shadow War Board

1. Add a review-only V4 Shadow War Board section or tab.
2. Load `v4_preview_outputs.csv`.
3. Show V4 ranks, player identity, lifecycle, Dynasty Asset Value, confidence,
   warnings, and unavailable sections.
4. Add filters for position, lifecycle, confidence label, warning text, and
   search.
5. Add row selection for compact v4 receipt preview if practical.
6. Add tests proving active War Board data is unchanged.
7. Browser-smoke the section.

### Phase 8C: V4 Shadow My Team

1. Add a review-only V4 Shadow My Team section or tab.
2. Join Niners roster/rank context to v4 preview rows.
3. Show roster rank, league rank, top-five rule status, V4 value, confidence,
   warnings, and unavailable sections.
4. Keep rule context separate from football value.
5. Hide or review-label legacy Core/Bubble/Shop/Release wording.
6. Add tests proving active My Team data is unchanged.
7. Browser-smoke the section.

### Phase 8D: V4 Shadow Receipts Drilldown

1. Add selected-player receipt drilldown for shadow rows.
2. Group receipts by v4 required sections.
3. Show raw fields, normalized score, weight, contribution, source status,
   warning, and unavailable reason.
4. Highlight missing/proxy/estimated evidence.
5. Keep raw rows behind Advanced.
6. Add tests proving receipt totals reconcile.
7. Browser-smoke receipt drilldown.

### Phase 8E: Old-vs-V4 Comparison

1. Add comparison section for active output versus v4 shadow output.
2. Show active rank/value/confidence beside v4 rank/value/confidence.
3. Classify movement direction, magnitude, and reason where available.
4. Flag large unexplained movement for review.
5. Add filters for Niners roster, top 50, position, large movement, and warning.
6. Add tests for comparison rows and movement labels.
7. Browser-smoke the section.

### Phase 8F: Promotion Blockers Panel

1. Add a V4 Promotion Blockers panel.
2. Group blockers by data, formula, confidence, source limitation, UI, and
   accepted limitation.
3. Include known blockers from Phase 7D.
4. Show why each blocker matters, affected players/surfaces, next action, and
   whether it blocks app promotion or only final readiness.
5. Add tests for blocker classification and labels.
6. Browser-smoke the panel.

## Phase 8 Acceptance Criteria

Phase 8 may be considered complete only when:

1. V4 is visible in app shadow surfaces.
2. Every v4 surface says it is review-only.
3. Active War Board and My Team remain unchanged.
4. No readiness gate has unlocked.
5. V4 receipts are inspectable for selected players.
6. Source limitations and confidence warnings remain visible.
7. Old-vs-v4 movement is reviewable.
8. Promotion blockers are explicit.
9. Full tests and static check pass.

## Phase 8 Non-Goals

Phase 8 must not:

- change Model v4 formula weights
- replace active rankings
- mark roster decisions ready
- mark draft ready
- mark final money decisions ready
- turn weak/blocked source-limited rows into trusted recommendations
- hide unavailable route metrics
- treat market or league rank as private football value

## Final Contract Decision

Proceed with Phase 8B-8F shadow integration.

Do not promote v4 into live decision surfaces yet. The app may show v4 only as a
review-only shadow model until Phase 8 surfaces are complete and a later
promotion decision explicitly allows the next state.
