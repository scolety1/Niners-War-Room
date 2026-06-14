# Rookie Production Readiness Gap Audit - 2026-06-13

## Verdict

GREEN for proceeding to Stage B production-candidate contract design.

Production/app promotion is not approved. The current rookie v0.3 artifacts are strong enough to define a production-candidate ordering contract and export design, but they are not ready to replace active production rankings, private scores, formulas, app tables, probabilities, bands, outcome columns, or veteran outcome heads.

## Current Review/Shadow State

Current export state:

- Review board rows: `211`.
- Shadow rows: `211`.
- `1.03` rows: `0`.
- `1.04` premium rows: `10`.
- Round 2 rows: `9`, all currently at `2.08` and all RBs.
- `5.04` watchlist rows: `119`.
- Shadow rows missing `promotion_status=shadow_only`: `0`.
- Shadow rows missing `production_allowed=no`: `0`.

Source confidence remains uneven:

- Full review/shadow set: `2` high, `16` medium, `193` low.
- Premium group: `1` high, `8` medium, `1` low.
- Round 2 group: `1` high, `4` medium, `4` low.
- `5.04` watchlist: `4` medium, `115` low.

The current state is review/shadow-complete, not production-promoted.

## What Is Ready For Production Candidate Use

The following pieces are ready to inform a production-candidate design:

- Stable player identity fields: `player_id`, `player_name`, `position`, and `school`.
- Review context fields: `current_pick_zone`, `v03_candidate_pick_zone`, `review_bucket`, `review_status`, and `tag_summary`.
- Source-safety fields: `source_confidence`, `prohibited_sources_detected`, `source_conflict_status`, and source-status-derived warnings.
- Risk fields: `hard_caps`, `soft_flags`, `manual_review_flags`, `remaining_true_gaps`, and gap/manual-flag counts where present.
- Required shadow markers: `promotion_status=shadow_only` and `production_allowed=no`.
- Human-review docs for `1.03`, `1.04`, `2.04`, `2.08`, and `5.04`.

These fields can support a production-candidate order only if the output is clearly labeled as a candidate artifact and preserves warnings beside the order.

## What Is Not Ready

The following are not ready:

- Active production ranking replacement.
- App or Streamlit display wiring.
- Rookie probabilities.
- Rookie probability bands.
- Veteran outcome-head usage.
- Private-score changes.
- Formula changes.
- Any outcome-column file.
- Any output that hides manual-review flags, source warnings, or remaining gaps.

The current evidence cannot safely become an automatic rookie draft recommendation board.

## Premium Pick Blockers

Premium blockers remain:

- `1.03` has no opened player.
- The `1.04` group has 10 manual-review candidates, not a final rank.
- Premium WRs still need route, separation, press, target-rate, YAC, contested, red-zone, and source-safety review.
- Premium RBs still need pass protection, short-yardage, first-down, fumble, receiving, goal-line, contact-survival, and injury review.
- Jordyn Tyson has explicit premium injury review blockers.
- Prohibited terms such as ADP, ranking, and projection remain quarantined warnings only.

These blockers prevent production promotion but do not prevent Stage B from designing a contract that preserves them.

## 1.03 Status

A production rookie candidate artifact may leave `1.03` empty.

Safe representation:

- Do not invent a player row for `1.03`.
- Use an explicit slot status such as `no_player_cleared`, `hold`, or `trade_down_review`.
- Preserve the explanation that `1.03` remains closed because no player clears the source-safe premium bar.
- Do not backfill `1.03` from `1.04` ordering.

This is safer than forcing a soft-evidence player into a premium slot.

## 1.04 Status

The `1.04` candidates can be included in a production-candidate order only if the output preserves manual-review warnings and does not become an automatic production recommendation.

Required conditions:

- Every row keeps injury/source/role/manual flags visible.
- Every row keeps remaining gaps visible.
- Every row keeps prohibited-source caveats visible.
- The output names the order as candidate/review order, not final value, probability, or outcome.
- The order cannot override `1.03` being empty.

No `1.04` player is currently cleared for blind production promotion.

## Round 2 Readiness

Round 2 can support production-candidate contract design with caution.

Current state:

- `9` rows.
- All are RBs.
- All currently carry `current_pick_zone=2.08`.
- No Round 2 WR, TE, or QB rows exist.

Readiness strengths:

- RB role tags and survival gaps are visible.
- Source confidence is visible.
- Low-confidence and needs-data rows remain distinguishable.

