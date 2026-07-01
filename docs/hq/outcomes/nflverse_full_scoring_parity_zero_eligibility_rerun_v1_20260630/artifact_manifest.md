# NFLVerse Full Scoring Parity Rerun With Zero Eligibility V1 - Artifact Manifest

## Verdict

`YELLOW_ZERO_ELIGIBILITY_PARITY_IMPROVED_REMAINING_BLOCKERS`

## Base

`origin/work/hq-parallel-control` at `933c8067c98eb706a0093e10df7da7d780652042`.

## Inputs validated

- Observed-row sidecar rows: `90,092`
- Nonzero component rows: `54,986`
- Explicit observed-zero rows: `35,106`
- Sidecar artifact SHA256: `e3c19d3c047e47fc2a34a5533cd477aa011a38c28f9a1d3a80b97fe8c9304d74`
- Sidecar coverage matrix rows: `23`
- Outcome label rows: `119,040`
- Zero eligibility matrix rows: `10,252`
- Zero eligibility parity subset rows: `6,222`

## Outputs

| File | Rows | SHA256 | Purpose |
| --- | ---: | --- | --- |
| `zero_eligibility_parity_matrix.csv` | `8` | `e2eb2afa377b6aa5aac4cd8a8d53a55ae447e621870e5e7eb0b59fe59f72de20` | Prior-vs-rerun parity comparison. |
| `matched_zero_eligibility_scoring_labels.csv` | `2,816` | `08a33bdf101697b08b639df223dea3a78edb72267f3b0c6a09503101ec9488c5` | Deterministic matched review rows from parity subset. |
| `remaining_zero_blocker_report.csv` | `8` | `306f8eac6fd359f8aaf2f9367e3d2b2e9596fb203ed804001390a8de9eeb2610` | Zero eligibility statuses and blockers. |

All outputs are review-only and keep label/model/training/source-truth/experiment approvals false.
