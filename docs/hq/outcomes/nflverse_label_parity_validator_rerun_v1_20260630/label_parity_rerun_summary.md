# Label Parity Validator Rerun Summary

## Executive verdict

`YELLOW_LABEL_PARITY_RERUN_PARTIAL_SCORING_OR_CENSORING_BLOCKERS`

The newly admitted Outcome row-level label source unblocks identity/season overlap for 2024 review comparison. The validator can now create direct same-season overlap rows between the NFLVerse first-down sidecar and Outcome V2 `season_outcome` labels.

Full parity is still not GREEN because scoring parity cannot be proven from the available sidecar columns. The sidecar contains nonzero first-down component rows only; it does not include every scoring input or explicit zero rows needed to recompute full Outcome fantasy scoring.

## Key counts

| Metric | Count |
| --- | ---: |
| Sidecar rows | 13,628 |
| Outcome label rows | 119,040 |
| Direct matched 2024 sidecar row records | 6,372 |
| Direct matched unique sidecar row IDs | 3,186 |
| Direct matched sidecar-label rows written | 25,488 |
| Direct matched players | 186 |
| 2025 sidecar rows unmatched | 7,256 |
| K sidecar rows excluded | 2 |

## Decision

Row-level overlap is now real and reviewable. Label truth, model use, training use, and source-truth use remain closed everywhere.
