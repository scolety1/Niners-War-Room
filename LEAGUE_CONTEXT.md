# League Context

League identity, lifecycle, and snapshot identity -- directive sections
1-3 of the NWR pre-UI product-architecture hardening pass. See
`PRODUCT_ARCHITECTURE.md` for how this fits into the whole product.

## League key

`LeagueProfile.profileId` is the stable league key used everywhere
(routes, the workspace context, snapshot hashing). It was already a
stable, unique, opaque id assigned at profile creation/import
(`redraft_engine_v1_service.LeagueProfile.profile_id`) -- this pass did
not invent a second identity. Frontend helper: `leagueKeyFor()` in
`desktop/apps/redraft/src/league-context.ts`.

## LeagueWorkspaceContext

Backend: `src/services/league_workspace_context_service.py`
(`LeagueWorkspaceContext` dataclass). Exposed at
`GET /api/v1/redraft/league-workspace-context` (facade method
`redraft_league_workspace_context`, operates on the currently active
profile).

Frontend type: `LeagueWorkspaceContext` in
`desktop/packages/contracts/src/index.ts`; client method
`NwrApiClient.redraftLeagueWorkspaceContext()`.

Fields (camelCase on the wire):

| Field | Source | Notes |
|---|---|---|
| `profileId` | `LeagueProfile.profile_id` | the league key |
| `provider` | `LeagueProfile.provider` | `local` \| `sleeper` \| `espn` \| `fantasypros` |
| `providerLeagueId` | `LeagueProfile.provider_league_id` | |
| `season` | `LeagueProfile.season` | |
| `lifecycle` | lifecycle resolver | see below |
| `lifecycleBasis` | lifecycle resolver | the real signal cited for the resolution, always populated |
| `currentWeek` | **always `null`** | see "Known gap" below |
| `scoringProfileHash` | `compute_scoring_profile_hash` | sha256 over roster+scoring+draft+teamCount+season |
| `rosterStateHash` | `compute_roster_state_hash` | `null` when no real roster read exists for this request (e.g. a local/non-Sleeper profile, or a failed live read) |
| `leagueSnapshotId` | `compute_league_snapshot_id` | always populated -- see LeagueSnapshot below |
| `syncStatus` | `LIVE` \| `DEGRADED` \| `NOT_APPLICABLE` | `LIVE`/`DEGRADED` only for a Sleeper profile with a provider league id |
| `syncAsOf` | `LeagueProfile.updated_at_utc` | |
| `issues` | accumulated during context build | never silently dropped |

Hashing reuses `provenance_hash` (`src/services/point_in_time_feature_
store_service.py`) -- the SAME deterministic sha256-over-canonical-JSON
helper the draft-room DecisionBundle's `roster_state_hash`/`available_
player_hash`/`league_profile_hash` provenance fields already used (see
`desktop_facade.py`'s `redraft_decision_bundle{,_v2}`). This pass extends
that existing pattern to the in-season surface, which had no hash/
snapshot field of any kind before this pass (confirmed by direct search).

## Lifecycle resolver

ONE authority, in two mirrored implementations that take the same four
inputs and return the same branch order:

- Backend: `src/services/league_lifecycle_service.py::resolve_league_lifecycle`
- Frontend: `desktop/apps/redraft/src/league-context.ts::resolveLeagueLifecycle`

Inputs: `archived` (profile flag), `draft_configured` (has a draft board
ever been set up for this profile in NWR), `drafted_count` (picks
recorded), `total_draft_picks` (`team_count * draft.rounds`),
`current_pick` (an active pick pointer, or `null`).

Rules, in order:

1. `archived` -> **OFFSEASON**.
2. not configured, or zero picks drafted -> **PRE_DRAFT**.
3. `drafted_count >= total_draft_picks` (and `total_draft_picks > 0`) ->
   **IN_SEASON** (completion always wins over a stale leftover
   `current_pick` pointer).
4. an active `current_pick` pointer -> **LIVE_DRAFT**.
5. otherwise (partial draft board, no pointer) -> **LIVE_DRAFT**, a
   deliberately conservative default -- never assume IN_SEASON from an
   ambiguous partial state.

### Known, disclosed gap

**No live NFL-calendar signal exists anywhere in this repository.**
Confirmed by direct search: no wrapper around Sleeper's `GET /v1/state/
nfl` (or any equivalent) exists in `src/services`. This means:

- OFFSEASON is reachable ONLY via an archived profile, never via "the
  season has actually ended" -- a real, live in-season league with an
  archived=false profile can never be classified OFFSEASON by this
  resolver.
- `currentWeek` on `LeagueWorkspaceContext` is always `null`. Every
  in-season tool (Start/Sit, Waivers THIS_WEEK, Compare This-Week mode)
  still takes `week` as an explicit owner-supplied input via its own page
  control -- unchanged by this pass.

Adding a live calendar signal was judged a new data-acquisition capability
(a new provider integration), out of this architecture-only pass's scope
-- the directive explicitly says not to reopen weekly-projection-provider
research. This is disclosed here rather than silently worked around with
a heuristic that could misclassify a real league.

## LeagueSnapshot

There is no separate `LeagueSnapshot` object/table -- "snapshot identity"
is the `leagueSnapshotId` string, a `provenance_hash` over
`{scoringProfileHash, rosterStateHash, week, extra}`. Two calls with the
same rules, the same roster read, and the same week always produce the
same id; a roster move, a rules edit, or a different week always changes
it. This is intentionally lightweight (an id, not a stored/versioned
object) -- directive section 3 asks for "identify/hash where supported,"
not a new persistent snapshot store, and every consumer already has the
real underlying data (roster, rules, week) available to it; the id exists
so two recommendations can be compared/audited for whether they came from
the same decision state, not to reconstruct that state from the id alone.

Wired into (as of this pass): `redraft_weekly_lineup` (Start/Sit),
`redraft_waivers`, `redraft_trade_analysis`, `redraft_trade_finder`,
`redraft_kdst_streamer`, and the standalone `redraft_league_workspace_
context`. See `DECISION_CONTRACTS.md` for the exact field per tool.

**CLOSURE pass update (2026-09-10):** `redraft_weekly_home_actions`
(Weekly Home) now ALSO surfaces this exact id at its top level -- taken
from its own internal `redraft_weekly_lineup` sub-call (which it already
made to build its action list), not independently recomputed. Every
decision card Weekly Home renders (actions, the embedded `lineup`
sub-payload, the embedded `freeAgents` sub-payload) derives from this
ONE response, closing the directive-section-3 gap the original pass left
open (see `PRODUCT_ARCHITECTURE.md` invariant F).

## Context isolation

`LeagueScopedPage` (`RedraftApp.tsx`) activates the target league before
rendering anything underneath a `/league/:leagueKey/*` route, and keys
the rendered subtree by `leagueKey`. Six `useAsync` call sites across
`in-season.tsx`/`pages.tsx` were found, during this pass, to be missing
`data.activeProfileId` in their dependency arrays -- a real bug that let
a previous league's Sleeper roster/waiver/trade data stay on screen after
switching leagues with the same mode/week selected. All six are fixed;
see `PRODUCT_ARCHITECTURE.md`'s "Context isolation" section for the list.
