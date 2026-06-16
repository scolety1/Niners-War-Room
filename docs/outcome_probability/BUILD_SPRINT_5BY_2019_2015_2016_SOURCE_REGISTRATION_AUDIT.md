# Sprint 5BY: 2019 And 2015-2016 Source Registration Audit

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_SOURCE_REGISTRATION_ONLY_MODELING_NOT_APPROVED`

Sprint type: `SOURCE_REGISTRATION_AUDIT_NO_FEATURE_LABEL_REBUILD_NO_MODELING`

## 1. Scope

Sprint 5BY formally audits `2019`, `2015`, and `2016` nflverse-style `player_stats.csv` source seasons for future controlled veteran Outcome expansion. This is a source-registration and inventory sprint only. It does not build feature/label rows, train models, generate probabilities, create coarse bands, create app-readable status/probability/band outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, score rookies through veteran heads, or create promoted artifacts.

Read-only evidence:

- `docs/outcome_probability/BUILD_SPRINT_5BX_NFLVERSE_2010_2019_SOURCE_COVERAGE_PIPELINE_FEASIBILITY.md`
- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`
- `src/services/nflverse_player_stats_import_service.py`
- `src/services/nflverse_raw_import_service.py`
- `scripts/import_nflverse_player_stats.py`
- prior 2017-2018 source-registration docs

Optional local-only audit exports were written under:

`local_exports/outcome_probability/sprint_5by_2019_2015_2016_source_registration_audit/`

These exports are internal-only and not app-readable.

## 2. Registration Decision

| Source season | Intended future use | Source-registration verdict | Modeling approval |
| ---: | --- | --- | --- |
| 2019 | bridge/completed prior season after 2018 | GREEN | not approved |
| 2015 | completed prior season for future 2016 target rows | GREEN | not approved |
| 2016 | completed prior season for future 2017 target rows | GREEN | not approved |

Registration meaning:

- A completed source season may support future target preseason `S+1` features.
- Same-season final stats may be used as target labels only, never as preseason features.
- This sprint approves source registration only. A later sprint must explicitly approve any rebuild, training expansion, calibration rerun, or modeling package.

## 3. Source Coverage

Source path:

`local_exports/truth_set_lab/v3/downloads/player_stats.csv`

| Source season | Total rows | REG rows | REG weeks | Unique player IDs | Duplicate key extra rows | Missing player ID | Missing team/recent_team | Missing position |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 2015 | 5318 | 5101 | 1-17 | 594 | 0 | 0 | 0 | 0 |
| 2016 | 5274 | 5062 | 1-17 | 593 | 0 | 0 | 0 | 0 |
| 2019 | 5261 | 5046 | 1-17 | 617 | 0 | 0 | 0 | 0 |

Duplicate key definition:

`player_id + season + week + season_type`

All audited seasons pass the key and identity requirements for future local-only source use.

## 4. Field Availability

| Source season | Passing fields | Rushing fields | Receiving fields | Rush first downs missing | Receiving first downs missing | Fumble-lost components | `special_teams_tds` |
| ---: | --- | --- | --- | ---: | ---: | --- | --- |
| 2015 | available | available | available | 0 | 0 | available | available |
| 2016 | available | available | available | 0 | 0 | available | available |
| 2019 | available | available | available | 0 | 0 | available | available |

Allowed completed prior-season source fields remain limited to source-safe raw components and identity/context fields:

- player identity and context: `player_id`, `player_name`, `player_display_name`, `recent_team`, `position`, `position_group`, `season`, `week`, `season_type`
- passing production: `completions`, `attempts`, `passing_yards`, `passing_tds`, `interceptions`
- rushing production: `carries`, `rushing_yards`, `rushing_tds`, `rushing_first_downs`
- receiving production: `receptions`, `receiving_yards`, `receiving_tds`, `receiving_first_downs`
- fumbles lost: `rushing_fumbles_lost`, `receiving_fumbles_lost`, `sack_fumbles_lost`

Derived completed-prior-season NWR total, NWR PPG, and position finish rank may be rebuilt only from source-safe components in a later row-generation sprint.

## 5. Return-Stat Gap

The local source includes `special_teams_tds`, but it does not include granular return yards, kick return yards, punt return yards, return TDs, kick return TDs, or punt return TDs.

Registration handling:

- `special_teams_tds` may remain registered as source evidence.
- Exact return-yard scoring is not reconstructable from `player_stats.csv` alone.
- Granular return scoring must remain excluded or require a separate approved source before any exact NWR scoring claim.
- This gap is not a RED/YELLOW source-registration blocker for local-only use because current safe rebuild policy can use source-safe non-return components and document the exclusion.

## 6. Forbidden And Quarantined Fields

Forbidden or quarantined from prediction features:

- `fantasy_points`
- `fantasy_points_ppr`
- `passing_epa`, `rushing_epa`, `receiving_epa`
- `dakota`
- `wopr`, `racr`, `pacr`
- `target_share`, `air_yards_share`
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

Any future row-generation sprint must enforce a positive allowlist and re-run a forbidden-field scan.

## 7. Feature-Source And Label-Source Suitability

| Source season | Completed prior-season feature source? | Same-season label source? | Repair needed before local-only row generation? |
| ---: | --- | --- | --- |
| 2015 | yes | yes, source-safe no exact return yards | none |
| 2016 | yes | yes, source-safe no exact return yards | none |
| 2019 | yes | yes, source-safe no exact return yards | none |

Same-season final stats may be used only for labels in a future target-season rebuild. They must not be used as preseason features for the same target season.

## 8. Risks

Residual risks for future work:

- exact return scoring remains blocked from this source alone;
- era drift remains relevant when combining 2015-2019 with later seasons;
- schema drift should be rechecked if any file is refreshed by nflreadr, nflreadpy, or a direct nflverse download;
- player identity joins to Sleeper/local IDs still need a separate bridge audit before any app-facing use;
- source registration is not model approval.

## 9. Release Stance

5BY does not approve modeling.

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but this sprint creates no app-readable status table.

## 10. Recommended Next Safe Sprint

Recommended next safe sprint if 5BY is accepted: Sprint 5BZ - local-only 2016-2017 historical feature/label rebuild package.

The 5BZ mapping should be:

- Target 2016: completed 2015 source features, final 2016 labels.
- Target 2017: completed 2016 source features, final 2017 labels.

5BZ must remain local-only row generation and must not approve modeling, probabilities, coarse bands, app wiring, rankings/sorting, hidden sort keys, or promoted artifacts.

## 11. Checks

Checks run:

- local CSV inventory completed with no downloads and no package installation
- `git diff --check` passed

Ruff was not required because no tracked Python file changed in 5BY. Pytest was not required because no tracked code or test file changed in 5BY.
