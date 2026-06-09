# Project Gold Sprint 4 / Phase 26: Source Gap Reconciliation

Last reviewed: 2026-05-14

## Status

Source gaps are now reconciled by decision scope. This is an audit and UI
clarity layer only. It does not fabricate projections, injuries, route data,
market values, or player scores.

## What Changed

Coverage rows now include:

- `source_gap_scope`
- `source_gap_summary`

Player rows now include:

- `source_gap_scopes`
- `source_gap_summary`

Summary rows now include `source_gap_scope` rollups.

## Scope Labels

| source_gap_scope | meaning |
|---|---|
| `none` | safe for roster review |
| `roster-critical` | blocks roster review until source evidence is fixed |
| `draft-critical` | not enough for draft |
| `final-money-critical` | blocks final-money confidence |
| `optional accepted` | accepted optional gap; confidence penalty retained |
| `future paid-data candidate` | needs paid/free source upgrade |

Accepted optional gaps continue to retain confidence penalties.

## Current Active Coverage Snapshot

Active data pack:

`local_exports/data_packs/lve_sleeper_20260505_pdf_ranks`

Active model source:

`local_exports/active_veteran_model_public_sources`

Current bucket-scope counts:

| source_gap_scope | bucket rows |
|---|---:|
| `none` | 915 |
| `optional accepted` | 477 |
| `final-money-critical` | 416 |
| `roster-critical` | 48 |

Current player-summary counts:

| source_gap_summary | players |
|---|---:|
| `blocks final-money confidence` | 208 |
| `blocks roster review until source evidence is fixed` | 24 |

Accepted optional gap penalty total:

`1419.0`

This confirms accepted gaps remain visible and still reduce confidence.

## External Audit Reconciliation

The external audit was directionally right that global source gaps remain, but
the app now separates those gaps by decision scope:

- Niners/current-roster critical source gaps are `roster-critical`.
- Non-Niners/global critical gaps are `final-money-critical`.
- Draft pool critical gaps can be marked `draft-critical` once draftable-player
  rows exist in source coverage.
- Optional projection, injury, and market gaps are either accepted with retained
  confidence penalty or marked as future paid/free source-upgrade candidates.

## Verification

Focused test:

- `tests/test_source_coverage_audit_service.py`

Result:

- `14 passed`
