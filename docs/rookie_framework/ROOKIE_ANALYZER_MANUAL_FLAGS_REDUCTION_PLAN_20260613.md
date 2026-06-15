# Rookie Analyzer Manual Flags Reduction Plan - 2026-06-13

## Executive Verdict

Verdict: GREEN.

Do not remove warnings blindly. The current analyzer warning load is correct for a review-only export. Stage 5 creates a reduction plan only; it does not change production rankings, private scores, formulas, app/Streamlit files, probabilities, bands, outcome columns, veteran outcome heads, or local export promotion status.

Current analyzer status counts:

- `ready`: `0`
- `rankable_with_warning`: `42`
- `manual_review_required`: `7`
- `blocked`: `43`
- `unavailable`: `119`

## True Blockers

These should block draft use until resolved:

- Active hard caps.
- Active source conflicts.
- `production_ready_status=blocked`.
- `production_ready_status=unavailable` when the row lacks source-safe evidence.
- Unresolved premium injury review.
- `1.03` player-forcing pressure when no player is source-cleared.
- TE/QB exception profiles without a clear role path.

Action: keep these visible. Do not downgrade them to display-only warnings without a later human-approved evidence update.

## Display-Only Warnings

These can remain visible without blocking analyzer display:

- `rankable_with_warning` status.
- Soft flags such as `SOURCE_LIMITED` when the row still has a clear role/path case.
- `RB_GOAL_LINE_SOFT_PROXY` when it is presented as a proxy, not a hard value.
- Quarantined source terms in `prohibited_sources_detected`, provided they stay warning-only and are not used as private value.
- `best_pick_fit`, `trade_down_signal`, and `emergency_stop_signal` when used as manual context only.

Action: keep these in the analyzer. They are the reason the analyzer is useful, but they must not be hidden or converted into clean readiness.

## Potential Safe-To-Ignore Candidates

Only after Tim confirms they do not affect the pick decision, these may become lower-priority display warnings:

- Duplicate soft-flag wording already represented in `manual_warnings`.
- Generic `SOURCE_LIMITED` labels on late 5.04 profiles that already have a clear role-path stash note.
- Repeated RB archetype tags when the same role is already captured by `tag_summary`.
- Repeated remaining-gap labels where a blocker row is already unavailable and non-actionable.

Action: do not remove yet. A later reduction patch may add a `warning_priority` or `warning_visibility` field, but it should not delete the original warning text.

## Needs Tim / Manual Review

These require direct human review before they can move down in severity:

- Jordyn Tyson injury and premium role review.
- Kaelon Black short-yardage and injury-history review.
- Jamal Haynes injury/manual role review.
- Jamarion Miller injury/manual role review.
- Chip Trayanum manual role review.
- Eli Stowers TE exception review.
- Sam Roush TE exception review.
- Premium WR route, separation, press, manufactured-touch, YAC, and target-earning concerns.
- RB pass protection, contact balance, fumble, receiving first-down, rushing first-down, and goal-line role concerns.

Action: keep `manual_review_required` until Tim answers the specific player question.

## Needs Roster Declaration Day

These should generally stay unresolved until roster context is available:

- Low-source 5.04 profiles without a clear role path.
- Late RB/WR stash candidates whose value depends on depth chart openings.
- TE/QB exceptions that require role clarity.
- Rows with `hold_until_roster_declaration` review status.

Action: do not promote these before Roster Declaration Day unless a later approved source-safe artifact changes the review status.

## Needs External Charting / Injury Confirmation

These require source-safe confirmation before warning reduction:

- PFF/SIS/manual-film gaps for route, separation, press, YAC, target rate, and first-down earning.
- RB pass protection, yards after contact, missed tackles forced, fumbles per touch, goal-line touch share, and receiving usage.
- QB designed-rush share, scramble rate, pressure-to-sack rate, and job-security exceptions.
- TE top-two target path and replaceability exceptions.
- Injury-history score, games missed, return status, and unresolved premium injury notes.

Action: keep external charting and injury gaps as warnings or blockers until confirmed by approved source-safe evidence.

## Reduction Sequence

Recommended order for a later reduction pass:

1. Resolve the seven `manual_review_required` rows with Tim.
2. Separate duplicate warning text from unique warning text.
3. Add a non-destructive warning priority field if needed.
4. Keep true blockers and source-safety blockers intact.
5. Rebuild analyzer exports and verify `ready` remains strict.

## What Not To Do

- Do not delete warnings to make rows look clean.
- Do not convert warnings into private scores.
- Do not use ADP, public rankings, projections, consensus, market, trade, draft-kit, or legacy `private_score` inputs.
- Do not create probabilities or bands.
- Do not wire app or Streamlit output.
- Do not use veteran outcome heads.
- Do not commit `data/`.
- Do not commit `local_exports/`.

## Safe Next Gate

Stage 6 may proceed to an analyzer explainer bundle if validation remains GREEN.
