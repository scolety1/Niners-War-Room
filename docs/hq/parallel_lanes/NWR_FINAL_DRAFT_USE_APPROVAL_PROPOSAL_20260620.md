# NWR Final Draft-Use Approval Proposal - 2026-06-20

Owner: Master/Main HQ

Status: Proposal only. This document does not grant final draft-day approval.

## Current State

The controlled local Mock Draft rehearsal against the pinned live-test snapshot is GREEN for the approved rehearsal scope. Final draft-day use remains YELLOW-HOLD until Tim/Master grants explicit approval.

Pinned snapshot:

```text
C:\NWR_SHARED_DATA\lane_exchange\pinned_live_snapshots\20260620_controlled_sim_v1\pinned_snapshot_manifest.json
```

Pinned snapshot scope:

```text
controlled_local_simulation_rehearsal_only
```

## Approval Items Required

Before NWR can move from controlled rehearsal to final draft-day use, Tim/Master must explicitly decide each item below.

| Approval item | Current status | Required decision |
| --- | --- | --- |
| Pinned snapshot use | GREEN for controlled rehearsal only | Approve or reject the pinned snapshot as the fixed source set for draft day. |
| Final manual draft-day use | YELLOW-HOLD | Approve or reject manual live use of Mock Draft using the pinned snapshot. |
| Controlled simulation output | YELLOW-HOLD | Decide whether rehearsal output may inform draft preparation, while remaining non-final advice. |
| Recommendations | BLOCKED | Decide whether recommendation paths stay blocked or receive a narrow, explicit approval. |
| Generated pick path | BLOCKED | Decide whether any generated pick workflow is allowed beyond controlled rehearsal. |
| Optional `stats_context` | Candidate/display-only only | Decide whether display-only stats may be viewed during draft prep; do not allow private value use. |
| Optional Outcome display | Absent/not required | Decide whether to keep Outcome optional or approve a display-only snapshot later. |
| Market/ADP context | Absent/not required | Decide whether any market/ADP context is allowed as display-only; never NWR private value. |

## Required Package Set

The current pinned package set is:

| Package | Rows | Status |
| --- | ---: | --- |
| `rookie_hq/frozen_rookie_mock_input` | 54 | Approved only for local live-test/rehearsal scope. |
| `drop_decision/dropped_veterans` | 12 | Approved only for local live-test/rehearsal scope. |
| `drop_decision/unavailable_players` | 23 | Approved only for local live-test/rehearsal scope. |
| `league_state/pick_order` | 50 | Sleeper-backed repair, approved only for local live-test/rehearsal scope. |
| `league_state/nwr_picks` | 5 | Approved only for local live-test/rehearsal scope. |
| `model_value/veteran_private_values` | 232 | Private value package, no-BOM repair, approved only for local live-test/rehearsal scope. |

## Current Safety Boundaries

Still blocked unless Tim/Master explicitly approves later:

- hosted deployment
- production approval
- production app wiring
- private value changes
- ranking changes
- model logic changes
- source data mutation
- ADP/market as NWR private value
- `stats_context` as private value
- final recommendations or final draft advice
- broad simulation or strategy comparison runs

## Recommended Approval Path

1. Confirm pinned snapshot remains unchanged and readable.
2. Confirm Mock Draft worktree is clean immediately before final use.
3. Review the controlled rehearsal report and caveats.
4. Approve or reject final manual draft-day use as a separate Tim/Master decision.
5. Keep recommendations and generated pick paths blocked unless a separate narrow prompt approves them.

## Master Verdict

GREEN for recording the proposal.

YELLOW-HOLD for final draft-day use until explicit Tim/Master approval.
