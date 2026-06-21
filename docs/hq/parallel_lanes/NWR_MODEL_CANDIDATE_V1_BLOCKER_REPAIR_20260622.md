# NWR Model Candidate V1 Blocker Repair - 2026-06-22

Status: GREEN for local-only blocker repair. No model is approved.

This repair addresses the Model Candidate V1 QA blocker caused by
`depth_chart_best_rank`. It does not approve private value, rankings, hidden
sort, Mock Draft behavior, simulations, final draft advice, deployment,
`latest_candidate`, or `latest_approved`.

## Blocker

The Model Candidate V1 QA Gate returned RED because WR `safe_no_snap` included
`depth_chart_best_rank`, which is rank-like and blocked for safe model inputs.

Decision applied: do not override the QA blocker. Treat `depth_chart_best_rank`
and rank/order/best/min depth-chart fields as blocked for safe model input
unless a future source-policy review explicitly approves them.

## Local-Only Repair Output

Repair output:
`C:\NWR_SHARED_DATA\model_candidates\model_candidate_v1_research_20260622\blocker_repair_depth_chart_rank_20260622`

Repaired package:
`C:\NWR_SHARED_DATA\model_candidates\model_candidate_v1_research_20260622_repaired`

## Blocker Audit Result

| Item | Result |
| --- | --- |
| Blocked field | `depth_chart_best_rank` |
| RB `role_usage_core` affected | no |
| WR `safe_no_snap` affected | yes |
| Other selected safe candidate rank-like depth fields | none after repair |
| Vendor package status | quarantined research-only |

## Repair Action

The WR path was re-evaluated as `safe_no_snap_no_depth_rank` with
`depth_chart_best_rank` removed. The full V1 24,408-fit grid was not rerun; only
the targeted affected WR evidence was rebuilt using the reviewed model family
and hyperparameters.

## Targeted WR Evidence

| Variant | Top-N | Years beating baseline | Worst drawdown | Result |
| --- | ---: | ---: | ---: | --- |
| `safe_no_snap_no_depth_rank` | 0.528 | 2 | -0.028 | remains research candidate |

The repaired WR path still passes the candidate gate after removing the blocked
field. It remains research-only and not approved for model/private-value/ranking
or draft use.

## Final Repair Decision

| Position | Repaired posture |
| --- | --- |
| QB | Baseline/control preferred. |
| RB | `role_usage_core` remains local-only research candidate. |
| TE | Baseline/reference preferred. |
| WR | `safe_no_snap_no_depth_rank` remains local-only research candidate. |
| WR vendor | Vendor research-only / yellow hold / source-license review required. |

## QA After Repair

| Check | Result |
| --- | --- |
| `depth_chart_best_rank` absent | PASS |
| Rank-like depth-chart fields absent | PASS |
| Vendor fields absent from safe package | PASS |
| Blocked/market/rank fields absent | PASS |
| Fantasy points inputs absent | PASS |
| Source/timing exists for each feature | PASS |
| Unknown timing absent | PASS |
| Blocked-field scan | PASS |
| Leakage scan | PASS |

QA result after repair: GREEN.

No raw local result tables, raw vendor rows, prediction dumps, or
`C:\NWR_SHARED_DATA` package contents are committed here.
