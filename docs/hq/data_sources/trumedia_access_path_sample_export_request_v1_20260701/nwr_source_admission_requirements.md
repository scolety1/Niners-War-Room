# NWR Source Admission Requirements

TruMedia remains unadmitted until a separate source-admission lane receives rights-cleared evidence and passes these checks.

## Required Before Any Data Use

1. Written permission from TruMedia covering the exact evaluation purpose.
2. Product and data source identified: NFL Core, NFL Advanced Analytics, NFL API, data warehouse, or partner export.
3. Field-level rights matrix naming TruMedia-owned, third-party, and non-exportable fields.
4. Schema dictionary for each export table.
5. Stable identifiers for player, team, game, and play joins.
6. Coverage matrix by season, season type, week, position, and field family.
7. Explicit zero/missing semantics for each field.
8. As-of/export timestamp and correction/update policy.
9. License note covering local storage, derived artifacts, private research, retention, and deletion.
10. No credentials committed, printed, or stored in repo.

## Sample Export Minimum

The first sample export is enough for source admission if it includes:

- Full player-week rows for WR/TE/RB receiving and route usage across at least two recent regular seasons.
- Player-game rows for the same field families, if available.
- Player-play rows for at least 8 representative games with route/target/alignment/coverage/tracking fields.
- Identity crosswalk with GSIS, PFF if available, player name, team, position, and source-native IDs.
- Schema/data dictionary and license/use note.
- Explicit zero/missing semantics and export timestamp.

## Admission Outcomes

Possible NWR statuses:

- `REVIEW_ONLY_PENDING_RIGHTS`
- `REVIEW_ONLY_SCHEMA_RECEIVED`
- `BLOCKED_LICENSED_GAP`
- `BLOCKED_FIELD_SEMANTICS`
- `BLOCKED_ZERO_MISSING_SEMANTICS`
- `BLOCKED_LOCAL_STORAGE_RIGHTS`
- `SOURCE_ADMISSION_CANDIDATE_NOT_PRODUCTION`

No status in this packet approves production use.

## Hard Blocks

- No production formula changes.
- No model training or tuning.
- No app wiring.
- No rankings, tiers, hidden sort, recommendations, or source-truth changes.
- No route proxies from participation or snap data.
- No zero-fill unless the vendor explicitly returns numeric zero and documents semantics.
- No raw vendor data in git unless the license explicitly allows it.

## Future Validation Checklist

- Validate row counts by grain.
- Validate uniqueness keys by grain.
- Validate joins to NWR identity tables without silently dropping rows.
- Validate player/team/week coverage by position.
- Validate route denominator against snap participation.
- Validate targets and receiving yards against known box-score sources where rights allow.
- Validate red-zone flags against play context if available.
- Validate missingness and explicit zero behavior field-by-field.
- Produce compact receipts only, unless raw row storage is licensed.

