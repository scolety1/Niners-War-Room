# Sprint 5BX: NFLverse 2010-2019 Source Coverage And Pipeline Feasibility

Outcome lane: veteran outcome probability column path only

Verdict: `INVENTORY_COMPLETE_LOCAL_PLAYER_STATS_FOUND_MODELING_NOT_APPROVED`

Sprint type: `DOCS_PLUS_LOCAL_INVENTORY_NO_FEATURE_LABEL_REBUILD_NO_MODELING`

## 1. Scope

Sprint 5BX inventoried local nflverse-style `player_stats` coverage for 2010-2019 and checked whether the repo has a safe path for future staged historical Outcome source registration. This sprint did not generate feature/label rebuild rows, train models, generate probabilities, create coarse bands, create app-readable status/probability/band outputs, wire app display, alter rankings/sorting, create hidden sort keys, touch rookie framework files, score rookies through veteran heads, or create promoted artifacts.

## 2. Gate 5BX-A

Gate result: pass.

The repo can safely read local nflverse-style `player_stats` data without package installation, model runs, app wiring, or unsafe downloads.

Local source path found:

- `local_exports/truth_set_lab/v3/downloads/player_stats.csv`

Existing repo pipeline references found:

- `src/services/nflverse_player_stats_import_service.py`
- `src/services/nflverse_raw_import_service.py`
- `scripts/import_nflverse_player_stats.py`
- `config/source_registry.csv`
- `config/api_source_permissions.csv`
- `app/pages/01_import_review.py`

The 5BX inventory did not invoke downloads or app wiring. It used Python stdlib CSV reading against the local file only.

## 3. Local-Only Inventory Export

Created local-only inventory package:

`local_exports/outcome_probability/sprint_5bx_nflverse_2010_2019_source_coverage/`

Created local-only files:

| File | Purpose | App-readable? |
| --- | --- | --- |
| `metadata_sprint_5bx.json` | inventory metadata and release blockers | no |
| `nflverse_2010_2019_player_stats_season_coverage.csv` | season-level coverage and key-quality inventory | no |
| `nflverse_2010_2019_field_availability.csv` | field-level availability inventory | no |
| `nflverse_2010_2019_source_paths.csv` | local source and repo reference paths | no |
| `README_SPRINT_5BX.md` | local inventory summary | no |

All outputs are internal-only and not app-readable.

## 4. 2010-2019 Season Coverage

The local `player_stats.csv` contains all requested seasons 2010-2019.

| Season | Rows | REG rows | REG weeks | Unique player IDs | Duplicate player-season-week-type extras | Missing player ID | Missing team | Missing position |
| ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 2010 | 5204 | 4988 | 1-17 | 580 | 1 | 0 | 0 | 0 |
| 2011 | 5301 | 5091 | 1-17 | 586 | 0 | 0 | 0 | 3 |
| 2012 | 5354 | 5150 | 1-17 | 603 | 0 | 0 | 0 | 21 |
| 2013 | 5231 | 5022 | 1-17 | 591 | 0 | 0 | 0 | 25 |
| 2014 | 5350 | 5129 | 1-17 | 589 | 0 | 0 | 0 | 20 |
| 2015 | 5318 | 5101 | 1-17 | 594 | 0 | 0 | 0 | 0 |
| 2016 | 5274 | 5062 | 1-17 | 593 | 0 | 0 | 0 | 0 |
| 2017 | 5319 | 5107 | 1-17 | 587 | 0 | 0 | 0 | 0 |
| 2018 | 5281 | 5070 | 1-17 | 614 | 0 | 0 | 0 | 0 |
| 2019 | 5261 | 5046 | 1-17 | 617 | 0 | 0 | 0 | 0 |

Coverage result: `GREEN_FOR_LOCAL_INVENTORY`, `YELLOW_FOR_FUTURE_MODELING_UNTIL_REPAIRS_AND_REGISTRATION`.

## 5. Field Availability

Passing, rushing, and receiving component fields are present for all inventoried seasons. Rushing and receiving first-down fields are present for all seasons with zero missing values in the local source rows.

