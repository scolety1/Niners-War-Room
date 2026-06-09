# NFLVerse Stats Upgrade Specification

This contract upgrades the Niners War Room toward a stats-first veteran model for
the LVE Dynasty League. It is intentionally local-first: network fetches may
create local CSV exports, but Streamlit pages and scoring services must consume
local files only.

## Goals

- Make nflverse-derived production, opportunity, role, first-down, age, and
  durability features the backbone of veteran private value.
- Keep market data out of `private_lve_value`.
- Use market/liquidity only for `trade_value` and at most a tiny capped keeper
  insulation layer.
- Prevent silent score mutation by separating raw imports, normalized features,
  model previews, and explicit apply steps.
- Preserve LVE-specific structure: 1QB, no PPR, 0.4 rushing/receiving first-down
  bonus, 3 WR, 2 RB, 1 TE, 2 flex, no TE premium, 23 keepers, and the forced
  league-rank top-five release rule.

## Template Group

Phase 1 adds header-only templates under:

```text
templates/real_data_inputs/nflverse_stats_upgrade/
```

These templates are source contracts, not generated model outputs. Copy them to
`local_exports/` before filling real rows.

| file | purpose |
|---|---|
| `nflverse_player_stats_weekly.csv` | Weekly passing, rushing, receiving, fumbles, and first-down stat components. |
| `nflverse_snap_counts_weekly.csv` | Weekly offensive snap and special-team snap context. |
| `nflverse_participation_player_weekly.csv` | Player-week participation aggregates and route/dropback proxies. |
| `nflverse_depth_chart_weekly.csv` | Depth chart rank and role intent. |
| `nflverse_injuries_weekly.csv` | Official injury and practice-report fields. |
| `nflverse_identity_map.csv` | Sleeper-to-nflverse identity bridge and review status. |
| `projection_raw_import.csv` | Legal exported projection stat lines before LVE rescoring. |
| `lve_opportunity_weekly.csv` | Expected opportunity and LVE-adjusted XFP features. |
| `lve_normalized_veteran_features.csv` | Final normalized `0-100` feature bridge into the stats-first veteran model. |

## Identity Rules

Identity matching must prefer deterministic IDs over names:

```text
1. sleeper_id
2. gsis_id
3. fantasy_data_id
4. espn_id
5. pfr_id
6. normalized name + position + team fallback
```

Ambiguous fallback matches are review items. They must not be normalized into
scored veteran features until fixed.

Phase 2 implements this as `src.services.nflverse_identity_service`. The service
validates `nflverse_identity_map.csv`, reports rostered players as `matched`,
`review`, `blocked`, or `unmatched`, and exposes only `review_status=ready`
matches to later nflverse import phases. A player without a ready identity bridge
must remain out of stats-derived model scoring.

## Raw Import Contracts

Phase 3 implements `src.services.nflverse_raw_import_service`. It validates the
raw nflverse CSV contracts for:

- player stats,
- snap counts,
- participation,
- depth charts,
- and injuries.

Validation checks required files, exact headers, required row values, numeric
fields, and unsupported positions. The readiness rows explicitly report
`scoring_effect=none; raw import contract only`. Raw files cannot change player
scores. They become useful only after later phases derive LVE scoring,
role/usage, injury, opportunity, and normalized veteran features.

## LVE Scoring Formula

Historical and projected stat lines must be rescored locally:

```text
lve_points =
  0.04 * passing_yards
+ 3.00 * passing_tds
- 2.00 * interceptions
+ 0.10 * rushing_yards
+ 4.00 * rushing_tds
+ 0.10 * receiving_yards
+ 4.00 * receiving_tds
+ 0.40 * rushing_first_downs
+ 0.40 * receiving_first_downs
- 2.00 * fumbles_lost
```

There is no reception point, no TE premium, and no passing first-down bonus.

