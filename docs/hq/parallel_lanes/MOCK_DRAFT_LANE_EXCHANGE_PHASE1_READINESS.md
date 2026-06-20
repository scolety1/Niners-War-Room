# Mock Draft Lane Exchange Phase 1 Readiness

## Purpose

Phase 1 adds a read-only Mock Draft validator for the NWR Lane Exchange V0 hub.
It prepares Mock Draft to validate draft-day input packages through Master-owned
exchange manifests without reading another lane worktree, copying real data, or
creating local Mock Draft snapshots.

## Source Contract

Master contract:

```text
C:\NWR\Niners-War-Room\docs\hq\parallel_lanes\NWR_LANE_EXCHANGE_V0_CONTRACT.md
```

Local-only exchange hub:

```text
C:\NWR_SHARED_DATA\lane_exchange\
```

Local-only registry:

```text
C:\NWR_SHARED_DATA\lane_exchange_registry\lane_exchange_v0_registry.json
```

The hub and registry are local-only operational inputs. They must not be copied
into Mock Draft or committed to Git.

## Required Packages

Mock Draft fails closed unless these packages have valid `latest_approved.json`
manifests:

- `rookie_hq/frozen_rookie_mock_input`
- `drop_decision/dropped_veterans`
- `drop_decision/unavailable_players`
- `league_state/pick_order`
- `league_state/nwr_picks`
- `model_value/veteran_private_values`

The validator never accepts `latest_candidate.json` for draft decisions.

## Optional Market Package

`market_behavior/display_only_market_context` is optional for minimum manual
draft mode. If present, it must be display-only and limited to opponent behavior,
availability, and likely pick timing.

ADP/market context must never become NWR private value, ranking, hidden sort key,
probability, band, promoted artifact, or app wiring.

## Validator Behavior

The validator:

- reads the local registry
- resolves package paths only under `C:\NWR_SHARED_DATA\lane_exchange\`
- checks `latest_approved.json` only
- validates required manifest fields
- requires `approval_status: approved`
- validates `approved_for`, `allowed_use`, and `forbidden_use`
- verifies data-file SHA256
- verifies row counts for CSV and supported JSON shapes
- rejects missing or malformed registry/manifests
- rejects unapproved packages
- rejects hash or row-count mismatches
- rejects private/market contamination
- rejects data or manifest paths outside the exchange hub
- writes no files and runs no simulations

## Current Local Status

At implementation time, the local exchange hub contained only its README and the
registry. Required package snapshots were not present. That means real exchange
draft readiness is expected to be RED until producer lanes publish approved
`latest_approved.json` packages.

This RED readiness is a safe fail-closed result, not a simulator failure.

## Commands

Read-only local check:

```powershell
$uv = "C:\Users\codex-agent\.local\bin\uv.exe"
& $uv run --locked python -B scripts/mock_draft_lane_exchange_readiness_check.py
```

Focused validation:

```powershell
python -m pytest tests/test_mock_draft_lane_exchange_validator.py
python -m ruff check src/services/mock_draft_lane_exchange_validator.py scripts/mock_draft_lane_exchange_readiness_check.py tests/test_mock_draft_lane_exchange_validator.py
```

Use an already-available interpreter with pytest/Ruff. Do not install packages,
run `uv sync`, change `uv.lock`, or write exchange snapshots from Mock Draft.

## Readiness Verdict Rules

- GREEN: all required packages are approved, hash-valid, row-count-valid,
  allowed for Mock Draft read-only/manual review, and free of contamination.
- YELLOW: optional market context is missing but all required packages are
  valid.
- RED: any required package, registry, manifest, hash, row count, approval, use
  label, path boundary, or contamination check fails.

No simulation approval is implied by this validator.
