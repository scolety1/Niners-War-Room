# Blocked Sidecar Rerun Report

Decision: `BLOCKED_NEEDS_DERIVATION_RUNNER`

## What Changed Since The Prior Builder

The prior `NO_ROW_LEVEL_SOURCE` blocker is resolved for review-only source admission. The repo now contains a tracked source admission receipt for:

- `player_stats_weekly`
- `player_stats_seasonal`

The raw player_stats source files remain local-only and untracked under the approved runner snapshot root.

## Why The Compact Sidecar Was Not Built

The sidecar builder needs an approved derivation path that reads the admitted local-only snapshot and emits a compact tracked review-only artifact. The existing approved runner, `scripts/run_nflverse_refresh_v0.ps1`, creates the local snapshot and then explicitly skips candidate generation by design.

No repo service or script currently provides the sidecar-specific compact derivation gate.

## Why Direct Raw Reads Were Not Used

The task requires using an approved runner/service if one exists. Reading the raw `C:\NWR_SHARED_DATA` snapshot directly inside this lane would bypass the missing derivation runner/gate.

## Current Result

- Sidecar artifact built: no.
- Sidecar rows created: 0.
- Receipt rows admitted: 2.
- Weekly source rows admitted: 76,804.
- Seasonal source rows admitted: 42,419.
- Quarantined fields used: no.
- Label truth promoted: no.
- Model/training/source-truth approvals granted: no.