Phase 4 implements `src.services.lve_scoring_derivation_service`. It derives
weekly LVE scoring from `nflverse_player_stats_weekly.csv` and can write
`lve_player_weekly_scoring.csv` as a generated local artifact. The output is
still review/derivation data only; it does not update veteran model outputs.

## Role And Usage Features

Phase 5 implements `src.services.lve_role_usage_service`. It derives role and
usage features from raw stats, snap counts, participation, and depth charts:

- games active,
- offensive snap share,
- starter-week rate,
- depth-chart role,
- route participation proxy,
- targets per dropback-snap proxy,
- RB workload earning,
- WR/TE target earning,
- role security,
- role fragility risk.

The route metric must remain labeled as a proxy because public nflverse
participation can support dropback/on-field participation, not guaranteed true
routes for every player. TE role security is capped when route role is weak,
because LVE has no TE premium.

## Injury Durability Features

Phase 6 implements `src.services.lve_injury_durability_service`. It derives
availability and durability features from injury reports plus weekly activity
signals:

- current injury status score,
- availability rate,
- questionable/doubtful/out history,
- limited and DNP practice history,
- same-area recurrence proxy,
- lower-body risk score,
- injury durability score,
- injury risk flags.

RB and WR lower-body injuries receive heavier penalties than QB lower-body
injuries. QB lower-body risk should mainly affect rushing-ceiling confidence,
not automatically destroy pocket-passing value. Missing injury rows are treated
as high durability but reduced confidence, because no public report is not the
same as a verified medical clearance.

## Projection Import Layer

Phase 7 implements `src.services.lve_projection_import_service`. Legal exported
projection stat lines in `projection_raw_import.csv` are rescored locally to LVE:

- no reception points,
- 3-point passing TDs,
- 4-point rushing/receiving TDs,
- 0.4 projected rushing/receiving first-down points,
- and no TE premium.

If projected rushing or receiving first downs are missing, the service estimates
them from position-level rates and adds a warning plus confidence penalty. This
keeps projections useful without pretending free projection sources usually
include first-down projections.

## Normalization Service

Phase 8 implements `src.services.lve_normalization_service`. It combines derived
weekly LVE scoring, role/usage, injury durability, and projection rows into
`lve_normalized_veteran_features.csv`.

The normalized rows are still preview-only. They are the bridge into later model
preview, not live recommendations. Missing source layers remain visible through
`missing_data_penalty`, `warnings`, and lower confidence.

## Normalized Feature Contract

`lve_normalized_veteran_features.csv` is the first file in this workflow that may
feed model preview. It should contain:

- `weighted_recent_lve_ppg_score`
- `expected_lve_points_score`
- `lve_projection_value`
- `role_security`
- `workload_earning`
- `target_earning_stability`
- `route_role`
- `first_down_td_fit`
- `age_curve`
- `injury_durability`
- `private_stat_value`
- `confidence`

All scored values must be `0-100`. Missing fields should be visible through
`missing_data_penalty`, `warnings`, and lower confidence, not hidden with fake
certainty.

## Market Cap Policy

Market data must follow these hard caps:

- `private_lve_value`: `0%` market weight.
- `keeper_score`: maximum `5%` market/trade-liquidity influence.
- `trade_value`: market/liquidity may dominate because it describes what other
  managers may pay, not private football value.
- League rank must not alter private value. It controls forced-release exposure
  and summer/declaration strategy only.

## Stats-First Formula Engine

NFLVerse Upgrade Phase 9 adds
`src.services.lve_stats_first_veteran_formula_service`. This engine consumes
`lve_normalized_veteran_features.csv` rows and produces isolated
`veteran_lve_stats_first_v1_0_0` scores. It is intentionally not wired into live
app recommendations until the preview/apply phases.

Formula boundaries:

- `private_lve_value` is built only from normalized football/stat features:
  recent LVE scoring, expected/opportunity value, projection value, role/security
  features, first-down/TD fit, age curve, and injury durability.
- `market_liquidity` has `0%` weight in `private_lve_value`.
- `keeper_score` can receive only a capped market nudge of `-2.5` to `+2.5`
  points, representing at most `5%` of the scale.
