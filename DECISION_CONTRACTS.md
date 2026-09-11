# Decision Contracts

`DecisionResultEnvelope` -- directive section 4 of the NWR pre-UI
product-architecture hardening pass. An OWNER-FACING contract only: it
never replaces or recomputes an engine's own real fields, and different
tools are never forced to share internal computation -- only the product
language for "what to do, why, what else, how confident, on what data,
prove it."

## Shape

Backend: `src/services/decision_envelope_service.py`
(`DecisionResultEnvelope` dataclass, `build_decision_envelope`).
Frontend: `DecisionResultEnvelope` in
`desktop/packages/contracts/src/index.ts`.

| Field | Type | Notes |
|---|---|---|
| `task` | string | e.g. `"START_SIT"`, `"WAIVER"` -- matches `in_season_decision_trace_service.TOOL_TYPES` where applicable |
| `profileId` | string | the league key |
| `leagueSnapshotId` | string \| null | see `LEAGUE_CONTEXT.md` |
| `generatedAtUtc` | string | stamped fresh on every build, never cached |
| `primaryRecommendation` | object \| null | `null` is a real, expressible state ("nothing to recommend" -- e.g. lineup already optimal), never a fabricated placeholder |
| `alternatives` | object[] | |
| `rationale` | string | plain-language, built from the same real fields as the recommendation |
| `confidenceState` | `HIGH` \| `NOMINAL` \| `LOW` \| `UNAVAILABLE` | a disclosed heuristic (weekly-projection freshness, unprojected-starter count, candidate presence) -- NOT a new validated confidence model; see "Confidence heuristic" below |
| `confidenceBasis` | string | the real signal the confidence state was read off |
| `dataHealth` | object \| null | reuses the tool's own already-computed provider-health block |
| `traceId` | string \| null | see "Trace IDs" below |
| `issues` | string[] | reused from the tool's own provider-health `issues` |

## Migration status (directive's stated order: Start/Sit, Waivers, Trades,
## Streamers, Draft)

| Tool | `traceId` | `leagueSnapshotId` | `decisionEnvelope` |
|---|---|---|---|
| Start/Sit (`redraft_weekly_lineup`) | YES | YES | **YES** |
| Waivers/Add-Drop/FAAB (`redraft_waivers`) | YES | YES | **YES** |
| Trade Analysis (`redraft_trade_analysis`) | YES | YES | **YES** (CLOSURE pass, 2026-09-10) |
| Trade Finder (`redraft_trade_finder`) | YES | YES | **YES** (CLOSURE pass, 2026-09-10) |
| K/DST Streamer (`redraft_kdst_streamer`) | YES (`traceIds`, plural -- see below) | YES | **YES**, one per position (`decisionEnvelopes`, CLOSURE pass) |
| Draft (`redraft_decision_bundle{,_v2}`) | no (has its own, older, separate provenance system -- see `DATA_AUTHORITY.md`) | no | not yet, deliberately |

