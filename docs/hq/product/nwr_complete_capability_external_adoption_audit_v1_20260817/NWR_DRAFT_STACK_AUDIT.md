# NWR Draft Stack Audit

## What exists

- Redraft Champion produces a 608-player governed QB/RB/WR/TE board for league-specific scoring, replacement methods and confidence.
- Redraft workspaces isolate profiles and persist local draft state.
- The practical mock implements a deterministic full snake draft, manual late K/DST and owner recommendations.
- The Redraft board can mark a player drafted and undo the last drafted ID.
- Sleeper adapters import league, scoring, draft and roster facts read-only.
- Legacy NWR draft-day services already demonstrate atomic runtime state, event logs, export/import/replay, backups, trade/pick history and undo.

## Gaps

- CPU picks currently follow NWR ranked availability with simple positional constraints, so mocks train against NWR rather than an opponent market model.
- There is no governed Redraft ADP snapshot or dispersion.
- Live Redraft state lacks explicit pick ownership/every-team rosters, event IDs, crash recovery receipts and comprehensive duplicate/stale mutation controls.
- Beat ADP, make-it-back, positional-run and tier-survival timing are absent.
- K/DST remain intentionally manual except for an optional streamer consensus view.

## Adopt/reuse decision

Keep NWR ranking and league-profile engines. Reconnect legacy event/recovery concepts. Adapt the MIT `zacharykirby` session architecture and the MIT `joewlos` historical availability concept. Build NWR-owned contracts and tests; no external model becomes authority.

## Acceptance gate

A 15-round owner draft must survive reload, reject duplicates, show correct snake owner/roster, undo exactly, preserve source hashes, operate without network/model access, and reproduce a seeded mock. CPU selection must be statistically based on ADP/history rather than NWR rank.
