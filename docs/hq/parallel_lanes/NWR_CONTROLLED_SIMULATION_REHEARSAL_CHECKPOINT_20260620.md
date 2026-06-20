# NWR Controlled Simulation Rehearsal Checkpoint - 2026-06-20

Owner: Master/Main HQ

Status: GREEN for controlled local simulation/rehearsal. YELLOW-HOLD for final draft-day use.

## Scope

This checkpoint records one controlled local Mock Draft simulation/rehearsal run against the pinned live-test snapshot.

This is not final draft-day approval, hosted deployment, production approval, app wiring approval, private-value change approval, ranking change approval, source-data mutation approval, or final recommendation/advice approval.

## Pinned Snapshot

```text
C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1\pinned_snapshot_manifest.json
```

Snapshot scope:

```text
controlled_local_simulation_rehearsal_only
```

Required pinned packages:

| Package | Rows | SHA256 |
| --- | ---: | --- |
| `rookie_hq/frozen_rookie_mock_input` | 54 | `ba6166b730a6c6f57ff0f51489ee8ce32c75d522b3c728a5b3bc6dbd0a969858` |
| `drop_decision/dropped_veterans` | 12 | `31cdb1030752962a2ab2536b91b0ca7c7116ae5843cf06599d428d698cf968a5` |
| `drop_decision/unavailable_players` | 23 | `647775ff34a7c55ddb3d0507d0de4c7aa3f9ff342f027b24d844e0a706ab69b4` |
| `league_state/pick_order` | 50 | `56b332a9716c0cfcfabe3d84f55199a981597668a3a18bcd0d3fc35e0b5de77c` |
| `league_state/nwr_picks` | 5 | `cdc0985c89b4f55fd86178d7104ca43373ccf466910f939752d383a85b577fa5` |
| `model_value/veteran_private_values` | 232 | `67fbff9911d4b6796a4027227978c55c780da11f4e6c54f3c4cf9841eed59310` |

## Simulation Report

```text
C:\NWR_SHARED_DATA\live_test_reports\mock_draft_controlled_sim\controlled_sim_pinned_snapshot_20260620_155537.md
```

## Command / Script

The run used an inline pinned-snapshot runner from the Mock Draft lane, using:

- `src.services.draft_state_service`
- `src.services.mock_draft_simulator_service.build_review_mock_draft_scenario`

No repo files were edited. The only output was the local-only report above.

## Seed

No seed was used. The run was deterministic because no random source or ADP/market timing rows were used. The service selected by fallback board order for review only.

## Validated Start State

| Check | Result |
| --- | --- |
| Mock Draft branch | `work/mock-draft-simulator` |
| Mock Draft HEAD | `e5a251171c1398b4e5b7bd665a4336597b45ac04` |
| Mock Draft status before/after | clean |
| Pick order | 50 rows, unique `overall_pick` |
| Pick `1.06` owner | `Dirt Devils` |
| Current pick | `1.01`, `Golden Boy Productions` |
| Next NWR pick | `1.03` |
| NWR picks | `3`, `4`, `14`, `18`, `44` |
| Available pool | 66 |
| Brian Thomas | joins and available |
| Alec Pierce | joins and available |
| ADP/market package | absent/not used |
| `stats_context` | not used as private value |

## Controlled Simulation Output

CONTROLLED SIMULATION OUTPUT ONLY - NOT FINAL DRAFT ADVICE.

The single rehearsal advanced from pick `1.01` to the next NWR pick at `1.03`.

| Pick | Owner | Simulated player | Position | Selection path |
| --- | --- | --- | --- | --- |
| `1.01` | `Golden Boy Productions` | `Jeremiyah Love` | RB | fallback board order |
| `1.02` | `WhoDat?` | `Makai Lemon` | WR | fallback board order |

At `1.03`, the report showed display-only availability rows. Those rows are not final advice or final recommendations.

## Safety Results

- Pinned manifest validated.
- Required package rows and hashes validated.
- No UTF-8 BOM found in required pinned inputs.
- No duplicate pick IDs found.
- No unavailable-player conflict found.
- No veteran private value join gaps found.
- Quality score firewall passed.
- No ADP/market package was used.
- `stats_context` was not used as private value.
- No `latest_candidate` changed.
- No `latest_approved` changed.
- Pinned snapshot was not changed.
- No source package was changed.
- No app wiring changed.
- No deployment ran.
- No commit or push occurred in Mock Draft.

## Blocked Uses

Still blocked unless Tim/Master explicitly approves later:

- final draft-day use
- final recommendations/final draft advice
- generated pick path beyond controlled rehearsal scope
- hosted deployment
- production approval
- production app wiring
- private value changes
- rankings changes
- source data mutation
- ADP/market as NWR private value
- `stats_context` as private value

## Remaining Gates

- Tim/Master final manual draft-day approval.
- Explicit decision whether controlled simulation output may inform draft decisions.
- Explicit decision whether recommendation output remains blocked or receives a narrow approval.
- Final clean Mock Draft status immediately before any live use.
- Confirmation that pinned snapshot remains unchanged.

## Master Verdict

GREEN for controlled local simulation/rehearsal against the pinned snapshot.

YELLOW-HOLD for final draft-day use and final advice until explicit Tim/Master approval.
