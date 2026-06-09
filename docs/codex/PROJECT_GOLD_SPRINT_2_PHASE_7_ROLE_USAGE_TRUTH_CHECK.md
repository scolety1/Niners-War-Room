# Project Gold Sprint 2 / Phase 7 Audit: Role And Usage Truth Check

Generated: 2026-05-14

## Status

The role/usage audit is complete and rankings remain review-only.

The audit found that role/usage is **not decision-ready** yet. The current public-data preview has useful derived usage from weekly stats, snap counts, and depth charts, but true route/participation data is effectively absent from the free import. That means WR/TE route-role and target-earning rows, plus some role-security rows, must be treated as proxy-supported review inputs rather than hard evidence.

## Artifacts

- Audit folder: `local_exports/model_audits/sprint2_phase7_role_usage_truth_20260514`
- Audit rows: `role_usage_truth_audit.csv`
- Summary rows: `role_usage_truth_summary.csv`
- Gap report: `role_usage_gap_report.csv`
- Manifest: `role_usage_truth_manifest.json`

## Row Counts

| item | count |
|---|---:|
| role/usage audit rows | 4,156 |
| derived usage rows | 1,611 |
| proxy usage rows | 2,521 |
| missing role/usage rows | 24 |
| rank-sensitive proxy/missing rows | 1,421 |

## Position Summary

| position | derived usage | proxy usage | missing |
|---|---:|---:|---:|
| QB | 140 | 420 | 4 |
| RB | 406 | 574 | 4 |
| WR | 695 | 993 | 16 |
| TE | 370 | 534 | 0 |

## What Changed

Two receipt/audit bugs were patched:

1. Normalized feature receipts now keep player identity fields from the normalized row instead of falling back to blank key values.
2. Role/usage receipt truth classification no longer inherits unrelated projection warnings. Role rows now show role-specific warnings such as `missing_participation_proxy` instead of being mislabeled as projection problems.

## Key Finding

`nflverse_participation_player_weekly.csv` is currently empty in the free public preview. Because of that:

- WR/TE `route_role` is a proxy/review input, not true route participation.
- WR/TE `target_earning_stability` can be partly derived from targets, target share, WOPR, and air-yards fields when present, but it is still missing true targets-per-route context.
- RB workload rows are partly supported by weekly stats and snap usage, but RB role security can still be proxy-sensitive when participation/depth context is incomplete.
- QB role security is mostly snap/depth based, but the audit still flags rows where the role score is a large rank driver while participation context is missing.

## Recommendation

Keep rankings review-only until role/usage has either:

1. better free import coverage for participation/route proxies, or
2. a paid/exported source for routes, route share, TPRR, snap share, and depth role, or
3. explicit accepted-review status for the affected rows.

The next Sprint 2 phase should focus on role/usage normalization and data-source strategy, especially true route/participation data for WR/TE and clearer RB workload/goal-line role evidence.