- `trade_value` may use market liquidity heavily because it models what other
  managers may pay, not private football value.
- QB and TE structural suppressions remain active unless the normalized football
  profile clears the elite exception gate.
- WR receives a small LVE lineup-demand bonus only when route/target indicators
  are strong enough to avoid rewarding empty depth.
- RB is split into `win_now_value` and `dynasty_hold_value`. One-season role,
  workload, and projection can lift win-now value, but private/keeper value
  must be anchored by dynasty hold: age window, injury durability, portable
  workload quality, and fragility controls. First-down/TD fit is capped when
  age or durability are weak, so role score alone cannot create an RB1 profile.
- WR is split into `win_now_value` and `dynasty_hold_value`. Win-now rewards
  recent LVE production, expected points, projection, route role, target
  earning, efficiency, and first-down/TD fit. Dynasty hold leans harder into
  target earning, route stability, production stability, age-adjusted value,
  and efficiency. Weak target earning or unstable route role adds penalties
  and risk flags, so young-market optimism cannot outrank proven WR production
  without statistical support.
- QB is split into `win_now_value` and `dynasty_hold_value` with a 10-team 1QB
  replacement baseline. Rushing is start-gated: it only becomes a major value
  driver when start security is strong. Elite dual-threat QBs and truly elite
  passing profiles can clear the exception gate; normal pocket starters and
  unsecured rushing profiles are pushed toward replacement-level value because
  3-point passing TDs and 1QB roster depth make them easier to replace.
- TE is split into `win_now_value` and `dynasty_hold_value` with no-premium
  suppression. Route participation and target earning are mandatory; useful
  but non-elite starters are capped near replacement, and blocker/low-route
  profiles are heavily penalized. Generic TE scarcity and public-market heat
  cannot directly inflate `private_lve_value`; only elite route/target profiles
  can clear the no-premium exception.
- Cross-position rebalance applies the final LVE board layer. Replacement
  baselines are QB `76`, RB `72`, WR `72`, and TE `69`, with row-level override
  fields for calibration. WR/RB profiles receive small lineup-demand boosts
  only when role and skill checks are real. Non-elite QB/TE profiles receive
  additional board suppression for 10-team 1QB and no TE premium. Preview output
  includes `overall_rank`, `position_rank`, `position_rank_label`,
  `cross_position_replacement_baseline`, `lve_lineup_demand_adjustment`, and
  `rank_audit`.

The engine also returns per-feature contribution rows, warning reasons, risk
flags, upside flags, and floor flags. Its output is suitable for Phase 10
preview tables and comparison reports, but it must not overwrite live
`veteran_model_outputs.csv` without the explicit apply workflow.

## Preview-Only Model Outputs

NFLVerse Upgrade Phase 10 adds
`src.services.lve_stats_first_preview_service`. It creates an isolated preview
folder under `local_exports/nflverse_model_previews/` by default.

Each preview contains:

- `stats_first_preview_manifest.json`
- `stats_first_veteran_model_preview_outputs.csv`
- `stats_first_feature_contributions.csv`

The manifest records source file, model version, row count, review status, and
the apply boundary. The preview output is intentionally not shaped as the live
pack's `model_outputs.csv` promotion file; later phases must compare and apply
it explicitly. Preview creation rejects duplicate preview ids, missing
normalized-feature headers, and empty normalized inputs. Review helpers classify
rows as `ready`, `review`, or `blocked` before any preview-vs-live comparison.

## Explicit Apply Workflow

NFLVerse Upgrade Phase 11 adds
`src.services.lve_stats_first_apply_service`. Applying a stats-first preview is
an explicit copy operation, not a mutation:

- The caller must provide the confirmation phrase
  `APPLY_STATS_FIRST_PREVIEW`.
- The selected/source data pack is validated first.
- The service reads one named preview and applies only rows that passed the
  preview review gate as `ready`.
