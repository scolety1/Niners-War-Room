# K/DST Prospective Benchmark V1 -- Preregistered Scaffolding (Work Unit 17)

Written BEFORE the first real week was populated. Scope: this is
SCAFFOLDING -- a real, reusable tracking mechanism -- not a full
multi-week study. Real 2026 NFL data is only 1-2 weeks in as of this pass
(current real NFL week per live `state/nfl` = 2; Week 1 is the only real,
fully-COMPLETE week). Every real number this pass produces is honestly
labeled `PRELIMINARY`, and no model/recommendation logic is tuned from it,
per the owner's standing instruction.

`fantasypros_kdst_consensus_service.py` (the real K/DST streamer) and
`weekly_lineup_optimizer_service.py`/any other recommendation logic are
NOT modified by this pass -- this module only READS real, already-fetched
inputs and computes comparison/tracking records over them.

## The real, honest finding this scaffolding starts from

Reading `desktop_facade.py`'s own real `redraft_kdst_streamer` call site
(the live production K/DST Streamer) BEFORE writing any benchmark code:
**NWR's own "recommendation" for K/DST IS, by construction, the
FantasyPros consensus ECR order** (`streamer_actions`/`sleeper_streamer_
actions`: the lowest-ECR player not already rostered by any team is the
`"ADD"` recommendation; the real rationale string the live UI shows is
literally `"... per FantasyPros consensus ECR."`). There is no separate
NWR-computed K/DST score anywhere in this codebase (confirmed: `_asset_
pool`/`generate_rankings` never project K/DST at all, by design). This
means "current NWR recommendation method vs. provider consensus" is NOT
two independent methods for K/DST the way it is for skill positions --
it is the SAME signal, with one real value-add layered on top: Sleeper
roster-availability filtering (skipping an already-rostered player to the
next-best ECR option). This benchmark measures that real value-add
directly (see "Arm 1 vs Arm 2" below), rather than pretending two
independent methods exist where only one does.

## Four comparison arms (per position, per week)

1. **NWR_RECOMMENDATION** -- the real, live `"ADD"` action NWR would
   surface this week: lowest-ECR player NOT already rostered by any real
   team in the league (per `sleeper_streamer_actions`'s own roster-status
   logic).
2. **PROVIDER_CONSENSUS** -- the raw FantasyPros ECR rank-1 player for the
   position/week, with NO roster-availability filtering applied at all.
   Differs from Arm 1 only when the naive rank-1 player is genuinely
   already rostered somewhere in the real league (see the DST identity-bug
   disclosure below for a real caveat on when this filter can silently
   fail to apply).
3. **RAW_PROJECTION** -- Sleeper's own real, live weekly projection
   endpoint (`weekly_projection_service.fetch_sleeper_weekly_projections`
   -> `pts_ppr`, labeled `SLEEPER_PROVIDER_SCORING`internally) -- a real,
   legitimately-available, NON-NWR projection source for K/DST specifically
   (unlike skill positions, K/DST get no NWR-computed
   `score_projection`). The real candidate under this arm is whichever
   unrostered K/DST has the HIGHEST real Sleeper-projected `pts_ppr` for
   that week -- a genuinely different selection signal than ECR rank.
   Reported `NOT_AVAILABLE` only if the live fetch itself fails (not a
   standing "K/DST are unmodeled" excuse -- this projection source is real
   and does exist for K/DST, unlike an NWR-computed one).
4. **REPLACEMENT_LEVEL** -- the K/DST the owner ALREADY had rostered
   before any streaming move that week (the real "prior roster option"
   concept `prospective_outcome_k_streamer_evaluator_v1_service.py`/the
   DST twin already define as `priorRosterOptionPlayerId`, reused here by
   NAME/DEFINITION, not by importing that module directly -- this
   benchmark has no real decision-trace record to read that field FROM
   yet, since the real production trace store is still empty; see the
   ledger). For week 1 (a season opener), "already had rostered" is the
   real roster as configured entering the week -- there is no real
   "prior" week to look back to yet.

