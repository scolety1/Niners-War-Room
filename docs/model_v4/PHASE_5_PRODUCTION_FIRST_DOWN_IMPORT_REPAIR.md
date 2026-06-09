# Model v4 Phase 5D Production And First-Down Import Repair

Generated: 2026-05-16

## Purpose

This phase repairs confirmed production and first-down evidence gaps by making the v4 review-only preview use structured nflverse production reports generated from the full v4 truth set. It does not change formulas, does not invent missing data, and keeps Model v4 review-only.

Detailed CSV: `docs/model_v4/PHASE_5_PRODUCTION_FIRST_DOWN_IMPORT_REPAIR.csv`

## Repair Summary

- Truth-set players reviewed: 80
- Players with covered production and first-down evidence after repair: 69
- Players still missing production/first-down evidence: 11
- Players repaired from the old source-scope/import-filter gap: 34
- Current v4 preview outputs regenerated under `local_exports/model_v4/review_only_latest`.
- Current v4 source reports regenerated under `local_exports/model_v4/source_reports`.

## Repair Status Counts

| status | players |
| --- | ---: |
| covered_from_structured_nflverse | 35 |
| missing_expected_source_season_gap | 10 |
| missing_identity_alias_review_needed | 1 |
| repaired_from_v4_source_scope_patch | 34 |

## Imported Production Fields

Sourced rows now carry the production and first-down fields required by Phase 5D into the v4 calculation row and receipt layer:

- passing yards, passing TDs, interceptions
- rushing attempts, rushing yards, rushing TDs
- targets, receptions, receiving yards, receiving TDs
- rushing first downs and receiving first downs
- fumbles lost when present in nflverse player stats

Rows are marked `imported_real_data` only when sourced from the structured nflverse player stats reports. Missing incoming-player rows remain missing/review rather than being treated as zero production.

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

## Remaining Missing Production/First-Down Cases

- Luther Burden
- Oronde Gadsden II
- Jayden Higgins
- Kaleb Johnson
- Ashton Jeanty
- Hollywood Brown
- Fernando Mendoza
- Jeremiyah Love
- Carnell Tate
- Jordyn Tyson
- Kenyon Sadiq

## Review-Only Guard

Model v4 remains review-only. This repair updates source mapping and evidence visibility only; it does not promote active rankings, unlock roster readiness, or alter scoring weights.
