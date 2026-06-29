# Outcome V2 5Y Extension Result

## Verdict

`GREEN_5Y_DATA_EXTENSION_BUILT`

This lane extended historical review-only Outcome V2 labels using public factual nflreadpy player-season data. It did not validate probabilities, build current-player probabilities, or wire Rankings.

## Builder

Added:

- `src/services/outcome_v2_5y_data_coverage_service.py`
- `scripts/build_outcome_v2_extended_historical_labels.py`
- `tests/test_outcome_v2_5y_data_coverage_service.py`

Runtime command used:

```powershell
C:\NWR_SHARED_DATA\tool_envs\overnight_tune_v0\Scripts\python.exe scripts\build_outcome_v2_extended_historical_labels.py --seasons 2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024
```

## Output Artifacts

Generated under:

`C:\NWR_SHARED_DATA\outcome_v2_horizon\historical_labels_extended\`

| Artifact | Rows | Tracked? | Notes |
| --- | ---: | --- | --- |
| `outcome_v2_extended_season_outcome_labels.csv` | 7,440 | no | Review-only exact first-down season labels. |
| `outcome_v2_extended_anchor_horizon_labels.csv` | 7,440 | no | Review-only this-year, next-year, and within-5Y horizon labels. |
| `outcome_v2_extended_label_manifest.csv` | 3 | no | Review-only manifest. |
| `outcome_v2_extended_5y_coverage_summary.csv` | 12 | no | Before/after 5Y coverage summary by position/threshold. |

## Coverage Before vs After

| Metric | Before | After |
| --- | ---: | ---: |
| Season label rows | 3,578 | 7,440 |
| Anchor horizon rows | 3,569 | 7,440 |
| Season coverage | `2019-2024` | `2012-2024` |
| Anchor season coverage | `2018-2023` | `2012-2024` |
| Complete 5Y rows | 296 | 1,064 |
| Censored/missing 5Y rows | 3,273 | 6,376 |
| Scoring mode | `exact_verified_first_downs` | `exact_verified_first_downs` |

The total censored/missing count is higher after extension because the label universe is larger. The important improvement is complete 5Y rows increased from 296 to 1,064.

## 5Y Coverage by Position and Threshold

| Position | Threshold | Complete before | Hits before | Complete after | Hits after | Misses after |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| QB | T6 | 54 | 18 | 203 | 75 | 128 |
| QB | T12 | 54 | 26 | 203 | 107 | 96 |
| RB | T6 | 61 | 26 | 224 | 60 | 164 |
| RB | T12 | 61 | 36 | 224 | 101 | 123 |
| RB | T24 | 61 | 38 | 224 | 137 | 87 |
| RB | T36 | 61 | 43 | 224 | 160 | 64 |
| WR | T6 | 108 | 18 | 395 | 74 | 321 |
| WR | T12 | 108 | 37 | 395 | 136 | 259 |
| WR | T24 | 108 | 51 | 395 | 190 | 205 |
| WR | T36 | 108 | 65 | 395 | 252 | 143 |
| TE | T6 | 73 | 22 | 242 | 68 | 174 |
| TE | T12 | 73 | 34 | 242 | 104 | 138 |

## First-Down / Scoring Status

The extension uses exact verified first-down scoring from player_stats:

- `passing_first_downs`
- `rushing_first_downs`
- `receiving_first_downs`

No scoring approximation was required. Return yards are included from punt/kickoff return yards, and return touchdowns use `special_teams_tds`.

## Missing Data Policy

The extension preserves the existing conservative missing-data rule:

- Missing target seasons are not converted to misses.
- Missing/censored windows emit `Not enough information`.
- Censored 5Y windows remain blocked for validation/app use.

## What This Does Not Do

This extension does not:

- Validate 5Y probabilities.
- Build current-player probability artifacts.
- Add Rankings or Outcome Lens columns.
- Change Dynasty Rank, tiers, model logic, source truth, hidden sort, trade value, pick value, or decision-page behavior.

## Next Step

Run a separate 5Y validation/calibration gate using these extended labels. The 5Y sample is materially improved, but app display still requires no-leakage validation, calibration checks, and current-player feature/identity gates.
