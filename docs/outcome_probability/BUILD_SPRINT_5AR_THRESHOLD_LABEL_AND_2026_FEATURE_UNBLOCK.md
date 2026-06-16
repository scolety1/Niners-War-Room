# Build Sprint 5AR: Threshold Label and 2026 Feature Unblock

## Verdict

`BLOCKED_BY_2026_FEATURE_COVERAGE`

Sprint 5AR added direct threshold label/schema mechanics and a 2026 feature
coverage audit path, but Sprint 5AS threshold model training should not start
yet. The current clone does not contain the expanded 2020-2024 per-row ranked
historical exports needed to compute actual threshold support, and the current
2026 app/sample pool has zero legal prediction feature rows.

This sprint did not create app probabilities, fake probabilities, placeholder
probabilities, app-readable probability tables, rankings, sorting, app wiring,
promoted artifacts, push, or deploy.

## Local Outputs

Local-only outputs were written under:

`local_exports/outcome_probability/sprint_5ar_threshold_label_and_2026_feature_unblock/`

Created files:

- `direct_threshold_label_schema.csv`
- `direct_threshold_label_support.csv`
- `threshold_label_legality_audit.csv`
- `current_2026_feature_source_inventory.csv`
- `current_2026_prediction_feature_coverage.csv`
- `current_2026_prediction_feature_coverage_summary.csv`
- `rookie_feature_blockers.csv`
- `threshold_monotonicity_readiness_plan.csv`
- `blocked_threshold_probability_unblockers.csv`
- `metadata_sprint_5ar.json`
- `README_SPRINT_5AR.md`

## Code Added

Added `src/services/nwr_outcome_threshold_label_service.py`.

The service defines:

- Direct threshold target schema for QB, RB, WR, and TE.
- Position-specific direct threshold labels.
- Null/non-applicable handling for thresholds outside a player's position.
- Legality audit rows for direct threshold labels.
- Support aggregation helper for future historical ranked rows.
- Current 2026 prediction feature coverage classification.
- Rookie blocker rows.
- Monotonicity readiness plan rows.
- Remaining unblocker rows.

## Direct Threshold Label Feasibility

Direct threshold labels are feasible from existing legal scoring mechanics if the
full historical ranked season rows are present.

The existing scoring pipeline already supports:

- reconstructed NWR scoring from raw components;
- modeled positions QB/RB/WR/TE only;
- position-specific season total ranks;
- position-specific qualified PPG ranks;
- deterministic rank ordering by score, then player name/player id;
- competition ranking for ties;
- K exclusion;
- forbidden public/market/projection/ranking/trade/private-score input scans.

Sprint 5AR direct labels use:

- `season_total_rank_pos`
- `qualified_ppg_rank_pos`
- best available rank between those two fields
- position-specific thresholds only

They do not use ADP, public rankings, projections, market values, trade values,
prior fantasy draft history, RotoWire projections/rankings/outlooks/values,
legacy `private_score`, same-season final stats as prediction features, or label
supplement sources as prediction features.

## Direct Threshold Schema

Targets now defined:

| Position | Targets |
| --- | --- |
| QB | `same_year_qb_t6`, `same_year_qb_t12`, `same_year_qb_t18`, `same_year_qb_t24` |
| RB | `same_year_rb_t6`, `same_year_rb_t12`, `same_year_rb_t24`, `same_year_rb_t36`, `same_year_rb_t48` |
| WR | `same_year_wr_t6`, `same_year_wr_t12`, `same_year_wr_t24`, `same_year_wr_t36`, `same_year_wr_t48` |
| TE | `same_year_te_t3`, `same_year_te_t6`, `same_year_te_t12`, `same_year_te_t18`, `same_year_te_t24` |

Non-applicable thresholds are null/not applicable, not false. Example: a WR row
gets WR threshold booleans and QB/RB/TE threshold values of null.

## Threshold Support

Support export status:

`blocked_until_historical_threshold_support_built`

The local export `direct_threshold_label_support.csv` contains one row per
position/target schema entry, but eligible rows/events/non-events are intentionally
blank because this clone lacks the full 2020-2024 per-row ranked historical
exports needed to compute actual support without fabrication.

Required next step:

Run `direct_threshold_support_rows(...)` against restored or rebuilt 2020-2024
historical rows containing `season`, `position`, `season_total_rank_pos`, and
`qualified_ppg_rank_pos`.

