# Label Overlap and Missingness Report

Verdict: `PARTIAL_SIDECAR_EVIDENCE_ONLY`

## Outcome V2 Label Coverage Evidence

The Outcome V2 2000-2024 validation packet reports review-only field decisions across QB, RB, WR, and TE labels.

Aggregated field evidence:

| Position | Fields | Complete Row Sum | Validation Row Sum | Review-Only Fields | Blocked Fields |
|---|---:|---:|---:|---:|---:|
| QB | 6 | 6,130 | 580 | 6 | 0 |
| RB | 12 | 20,316 | 1,860 | 11 | 1 |
| WR | 12 | 30,152 | 2,884 | 12 | 0 |
| TE | 6 | 8,632 | 844 | 6 | 0 |

The blocked field is an Outcome V2 calibration decision, not an NFLVerse sidecar decision.

## Rookie Drafted-Only Sidecar Evidence

The tracked drafted-only sidecar feasibility matrix contains 52 rows: 13 seasons for each of QB, RB, WR, and TE.

Aggregated review evidence:

| Position | Matrix Rows | Matched Drafted Players | Outcome V2 Label Overlap | Rows Needing Historical Refresh | Partial Future-Lane Rows |
|---|---:|---:|---:|---:|---:|
| QB | 13 | 149 | 112 | 12 | 1 |
| RB | 13 | 273 | 245 | 12 | 1 |
| WR | 13 | 421 | 377 | 12 | 1 |
| TE | 13 | 182 | 163 | 12 | 1 |

## Missingness Finding

The current tracked sidecar evidence does not compute:

- matched player_stats rows against Outcome V2 label rows;
- unmatched existing labels;
- unmatched NFLVerse rows;
- duplicate or collision handling;
- scoring parity mismatches;
- right-censoring parity mismatches.

Those fields remain `Not enough information` for this packet.

## Censoring Rule

Incomplete outcome windows are censored, not misses. A sidecar parity lane must preserve existing Outcome V2 censoring behavior and must not convert missing or future-incomplete windows into false outcomes.

## No-Zero Rule

Missing label, player_stats, or sidecar match data is `Not enough information`. It is not zero production, not a failed outcome, and not a low-probability signal.
