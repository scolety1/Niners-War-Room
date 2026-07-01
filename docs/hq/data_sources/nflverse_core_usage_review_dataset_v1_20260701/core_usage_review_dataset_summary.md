# Core Usage Review Dataset Summary

Verdict: `YELLOW_CORE_USAGE_REVIEW_DATASET_BUILT_REVIEW_ONLY`

This packet creates the first practical review-only NFLVerse Core Usage Review Dataset V1 after the merged NFLVerse evidence checkpoint.

## Dataset

- Artifact: `nwr_nflverse_usage_review_dataset_v1.parquet`
- Grain: player-week
- Rows: 76804
- Seasons: 2024;2025
- Week range: 1 to 22
- Red-zone sidecar rows: 6424

## Included Families

- Targets, carries, receptions.
- Null-preserving touches and opportunities.
- Rushing/receiving yards, air yards, yards after catch.
- Rushing/receiving first downs.
- QB passing attempts/completions/yards/touchdowns/interceptions/first downs.
- Offensive snaps and offense percentage where the review-only snap join succeeded.

## Not Included

- Current roster/status/injury/depth/schedule context.
- Routes, TPRR, YPRR, or participation-derived route proxies.
- Ambiguous normalized `rz_att`.
- Production model/training/source-truth/rank/app/recommendation approvals.

This is safe for review and future experimentation gate preparation only.
