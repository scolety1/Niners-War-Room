# Truth Set Lab v3 Phase 1: Free Data Source Contract

Generated: 2026-05-15

## Status

Implementation contract only. No model scores, formulas, active rankings, readiness gates, or preview outputs were changed.

## Archived Research

Original DOCX reports were archived under:

`docs/codex/truth_set_lab_v3_source_research/raw_reports/`

Extracted text copies are stored in:

`docs/codex/truth_set_lab_v3_source_research/`

Reports reviewed:

- `NFL Data Evaluation.docx`
- `NFL Data Sources for Fantasy.docx`
- `NFL role_usage data sources.docx`

Primary contract output:

`local_exports/truth_set_lab/v3/reports/free_data_source_contract.csv`

## Core Finding

Truth Set Lab v3 should **not** ask agents to manually compile player production or role/usage rows. The reports agree that the cleanest free/public path is:

1. Import production and first downs directly from nflverse/nflreadr player stats.
2. Derive target share, RB opportunity share, red-zone usage, and goal-line usage from nflverse play-by-play.
3. Import snap share from nflverse/nflreadr snap counts.
4. Explicitly mark routes run, route participation, TPRR, and YPRR as unavailable from free public structured data unless a legal structured source is later provided.

That is a different strategy from the failed v1/v2 agent CSV approach. Agents can verify sources later, but Codex should build the actual local derivation from structured nflverse files.

## Source Contract Summary

| Model input | Classification | v3 action | Model policy |
|---|---|---|---|
| production | `free_direct` | Build native nflverse import | Real evidence after validation |
| rushing/receiving first downs | `free_direct` | Import from player stats; derive only if missing | Real evidence after validation |
| target share | `free_derivable` | Derive from play-by-play and/or validate player_stats field | Derived real evidence |
| snap share | `free_direct` | Import snap counts | Real role evidence, not route evidence |
| RB carry share | `free_derivable` | Derive from play-by-play | Derived real evidence |
| RB target share | `free_derivable` | Derive from play-by-play | Derived real evidence |
| weighted opportunities | `free_derivable` | Compute from carries and targets | Derived model feature; formula must be documented |
| red-zone usage | `free_derivable` | Derive with `yardline_100 <= 20` | Derived real evidence |
| goal-line usage | `free_derivable` | Derive with `yardline_100 <= 5` or explicit threshold | Derived real evidence |
| routes run | `paid_likely_required` | Do not build from agents | Unavailable free/public |
| route participation | `paid_likely_required` | Do not build from agents | Unavailable free/public |
| TPRR | `paid_likely_required` | Do not build from agents | Unavailable free/public because routes are unavailable |
| YPRR | `paid_likely_required` | Do not build from agents | Unavailable free/public because routes are unavailable |
| injuries | `free_direct` but limited | Keep as context/confidence only | Do not boost confidence from unsourced healthy rows |
| projections | `free_proxy_only` | Recompute LVE from raw stats when legally available | Preview/review only until a stronger source exists |

## Implementation Rules For Later v3 Phases

### Build Now

- Native nflverse production import.
- Native first-down import from player stats.
- Play-by-play derived usage:
  - target share
  - RB carry share
  - RB target share
  - weighted opportunities
  - red-zone carries/targets
  - goal-line carries/targets
  - short-yardage carries where play-by-play supports it
- Snap share import from snap counts.

### Label Honestly

- `routes_run`: `unavailable_free_public`
- `route_participation`: `unavailable_free_public`
- `targets_per_route_run`: `unavailable_free_public`
- `yards_per_route_run`: `unavailable_free_public`

Snap share and target share may become proxy context, but they must never be displayed as true route participation.

### Reject

- Manually compiled player production rows from agents.
- Role/usage CSVs with prose or question marks in numeric columns.
- Proprietary table data copied from sites with no legal export path.
- External fantasy-point projection totals that are not recomputed using LVE scoring.

## Remaining Weaknesses Without Paid Data

The free/public path can cover production, first downs, snap share, target share, RB opportunity share, red-zone usage, and goal-line usage. It cannot provide true route counts, route participation, TPRR, or YPRR in a clean legal structured way.

That does not make the project hopeless. It means v3 should lean on real production, first downs, snaps, targets, and play-by-play opportunity while carrying a visible route-data gap warning for pass catchers.

## Next Phase

Implement Truth Set Lab v3 Phase 2: Native nflverse Production Import.

The key objective is to eliminate the rejected agent production CSV from the trust path and replace it with structured nflverse player stats.

