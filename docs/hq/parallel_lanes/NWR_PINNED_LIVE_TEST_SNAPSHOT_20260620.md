# NWR Pinned Live-Test Snapshot - 2026-06-20

Owner: Master/Main HQ

Status: GREEN. The pinned local live-test snapshot was created for controlled local simulation/rehearsal only.

## Pinned Snapshot

| Field | Value |
| --- | --- |
| Snapshot label | `20260620_controlled_sim_v1` |
| Pinned snapshot path | `C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1` |
| Manifest | `C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1\pinned_snapshot_manifest.json` |
| README | `C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1\PINNED_SNAPSHOT_README.md` |
| Approval scope | `controlled_local_simulation_rehearsal_only` |
| Created by | Master/Main HQ |
| `latest_candidate` changed | No |
| `latest_approved` changed during pin creation | No |
| Source CSV changed | No |
| Simulation run | No |
| Deployment run | No |

Tim approved freezing the current validated local-live-test package set for controlled local simulation/rehearsal only. This does not approve hosted deployment, production, broad final draft-day use, source data mutation, private value changes, rankings changes, app wiring changes, or market/ADP private-value blending.

## Pinned Packages

| Package | Rows | SHA256 |
| --- | ---: | --- |
| `rookie_hq/frozen_rookie_mock_input` | 54 | `ba6166b730a6c6f57ff0f51489ee8ce32c75d522b3c728a5b3bc6dbd0a969858` |
| `drop_decision/dropped_veterans` | 12 | `31cdb1030752962a2ab2536b91b0ca7c7116ae5843cf06599d428d698cf968a5` |
| `drop_decision/unavailable_players` | 23 | `647775ff34a7c55ddb3d0507d0de4c7aa3f9ff342f027b24d844e0a706ab69b4` |
| `league_state/pick_order` | 50 | `56b332a9716c0cfcfabe3d84f55199a981597668a3a18bcd0d3fc35e0b5de77c` |
| `league_state/nwr_picks` | 5 | `cdc0985c89b4f55fd86178d7104ca43373ccf466910f939752d383a85b577fa5` |
| `model_value/veteran_private_values` | 232 | `67fbff9911d4b6796a4027227978c55c780da11f4e6c54f3c4cf9841eed59310` |

The pinned `model_value/veteran_private_values` package uses the repaired no-BOM package:

```text
C:\NWR_SHARED_DATA\lane_exchange\model_value\veteran_private_values\20260620_1535_nobom_live_test
```

## Validation Results

- All six required `latest_approved` pointers exist.
- All target manifests parse as strict UTF-8 without BOM.
- All data files exist.
- All data files parse as strict UTF-8 without BOM.
- SHA256 validates for every pinned data file.
- Row count validates for every pinned data file.
- Each required manifest has `approval_status: approved`.
- Each required manifest allows local live-test, read-only validation, or controlled local simulation/rehearsal scope.
- Required simulation inputs do not use `latest_candidate`.
- No required package has ADP/market/private-value leakage beyond approved NWR private value fields in `model_value/veteran_private_values`.
- `model_value/veteran_private_values` has `contains_private_value: true`, `contains_market_data: false`, and `contains_adp: false`.
- No shared-data files are tracked by Git.

## Validated Live-Test State

- Mock Draft Phase D final-readiness non-simulation check: GREEN.
- Pick order is unique.
- Pick `1.06` owner is `Dirt Devils`.
- Current pick is `1.01`, owner `Golden Boy Productions`.
- Next NWR pick is `1.03`.
- NWR picks are `3`, `4`, `14`, `18`, `44`.
- Available pool is 66.
- Brian Thomas and Alec Pierce join correctly and are available.
- No ADP/market/private-value leakage was found in required package headers/manifests.
- `stats_context` packages remain display-only `latest_candidate`, not approved private value.

## Caveats

- This is not final draft-day approval.
- This is not hosted deployment approval.
- This is not production approval.
- This is not app wiring approval.
- This is not approval to change private values, rankings, formulas, source data, hidden sorts, probabilities, bands, or promoted artifacts.
- `rookie_hq/frozen_rookie_mock_input` remains approved only for local live-test/simulation rehearsal scope unless Tim/Master grants final draft-day approval.
- `drop_decision/dropped_veterans` and `drop_decision/unavailable_players` are local-only exchange packages and do not reopen Drop Decision.
- `league_state/pick_order` and `league_state/nwr_picks` are Sleeper source-backed but still require final human/Master approval for final draft-day use.
- `stats_context` remains display-only candidate context and is not part of required simulation input.
- Outcome V1 and market_behavior packages remain absent/not required.

## Allowed Scope

```text
controlled_local_simulation_rehearsal_only
```

## Forbidden Uses

- hosted deployment
- production
- final draft-day use without explicit approval
- private value changes
- app wiring changes
- source data mutation
- market/ADP private-value blending
- rankings changes
- recommendations unless separately approved

## Exact Next Mock Draft Controlled Simulation Prompt

```text
You are Mock Draft HQ for Niners War Room.

Repo:
C:\NWR\Niners-War-Room-mock-draft

Branch:
work/mock-draft-simulator

Task:
Run a controlled local simulation/rehearsal using the pinned live-test snapshot only.

Pinned snapshot:
C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1\pinned_snapshot_manifest.json

Explicit approval:
Tim/Master approves controlled local simulation/rehearsal only against this pinned snapshot.

This is not final draft-day approval, hosted deployment, production approval, recommendation approval beyond the explicit rehearsal scope, app wiring approval, or source-data/private-value/ranking change approval.

Hard guardrails:
Do not alter source packages. Do not update latest_candidate. Do not update latest_approved. Do not create or alter pinned snapshots. Do not deploy. Do not push. Do not touch Rookie, Drop Decision, Outcome, Deployment V2, Trading Lab, QA/Data Hygiene, or Master worktrees. Do not import ADP/market. Do not use stats_context as private value.

Use only the six required packages pinned in:
C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1\pinned_snapshot_manifest.json

Before simulation/rehearsal:
Validate pinned manifest, row counts, SHA256, no BOM, package allowed scope, pick order uniqueness, NWR picks, current pick 1.01, next NWR pick 1.03, available pool 66, Brian Thomas/Alec Pierce availability, and no ADP/market leakage.

Allowed:
Run the minimum controlled local rehearsal/simulation path needed to verify operator workflow and state behavior. Write local-only report under:
C:\NWR_SHARED_DATA\live_test_reports\mock_draft_controlled_sim\

Return:
Branch/head/status, pinned snapshot validation, command(s) run, whether simulation/rehearsal path was entered, generated outputs if any, warnings/caveats, local report path, repo status, and GREEN/YELLOW/RED verdict.
```

## Master Verdict

GREEN for pinned local live-test snapshot creation.

YELLOW-HOLD for final draft-day use until Tim/Master separately grants final draft-day approval.