## Label Legality Audit

The threshold label legality audit passes at the schema/code level:

- Rank source: position-specific reconstructed NWR scoring ranks.
- Source fields: `season_total_rank_pos` and `qualified_ppg_rank_pos`.
- Public fantasy totals: not label inputs.
- Non-applicable thresholds: null/not applicable, not false.
- Prediction-feature leakage: threshold labels are outcomes only, not features.

## 2026 Feature Coverage Findings

Measured current app/sample pool:

- Source: `sample_data/2026_pre_declaration`
- Rows: 24
- Position counts: QB 2, RB 5, TE 4, WR 13
- Veteran rows with legal features: 0
- Rookie rows blocked/separate: 0
- Rows missing identity/current-player linkage: 24
- Rows with missing required renamed prior-season features: 24
- K rows not applicable: 0

Every measured row is blocked. The current app/sample rows also include app
display/context fields that would be forbidden if misused as prediction features,
which confirms the app row shape is not a legal feature snapshot.

Why Sprint 5AQ found zero legal 2026 feature rows:

- The configured `local_exports` active data pack/current-player rows are absent
  in this clone.
- The sample app pool lacks legal prior completed-season feature facts.
- Current rows have missing Model v4 current-player identity linkage.
- No 2026 legal outcome feature snapshot generator output exists locally.
- The app row/service surface is not a feature snapshot surface.

## 2026 Feature Generator Plan

A future 2026 generator must emit local-only feature snapshot rows with the
renamed Sprint 5R schema:

- `age_at_snapshot`
- `position`
- `experience_at_snapshot`
- `prior_season_nwr_ppg`
- `prior_season_nwr_finish_rank`
- `prior_completed_season_games`
- `prior_completed_season_games_played`
- `prior_completed_season_games_active`
- `prior_completed_season_rushing_first_downs`
- `prior_completed_season_receiving_first_downs`
- `prior_completed_season_receptions`
- `prior_completed_season_rushing_yards`
- `prior_completed_season_receiving_yards`
- `prior_completed_season_passing_yards`

It must block old ambiguous names like `prior_nwr_ppg` and
`prior_games_played`. It must block app display fields and forbidden source
families such as ADP, market ranks, private scores, projections, public rankings,
trade values, and RotoWire outlook/value/projection/ranking sources.

## Rookie Handling Recommendation

Do not force veteran prior-season features onto rookies.

Rookies should remain blocked for the veteran threshold model and should get a
separate rookie model/head only after a legal rookie feature schema is defined.
Draft capital or rookie-specific inputs must be separately audited before use.

## Monotonicity Readiness Plan

No probabilities were computed in Sprint 5AR.

Future player-level threshold probabilities must pass position-specific
monotonicity before any release:

- QB: T6 <= T12 <= T18 <= T24
- RB: T6 <= T12 <= T24 <= T36 <= T48
- WR: T6 <= T12 <= T24 <= T36 <= T48
- TE: T3 <= T6 <= T12 <= T18 <= T24

Non-applicable thresholds are excluded from each chain.

If future internal predictions fail monotonicity, repair should be documented as
an internal-only post-processing audit, such as pooling adjacent threshold heads
or applying cumulative monotonic adjustment. No repair was applied in this
sprint.

## Remaining Blockers

1. Historical direct threshold support has not been computed from restored or
   rebuilt 2020-2024 per-row ranked rows.
2. Current 2026 legal feature coverage is zero.
3. Current app/sample rows are identity/current-player blocked.
4. Rookies require a separate model/head.
5. Player-level threshold probabilities do not exist, so monotonicity cannot be
   evaluated.
6. No calibration, release gate, display gate, or HQ approval exists for actual
   probabilities.

## 5AS Decision

Sprint 5AS threshold model training should not start yet.

Start 5AS only after:

1. Historical direct threshold support is rebuilt and sparse/one-class flags are
   known by position/target.
2. A legal 2026 veteran feature snapshot generator produces coverage greater
   than zero.
3. Rookies are explicitly blocked or routed to a separate legal rookie head.
4. The direct threshold labels are confirmed mature for 2020-2024.

## Confirmed Non-Actions

- No probabilities created.
- No fake or placeholder probabilities created.
- No calibrated probabilities created.
- No app wiring changed.
- No rankings or sorting changed.
- No app-readable probability tables created.
- No model artifact promoted or released.
- No push or deploy occurred.
