# Roster Field and League Context Review

## Field contract

The source packet's 34-field roster snapshot contract is documentation only. No schema, validator, service, data pack, or application consumer implements it.

The tracked synthetic roster currently has 13 columns: league/team and display labels, season and snapshot date, canonical player/display fields, position, `roster_status`, official rank, and source. It lacks governed fields required for roster slot, starter/bench state, taxi, IR, exact identity resolution, validation/lifecycle state, integrity, source-as-of time, hydration start/finish, retained-data status, and last-known-good references. `roster_status` is not a substitute for the documented closed enums.

No missing field was repaired or reinterpreted.

## League context

The canonical human-readable authority documents 10 teams; 1 QB, 2 RB, 3 WR, 1 TE, two WR/RB/TE flex, 1 kicker, and 14 bench; two regular-season IR and zero preseason IR; non-PPR, no TE premium; and no defense beginning in 2024.

The runtime YAML carries team count, roster limits, regular-season IR, kicker inclusion, draft rules, and keeper/declaration context, but it does not type the full lineup, two flex slots and eligibility, bench, phase-specific IR, scoring labels, DST treatment, taxi policy, or tracker draft-pick treatment. Taxi authority remains unknown.

The current `STARTER_FORMAT` constant contains only QB/RB/WR/TE counts. It omits both flex slots and kicker and is not connected to the canonical rules lock. It is not authorized as hydration or lineup truth.

Only exact raw roster and position counts plus visible missing/unresolved counts can be considered for a future initial slice after identity exists. Starter, flex, bench, taxi, IR capacity, replacement, and lineup-gap claims remain blocked.