CLOSURE pass (2026-09-10) update: all five in-season/trade tools the
directive named now have the full envelope. Trade Analysis's `alternatives`
is honestly `[]` -- it evaluates exactly the one proposed trade an owner
submitted, it does not generate alternative trades (that is Trade
Finder's job). Draft remains deliberately without this envelope, an
UNCHANGED judgment from the original pass (it already has its own hash/
provenance system, and reopening draft-recommendation modeling stays out
of scope) -- not a gap this closure pass left open by omission.

## Draft's exclusion, re-examined (CLOSURE pass part 3, 2026-09-10,
## directive section 3)

The directive asked this pass to actually read Draft's real recommendation/
provenance code and judge honestly whether staying separate is still
justified, rather than re-stamp the prior pass's conclusion unexamined.
Read: `desktop_facade.py::redraft_decision_bundle{,_v2}`,
`decision_bundle_live_service.py`, `score_provenance_service.py`,
`in_season_decision_trace_service.py`.

**Verdict: VALIDATED -- the exclusion is a real architectural difference,
not deferred effort.** Three concrete, code-level reasons:

1. **Draft's own provenance is already a richer, purpose-built system,
   not a gap.** `ScoreProvenance` (`score_provenance_service.py`) bundles
   13 real fields (`leagueProfileHash`, `rosterStateHash`,
   `availablePlayerHash`, `universeHash`, `projectionModelVersion`,
   `marketSnapshotHash`, `featureSetVersion`, `teamScoreVersion`,
   `championshipEquityVersion`, `pickScoreVersion`, `optimizerVersion`,
   `seed`, `simulationCount`) into one hashed `bundleHash`, purpose-built
   for a full-candidate-set SIMULATION result (directive section 28,
   predates this pass entirely). `LeagueSnapshot`'s `leagueSnapshotId` is
   deliberately lighter -- one id over `{scoringProfileHash,
   rosterStateHash, week, extra}` (see `LEAGUE_CONTEXT.md`) -- built for a
   single-roster-read in-season tool. Wrapping Draft in the envelope would
   not ADD reproducibility; it would either duplicate the richer hash
   Draft already has under a second, less detailed name, or silently
   drop fields the existing system already proves.
2. **Draft has no backend-declared single recommendation to put in
   `primaryRecommendation`.** Every migrated tool (Start/Sit, Waivers,
   Trade Analysis, Trade Finder, K/DST Streamer) computes exactly one
   real recommendation (or a small explicit candidate set) server-side.
   Draft's `DecisionBundle` returns an ordered field of MANY live
   candidates, each carrying its own `pickScore`/`teamScoreAfter`/
   `equityGain`/`metricStatus`/`uncertainty` -- richer, per-candidate
   confidence information than the envelope's single coarse
   `confidenceState` (`HIGH`/`NOMINAL`/`LOW`/`UNAVAILABLE`) could
   represent without a real information loss. "NWR PICK NOW" (the closest
   thing to a single recommendation) is a FRONTEND-computed UI banner
   (`findPickNow` in `draft-room-v2.tsx`, row 1 of the already-sorted
   candidate list) -- the backend itself never designates one candidate as
   canonical. Forcing a `primaryRecommendation` field would mean either
   inventing a new backend concept Draft's real interaction contract does
   not use, or faking it from frontend logic -- neither is a real
   architecture improvement.
3. **The trace-id schema this pass extended is genuinely the wrong
   shape for Draft.** `in_season_decision_trace_service.TOOL_TYPES`
   (`START_SIT`, `WAIVER`, `ADD_DROP`, `FAAB`, `TRADE`, `K_STREAMER`,
   `DST_STREAMER`) is a WEEK-scoped taxonomy -- `DecisionTraceRecord.week`
   is a real, load-bearing field for every existing member. A draft pick
   has no week. Giving Draft a `traceId` through this same schema would
   require inventing a `DRAFT` tool type with `week` permanently `null`
   and `alternatives`/`recommendation` shapes that don't match any other
   member -- a real, non-trivial schema change, not the small addition
   the other 5 tools got. Draft's real, permanent, append-only pick
   record already exists -- the draft board itself (`draft_boards/
   <profile_id>.json`) -- which is arguably a MORE complete trace (every
   real pick, forever) than a `traceId` would add.

This is not "the same conclusion restated" -- it is a genuine re-
examination that could have gone the other way (e.g. if Draft's
provenance had turned out to be a thin, incomplete stub, migrating it
would have been the honest answer). It didn't: Draft's own system is
real, tested (`score_provenance_service.py`'s own test suite,
pre-existing), and already exceeds what the envelope would add. No code
change follows from this section -- the correct action, per the
directive's own instruction not to force uniformity onto a genuinely
different contract, is to leave Draft as-is and document why precisely
(this section), which is what this CLOSURE pass part 3 did.

### K/DST Streamer's `traceIds` (plural)

One streamer call produces up to two real recommendations (K and DST),
so a single top-level `traceId` would silently drop one. `traceIds` is a
flat list of `{position, traceId}` -- NOT a `{K: ..., DST: ...}` dict,
for the same reason the existing `positions` field on this same response
is a flat list: the desktop API's generic camelCase JSON-key transform
mangles literal `"K"`/`"DST"` dict keys (a real, already-documented,
live-reproduced bug for this exact response shape).

## Trace IDs (directive invariant C: "every recommendation can expose a
## trace ID")

`in_season_decision_trace_service.py` (schema v1, append-only jsonl) is
unchanged -- it already recorded a trace for Start/Sit, Waivers, FAAB,
Trade Analysis, Trade Finder, and (as of a prior pass) K/DST Streamer.
The real gap this pass closed: `_record_decision_trace_safe` (the
facade's logging wrapper) always returned `None`, so no HTTP response
ever exposed the trace id it had just written. It now returns the real
`trace_id` on success (`None` only on a swallowed logging failure, which
was already the pre-existing best-effort contract) -- every one of the
five in-season tools above now returns it. `load_decision_traces`
(pre-existing, previously never called from anywhere) is now a real
consumer inside the new Data Health authority's `DECISION_ENGINE`
category.

## Confidence heuristic (disclosed, not a new model)

`confidenceState`/`confidenceBasis` are read off REAL, ALREADY-COMPUTED
signals each tool already had -- never a new score:

- Start/Sit: `LOW` if weekly projections are `STALE`, or if any starter
  has no usable projection; `NOMINAL` otherwise.
- Waivers: `LOW` if THIS_WEEK projections are `STALE`; `UNAVAILABLE` with
  zero add candidates; `NOMINAL` otherwise.
- Trade Analysis (CLOSURE pass): `LOW` if any traded player carries a
  real status flag or the evaluation raised a real roster-construction
  risk flag; `NOMINAL` otherwise.
- Trade Finder (CLOSURE pass): `NOMINAL` when a real win-win candidate
  was found across every live opponent roster; `UNAVAILABLE` when none
  was (never fabricated).
- K/DST Streamer (CLOSURE pass): `NOMINAL` per position when a real
  ADD/top candidate exists; `UNAVAILABLE` per position otherwise.

This is explicitly a heuristic over existing freshness/coverage signals,
the same honesty posture the directive requires elsewhere in this
product (e.g. `weekly-shared.tsx`'s own `statusTone` docstring: "a
heuristic, not a validated severity model").

## Real test-environment limitation (disclosed)

A freshly created local profile in this worktree has an EMPTY governed
ranking, because the bundled 2026 projection seed's governance approval
receipt expired 2026-09-09 -- one day before this session (2026-09-10);
see `DATA_AUTHORITY.md` for the exact, verified root cause. This blocks
`redraft_weekly_lineup`/`redraft_waivers`/`redraft_trade_analysis`/
`redraft_trade_finder` from being exercised end-to-end in THIS
environment regardless of this pass.
The new fields on those four are verified by:

1. Pure-function unit tests on `league_workspace_context_service.py` /
   `decision_envelope_service.py` (25 tests, `tests/test_league_
   workspace_context_service.py`, `tests/test_decision_envelope_
   service.py`).
2. A direct facade-level proof (`tests/test_desktop_facade_architecture_
   wiring.py`) that the standalone endpoints (`redraft_league_workspace_
   context`, `redraft_data_health`) degrade honestly against this same
   gap without crashing.
3. A live, Sleeper-mocked facade test of `redraft_kdst_streamer` (the one
   in-season tool that does NOT depend on the governed ranking) proving
   `traceIds`/`leagueSnapshotId` are real and correctly shaped end to end.
4. Code review + an unchanged backend regression baseline (135 passed, 5
   pre-existing failures, 0 new) -- not a substitute for #1-3, but
   additional evidence nothing else broke.

A full live round trip of Start/Sit/Waivers/Trade Analysis/Trade Finder
with the new envelope fields was NOT exercised in this session -- this is
the same real, external constraint (no governed 2026 projection snapshot
installed, no safe non-owner Sleeper league available) already disclosed
in the prior `NWR_PROSPECTIVE_2026_IN_SEASON_FREEZE_V2` pass, not new to
this one.
