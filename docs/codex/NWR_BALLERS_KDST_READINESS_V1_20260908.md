# Ballers K/DST Pipeline Readiness — V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 8.

## Finding: already substantially satisfied by existing + Section 7 work

The directive asks for a K schema (canonical player, source name, team, rank, position rank,
tier, ADP, bye, other fields), a DST schema (canonical team defense, source team, rank,
position rank, tier, ADP, bye, other fields), team-based DST matching, player-identity-based K
matching, never overwriting canonical NWR state, and a clear non-NWR-score label. All of this
already exists, real and tested:

- `_UDK_SUPPORTED_POSITIONS` (`redraft_draft_room_v1_service.py`) includes `K`/`DST` alongside
  QB/RB/WR/TE -- `parse_udk_position_csv`/`parse_udk_position_pdf` treat them as first-class
  positions through the identical rich schema (name, position, team, `byeWeek`, `rank`,
  `points`, `risk`, `upside`, `adpRaw`, `tier`, `outlook`, `dynastyLocked`) -- no separate,
  narrower K/DST-only schema.
- Matching rules already real and tested (from a prior session, "post-draft overnight,
  section 15"): `_match_adp_player` matches DST by **team only** (a DST row's `Name` cell text
  is never used for identity); K matches by player identity, same as any skill position.
- Storage is fully additive/separate (`udk_provider_cache/<profile>.json`, `provider:
  "Fantasy Footballers Podcast UDK"`) -- never merges into or overwrites canonical NWR
  player/team/status fields. K/DST positions are always MANUAL/unmodeled by NWR design (no
  NWR score is ever assigned), so there is no NWR-authority field for a Ballers import to
  conflict with in the first place.
- Real, disclosed, non-NWR-score labeling: `provider: "Fantasy Footballers Podcast UDK"` on
  the rich-schema path, `authority: "EXTERNAL_UDK_UNMODELED_BY_NWR"` on the current-roster
  fallback path (`parse_udk_kdst_snapshot`). The directive's literal phrase "BALLERS
  REFERENCE" is this project's own descriptive shorthand for an owner-authorized external
  source in general -- the real, existing labels already carry the same disclosure intent
  under the product's real name (the owner's actual product is Fantasy Footballers Podcast's
  "UDK", not literally branded "Ballers").

## What this unit verified and added

1. Confirmed (existing tests, rerun clean) that DST-by-team / K-by-identity matching already
   works correctly through the rich-schema path.
2. Added one new test proving K/DST rows also get every real Section 7 addition automatically
   (no K/DST-specific code path to silently diverge): `perPositionCounts`, `duplicateRows`,
   real `byeWeek`/`tier`/`adpRaw` fields survive the round trip, and re-import versioning +
   rollback work identically for K/DST as for any skill position.
3. No new K/DST-specific code was written -- per the directive's own "REUSE FIRST" discipline
   applied elsewhere this session, building a second, K/DST-specific schema when the existing
   generic one already satisfies every real requirement would be exactly the kind of
   duplicated, drift-prone implementation this project avoids.

## Tests

1 new test (`test_udk_kdst_rows_get_the_full_real_ballers_schema_and_versioning`); full
`test_redraft_draft_room_v1_service.py` regression: 60 passed, 1 pre-existing skip (unchanged
`BLOCKED_PENDING_OWNER_SAMPLE`). Both real boards re-verified byte-identical.

## Status

Section 8: **DONE.** No code changes required beyond the confirming test -- the real pipeline
was already ready.
