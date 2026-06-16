# Sprint 5BU: Local-Only 2018-2019 Historical Feature and Label Rebuild Plan

Outcome lane: veteran outcome probability column path only

Verdict: `LOCAL_ONLY_REBUILD_PLAN_DEFINED_MODELING_NOT_APPROVED`

Sprint type: `DOCS_ONLY_REBUILD_PLAN_NO_ROWS_NO_MODELING`

## 1. Scope

Sprint 5BU defines a future local-only rebuild plan for 2018 and 2019 historical veteran Outcome feature snapshots and labels. This sprint does not run the rebuild, generate a feature matrix, generate a label table, train models, generate outcome probabilities, create app-readable probability/band/status outputs, wire app display, alter rankings/sorting, create hidden sort keys, change rookie framework files, score rookies through veteran heads, or create promoted artifacts.

Evidence reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5BR_PRE_2020_HISTORICAL_UNIVERSE_FEASIBILITY_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5BS_PRE_2020_SOURCE_REGISTRATION_INVENTORY_2017_2018.md`
- `docs/outcome_probability/BUILD_SPRINT_5BT_FORMAL_2017_2018_COMPLETED_PRIOR_SEASON_REGISTRATION_AUDIT.md`

## 2. Target And Source Season Mapping

| Target season | Feature source season | Label source season | Legal rule |
| ---: | ---: | ---: | --- |
| 2018 | completed 2017 source season only | final 2018 same-season stats only | source season `S` supports target preseason `S+1` |
| 2019 | completed 2018 source season only | final 2019 same-season stats only | source season `S` supports target preseason `S+1` |

Same-season final stats may be used only as labels for the target season. They must never be used as preseason features for that same target season.

## 3. Future Local-Only Output Paths

If HQ later approves a rebuild sprint, outputs should be local-only under:

`local_exports/outcome_probability/sprint_5bv_2018_2019_historical_feature_label_rebuild/`

Planned future files:

| Planned file | Purpose | App-readable? |
| --- | --- | --- |
| `metadata_sprint_5bv.json` | run metadata, source commit, source paths, gate status | no |
| `historical_2018_2019_feature_snapshots.csv` | local-only feature snapshots for eligible target rows | no |
| `historical_2018_2019_outcome_labels.csv` | local-only target-season labels rebuilt from source-safe NWR components | no |
| `historical_2018_2019_trainability_report.csv` | emitted/blocked row counts and blocker reasons | no |
| `historical_2018_2019_feature_missingness.csv` | missingness by field/season/position | no |
| `historical_2018_2019_label_support.csv` | outcome support by season/position/head | no |
| `historical_2018_2019_legality_audit.csv` | same-season leakage and completed-prior-season checks | no |
| `historical_2018_2019_forbidden_feature_scan.csv` | forbidden/quarantined field scan | no |
| `historical_2018_2019_identity_team_position_audit.csv` | identity, team, and position join checks | no |
| `historical_2018_2019_duplicate_key_audit.csv` | player-week and target-row uniqueness checks | no |
| `historical_2018_2019_population_policy_audit.csv` | rookie, kicker, blocked, waived, and unscored policy audit | no |
| `README_SPRINT_5BV.md` | local-only packet summary and release blockers | no |

This plan does not create these files.

## 4. Feature-Source Policy

Future feature construction must obey:

1. Use only completed prior-season source facts.
2. Use 2017 source rows only for 2018 target preseason features.
3. Use 2018 source rows only for 2019 target preseason features.
4. Exclude postseason rows unless a later source-policy sprint explicitly approves postseason handling.
5. Aggregate weekly rows before season-level feature use.
6. Preserve missing optional fields rather than filling from future data.
7. Carry source season, target season, and provenance columns through all local-only outputs.
8. Mark every output row as not app-readable and not release-ready.

## 5. Label-Source Policy

Future label construction must obey:

1. Use final target-season stats only as labels.
2. Use 2018 final source-safe stats only to label 2018 outcomes.
3. Use 2019 final source-safe stats only to label 2019 outcomes.
4. Do not use label source columns as preseason prediction features.
5. Do not copy `fantasy_points` or `fantasy_points_ppr` as labels or features.
6. Rebuild NWR scoring labels from allowlisted raw scoring components.
7. Store labels only in local-only audit artifacts if HQ later approves the rebuild.

## 6. Legal Prior-Season Feature Fields

Allowed prior-season source fields:

| Feature family | Source fields |
| --- | --- |
| Games or active games | `week`, `season_type`, player-week presence |
| Passing volume/production | `completions`, `attempts`, `passing_yards`, `passing_tds`, `interceptions` |
| Rushing volume/production | `carries`, `rushing_yards`, `rushing_tds`, `rushing_first_downs` |
| Receiving volume/production | `receptions`, `receiving_yards`, `receiving_tds`, `receiving_first_downs` |
| Fumbles lost | `rushing_fumbles_lost`, `receiving_fumbles_lost`, `sack_fumbles_lost` |
| Identity/context for joins | `player_id`, `player_name`, `player_display_name`, `recent_team`, `position`, `position_group`, `season`, `week`, `season_type` |

Allowed derived features, if later rebuild checks pass:

- prior completed-season NWR PPG
- prior completed-season NWR finish rank
- games played or active games
- age and experience from stable identity/DOB joins

## 7. Forbidden And Quarantined Fields

Forbidden or quarantined:

- `fantasy_points`
- `fantasy_points_ppr`
- EPA fields
- `dakota`
- `wopr`
- `racr`
- `pacr`
- `target_share`
- `air_yards_share`
- ADP
- public rankings
- projections
- consensus
- market values
- trade values/calculators
- RotoWire rankings/projections/outlooks/values
- prior fantasy draft history
- legacy `private_score`
- same-season target final stats as preseason features
- label supplement sources as prediction features

Any future rebuild must use a positive allowlist. Fields not explicitly allowed should be excluded by default.

## 8. NWR Scoring Reconstruction Approach

Future NWR scoring reconstruction should:

1. Rebuild scoring from raw source-safe components.
2. Use passing, rushing, receiving, interception, and fumble-lost components from the allowed source list.
3. Include rushing and receiving first downs because 5BT registered them as present and safe for 2017 and 2018 completed prior-season use.
4. Exclude fantasy total shortcuts.
5. Exclude incomplete return-yard/return-TD handling unless a later scoring policy approves it.
6. Preserve season and position context for threshold labels.
7. Emit tie-handling and rank-method metadata in the local-only label support audit.

## 9. Position Threshold Label Approach

Future target labels should be rebuilt by position and target season.

Planned threshold families:

| Position | Candidate threshold heads | Notes |
| --- | --- | --- |
| QB | future inventory labels only | Do not release or model without separate support review. |
| RB | T6/T12/T24/T36/T48 if support exists | T6/T12 remain likely sparse and must be audited. |
| WR | T6/T12/T24/T36/T48 if support exists | WR calibration risk remains high from prior sprints. |
| TE | future inventory labels only | Do not release or model without separate support review. |

For every threshold, the label definition must preserve top-N-or-better semantics:

`P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)`

This plan does not approve any modeling or display for these labels.

## 10. Identity, Team, And Position Requirements

Future rebuild must check:

- `player_id` coverage
- player name/display name coverage
- identity/DOB join coverage for age/experience
- `recent_team` coverage and team abbreviation consistency
- `position` and `position_group` coverage
- position eligibility for QB/RB/WR/TE labels
- player/team changes across a season
- ambiguous or duplicate identity joins

Rows that fail required identity, team, or position checks should be blocked and reported, not repaired from future or app-facing data.

## 11. Duplicate-Key Checks

Required checks:

| Key | Purpose |
| --- | --- |
| `player_id + source_season + week + season_type` | raw player-week uniqueness |
| `player_id + target_season` | feature snapshot uniqueness |
| `player_id + target_season + position` | label-row uniqueness where position-specific labels are created |
| `player_id + target_season + threshold_head` | threshold-label uniqueness |

Any duplicate key failure should block the affected rows until resolved by a separate audit.

## 12. First-Down Completeness Checks

Future rebuild must confirm:

- `rushing_first_downs` non-missing coverage by source season.
- `receiving_first_downs` non-missing coverage by source season.
- first-down aggregation totals are nonnegative and plausible.
- source-season first-downs are used only as prior-season features.
- target-season first-downs are used only inside labels, not same-season features.

If first-down completeness fails, the rebuild should block or require a separate first-down reconstruction policy sprint.

## 13. Leakage Checks

Required leakage gates:

| Gate | Required result |
| --- | --- |
| Completed prior-season feature source | pass |
| Target-season final stats as features | fail/block if detected |
| Fantasy total shortcuts | excluded |
| Forbidden market/rank/projection fields | absent or excluded |
| Label source columns in feature table | blocked |
| Postseason rows in regular-season feature source | excluded unless separately approved |
| Derived feature timestamp | source season `S` before target season `S+1` |

The future rebuild should produce a local-only legality audit with explicit pass/fail rows.

## 14. Row Eligibility And Exclusion Policy

Eligible future rows:

- veteran QB/RB/WR/TE rows with valid source-season identity, team, position, and required feature coverage
- target-season labels reconstructable from source-safe components
- rows that pass same-season leakage and forbidden-field scans

Blocked rows:

- missing required identity
- missing required source-season features
- missing target-season labels
- duplicate unresolved keys
- source/target season mismatch
- forbidden feature contamination
- same-season feature leakage
- invalid or unsupported position

Waived/unscored/current-player policy:

- This future rebuild is historical only.
- Current waived/blocked/unscored rows must not be scored by this process.
- If a historical player lacks required coverage, block the row rather than imputing from future data.

Rookies/kickers:

- Rookies must not be scored through veteran heads.
- Kicker rows remain not applicable.
- Non-QB/RB/WR/TE rows remain excluded unless a later sprint approves a different population.

## 15. Required Future Tests And Checks

Before any future rebuild can be trusted:

1. `git diff --check` for the rebuild sprint.
2. Source path existence and schema check.
3. 2017/2018 component allowlist check.
4. Forbidden/quarantined field scan.
5. Player-week duplicate-key audit.
6. Feature snapshot duplicate-key audit.
7. Identity/DOB join coverage audit.
8. Team and position mapping audit.
9. First-down completeness and aggregation audit.
10. NWR scoring reconstruction sanity check.
11. Label support by season/position/head.
12. Same-season leakage audit.
13. Population policy audit.
14. Artifact quarantine audit.
15. App/import isolation audit.
16. Adversarial audit before modeling.

## 16. Modeling And Release Decision

This plan does not approve modeling now.

Still not approved:

- actual feature matrix generation
- actual label table generation
- model training
- calibration rerun
- exact percentages
- coarse bands
- app wiring
- app-readable status tables
- rankings/sorting usage
- hidden sort keys
- promoted artifacts

## 17. Recommended Next Safe Sprint

Recommended next safe sprint:

`Sprint 5BV - Local-Only 2018-2019 Historical Feature and Label Rebuild Package`

Scope only if HQ approves:

- Generate local-only 2018/2019 feature and label audit artifacts under the planned quarantine path.
- Run legality, identity, duplicate-key, first-down, label-support, population, and artifact-quarantine checks.
- Do not train models.
- Do not create app-readable outputs.
- Do not release probabilities or bands.

Alternative if HQ wants another gate before row generation:

`Sprint 5BV - 2018-2019 Rebuild Contract Adversarial Audit`

## 18. Final Gate Label

Final gate label:

`LOCAL_ONLY_2018_2019_REBUILD_PLAN_READY_MODELING_AND_RELEASE_BLOCKED`

Meaning:

- The local-only future rebuild contract is defined.
- Target/source season mapping is explicit.
- Feature and label policies are separated.
- Required checks and quarantine paths are defined.
- Modeling is not approved.
- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting and hidden sort keys remain blocked.
- Promoted artifacts remain blocked.
