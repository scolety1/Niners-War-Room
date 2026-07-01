# NFLVerse Full Scoring Parity Rerun V1 - Artifact Manifest

## Verdict

`YELLOW_FULL_SCORING_PARITY_PARTIAL_GLOBAL_ZERO_OR_RETURN_SPECIAL_BLOCKERS`

## Base

`origin/work/hq-parallel-control` at `a76224f4b490044060ff59e73ed868fe4200d1fe`.

## Inputs

- Sidecar artifact: `docs/hq/outcomes/nflverse_observed_row_full_scoring_sidecar_builder_v1_20260630/observed_row_full_scoring_sidecar_artifact.csv`
- Sidecar SHA256: `e3c19d3c047e47fc2a34a5533cd477aa011a38c28f9a1d3a80b97fe8c9304d74`
- Sidecar rows: `90,092`
- Label source artifact: `docs/hq/outcomes/outcome_row_level_label_source_admission_v1_20260630/compact_outcome_row_level_label_source.csv`
- Label rows: `119,040`

## Outputs

| File | Rows | SHA256 | Purpose |
| --- | ---: | --- | --- |
| `full_scoring_parity_matrix.csv` | `16` | `e851d6200c73d1a8768f89b121e3159494056640ac7996384735d5916c2a6a50` | Label-family/position/year parity status. |
| `observed_row_scoring_overlap_matrix.csv` | `8` | `71079b691d212416ff8ec10821d017e33440ec7f0b8949f8ac76841aa1064b88` | Player-season overlap by position/year. |
| `matched_observed_row_scoring_labels.csv` | `2,976` | `6bc1c7d2a29716deccdf554f10074aa44d304e91672dc43e8aafca156c7ac228` | Deterministic matched review rows. |

## Approval posture

All label truth, model use, training, and source-truth approval flags remain `false`. This packet creates no probabilities and runs no model experiment.
