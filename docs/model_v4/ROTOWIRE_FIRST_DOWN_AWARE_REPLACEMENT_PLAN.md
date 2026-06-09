# RotoWire First-Down-Aware Replacement And VORP Plan

Date: 2026-05-17

Status: review-only implemented, pending external audit

## Why This Exists

The RotoWire evidence spine now supports a stats-first review layer,
replacement baselines, VORP review rows, and a dynasty candidate layer. The
previous replacement/VORP output was useful for review, but it was not final
for this league because the replacement baseline was based on 2025 LVE-style
production without rushing/receiving first-down points. The current review-only
implementation now adds estimated rushing/receiving first-down points where
direct current first-down fields are unavailable.

League scoring gives:

- rushing first down: 0.4
- receiving first down: 0.4
- passing first downs: not included

First-down scoring is therefore a core value signal for RB, WR, and TE and a
format-specific suppression factor for QB.

## Current Evidence Check

The current RotoWire player-stat exports do not expose direct rushing or
receiving first-down fields in the cleaned player-stat table. Current searched
field names did not show sourced direct fields such as `rush_first_downs`,
`receiving_first_downs`, `first_downs`, `fd`, or `1d`.

That means RotoWire role, target, route, red-zone, and alignment evidence can
support first-down estimation, but it must not be labeled as direct
first-down data.

Direct historical rushing/receiving first-down evidence remains source-safe
when it comes from the existing nflverse production import path.

Current local nflverse first-down coverage in the Model v4 source report is
2022-2024. The 2025 RotoWire player-stat exports can be paired with those
historical rates for estimation, but that 2025 first-down layer would be
estimated, not direct.

## Required Source Status Rules

| Evidence type | Allowed label | Notes |
| --- | --- | --- |
| Direct nflverse rushing first downs | imported_real_data | May enter historical scoring and receipts. |
| Direct nflverse receiving first downs | imported_real_data | May enter historical scoring and receipts. |
| RotoWire target, route, snap, red-zone evidence | imported_real_data | Role evidence only; not direct first-down data. |
| Estimated rushing first downs | estimated_from_history | Uses sourced carries plus historical player/position rates. |
| Estimated receiving first downs | estimated_from_history | Uses sourced targets/receptions/routes plus historical player/position rates. |
| Unsourced or hand-entered first downs | rejected | Cannot enter model value. |

No estimated first-down field may be displayed or stored as direct evidence.

## Target Architecture

1. Build a player-season direct first-down table from nflverse.
2. Join the table to RotoWire player-season identity rows.
3. Recompute historical LVE fantasy points:
   - base scoring from passing/rushing/receiving/fumbles
   - plus `0.4 * (rushing_first_downs + receiving_first_downs)`
4. Recompute replacement baselines by position using LVE plus first-down
   scoring.
5. Recompute VORP review rows using first-down-aware baselines.
6. For missing direct first downs, estimate only in a clearly labeled preview
   lane:
   - player recent rushing first-down rate per carry
   - player recent receiving first-down rate per target or reception
   - position fallback rate when player history is insufficient
7. Add receipt rows showing:
   - direct first downs used
   - estimated first downs used
   - estimation basis
   - confidence impact
8. Add warning rows when the VORP score depends on estimated first downs.

## Baseline Formula Shape

Historical player points:

```text
lve_base_points
+ 0.4 * direct_rushing_first_downs
+ 0.4 * direct_receiving_first_downs
```

Estimated first-down points:

```text
estimated_rushing_first_downs =
  carries * player_or_position_recent_rush_fd_rate

estimated_receiving_first_downs =
  targets_or_receptions * player_or_position_recent_receiving_fd_rate
```

Estimated values must produce:

```text
source_status = estimated_from_history
confidence_impact = penalty
receipt_warning = first_down_projection_estimated_not_direct
```

## Tests Required Before Promotion

- Direct first-down fields from nflverse score at exactly 0.4.
- Estimated first downs are labeled `estimated_from_history`.
- Estimated first downs never appear as `imported_real_data`.
- Missing first-down evidence creates a warning, not a zero-production penalty.
- Replacement baselines change when first-down scoring is enabled.
- QB replacement remains suppressed because passing first downs are not scored.
- RotoWire route/snap evidence cannot be mistaken for direct first-down data.

## Current Limitation

The current VORP review rows are first-down-aware and valid for review, but
they are not final roster-decision evidence until the external audit accepts
the estimation approach.

Known limitation:

- direct first-down source history currently covers 2022-2024;
- 2025 first downs are estimated from history and labeled
  `estimated_from_history`;
- estimates remain review-only and may not be promoted as direct evidence.
