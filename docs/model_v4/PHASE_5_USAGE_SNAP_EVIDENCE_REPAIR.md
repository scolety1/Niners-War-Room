# Model v4 Phase 5E Usage And Snap Evidence Repair

Generated: 2026-05-16

## Purpose

This phase repairs confirmed usage and snap evidence gaps using derived nflverse play-by-play usage and official nflverse snap-count imports. It explicitly preserves that snap share is a proxy role signal, not route participation, and Model v4 remains review-only.

Detailed CSV: `docs/model_v4/PHASE_5_USAGE_SNAP_EVIDENCE_REPAIR.csv`

## Repair Summary

- Truth-set players reviewed: 80
- Players with covered usage and snap evidence after repair: 70
- Players still missing usage/snap evidence: 10
- Route-unavailable warning rows emitted for usage/snap components: 560
- Current v4 preview outputs regenerated under `local_exports/model_v4/review_only_latest`.
- Current v4 source reports regenerated under `local_exports/model_v4/source_reports`.

## Repair Status Counts

| status | players |
| --- | ---: |
| covered_from_structured_sources | 35 |
| missing_expected_source_season_gap | 10 |
| repaired_from_v4_source_scope_patch | 34 |
| repaired_identity_alias_mapping | 1 |

## Usage Fields Now Visible

- target share
- RB carry share
- RB target share
- weighted opportunities
- red-zone carries and targets
- goal-line carries and targets
- underlying targets, carries, and team denominators where sourced

## Snap/Proxy Role Fields Now Visible

- offensive snaps
- games with offensive snaps
- average snap share
- snap source status and identity warning where present

## Route Honesty Guard

The v4 preview still does not estimate or score route participation, routes run, TPRR, or YPRR from snap share. Covered usage and snap rows now emit explicit review warnings:

- `route_participation_unavailable`
- `routes_run_unavailable`
- `tprr_unavailable`
- `yprr_unavailable`
- `snap_share_proxy_only_not_route_participation`

## Example Players Repaired By Source-Scope Patch

- Breece Hall
- Saquon Barkley
- Jonathan Taylor
- Josh Jacobs
- James Cook
- Kenneth Walker III
- Derrick Henry
- Nico Collins
- Garrett Wilson
- Drake London
- Marvin Harrison Jr.
- Ladd McConkey

## Remaining Missing Usage/Snap Cases

- Luther Burden
- Oronde Gadsden II
- Jayden Higgins
- Kaleb Johnson
- Ashton Jeanty
- Fernando Mendoza
- Jeremiyah Love
- Carnell Tate
- Jordyn Tyson
- Kenyon Sadiq

## Identity Alias Repair

Hollywood Brown now maps to Marquise Brown for structured nflverse production-derived usage and snap source reports. The snap rows still retain the PFR identity-map warning where the PFR ID is not present in the local identity map.

## Review-Only Guard

Model v4 remains review-only. This phase repairs source mapping, evidence visibility, and warnings only; it does not promote active rankings, unlock roster readiness, or alter scoring weights.
