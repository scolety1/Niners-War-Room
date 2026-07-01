# Sleeper/NFLVerse Usage Red-Zone Source Admission V1

Verdict: `YELLOW_USAGE_REDZONE_SOURCE_ADMISSION_REVIEW_ONLY_WITH_ROUTE_GAPS`

Base HEAD: `866e3d0c0ff61a7c13f761d3999cc2e8d77e9a05`

This packet admits compact source receipts for review-only evaluation of Sleeper weekly stats and existing NFLVerse/NFL Usage usage context. It does not approve production model use, training use, label truth, source truth, probabilities, recommendations, rankings, hidden sorts, or app wiring.

## What Was Checked

- Sleeper weekly stats public API for regular-season weeks 1-18 in 2024 and 2025.
- Existing tracked NFL Usage field inventories and historical usage coverage matrices.
- Approved local NFLVerse cache metadata/headers for player_stats, snap_counts, ff_opportunity, participation, and FTN charting. Raw cache files were inspected read-only and were not copied into git.

## Coverage Result

- Sleeper week receipts sampled: 36
- Sleeper successful week receipts: 36
- Sleeper player rows observed across receipts: 81658
- 2024 Sleeper weeks/rows: 18 weeks / 40641 rows
- 2025 Sleeper weeks/rows: 18 weeks / 41017 rows

Sleeper exposed `rec_rz_tgt`, `rush_rz_att`, `pass_rz_att`, `rz_att`, `rec_tgt`, `rush_att`, `rec`, `off_snp`, and `tm_off_snp` in every sampled week. Route candidate fields were not present in the sampled Sleeper weekly stats.

## Main Decisions

- Red-zone fields are source-admission candidates for review-only lagged usage work, not approved model features.
- The next checkpoint should be a Core Usage Review Dataset V1 builder, focused on lagged factual usage/context artifacts rather than full fantasy scoring parity.
- Full scoring parity, return touchdown subtype gaps, and route-efficiency metrics do not block this phase.
- `rz_att` remains ambiguous and should not be used until semantics are independently documented.
- Red-zone opportunities are opportunities, not guaranteed touches.
- Missing Sleeper fields are sparse/unavailable, not zero, unless the API explicitly returns numeric zero. In this sample, the audited Sleeper fields appeared only as nonzero values.
- Existing NFL Usage docs provide historical overlap for targets/receptions/touches/snaps and PBP-derived red-zone carries/targets/touches, but those remain gated by the existing usage/source-governance gates.
- PBP-derived red-zone counts using `yardline_100 <= 20` are acceptable as review-only validation/fallback artifacts when built by an approved source-governance lane.
- Routes/TPRR/YPRR are deferred unless a rights-cleared upload or already approved compact source exists; do not create route proxies from participation data.
- Core build-ready review families for the next lane are targets, carries, receptions, rushing/receiving yards, air yards, yards after catch, first downs, offense snaps, snap share, touches, opportunities, and typed red-zone opportunities after source semantics checks.

## Files

- `sleeper_weekly_stats_receipt.csv`
- `usage_redzone_field_mapping.csv`
- `season_week_coverage_matrix.csv`
- `route_field_presence_audit.csv`
- `missingness_and_zero_policy.md`
- `guardrail_report.md`
- `next_dataset_handoff.md`
- `merge_safety_report.md`
