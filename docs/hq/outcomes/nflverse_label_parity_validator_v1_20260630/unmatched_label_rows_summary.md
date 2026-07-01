# Unmatched Label Rows Summary

Decision: `SUMMARY_ONLY_NO_ROW_LEVEL_LABEL_ARTIFACT`

## Why No `unmatched_label_rows.csv`

The tracked Outcome V2 label evidence is field-level, not row-level. It does not provide player ID, season, position, label hit, and censoring fields needed to identify unmatched label rows.

## Available Label Evidence

| Position | Complete Row Sum | Validation Row Sum | Review-Only Fields | Blocked Fields |
|---|---:|---:|---:|---:|
| QB | 6,130 | 580 | 6 | 0 |
| RB | 20,316 | 1,860 | 11 | 1 |
| WR | 30,152 | 2,884 | 12 | 0 |
| TE | 8,632 | 844 | 6 | 0 |

## Required Future Label Artifact

A future validator needs row-level labels with:

- player identity key;
- player name;
- position;
- season;
- label family;
- hit/miss value where complete;
- censoring status;
- label source and scoring mode.

Until then, unmatched labels remain `Not enough information`.
