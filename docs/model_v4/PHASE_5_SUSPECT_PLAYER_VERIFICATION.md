# Model v4 Phase 5C Suspect Player Verification

Generated: 2026-05-16

## Purpose

This report verifies the audit-named suspect players before any score or formula changes. It checks local IDs, Sleeper/nflverse bridge data, source rows, component rows, receipt rows, warnings, lifecycle, teams, and missing buckets.

Detailed CSV: `docs/model_v4/PHASE_5_SUSPECT_PLAYER_VERIFICATION.csv`

## Source Patch Applied

Phase 5C applied the confirmed source-scope patch from Phase 5B: `scripts/build_model_v4_preview.py` now rebuilds v4 source reports from the 80-player v4 truth set before writing review-only preview artifacts, and `model_v4_preview_engine_service` defaults to `local_exports/model_v4/source_reports`.

This corrected the false missing production/usage/snap rows for several established veteran controls. It did not alter formula weights or unlock readiness gates.

## Verification Summary

| classification | players |
| --- | ---: |
| source_gap_or_expected_missing | 7 |
| verified_clear | 6 |

| patch status | players |
| --- | ---: |
| fixed_by_phase5c_source_scope_patch | 6 |
| no_code_patch_needed | 7 |

## Player Results

| player | identity/source verdict | key notes | next action |
| --- | --- | --- | --- |
| Chase Brown | verified_clear | identity and source rows clear | Identity/source rows clear; remaining concern is formula/normalization audit if ranking still surprises. |
| Brock Bowers | verified_clear | identity and source rows clear | Identity/source rows clear; any concern is TE no-premium formula sanity, not identity. |
| Saquon Barkley | source_gap_or_expected_missing | no projection row in current projection source | Projection unavailable or outside current projection source; retain confidence penalty. |
| Derrick Henry | source_gap_or_expected_missing | no projection row in current projection source | Projection unavailable or outside current projection source; retain confidence penalty. |
| Jonathan Taylor | source_gap_or_expected_missing | no projection row in current projection source | Projection unavailable or outside current projection source; retain confidence penalty. |
| Davante Adams | source_gap_or_expected_missing | production source season 2024 team NYJ differs from current truth team LA; treated as historical context; usage source season 2024 team NYJ differs from current truth team LA; treated as historical context; snap source season 2024 team NYJ differs from current truth team LA; treated as historical context no projection row in current projection source | Projection unavailable or outside current projection source; retain confidence penalty. |
| Tyreek Hill | source_gap_or_expected_missing | no projection row in current projection source snap identity warning: pfr_id_not_in_identity_map | Projection unavailable or outside current projection source; retain confidence penalty. |
| Travis Kelce | source_gap_or_expected_missing | no projection row in current projection source | Projection unavailable or outside current projection source; retain confidence penalty. |
| Luther Burden | source_gap_or_expected_missing | No native nflverse player_stats rows matched this truth-set player in requested seasons. | Keep as review-only year-one bridge until newer NFL source season is available. Do not invent NFL production; import newer season data when available. |
| Brian Thomas Jr. | verified_clear | Sleeper/display bridge uses Brian Thomas while nflverse/source name uses Brian Thomas Jr. | No identity/source patch needed before normalization/formula review. |
| Malik Nabers | verified_clear | identity and source rows clear | No identity/source patch needed before normalization/formula review. |
| Jaxon Smith-Njigba | verified_clear | identity and source rows clear | No identity/source patch needed before normalization/formula review. |
| Puka Nacua | verified_clear | identity and source rows clear | No identity/source patch needed before normalization/formula review. |

## Confirmed Clears

The following players have no local identity/source bug after the Phase 5C source-scope patch:

Chase Brown, Brock Bowers, Brian Thomas Jr., Malik Nabers, Jaxon Smith-Njigba, Puka Nacua

## Remaining Source Gaps Or Expected Missing Evidence

These players still have source gaps that should remain review-only rather than be filled by assumptions:

Saquon Barkley, Derrick Henry, Jonathan Taylor, Davante Adams, Tyreek Hill, Travis Kelce, Luther Burden

## Issues Needing Review

These players still have explicit source/identity review flags after local verification:

None

## Key Conclusions

- Chase Brown source rows are internally consistent: same nflverse player ID across production, usage, and snap; no wrong identity join found.
- Brock Bowers source rows are internally consistent. The external audit claim that he has no NFL source context is not supported locally.
- Saquon Barkley, Derrick Henry, Jonathan Taylor, Davante Adams, Tyreek Hill, and Travis Kelce now have production, first-down, usage, and snap evidence after the v4 source-scope patch. Their remaining projection gaps are source availability problems, not proof they are low-value assets.
- Luther Burden remains a true source-season gap for NFL production/usage/snap because the local nflverse source seasons are 2022-2024. Keep him as review-only young bridge until newer source season data exists.
- Brian Thomas Jr. uses a display-name alias: Sleeper identity says Brian Thomas while the nflverse/stat bridge uses Brian Thomas Jr. The GSIS/source identity is consistent.
- Jaxon Smith-Njigba and Puka Nacua source rows are clear; any remaining concern is WR normalization/formula review, not identity.

## Review-Only Guard

Model v4 remains review-only. This phase verified source identity and patched source-scope generation only. No formula weights were changed and no readiness gate was unlocked.