- A new data-pack directory is created under `local_exports/data_packs/` by
  default.
- The source pack is copied, then only the copied pack's `model_outputs.csv` is
  updated.
- A `stats_first_applied_pack_manifest.json` records source pack, preview id,
  model version, applied row count, and the review next action.

The applied pack copy must still go through Import Review admission before it is
used under draft pressure. Duplicate applied pack ids, missing preview files,
non-ready preview rows, invalid source packs, and missing confirmation all block
the apply step.

## UI Trust Pass

NFLVerse Upgrade Phase 12 exposes the stats-first lane in `Sources & Overrides`.
The UI separates:

- normalized feature file status,
- preview creation,
- preview review gate,
- explicit copied-pack apply,
- applied pack review,
- and the final instruction to return to Import Review for admission.

The page avoids decision-ready language for previews and copied packs. Only an
Import Review admission decision can make a generated pack decision-ready.

## Calibration Replay Page

NFLVerse Upgrade Phase 13 adds stats-first calibration to `Historical Replay`.
The page now keeps rookie historical replay and veteran stats-first calibration
separate. The stats-first tab shows:

- LVE trap scenarios such as obvious keep/cut, WR over speculative RB, 1QB QB
  suppression, no-premium TE suppression, and market-not-private-value.
- Sensitivity checks for role and market movement.
- Preview replay summaries for isolated stats-first previews.
- Readiness rows that explicitly state calibration is isolated from current
  boards.

These rows are diagnostics only. They can justify future formula review, but
they cannot update model outputs or data packs.

## Draft-Day Freeze Integration

NFLVerse Upgrade Phase 14 extends Draft Freeze so a freeze can preserve
stats-first evidence alongside the final board export. The freeze service now
backs up:

- selected data pack,
- board exports,
- live `model_outputs.csv`,
- stats-first preview artifacts,
- stats-first applied-pack manifests and outputs.

Stats-first artifacts are copied under `stats_first_backup/`. This is backup
only; freezing does not create previews, apply previews, mutate the active pack,
or bypass Import Review admission.

## Final QA And Safety Gate Audit

NFLVerse Upgrade Phase 15 adds a final audit across the decision pipeline:

- The selected data pack must be decision-ready and admitted by Import Review.
- Stats-first previews must contain a preview-only manifest boundary and an
  output file.
- Stats-first applied packs must preserve the copied-pack/no-overwrite manifest
  boundary.
- Draft freezes must include no-mutation metadata, refresh-lock metadata, and a
  money-decision certificate.
- Missing preview/apply/freeze artifacts are review gates, not silent passes.
- Malformed preview/apply/freeze artifacts are blocking gates.

The Draft Freeze page renders this safety-gate summary before freeze creation.
The audit is read-only: it does not score players, apply previews, select packs,
or mutate files.

## Review And Apply Boundary

These are review-only:

- raw nflverse exports,
- projection imports,
- identity fallback matches,
- normalized feature previews,
- isolated model previews,
- preview-vs-live comparisons,
- calibration recommendations.

These may update app-visible model outputs only after an explicit apply workflow:

- normalized veteran features promoted to model input candidates,
- previewed `veteran_model_outputs.csv`,
- copied generated data packs with applied model output rows.

The selected source pack must never be overwritten in place.

## Implementation Phases

1. Schema and docs.
2. Identity bridge.
3. Raw nflverse import contracts.
4. LVE scoring derivation.
5. Role and usage features.
6. Injury durability features.
7. Projection import layer.
8. Normalization service.
9. Stats-first veteran formula engine.
10. Preview-only model outputs.
11. Explicit apply workflow.
12. UI trust pass.
13. Calibration replay page.
14. Draft-day freeze integration.
15. Final QA and safety gate audit.

## Phase 1 Acceptance

Phase 1 is complete when:

- the nflverse template group exists,
- all template headers are registered in `real_input_template_service`,
- template validation tests cover the new group,
- no scoring behavior changes,
- no network fetch/runtime importer is added yet.
