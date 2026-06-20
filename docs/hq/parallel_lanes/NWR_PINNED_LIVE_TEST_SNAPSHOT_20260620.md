# NWR Pinned Live-Test Snapshot - 2026-06-20

Owner: Master/Main HQ

Status: RED. The pinned local live-test snapshot was not created because a required package failed the explicit no-UTF-8-BOM validation gate.

## Requested Snapshot

| Field | Value |
| --- | --- |
| Intended label | `20260620_controlled_sim_v1` |
| Intended path | `C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1` |
| Approval scope requested | `controlled_local_simulation_rehearsal_only` |
| Created | No |
| `latest_candidate` changed | No |
| `latest_approved` changed | No |
| Source CSV changed | No |
| Simulation run | No |
| Deployment run | No |

Tim approved freezing the current validated local-live-test package set for controlled local simulation/rehearsal only. That approval does not approve hosted deployment, production, broad final draft-day use, source data mutation, private value changes, rankings changes, app wiring changes, or market/ADP private-value blending.

## Blocking Validation Failure

Validation stopped before writing the pinned manifest because this required data file contains a UTF-8 BOM:

```text
C:\NWR_SHARED_DATA\lane_exchange\model_value\veteran_private_values\20260620_003702_candidate\veteran_private_values_candidate.csv
```

The task required every pinned package to pass no-BOM validation, and the hard guardrails forbid altering source CSV data. Because of that, Master did not create the pinned snapshot.

An empty partial folder was created before the BOM check failed and was removed:

```text
C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1
```

## Required Package Set

These are the intended packages and row counts from the validated Phase D state:

| Package | Rows | Pin status |
| --- | ---: | --- |
| `rookie_hq/frozen_rookie_mock_input` | 54 | Not pinned |
| `drop_decision/dropped_veterans` | 12 | Not pinned |
| `drop_decision/unavailable_players` | 23 | Not pinned |
| `league_state/pick_order` | 50 | Not pinned |
| `league_state/nwr_picks` | 5 | Not pinned |
| `model_value/veteran_private_values` | 232 | BLOCKED by BOM in required data file |

Known validated Phase D state remains:

- Pick order is unique.
- Pick `1.06` owner is `Dirt Devils`.
- Current pick is `1.01`, owner `Golden Boy Productions`.
- Next NWR pick is `1.03`.
- NWR picks are `3`, `4`, `14`, `18`, `44`.
- Available pool is 66.
- Brian Thomas and Alec Pierce join correctly and are available.
- No ADP/market/private-value leakage was found in Phase D.
- `stats_context` packages remain display-only `latest_candidate`, not approved private value.

## Caveats

- `rookie_hq/frozen_rookie_mock_input` remains approved only for local live-test scope unless Tim/Master grants final draft-day approval.
- `drop_decision/dropped_veterans` and `drop_decision/unavailable_players` are local-only exchange packages and do not reopen Drop Decision.
- `league_state/pick_order` and `league_state/nwr_picks` are Sleeper source-backed but still require final human/Master approval for final draft-day use.
- `model_value/veteran_private_values` remains the current private value input, but it cannot be included in a no-BOM pinned snapshot until a source-backed, no-BOM repair package is explicitly approved.
- `stats_context` is display-only candidate context and is not part of required simulation input.
- Outcome V1 and market_behavior packages remain absent/not required.

## Allowed Scope If Repaired Later

If a repaired no-BOM pinned snapshot is later created, its scope should remain:

```text
controlled_local_simulation_rehearsal_only
```

## Forbidden Uses

The pinned snapshot, if repaired later, must still forbid:

- hosted deployment
- production
- final draft-day use without explicit approval
- private value changes
- app wiring changes
- source data mutation
- market/ADP private-value blending
- rankings changes
- recommendations unless separately approved

## Exact Next Repair Prompt

```text
You are Master/Main HQ for Niners War Room.

Repair the pinned live-test snapshot blocker without altering existing source CSVs or latest_approved pointers.

Create a new local-only timestamped model_value/veteran_private_values package that is byte-identical in rows/columns/content to the current approved package except encoded as strict UTF-8 without BOM. Preserve row count 232, private-value scope, all caveats, approval limited to controlled local live-test/simulation rehearsal only, and no ADP/market/probability/hidden-sort leakage.

Do not change existing source CSVs. Do not alter latest_candidate or latest_approved unless explicitly approved in this prompt. Do not touch other lane worktrees. Validate SHA, row count, no BOM, headers, and allowed/forbidden uses. Then retry creating pinned snapshot 20260620_controlled_sim_v1.
```

## Master Verdict

RED for pinned snapshot creation because a required package failed the no-BOM validation gate.

GREEN for preserving safety: no source data, pointers, packages, other lane worktrees, deployments, simulations, or app wiring were changed.
