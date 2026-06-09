# Model v4 Phase 5A External Audit Triage

Generated: 2026-05-16

## Purpose

This document turns the external Model v4 Phase 4 audit into verified local issues. The audit is useful, but it is not treated as automatically correct. Each finding was checked against the current v4 review-only files, receipts, source coverage, and player context.

Primary triage table:

- `docs/model_v4/PHASE_5_EXTERNAL_AUDIT_TRIAGE.csv`

Reviewed local evidence:

- `local_exports/model_v4/review_only_latest/v4_preview_outputs.csv`
- `local_exports/model_v4/review_only_latest/v4_normalized_component_rows.csv`
- `local_exports/model_v4/review_only_latest/v4_receipt_rows.csv`
- `local_exports/model_v4/review_only_latest/v4_source_coverage_rows.csv`
- `local_exports/model_v4/review_only_latest/v4_warning_rows.csv`
- `local_exports/model_v4/review_only_latest/v4_preview_summary.json`
- `docs/model_v4/PHASE_4_WR_EVIDENCE_AUDIT.csv`
- `docs/model_v4/PHASE_4_CHECKPOINT.md`
- `docs/model_v4/FEATURE_SOURCE_CONTRACT.md`
- `docs/model_v4/FORMULA_LANE_ARCHITECTURE.md`
- `docs/model_v4/SANITY_FIXTURE_CONTRACT.csv`

## Executive Verdict

The external audit is directionally right about the main problem: Model v4 is not ready for trusted roster decisions yet. The dominant blockers are not UI polish. They are evidence coverage, missing-data semantics, and WR/RB normalization review.

The audit also contains several factual errors or overstatements. Those should not drive changes:

- Brock Bowers is not a player with no NFL context in the local 2026 model. Local v4 treats him as a `year_two_nfl_bridge` player with imported production, first-down, usage, snap, and young-prior rows.
- Brian Thomas Jr. and Malik Nabers are not treated locally as incoming rookies with no NFL data. They are `year_two_nfl_bridge` players with imported production/first-down/usage evidence.
- Public play-by-play cannot safely create true route participation, routes run, TPRR, or YPRR. The current route honesty policy is correct.

External spot-checks also contradict the audit's strongest young-player factual overstatement:

- NFL.com lists Brock Bowers with a 2024 Las Vegas stat line, including 17 games and 112 receptions: https://www.nfl.com/players/brock-bowers/stats/career
- NFL.com lists Malik Nabers with a 2024 New York Giants stat line, including 15 games and 109 receptions: https://www.nfl.com/players/malik-nabers/stats/
- The Jaguars' official player logs show Brian Thomas Jr. 2024 game production: https://www.jaguars.com/team/players-roster/brian-thomas-jr/logs/2024/reg/

The model must remain review-only.

## Confirmed Or Likely High-Impact Issues

### 1. Missing Evidence Is Currently Too Destructive

Several established veterans show very low Dynasty Asset Value because production, first-down, usage, snap, and projection sections are missing. Local examples include Saquon Barkley, Derrick Henry, Jonathan Taylor, Davante Adams, Tyreek Hill, and Travis Kelce.

This is not the same thing as being bad. It is an absence-of-evidence problem. Missing data should produce review/blocked confidence, not a fake near-zero player value that looks like a football conclusion.

Classification: `confirmed bug`

Next patch: Phase 5H, after source root-cause checks.

### 2. Production, First-Down, Usage, Snap, And Projection Coverage Need Root-Cause Audit

The source coverage rows show many missing component sections. Phase 5 must separate:

- true unavailable source gaps
- import/join bugs
- stale source problems
- player universe mismatch
- position-specific not-applicable fields

Classification: `data/source gap`

Next patch: Phase 5B.

### 3. WR Production And Usage Normalization Need Review

The local WR Evidence Audit already flags this without requiring a formula rewrite yet:

- 5 of 9 reviewed WRs have `production_normalization_review`
- 8 of 9 reviewed WRs have `usage_normalization_review`
- `true_formula_imbalance_review` is false in the current WR audit

That means the next step is to inspect production and usage scaling before touching formula weights.

Classification: `normalization issue`

Next patch: Phase 5G.

### 4. Chase Brown Needs A Source Trace

Local rows for Chase Brown are internally populated and consistent:

- position/team: RB, CIN
- lifecycle: `year_three_nfl_bridge`
- production status: `imported_real_data`
- first-down status: imported
- usage status: `derived_real_data`

However, because Chase Brown materially affects Niners top-five rule context and the audit flags him as suspicious, Phase 5 should verify the raw source season, identity, usage math, and receipt contribution.

Classification: `likely bug`

Next patch: Phase 5C.

### 5. Brock Bowers Claim Is A False Positive, But TE Suppression Still Needs Review

