# Outcome V1 Lane Exchange Capability

## Scope

Outcome V1 now has a lane-local utility for the Lane Exchange V0 contract.
This is a validation and publication-safety layer only. It does not change the
Outcome model, approved Outcome heads, numeric display artifact, Rankings app
behavior, player-id visibility, sorting, ranking, or promoted artifacts.

## Contract And Registry Inputs

- Master contract:
  `C:\NWR\Niners-War-Room\docs\hq\parallel_lanes\NWR_LANE_EXCHANGE_V0_CONTRACT.md`
- Local-only registry:
  `C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json`
- Local-only hub:
  `C:\NWR_SHARED_DATA\lane_exchange\`

The hub and registry are local-only operational state. Exchange snapshots,
archives, generated data, and `C:\NWR_SHARED_DATA` contents must not be
committed to Git.

## Outcome Exchange Role

Registry lane id: `outcome_v1`

Owned package:

- `outcome_v1/outcome_display_snapshot`

Consumed packages:

- none by default

Outcome V1 may validate any explicitly requested `latest_approved` package by
manifest, hash, row count, approval status, and allowed-use label. It does not
infer approval from file presence.

## Publishing Gate

Outcome candidate publishing is blocked unless the registry explicitly gives
`outcome_v1` a `candidate_publish_allowed: true` or `publish_allowed: true`
flag. The current registry entry requires later explicit approval, so real
Outcome publication is fail-closed.

When publishing is allowed, the utility writes only an Outcome-owned candidate
snapshot under:

```text
C:\NWR_SHARED_DATA\lane_exchange\outcome_v1\outcome_display_snapshot\
```

It writes `latest_candidate.json` only. It does not write
`latest_approved.json`, promote artifacts, or approve itself.

## Read-Only Readiness Check

```powershell
.\.venv\Scripts\python.exe scripts\outcome_lane_exchange_readiness_check.py
```

Optional explicit approved-package validation:

```powershell
.\.venv\Scripts\python.exe scripts\outcome_lane_exchange_readiness_check.py `
  --package rookie_hq/frozen_rookie_mock_input `
  --required-use mock_draft_read_only_validation
```

The script does not publish data. It reports the Outcome role, owned packages,
consumed packages, current publish gate, and any explicitly requested
`latest_approved` validation results.

## Guardrails Preserved

- Approved Outcome heads remain limited to QB T12, RB T12, RB T24, WR T12,
  WR T24, WR T36, and TE T12.
- No Top 6 or unapproved heads are added.
- No Outcome sorting or ranking behavior is introduced.
- No hidden sort keys, `rank_delta`, or `ranking_delta` artifact fields are
  added.
- `player_id` remains the join key and stays hidden from visible/raw advanced
  tables.
- No app page imports this exchange utility.
- No real exchange snapshots or `C:\NWR_SHARED_DATA` files are committed.

## Validation Intent

Focused tests use temporary fake registries, temporary fake hubs, and temporary
fake CSV snapshots only. They prove the real registry shape blocks publishing,
approved manifests are validated read-only, non-approved or mismatched manifests
fail closed, and an explicitly allowed fake registry can publish only an
Outcome-owned candidate snapshot.
