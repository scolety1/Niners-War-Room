# Sidecar Overlap Summary

Verdict: `YELLOW_PLAYER_STATS_SIDECAR_OVERLAP_READY_NO_LABEL_PROMOTION`

## Executive Summary

The lane finds enough tracked evidence to define a review-only overlap posture, but not enough row-level NFLVerse `player_stats` data to compute true sidecar matches or unmatched rows.

The correct current status is:

- sidecar review comparison may proceed later;
- label truth is not changed;
- model, training, and source-truth approvals remain false;
- active current-player and rookie probabilities remain unchanged;
- row-level unmatched reports are blocked by missing tracked sidecar rows.

## Tracked Evidence

### Outcome V2 2000-2024 Labels

Aggregated review evidence from the field-level decision table:

| Position | Fields | Complete Row Sum | Positive Row Sum | Validation Row Sum | Review-Only Fields | Blocked Fields |
|---|---:|---:|---:|---:|---:|---:|
| QB | 6 | 6,130 | 1,247 | 580 | 6 | 0 |
| RB | 12 | 20,316 | 4,178 | 1,860 | 11 | 1 |
| WR | 12 | 30,152 | 4,958 | 2,884 | 12 | 0 |
| TE | 6 | 8,632 | 1,182 | 844 | 6 | 0 |

These are existing evaluation labels only, not input features.

### Rookie Drafted-Only Sidecar Feasibility

The drafted-only feasibility matrix has `52` rows: 13 seasons for each of QB, RB, WR, and TE.

Aggregated review evidence:

| Position | Matrix Rows | Matched Drafted Players | Outcome V2 Label Overlap | Historical Refresh Needed Rows | Partial Future-Lane Rows |
|---|---:|---:|---:|---:|---:|
| QB | 13 | 149 | 112 | 12 | 1 |
| RB | 13 | 273 | 245 | 12 | 1 |
| WR | 13 | 421 | 377 | 12 | 1 |
| TE | 13 | 182 | 163 | 12 | 1 |

These counts describe review coverage in the feasibility packet. They are not a computed NFLVerse player_stats-to-label sidecar match.

### Tracked NFLVerse Player Stats Template

`templates/real_data_inputs/nflverse_stats_upgrade/nflverse_player_stats_weekly.csv` has `0` rows. It provides schema shape only.

## Overlap Status

True sidecar overlap is `NOT_COMPUTED_ROW_LEVEL_SIDECAR_MISSING`.

The current packet therefore reports count-level evidence and keeps row-level match, unmatched-label, unmatched-NFLVerse, identity match-rate, scoring parity, and censoring parity as `Not enough information`.

## Missingness Rule

Missing sidecar evidence is not a failure. Missing/incomplete labels are censored or `Not enough information`, not misses and not zero production.