Each arm records: `playerId` (Sleeper), `playerName`, `team`,
`sourceValue` (ECR rank or projected points, whichever the arm uses),
`actualPoints` (real, once the week's real stats are available --
`None`/`dataStatus="PENDING"` before then), `dataStatus`
(`OK`/`NOT_AVAILABLE`/`PENDING`).

## A real, mechanical DST identity-matching defect found this pass (documented, NOT fixed -- hard boundary)

Live-verified against the real Fantasy Gamers league (read-only, Week 1
2026): `sleeper_streamer_actions`'s real identity key
(`_identity(player.get("full_name") or player.get("search_full_name"),
position, team)`) returns `("", "", "")` for EVERY real Sleeper DST roster
entry, because Sleeper's own `players/nfl` catalog gives DST entries
`first_name`/`last_name` only (e.g. `"New England"`/`"Patriots"`), never a
`full_name`/`search_full_name` field -- unlike `resolve_roster_canonical_
ids`/`sleeper_free_agent_pool`/`weekly_projection_service.build_weekly_
projection_rows`, which all already carry the DST name-fallback
(`if position == "DST" and not name and team: name = f"{team} D/ST"`)
that `sleeper_streamer_actions` alone is missing. Live-verified
consequence: a real query against all 10 real DST rows this league
actually rosters showed EVERY ONE reported `rosterStatus: "AVAILABLE"` --
none were recognized as `"YOUR_STARTER"`/`"YOUR_ROSTER"`/
`"ROSTERED_ELSEWHERE"`, even the owner's own real, started DST that week
(`"NE"`). K identity matching is NOT affected (K catalog entries DO carry
`full_name`) -- live-verified the owner's own real K (`Ka'imi Fairbairn`)
correctly resolved to `"YOUR_STARTER"`.

**Real consequence for this benchmark**: Arm 1 (NWR_RECOMMENDATION) for
DST is, in practice, ALWAYS identical to Arm 2 (PROVIDER_CONSENSUS) --
the roster-availability filter that should differentiate them structurally
never fires for DST, regardless of true availability. For K, the two arms
DID genuinely differ in the real Week 1 data (see Results): NWR correctly
skipped two real, actually-rostered kickers (Aubrey, Dicker) that the naive
ECR rank-1/2 would have suggested.

A second, smaller, real identity nuance found and disclosed (not a bug in
this codebase, a real provider convention difference): FantasyPros uses
team code `"JAC"` for Jacksonville; Sleeper uses `"JAX"`. Every other
real team code checked this pass matched exactly. This benchmark's own
scripts translate `JAC -> JAX` explicitly and disclosedly when joining
FantasyPros rows to Sleeper's real stats/projections by team code --
`fantasypros_kdst_consensus_service.py` itself is unaffected (its own
identity join is name-based, not team-code-based) and was not touched.

**Per the hard boundary ("measure them, don't modify them"), neither
finding above was fixed.** Both are flagged here for a future worker
explicitly authorized to touch `fantasypros_kdst_consensus_service.py`.

## Sample-size honesty rule

No `MIN_SAMPLE_SIZE` threshold is invented here claiming statistical
validity (the existing project-wide `MIN_SAMPLE_SIZE_FOR_PER_CLASS_
SUMMARY = 20`, from `prospective_outcome_evaluation_v1_service.py`, is
about decision-trace evaluation classes -- not directly reusable for a
weekly, per-position streamer arm-comparison series with a totally
different real cadence). Instead: `summarize_kdst_benchmark` always
reports the real `sampleSizeWeeks` count alongside every number, and
ALWAYS labels the result `"PRELIMINARY"` while `sampleSizeWeeks < 8` (a
disclosed, arbitrary transparency floor -- roughly half an NFL regular
season -- not a claim of statistical power at that count either; it is
simply the point past which this benchmark stops SHOUTING "preliminary"
on every line, since a genuinely wrong conclusion from n=1 or n=2 weeks is
the specific, named risk the owner's directive warns against). No
challenger is proposed from this pass's real n=1-week result, regardless
of what that one week shows.