| Season range | Passing fields | Rushing fields | Receiving fields | Rush first downs | Receiving first downs |
| --- | --- | --- | --- | --- | --- |
| 2010-2019 | available | available | available | available, 0 missing | available, 0 missing |

Fumble-lost component fields are available through:

- `rushing_fumbles_lost`
- `receiving_fumbles_lost`
- `sack_fumbles_lost`

Return-stat coverage is incomplete for exact NWR return scoring. The local player_stats schema does not include granular return yards, kick return yards, punt return yards, return TDs, kick return TDs, or punt return TDs. It does include `special_teams_tds`, so return/special-teams touchdown evidence is partial, but return-yard scoring cannot be reconstructed from this file alone.

Return/fumble result:

- fumble-lost components: available
- special-teams TDs: available
- granular return TDs: unavailable
- return yards: unavailable
- exact return scoring from player_stats alone: not approved

## 6. Pipeline Feasibility

The repo already contains a local player_stats transform path:

- `scripts/import_nflverse_player_stats.py` can transform a local official `player_stats.csv` into the repo's local weekly player stats contract.
- `src/services/nflverse_player_stats_import_service.py` defines source URLs, transform behavior, supported positions, and field mapping.
- `src/services/nflverse_raw_import_service.py` validates local raw nflverse CSV contracts.

For future Outcome expansion, the safest near-term path is Python stdlib/pandas local CSV reading from already-downloaded files, because it matches the repo's existing local-first workflow and does not require R or package installation inside the sprint. R `nflreadr` remains the most canonical future retrieval/export path if new seasons or missing source files must be acquired outside Codex review. Python `nflreadpy` may be useful later, but should not be introduced until a separate dependency and source-policy sprint approves it.

No unsafe downloads were performed in 5BX.

## 7. Risks And Blockers

Future modeling is not approved from this inventory alone.

Major blockers and risks:

- 2010 has one duplicate `player_id + season + week + season_type` extra row that needs row-level inspection.
- 2011-2014 have missing position values and need repair or exclusion policy before use.
- Return-yard scoring is not reconstructable from local `player_stats.csv` alone.
- Special-teams TDs are available, but they are not granular enough to separate return TD type.
- Historical era drift remains material across 2010-2019 because offensive environment, positional usage, and schedule context differ from later calibration windows.
- Schema/source drift must be checked before any feature/label rebuild, especially if future retrieval uses nflreadr/nflreadpy rather than the existing local CSV.
- Player ID continuity appears usable at the file level, but future joins must keep `player_id` as the primary key and audit any Sleeper/local identity bridge separately.
- Team and position mappings are mostly strong, but missing positions in 2011-2014 block direct modeling use until resolved.
- Same-season final stats remain labels only and must never become preseason features.

## 8. Recommended Staging

Recommended next safe sprint: Sprint 5BY - formal source registration audit for the cleanest next pre-2020 source window.

Staging recommendation:

1. Use 2017-2019 as the nearest clean continuity window for source registration extension, noting that 2017-2018 already received formal 5BT/5BV treatment.
2. Audit 2019 as a completed prior-season source candidate for future controlled target-season use before expanding earlier.
3. Then audit 2015-2016 because they have complete identity/team/position coverage in this inventory.
4. Defer 2010-2014 until duplicate-key and missing-position repair policy is defined.

No 2010-2019 modeling, feature/label rebuild, probability generation, or display path is approved by 5BX.

## 9. Release Stance

Exact percentages remain blocked.

Coarse bands remain blocked.

App wiring for real probabilities or bands remains blocked.

Rankings/sorting and hidden sort keys remain blocked.

Promoted artifacts remain blocked.

Existing status-only Outcome Model Status copy remains safe, but this sprint creates no app-readable status table.

## 10. Checks

Checks run:

- local CSV inventory completed with no downloads and no package installation
- `git diff --check` passed

Ruff was not required because no tracked Python file changed in 5BX. Pytest was not required because no tracked code or test file changed in 5BX.
