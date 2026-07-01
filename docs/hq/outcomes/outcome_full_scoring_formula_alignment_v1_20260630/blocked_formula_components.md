# Blocked Formula Components

## Blocked or subtype-limited

| Component | Status | Reason |
| --- | --- | --- |
| Direct `return_tds` | Blocked | No direct audited NFLVerse field present. |
| Direct `special_tds` | Blocked | No separate audited field present apart from `special_teams_tds`. |
| Return-vs-special TD subtype parity | Blocked | `special_teams_tds` is composite; it can be counted once for point-total parity but cannot prove subtype. |
| Imported `fantasy_points` / `fantasy_points_ppr` | Blocked | Quarantined fields; cannot prove formula parity. |
| EPA/CPOE/share-style fields | Blocked | Quarantined and not scoring formula components. |
| Global zero rows | Blocked | Missing rows remain `Not enough information` until a zero-row completeness gate lands. |

## Not blocked for observed rows

Fumbles lost and return yards are no longer formula-level blockers if the future builder applies the composite sum rules exactly once per observed player-week.
