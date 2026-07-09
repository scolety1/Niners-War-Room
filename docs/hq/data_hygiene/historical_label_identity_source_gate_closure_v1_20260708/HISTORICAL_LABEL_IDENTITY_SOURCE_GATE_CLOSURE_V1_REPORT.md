# Historical Label / Identity / Source Gate Closure V1

## Verdict

`YELLOW_DATA_HYGIENE_CLEARS_COMPONENT_SIGNAL_TESTS_ONLY`

## Clear Answer

Data Hygiene clears Formula Gauntlet for future review-only component signal tests, but does not clear review-only position-scoped tournaments or full Formula Gauntlet because source/use gates remain review-only or blocked, exact Model v4 historical replay is still blocked, and sparse-history/low-games policies need a formal tournament contract before execution.

Maximum cleared level:

`CLEARED_FOR_REVIEW_ONLY_COMPONENT_SIGNAL_TESTS`

This is a Data Hygiene recommendation only. Master HQ must separately approve any execution lane.

## Historical Label Readiness

Historical labels are sufficient for review-only component signal tests:

- Outcome row-level label source admission verdict: `GREEN_OUTCOME_ROW_LEVEL_LABEL_SOURCE_ADMITTED_REVIEW_ONLY`.
- Compact label rows: `119,040`.
- Compact season coverage: `2012-2024`.
- Positions: QB, RB, WR, TE.
- Scoring mode: `exact_verified_first_downs`.
- Outcome V2 2000-2024 validation gate: `YELLOW_PARTIAL_REVIEW_ONLY_APPROVAL`.
- 2000-2024 season label rows: `13,652`.
- 2000-2024 anchor horizon rows: `13,652`.
- Field decisions: `35` approved review-only, `1` blocked weak calibration.
- Partial replay benchmark labels: `5,518` rows for 2013-2025 QB/RB/WR/TE component signal tests.

Labels remain evaluation targets. They are not production label truth, model inputs, training approval, source truth, app wiring, or ranking behavior.

## Identity Join Safety

The historical component-signal panel is identity-safe enough for review-only component tests:

- V2/V3 substrate rows: `5,518`.
- Matched feature-label rows: `5,518`.
- Unmatched feature rows: `0`.
- Unmatched label rows: `0`.
- Duplicate player-season keys: `0`.
- Position mismatch rows: `0`.
- Distinct GSIS/player IDs: `1,552`.
- Names are audit fields only; no name matching used.
- Historical receipt readiness matrix has `52 / 52` season-position rows with `identity_coverage=1.0` and `label_coverage=1.0`.

Broader identity is not universally cleared. NFLVerse current identity overlays remain review-only, some rows are still gated, and no name-only joins are approved.

## Source / Use Gate Matrix

Cleared only for review-only component signal testing:

- PYF / prior-year NWR points: safe as mandatory anchor comparator.
- Partial V3 lagged factual component receipts: review-only, partial replay only.
- Historical first-down/yards/opportunity-style component signals: review-only component signal testing only.

Not cleared:

- Production model use.
- Source-truth promotion.
- Full Formula Gauntlet.
- Exact Model v4 replay.
- Route/YPRR/TPRR.
- PFR advanced stats.
- Current ADP, market, injury, depth chart, current roster status.
- Current-board fields backfilled into history.

## Missingness Policy

Current missingness handling supports component signal tests only:

- V2/V3 reports say missing values were not forced to zero.
- Snap/offense null fences retained: `811` rows per snap field.
- Air-yard/YAC null fences retained: `663` rows per field.
- Rows with at least one optional source fence: `1,371`.
- Missing snap count is not zero snaps.
- Missing opportunity is not zero opportunity unless an explicit source zero exists.
- Missing roster status is not inactive/off-roster unless separately proven.

Formula Gauntlet still needs a formal missingness threshold contract before tournaments, especially for sparse-history rows (`1,453`, `26.3%`) and prior-production decline false positives (`572`, `10.4%`).

## Leakage / As-Of Safety

The existing partial component signal substrate is leakage-safe for review-only component tests:

- Feature season N to target season N+1 lag: pass.
- Target outcomes separated from features: pass.
- Current-only roster/status/injury/depth/schedule context excluded: pass.
- Market/vendor/projection/ADP/rank fields excluded as source truth: pass.
- Routes, route proxies, TPRR, YPRR, and ambiguous `rz_att` absent: pass.
- Partial replay reported leakage guardrail errors: `0`.

This does not clear future fields automatically. Every future Formula Gauntlet input family still needs its own decision-date/as-of proof.

## PYF Baseline Readiness

PYF is ready as the mandatory review-only anchor comparator:

- PYF/prior-year points baseline exists in the accepted partial replay benchmark.
- Coverage: `5,518` rows across QB/RB/WR/TE and 2013-2025 target seasons.
- Position rows: QB `754`, RB `1,429`, WR `2,124`, TE `1,211`.
- PYF beat the best non-PYF component signal in every position.

PYF is a comparator, not a production formula.

## Clearance Decision

Maximum cleared Formula Gauntlet level:

`CLEARED_FOR_REVIEW_ONLY_COMPONENT_SIGNAL_TESTS`

Not cleared:

- `CLEARED_FOR_REVIEW_ONLY_POSITION_SCOPED_TOURNAMENTS`
- `CLEARED_FOR_FULL_REVIEW_ONLY_FORMULA_GAUNTLET`
- Any production/model/source-truth use

## Remaining Blockers

1. Exact Model v4 historical replay chain is missing: `checkpoint_review_score`, `position_specific_review_score`, lifecycle/age/role/confidence receipts, and WR/QB v2 overlay receipts.
2. Route/YPRR/TPRR remain blocked pending a permitted route denominator source and source admission.
3. Source/use gates remain review-only for the existing component panel.
4. Sparse-history and low-games guardrails need formal threshold definitions before tournaments.
5. Broader current/source identity gates still contain review-only, gated, or blocked rows.
6. No future tournament contract has been approved by Master HQ.

## Recommendation To Master HQ

Recommend option 2:

`Allow review-only component signal tests`

Do not allow position-scoped tournaments or full Formula Gauntlet yet. The next lane should write a narrow Master HQ execution contract for component signal tests only, or continue exact receipt/source recovery first.
