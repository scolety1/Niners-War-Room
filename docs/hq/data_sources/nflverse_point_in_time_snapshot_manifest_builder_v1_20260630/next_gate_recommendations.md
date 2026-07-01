# Next Gate Recommendations

## Recommended Next Step

Run a narrow source-specific snapshot collection gate before replay. Start with one of:

1. `schedules`: collect release/update timestamps, game IDs, week, game date, reschedule history, and anchor-relative availability.
2. `draft_picks`: collect draft event/publication timestamp and define post-draft-only anchors.
3. `weekly_rosters`: collect frozen season-week snapshots with extraction timestamp and no future-week survival backfill.

## Required Before Replay Approval

A future HQ gate must produce:

- source snapshot IDs;
- extraction timestamps;
- feature as-of/publication timestamps;
- prediction anchors;
- row counts by season/week/player and identity gate;
- missingness/censoring policy;
- leakage diagnostics;
- explicit exclusion of unresolved identity rows and future/post-outcome rows.

Do not run experiments or model training from this packet. This packet is substrate inventory only.