Readiness blockers:

- `2.04` is not separately populated.
- Several rows rely on inherited tags or low source confidence.
- RB survival fields remain missing for many candidates.

## 5.04 Readiness

The `5.04` watchlist can support candidate design only as an asymmetric dart / watchlist layer.

Readiness strengths:

- `119` watchlist rows are separated from premium and Round 2 rows.
- `tag_summary` is present.
- Capped/manual groups remain separated in the full shadow export.

Readiness blockers:

- `115` of `119` watchlist rows are low source confidence.
- Many rows are source-limited parking-lot names.
- TE remains discounted unless a true receiving exception is source-safe.
- No QB exception should be created from current watchlist artifacts.

## Source-Safety Blockers

The following block production movement:

- `excluded` evidence used as a positive signal.
- ADP, public ranking, consensus, projection, fantasy forecast, trade calculator, market value, draft-kit rank, league rank, prior draft history, RotoWire ranking/projection, or legacy `private_score` used as private value.
- `conflict_review` affecting identity, role, injury, or premium evidence.
- Missing provenance for evidence that changes order.
- Any source warning hidden from the candidate output.

Source-safety statuses that can influence production order:

- `use_now`: may influence candidate order if provenance is preserved.
- `use_as_soft_flag`: may influence only as bounded review context or risk/tiebreaker if Stage B explicitly defines how; it cannot open zones, override caps, or become hard private value.

Statuses that can only display warnings or block movement:

- `manual_review_only`: display warning; do not create positive private value.
- `unavailable`: display remaining gap; do not infer.
- `excluded`: display or quarantine; never positive value.
- `conflict_review`: display and block affected movement until resolved.

## Missing-Data Blockers

Missing-data blockers include:

- Premium WR target earning fields: career YPRR, TPRR, first downs per target, red-zone share, press/separation, YAC, and contested context.
- Premium RB survival fields: pass protection, short-yardage, first-down rates, fumbles, receiving role, goal-line share, contact survival, and injury.
- Round 2 RB survival fields where inherited tags lack support.
- TE exception fields: route participation, receiving-vs-blocking usage, target command, and injury.

Unavailable fields must not be inferred.

## Injury Blockers

Jordyn Tyson is the clearest injury blocker. Games missed, return status, recurrence, and single-event versus recurring/chronic classification must be reviewed before any premium movement.

Other injury blockers:

- Kaelon Black injury history.
- Round 2 RB injury context where pass protection or workload profile is already fragile.
- TE exception injury context if route/target evidence is thin.

Injury notes remain manual-review context unless a future approved policy defines hard injury handling.

## Implementation Blockers

Implementation blockers before production promotion:

- No production-candidate export contract exists yet.
- No production-candidate export script exists yet.
- No tests exist for production-candidate ordering rules.
- No rollback plan exists yet.
- No final approval checkpoint exists yet.
- No HQ approval exists for active production/app promotion.

The current scripts correctly write only local review/shadow exports and do not read or write production ranking files, app files, outcome-column files, veteran outcome heads, `data/`, or app-readable rookie probability/band artifacts.

## Exact Gates Required Before Production Promotion

Before any production promotion, all gates below must pass:

1. Stage B defines a production-candidate contract and export design that preserves source statuses, warnings, gaps, and no-promotion markers.
2. Stage C audits the candidate design against source safety, row counts, premium blockers, and stop conditions.
3. Stage D creates a production-promotion proposal and rollback plan without modifying production rankings or app files.
4. Stage E creates a final approval checkpoint summary.
5. HQ explicitly approves a later implementation task.
6. A separate future implementation gate defines exact files, tests, artifact paths, app behavior, rollback procedure, and signoff.

Until those gates pass, production/app promotion remains blocked.

## Production Output Naming

The production-candidate output should avoid probability, outcome, and final-value language.

Recommended name:

- `rookie_production_candidate_order_v03`

Avoid names such as:

- `rookie_probability`
- `rookie_band`
- `rookie_outcome`
- `private_score`
- `final_rookie_rank`
- `production_projection`

## Recommendation For Stage B

Proceed to Stage B.

Stage B should define a production-candidate ranking contract and export design that remains non-app, non-probability, non-band, and non-veteran-outcome. It should allow `1.03` to remain empty, preserve `1.04` manual-review warnings, and explicitly state which source statuses can affect order versus display warnings only.

Stage B must not change active production rankings.