The external report's claim that Bowers never played an NFL snap is not valid for this local 2026 model context. Do not delete or suppress Bowers production based on that claim.

Separate issue: a no-TE-premium league should still sanity-check whether TE values are properly suppressed versus RB/WR assets.

Classification:

- External identity claim: `false positive`
- TE value concern: `formula concern`

Next patch: Phase 5C source trace, then fixture-backed formula review later if needed.

### 6. First-Down Projection Gap Remains Real

Receipts show:

- `missing_first_down_projection`
- `supplied_projection_points_ignored`

Historical first downs can be imported for past production, but projected first downs are not direct evidence. Any estimator must be clearly labeled and confidence-penalized.

Classification: `data/source gap`

Next patch: Phase 5F.

## Findings Already Handled Correctly

### Route Metrics Are Quarantined

Local warnings show:

- route metrics are not used
- snap share is proxy-only
- route participation is unavailable unless a licensed structured source is supplied

No fake route derivation should be added from play-by-play.

### Market And League Rank Are Separated

Current lane contracts keep:

- market out of private Dynasty Asset Value
- league rank out of Dynasty Asset Value
- top-five release logic as roster-rule context only

These should stay protected by tests.

### Young-Player Prior Is Visible And Not Currently Dominant

Young-prior contributions are visible in receipts and small enough that they are not blindly boosting missing-evidence players into trusted assets. Luther Burden remains weak/review rather than falsely promoted.

## Phase 5 Patch List

### Phase 5B: Missing Evidence Root-Cause Audit

Goal: Determine why many players have missing production, first-down, usage, snap, or projection evidence.

Work:

- Export missing evidence by player and component.
- Classify each missing section as import bug, true source gap, not applicable, stale source, or player universe mismatch.
- Identify high-impact roster players and sanity fixtures affected.

### Phase 5C: Suspect Player Source Trace

Goal: Trace identity and raw source rows for audit-sensitive players.

Players:

- Chase Brown
- Brock Bowers
- Brian Thomas Jr.
- Malik Nabers
- Luther Burden
- top missing-data veterans such as Saquon Barkley, Derrick Henry, Jonathan Taylor, Davante Adams, Tyreek Hill, Travis Kelce

Work:

- Trace identity keys.
- Trace source season/team/position.
- Trace production, first-down, usage, snap, projection, and young-prior rows.
- Confirm or reject suspected anomalies.

### Phase 5D: Production And First-Down Import Repair

Goal: Fix import/join issues for native production and historical first downs if Phase 5B/5C proves they exist.

Work:

- Repair source joins only where verified.
- Keep unavailable data visible.
- Do not use rejected manual production tables.

### Phase 5E: Usage And Snap Repair

Goal: Fix derived play-by-play usage and imported snap share if Phase 5B/5C proves bugs.

Work:

- Verify target share, carry share, weighted opportunities, red-zone, and goal-line math.
- Keep snap share labeled as proxy-only.
- Keep route metrics unavailable.

### Phase 5F: Projection And First-Down Projection Policy

Goal: Make projection evidence safe and explicit.

Work:

- Verify projection source status and team-match flags.
- Keep supplied non-LVE projection points ignored.
- Design first-down estimate policy or keep missing projected first downs penalized.

### Phase 5G: WR/RB/TE Normalization Audit

Goal: Determine whether surprising cross-position results are source-driven, normalization-driven, or formula-driven.

Work:

- Audit WR production normalization.
- Audit WR usage normalization.
- Audit RB opportunity normalization.
- Audit no-TE-premium suppression.
- Do not change weights unless fixtures and receipts prove a formula issue.

### Phase 5H: Missing-Data Scoring Semantics Patch

Goal: Prevent missing evidence from masquerading as a football downgrade.

Work:

- Missing core evidence should reduce confidence and mark review-needed.
- Missing evidence should not create near-zero trusted Dynasty Asset Value for established veterans.
- Add tests for veteran missing-data controls.

### Phase 5I: Regenerate V4 Preview And Movement Audit

Goal: Recompute v4 preview after data and normalization fixes.

Work:

- Regenerate preview outputs, receipts, coverage, and warnings.
- Compare movement versus Phase 4.
- Explain every large movement.

### Phase 5J: Phase 5 Checkpoint

Goal: Decide whether v4 is ready for another external audit or Phase 6 app promotion planning.

Work:

- Summarize fixed bugs.
- Summarize unresolved source gaps.
- Summarize formula concerns.
- Confirm readiness remains review-only unless gates independently pass.

## Formula Change Policy

No formula changes were made in Phase 5A.

Formula changes should wait until:

1. source coverage root causes are classified,
2. suspect player identity/source traces are complete,
3. WR/RB/TE normalization is audited,
4. fixtures identify a repeatable formula failure,
5. receipts explain the before/after effect.

## Status

Model v4 remains review-only. Active rankings and decision gates are unchanged.
