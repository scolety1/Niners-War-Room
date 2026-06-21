# NWR Model Candidate V1 Post-Tune Forensic Audit - 2026-06-22

Status: GREEN for post-tune forensic audit. No model is approved.

This audit inspected the repaired Model Candidate V1 research package before a
draft-day export build. It does not approve private value, rankings, hidden sort,
Mock Draft behavior, simulations, final draft advice, deployment,
`latest_candidate`, or `latest_approved`.

## Local-Only Audit Path

`C:\NWR_SHARED_DATA\model_candidates\model_candidate_v1_research_20260622_repaired\post_tune_forensic_audit_20260622`

Local-only outputs created:

- `POST_TUNE_FORENSIC_AUDIT_SUMMARY.md`
- `POST_TUNE_FEATURE_AUDIT.csv`
- `POST_TUNE_STABILITY_AUDIT.csv`
- `POST_TUNE_OVERFIT_AUDIT.csv`
- `POST_TUNE_MISS_ANALYSIS.md`
- `POST_TUNE_PATCH_DECISION.md`
- `POST_TUNE_DECISION_LOG.md`
- `TARGETED_PATCH_RESULTS.csv`
- `TARGETED_PATCH_YEARLY_STABILITY.csv`
- `TARGETED_PATCH_README.md`

## Audit Verdict

Verdict: NO_ACTION_GREEN.

The repaired package remains the best safe research form currently available.
A targeted WR robustness patch was run, but it did not identify a materially
better safe replacement. No package promotion is granted.

## Target Definition

The tune uses `next_nwr_points` and `next_nwr_ppg` as historical target
outcomes. Top-N hit rate is based on `next_nwr_points` ordering and is applied
consistently to baseline and candidate rows.

Top-N thresholds are:

| Position | Top-N |
| --- | ---: |
| QB | 12 |
| RB | 24 |
| WR | 36 |
| TE | 12 |

This matches the current implemented NWR scoring posture as closely as the
current backtest stack supports. It does not approve external fantasy scoring
fields such as `fantasy_points` or `fantasy_points_ppr` as inputs.

## Feature Audit

| Area | Result |
| --- | --- |
| `depth_chart_best_rank` absent | PASS |
| Rank-like depth-chart fields absent | PASS |
| ADP/ECR/rank/projection/market/trade/private-value fields absent | PASS |
| `fantasy_points` / `fantasy_points_ppr` absent as inputs | PASS |
| Vendor fields absent from safe package | PASS |
| Source/timing rows present | PASS |
| Unknown timing fields | none |

Factual target-volume/rate fields such as `targets` and `yards_per_target` are
allowed; target outcome columns remain blocked.

## Stability Audit

| Position | Candidate | Top-N | Years beating baseline | Worst drawdown | Excluding best year | Result |
| --- | --- | ---: | ---: | ---: | --- | --- |
| RB | `role_usage_core` | 0.500 | 3 | -0.042 | still has 2 positive seasons | remains candidate |
| WR | `safe_no_snap_no_depth_rank` | 0.528 | 2 | -0.028 | edge is thinner, 1 positive season | remains candidate with caveat |

Neither candidate has a major collapse flag or one-lucky-year flag. WR remains
safe enough for research export, but its edge is thinner than RB and should stay
clearly labeled as research-only.

## Overfit Audit

Both selected candidates use ExtraTrees, a flexible model family.

RB `role_usage_core` was supported by a broad V1 peer grid. Simpler nearby
models trailed on Top-N, while the selected row retained stable year-level
evidence.

WR `safe_no_snap_no_depth_rank` received a targeted robustness patch with
additional seeds and nearby simpler model checks. One higher Top-N seed reached
0.556, but failed the stability gate as a one-lucky-season result. Safe patch
rows tied the repaired Top-N/stability posture with only small secondary-metric
differences, so no replacement was adopted.

## Miss Analysis

Local-only miss summaries were generated for RB and WR. The artifacts identify
false positives and false negatives by year, but they do not contain verified
injury, team-change, or role-change reason labels. Misses should therefore be
treated as role/season outcome noise pending separate qualitative review. No
raw prediction dumps are committed in this repo summary.

## Snap / No-Snap

RB `role_usage_core` uses snap-related role features: `offense_snaps` and
`offense_pct`.

WR `safe_no_snap_no_depth_rank` remains a no-snap candidate and excludes snap
fields. It remains useful because it still clears the Top-N/stability gate after
removing `depth_chart_best_rank`.

## Vendor Isolation

Vendor isolation remains PASS. WR `vendor_rotowire_receiving_redzone` remains
research-only / yellow hold / source-license review required. Vendor features
are not mixed into the safe candidate package and must not flow into private
value, rankings, Mock Draft, simulations, or final advice.

## Final Posture

| Position | Posture |
| --- | --- |
| QB | Baseline/control preferred. |
| RB | `role_usage_core` remains local-only research candidate. |
| TE | Baseline/reference preferred. |
| WR | `safe_no_snap_no_depth_rank` remains local-only research candidate. |
| WR vendor | Vendor research-only / yellow hold / source-license review required. |

## Readiness For Draft-Day Export

Readiness: GREEN for building a research-only draft-day export package from the
repaired candidate posture.

This is not final approval, not production approval, not latest-approved, not
draft-ready, and not draft advice. A separate explicit export/freeze gate is
still required.

No raw local result tables, raw vendor rows, prediction dumps, or
`C:\NWR_SHARED_DATA` package contents are committed here.
