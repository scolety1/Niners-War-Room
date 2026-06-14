# Rookie Production Implementation Readiness Proposal - 2026-06-13

## 1. Executive Verdict

Implementation is not approved now.

What is approved now is production-candidate planning only. The current rookie lane may describe how a future implementation could be made safe, but it must not implement production promotion, change production rankings, change private scores, create probabilities, create bands, wire app or Streamlit display, touch Outcome Columns HQ files, or use veteran outcome heads.

The `rankable_with_warning` patch changed the planning picture by separating orderable-but-warning-visible candidates from clean `ready` candidates. It made the candidate export more useful for review, but it did not approve production implementation. There are still `0` clean ready rows.

## 2. Current Status Interpretation

Current production-candidate status counts:

- `ready = 0`
- `rankable_with_warning = 42`
- `manual_review_required = 7`
- `blocked = 43`
- `unavailable = 119`

Interpretation:

- `ready = 0`: no player is clean enough to appear as warning-free production-ready. This is correct and should remain strict.
- `rankable_with_warning = 42`: these players can be ordered in the candidate export only when warnings, manual context, source caveats, and remaining gaps stay visible.
- `manual_review_required = 7`: these players need a human decision before production ranking movement, including premium injury/manual-review cases and TE/RB exception questions.
- `blocked = 43`: these players have hard caps, source conflicts, capped review status, or other stop conditions that block production movement.
- `unavailable = 119`: these players lack enough source-safe evidence, need roster-declaration context, or have insufficient data for production movement.

The status mix is useful for planning. It is not sufficient for implementation because the lane still has no clean ready rows and many warning/manual/blocker rows.

## 3. What A Future Production Implementation May Do

Only if explicitly approved later, a future production implementation may:

- Display a rookie production-candidate order derived from the approved candidate export.
- Display warnings beside each candidate row.
- Display manual-review context beside each candidate row.
- Display blocked and unavailable status clearly.
- Keep `1.03` as `trade_down_review`, `hold`, `manual_review_required`, or `no_player_cleared` if no source-safe player is supported.
- Keep `rankable_with_warning` visibly separate from clean `ready`.
- Preserve `production_candidate_only`, `app_read_allowed`, and `probabilities_created` semantics until an explicit later approval changes them.

Any future implementation must remain rookie-only and must be governed by a separate HQ-approved implementation prompt that names exact files, behavior, tests, rollback, and signoff.

## 4. What Future Production Implementation Must Not Do

A future production implementation must not:

- Create rookie probabilities.
- Create probability bands.
- Use veteran outcome heads.
- Overwrite or replace private scores.
- Use market, rank, projection, consensus, ADP, trade, draft-kit, or public best-player-list material as private value.
- Hide warnings to make a row look clean.
- Force `1.03` open.
- Treat `rankable_with_warning` rows as clean `ready`.
- Convert scouting prose into numeric grades.
- Convert secondary charting into hard private value.
- Infer unavailable fields.
- Promote app-readable artifacts without explicit HQ approval.

## 5. Implementation Blockers Remaining

Football/source blockers:

- Premium WR route, separation, press, YAC, target-earning, and role evidence remains incomplete.
- RB pass-protection, contact balance, fumble, first-down, goal-line, receiving, and injury gaps remain visible.
- TE and QB exception cases remain narrow and manual, not broadly cleared.

Premium-pick blockers:

- `1.03` remains unsupported and must not be forced open.
- Jordyn Tyson still requires injury review before premium production movement.
- Kaelon Black still requires short-yardage and injury-history review.
- `1.04` candidates are warning-rankable at best, not clean ready.

Source-safety blockers:

- Quarantined rank/projection/market terms must remain warnings or excluded context only.
- Manual-review-only evidence cannot become positive private value.
- Soft secondary charting cannot open premium zones by itself.
- Source conflicts must continue to block affected movement until resolved.

Missing-data blockers:

- Many `5.04` candidates remain unavailable because of low source confidence or missing role-path evidence.
- Roster Declaration Day context may still be needed before late watchlist rows can move.
- Some profiles require PFF/SIS/manual film confirmation before production movement.

App/UI blockers:

- No app display contract exists.
- No visible warning UX has been approved.
- No feature flag has been approved.
- No production-facing representation of `1.03` has been approved.
- No rollback switch has been implemented or approved.

Testing blockers:

- Future implementation needs tests proving warning visibility, manual-review visibility, blocked/unavailable display, and no app-readable probability/band output.
- Future implementation needs import/dependency checks proving no Streamlit, outcome, veteran head, private-score, or production-ranking dependency leakage.
- Future implementation needs row-count and marker assertions for all candidate splits.

## 6. Minimum Approval Gate For Implementation

Before any production integration is coded, all of the following must be true:

- Tim/HQ explicitly approves a separate production implementation prompt.
- The prompt names exact files that may be touched.
- The prompt defines an app display contract or states that no app display is allowed.
- The prompt defines how `ready`, `rankable_with_warning`, `manual_review_required`, `blocked`, and `unavailable` will be shown.
- The prompt defines how `1.03` is represented without forcing a player.
- A rollback plan is written before edits begin.
- Tests are specified before edits begin.
- No contamination blockers remain from ADP, rankings, projections, consensus, market, trade, draft-kit ranks, public best-player lists, or legacy `private_score`.
- Warning UX is visible and cannot be suppressed by default.
- No rookie probabilities or bands are introduced.
- No veteran outcome heads are used.
- `data/` and `local_exports/` remain uncommitted.

If any one of these conditions is missing, implementation must stop.

## 7. Recommended Future Implementation Shape

If HQ later approves implementation, the safest shape is:

- Read the approved production-candidate export through a rookie-only adapter.
- Show rookie production-candidate order separately from existing rankings.
- Label the view as candidate/review output, not final rookie rankings.
- Display `production_ready_status`, `promotion_blockers`, `manual_warnings`, `source_confidence`, `source_safety_notes`, and remaining gaps prominently.
- Keep `rankable_with_warning` separate from clean `ready`.
- Show blocked and unavailable rows as non-actionable.
- Keep `1.03` empty or represented as trade-down/manual-review if unsupported.
- Feature-gate the view off by default if app-facing work is later approved.
- Make rollback a single config/feature disable plus removal or quarantine of generated artifacts.
- Do not replace existing private scores.
- Do not write probabilities, bands, outcome columns, veteran-head inputs, or production ranking replacements.

This shape is still a proposal. It is not an instruction to implement.

## 8. Stop Recommendation

Pause rookie lane now unless Tim explicitly approves a separate production implementation prompt.

The current lane has reached a useful planning checkpoint:

- candidate status semantics are clearer;
- `rankable_with_warning` is audited GREEN;
- warning rows are orderable only with visible warnings;
- clean ready rows remain `0`;
- implementation remains blocked.

The next action should be either explicit HQ approval for a tightly scoped implementation prompt or no further production movement until the remaining manual/source blockers are resolved.
