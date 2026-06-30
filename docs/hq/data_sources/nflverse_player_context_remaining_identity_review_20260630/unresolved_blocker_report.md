# Unresolved Blocker Report

## Blocker Counts

| Blocker Category | Count |
| --- | ---: |
| `NEEDS_NWR_BINDING_REVIEW` | 2 |
| `NO_APPROVED_NFLVERSE_CANDIDATE` | 7 |
| `TEAM_TIMELINE_OR_COLLISION_REVIEW` | 4 |


## Blocker Meanings

- `NEEDS_NWR_BINDING_REVIEW`: human-approved NFLVerse/GSIS identity exists, but NWR/Sleeper binding was not safe enough to apply.
- `TEAM_TIMELINE_OR_COLLISION_REVIEW`: possible identity candidate exists, but team/timeline, same-name/collision, or missing NWR/Sleeper binding evidence remains unresolved.
- `NO_APPROVED_NFLVERSE_CANDIDATE`: no exact approved local NFLVerse/GSIS candidate is present in tracked identity-hardening evidence.

DynastyProcess, market, ADP, vendor/private data, Gmail, and `ff_rankings` are not identity truth for this gate.

No blocker category authorizes app exposure, artifact rebuild, model use, source-truth use, rank logic, hidden sort, trade value, or pick value.
