# Label Parity Validation Contract

Verdict: `YELLOW_LABEL_PARITY_VALIDATION_CONTRACT_DEFINED_NO_BUILD`

## Scope

The future `Label Parity Validator V1` may run only after a row-level NFLVerse `player_stats` sidecar exists. It compares sidecar rows to existing Outcome/Rookie evaluation labels without promoting either side to model input, training truth, or source truth.

## Required Inputs

- validated `player_stats_sidecar_rows.csv`;
- sidecar schema manifest;
- sidecar coverage report;
- existing Outcome V2 evaluation label artifacts;
- existing Rookie Outcome evaluation label artifacts where applicable;
- identity-safe join manifest;
- censoring policy.

## Required Outputs

- `label_parity_validation_matrix.csv`
- `label_parity_validation_report.md`
- `label_parity_mismatch_taxonomy.md`
- `unmatched_existing_labels.csv`
- `unmatched_nflverse_sidecar_rows.csv`
- `censoring_parity_report.md`
- `no_label_truth_promotion_report.md`

## Required Matrix Fields

- `outcome_family`
- `position`
- `season`
- `label_source`
- `sidecar_source`
- `existing_label_rows`
- `sidecar_rows`
- `matched_players`
- `unmatched_existing_labels`
- `unmatched_nflverse_rows`
- `identity_match_rate`
- `scoring_parity_status`
- `first_down_scoring_status`
- `censoring_parity_status`
- `mismatch_category`
- `acceptance_threshold_status`
- `label_truth_allowed`
- `model_use_allowed`
- `training_allowed`
- `source_truth_allowed`

## Validation Rules

- Labels are evaluation targets only.
- NFLVerse `player_stats` is sidecar/review-only.
- Missing labels are not failures.
- Missing sidecar rows are not player misses.
- Censored windows are not misses.
- Missing values are not zero, false, healthy, clean, low risk, or low probability.
- Mismatch categories must be reported rather than silently resolved.

## Approval Boundary

The validator may create parity evidence for later HQ review. It may not rewrite labels, promote label truth, create active probabilities, approve experiments, approve model input, approve training input, or approve source truth.
