# Project Gold Sprint 4 / Phase 28: Route/Participation Data Gap Gate

## Summary

Phase 28 makes the largest remaining model weakness explicit: route participation and pass-game usage are still mostly proxy-driven in the free/public-data build. No paid data was added, no formulas were tuned, and rankings remain review-only.

## What Was Added

- A route/participation gap gate service that labels player rows as:
  - `imported_real_data`
  - `derived_proxy`
  - `missing_proxy`
  - `neutral_default`
- A Model Lab > Source Coverage section for the gate.
- A CSV exporter for audit packets.
- Tests for route/participation labels, Niners roster slicing, top-player slicing, RB receiving-role slicing, and report export.

## Generated Audit Packet

Path:

`local_exports/model_audits/sprint4_phase28_route_participation_gap_gate_20260514`

Files:

- `route_participation_gap_players.csv`
- `route_participation_gap_areas.csv`
- `route_participation_gap_summary.csv`
- `route_participation_gap_manifest.json`

## Active Model Findings

The active free/public model has route/participation gaps across every decision slice:

| Area | Status | Players | Gap Rows | Paid Data Material Rows |
|---|---:|---:|---:|---:|
| Niners roster | review | 24 | 24 | 9 |
| Top 50 overall | review | 50 | 50 | 50 |
| WR/TE top 30 | review | 60 | 60 | 30 |
| RB receiving-role players | review | 62 | 62 | 62 |

Overall labels:

| Status | Rows | Paid Data Material Rows |
|---|---:|---:|
| derived_proxy | 385 | 61 |
| missing_proxy | 648 | 52 |
| neutral_default | 6 | 1 |

## Interpretation

This confirms the external audit concern: the current public-data build can inspect production, age, identity, first-down scoring, and broad role proxies, but it does not yet have direct route participation for most pass catchers or RB receiving-role profiles. That means route-sensitive rankings should stay review-only until those gaps are either accepted as risk or improved with a paid/exported source.

## Paid Data Fields That Would Help Most

- routes run
- route share
- targets per route run
- yards per route run
- pass route participation
- RB route share

## Verification

Focused tests passed:

```text
21 passed
```

Full static check should remain the final validation step for the phase.
