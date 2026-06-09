# Model v4 Phase 5B Missing Evidence Root Cause Audit

Generated: 2026-05-16

## Purpose

This audit explains why the current v4 preview has missing production, first-down scoring fit, usage/opportunity, snap/proxy role, and projection evidence. It does not invent data, does not change formulas, and keeps v4 review-only.

Detailed CSV: `docs/model_v4/PHASE_5_MISSING_EVIDENCE_ROOT_CAUSE.csv`

## Executive Summary

- Current v4 review-only latest missing target evidence rows: 222
  - production: 45
  - first-down scoring fit: 45
  - usage/opportunity: 45
  - snap/proxy role: 45
  - projection: 42
- Phase 5B source-scope rerun missing target evidence rows: 86
  - production: 11
  - first-down scoring fit: 11
  - usage/opportunity: 11
  - snap/proxy role: 11
  - projection: 42

The largest confirmed root cause is an import-filter scope bug: the v4 preview was using v3 source reports generated for the older 40-player truth set while the v4 truth set has 80 players. Rerunning production, usage, and snap imports against the 80-player v4 truth set reduces missing production/first-down/usage/snap rows from 45 each to 11 each.

Projection gaps do not improve from the source-scope rerun because the projection source is still the older 40-player manual export. Projection repair needs a separate expanded projection source or a new public/structured projection import.

## Root Cause Counts

| root cause | rows |
| --- | ---: |
| expected rookie/incoming-player gap | 25 |
| identity mapping failure | 4 |
| import filter excluded player | 171 |
| source season missing | 22 |

## Root Cause By Bucket

| root cause | production | first-down scoring fit | usage/opportunity | snap/proxy role | projection |
| --- | ---: | ---: | ---: | ---: | ---: |
| expected rookie/incoming-player gap | 5 | 5 | 5 | 5 | 5 |
| identity mapping failure | 1 | 1 | 1 | 1 | 0 |
| import filter excluded player | 34 | 34 | 34 | 34 | 35 |
| source season missing | 5 | 5 | 5 | 5 | 2 |

## Phase 5B Source-Scope Rerun

Scratch source reports were generated under `local_exports/model_v4/phase5b_source_reports`. These reports are review-only and do not overwrite active rankings.

| source | truth-set players | matched | missing | notes |
| --- | ---: | ---: | ---: | --- |
| nflverse production | 80 | 69 | 11 | requested seasons 2022, 2023, 2024 |
| play-by-play derived usage | 80 | 69 | 11 | requested seasons 2022, 2023, 2024 |
| snap share | 80 | 69 | 11 | identity warnings 110 |

Scratch v4 preview generated with those source reports: `local_exports/model_v4/phase5b_preview_scope_test`.

## Confirmed Findings

### 1. Import Filter Excluded Player

This is confirmed for production, first-down scoring fit, usage/opportunity, and snap/proxy role rows that become covered when the source reports are rerun against the full 80-player v4 truth set. This is the main Phase 5B patchable issue.

Action: regenerate official v4 review-only preview inputs from `local_exports/model_v4/phase5b_source_reports` after reviewing this audit. Do not promote to active rankings.

### 2. Source Season Missing

Year-one bridge players such as Luther Burden, Kaleb Johnson, Jayden Higgins, Oronde Gadsden II, and Ashton Jeanty still have no nflverse production/usage/snap rows after the 80-player rerun because local source seasons are 2022-2024. If they just completed their first NFL season, this requires newer source-season data rather than formula tuning.

Brandon Aiyuk and Keenan Allen also have projection source rows but no usable offensive projection stat fields, so their projection bucket remains missing by source availability.

### 3. Expected Rookie/Incoming-Player Gap

Incoming draft-room rookies have no NFL production/usage/snap history by design. They should use rookie/prospect lanes rather than veteran NFL evidence until data exists.

### 4. Identity Mapping Failure

Hollywood Brown remains missing after the 80-player source rerun. The likely root cause is an alias mismatch with nflverse naming, where the player is commonly represented as Marquise Brown. This needs an identity alias patch before source rows can be trusted.

### 5. Projection Source Scope Gap

Projection coverage remains missing for 42 players. Most of those are not in the older 40-player projection export. This is not fixed by nflverse production/usage/snap reruns. It needs an expanded projection source or explicit projection-unavailable confidence handling.

## Patch Status

| patch status | rows |
| --- | ---: |
| no_patch_expected | 25 |
| not_patched_identity_alias_needed | 4 |
| not_patched_projection_reexport_needed | 35 |
| not_patched_projection_source_needed | 2 |
| not_patched_source_update_needed | 20 |
| patched_in_phase5b_scratch_preview | 136 |

No formulas were changed. No missing data was invented. Active rankings were not overwritten.

## Exact Next Patches

1. Regenerate the official v4 review-only preview from the Phase 5B source reports, or update the v4 preview engine/source build flow so it always creates production/usage/snap reports from the 80-player v4 truth set.
2. Add an identity alias review for Hollywood Brown / Marquise Brown before using his historical source rows.
3. Import newer nflverse seasons when available for year-one bridge players, or keep those players as review-only young bridge assets with missing NFL evidence.
4. Build or import an expanded projection source for the full v4 truth set; until then, keep projection gaps visible and confidence-penalized.
5. Re-run the v4 preview and movement audit after the above source repairs.

## Review-Only Guard

Model v4 remains review-only. This phase creates source-scope reports and a scratch preview only; it does not mark roster, draft, or final money decisions ready.
