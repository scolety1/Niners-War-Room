# V2 Source Semantics Audit Summary

V2 expanded the substrate to `5,518` rows over feature seasons `2012-2024` and target seasons `2013-2025`. V3 starts from that tracked V2 parquet and audits every V2 feature column.

## Column Decisions

- Allowed review-only features: `22`
- Null-fenced features: `4` (`prior_offense_pct, prior_offensive_snaps, prior_receiving_air_yards, prior_receiving_yards_after_catch`)
- Blocked or absent feature families: `5`

The V2 optional source fences remain intact:

- Snap/offense fields null-fenced rows: `811`
- Air-yard/YAC fields null-fenced rows: `663`
- Rows with any optional source fence: `1,371`
