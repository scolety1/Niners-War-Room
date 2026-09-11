# Data Authority

Every data/trust authority this product depends on, what's live vs.
static vs. manual, and the real disclosed gaps -- directive sections 5-6
of the NWR pre-UI product-architecture hardening pass.

## Player status: two distinct concepts, kept distinct

### `PlayerStatusOverride` (unchanged, the manual intake mechanism)

`src/services/current_player_status_overrides_service.py`. A manual,
individually-sourced, cited, verified correction layer over the frozen
projection snapshot -- four kinds only: `SEASON_OUT`, `NOT_WITH_TEAM`,
`ADMINISTRATIVE_EXEMPT`, `TEAM_CORRECTION`. Applied at exactly two real
call sites building a live current-season ranking. This pass did not
change this module's behavior at all -- it remains the single, real
intake mechanism (`add_verified_status_override`, requiring ≥1 cited
source per entry).

### `PlayerAvailabilityStatus` (new this pass, a broad READ authority)

`src/services/player_availability_status_service.py`. Directive section
5 asked for a canonical, BROAD status authority (injury designation,
practice state, IR/PUP/NFI, suspension, administrative/exempt, released,
current team, source, freshness) kept distinct from the override
mechanism above and from any `PlayerNewsItem` concept.

**Real finding from this pass's own research** (grep across the entire
repo, not assumed): **there is no live/automated in-season injury-news
feed anywhere in this codebase.** Every "injury"-named module under
`src/services` --
`injury_availability_context_service.py`,
`injury_context_flags_service.py`,
`injury_context_source_gate_service.py`,
`rotowire_local_team_status_service.py` -- reads a STATIC, historical,
offline CSV export used for model-training/backtest feature context, not
a live feed. The manual override mechanism above is the ONLY real,
current-season status source this app has.

`PlayerAvailabilityStatus` is therefore an honest WRAPPER, not a second
data source: it re-expresses the same overrides in the broader schema,
leaving every field the overrides don't actually cover as `null` --
never fabricated. `injuryDesignation` is populated only for `SEASON_OUT`
(as `"OUT"`); `practiceState` and `irPupNfi` are always `null` today (no
real source for them exists). `authorityHealth.automatedFeed` is always
`false`, with an explicit issue string disclosing this gap on every read
-- see `redraft_player_availability_status` /
`GET /api/v1/redraft/player-availability-status`.

**If a real live feed is ever added**, it plugs into `load_player_
availability_statuses` as a second composed source without any consumer
needing to change -- the same "wrap, don't fork" instruction this module
follows for the override mechanism itself.

**Not yet done this pass:** no product surface (Draft/Lineup/Waivers/
Trades) was migrated to CONSUME this new authority -- each still renders
its own local status heuristic (e.g. `weekly-shared.tsx`'s `statusTone`,
a UI-only string-matching heuristic with no shared backend authority
behind it, and the Draft Drawer's own separate status-override display).
This is disclosed as a real gap in the final handoff (PLAYER STATUS
AUTHORITY: the authority itself is built and live; consumer migration is
NOT done).

## Weekly projections (unchanged this pass)

`src/services/weekly_projection_provider_service.py` (from the prior
`NWR_PROSPECTIVE_2026_IN_SEASON_FREEZE_V2` pass, untouched by this one).
Sleeper is an APPROVED TEMPORARY/STOPGAP provider behind a `Weekly
ProjectionProvider` protocol seam; schema validation, coverage-collapse
detection, a 5-minute cache, and a 36-hour-bounded stale-snapshot
fallback (always labeled `STALE`) all already exist. This pass did not
touch this module's logic -- only added `traceId`/`leagueSnapshotId`
identification on top of the tools that call it.

## Market / ADP

Existing `AdpSnapshot` machinery (`load_adp_snapshot`,
`redraft_bootstrap`'s `draftBoard.adp` field), unchanged. Reflected as
its own `MARKET_ADP` category in the new Data Health authority (below).

## Draft-day rest-of-season projections

The governed `RankingResult` (`generate_rankings`, unchanged). Real,
disclosed, pre-existing environment gap found while testing this pass --
and root-caused precisely, not just observed: the bundled seed CSV
(`docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/
GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv`) is present and its
sha256 matches `desktop_facade.REDRAFT_SEED_SHA256` exactly -- the file
itself is fine. Its governance approval receipt
(`NWR_DATA_GOVERNANCE.json`) has `"valid_until": "2026-09-09"`, and
`redraft_engine_v1_service`'s own receipt validator rejects it with
`"Projection approval receipt has expired."` whenever `valid_until <
today` -- today is 2026-09-10, one day past expiry. This is the exact
same class of issue this repo's own history already shows recurring
(the receipt's own `renewal_record` documents an earlier such expiry,
renewed 2026-09-06 with explicit real owner authorization). Renewing it
again requires the same real owner authorization this agent cannot
self-issue -- consistent with this repo's own established practice, and
explicitly out of this architecture-only pass's scope (renewing data
governance is a data-admission action, not a routing/context/contracts
change). Confirmed live: a freshly created local profile's ranking is
genuinely empty in THIS environment (`ranking.ready == False`,
`redraft_bootstrap().data.rankings == []`), and the real Draft Room
UI surfaces the honest error "The active Redraft ranking is unavailable:
Governed 2026 projection snapshot is missing." when a pick is attempted
-- verified in the rendered Chrome acceptance pass (`PRODUCT_
ARCHITECTURE.md`, section 12). This is the same gap already documented
in `docs/codex/overnight_v3/NWR_PROSPECTIVE_2026_IN_SEASON_FREEZE_V2.md`'s
"Known limitations" and reflected in this branch's 5-failure pre-existing
test baseline -- not introduced by this pass, and every new endpoint
this pass added degrades honestly against it (verified directly, see
`DECISION_CONTRACTS.md`).

## Decision engine

`marginal_roster_utility_v2` and every other real engine (weekly lineup
optimizer, waiver engine, trade analysis, trade finder, roster legality)
are unchanged, called read-only by every new module this pass added. The
new `in_season_decision_trace_service.load_decision_traces` function
(pre-existing but never called from anywhere before this pass) is now a
real consumer: the Data Health authority's `DECISION_ENGINE` category
reports the most recent real trace's timestamp for the active profile.

## Data Health authority (directive section 6)

`src/application/desktop_facade.py::redraft_data_health` /
`GET /api/v1/redraft/data-health`. Replaces the OLD bootstrap-only
`health` block's stale "External network: OFF / Local runtime only /
Streamlit fallback: Preserved" framing (still visible verbatim in git
history in `pages.tsx`'s old `DataHealthPage`) -- directly contradicted
by this app's real, live Sleeper/FantasyPros calls.

Seven categories, each with `status`, `source`, `lastUpdate`,
`freshness`, `degradationReason`, `impactOnRecommendations`:

| Category | Real source | Degrades to |
|---|---|---|
| `LEAGUE_SYNC` | `LeagueProfile.provider`/`updatedAtUtc` | `NOT_APPLICABLE` for a local/manual profile |
| `WEEKLY_PROJECTIONS` | `weekly_projection_provider_service` health | `NOT_APPLICABLE` without an active Sleeper league; `UNAVAILABLE` on a real fetch failure |
| `ROS_PROJECTIONS` | governed `RankingResult.ready` | `DEGRADED`/`UNAVAILABLE` on the snapshot gap above |
| `MARKET_ADP` | `load_adp_snapshot` | `UNAVAILABLE` with no imported ADP |
| `PLAYER_STATUS` | `player_availability_authority_health` | always `OK` (the manual authority always answers; its own health discloses the automated-feed gap) |
| `DECISION_ENGINE` | `load_decision_traces` | `NO_ACTIVITY` with zero recorded traces for the profile |
| `SNAPSHOT` | `redraft_league_workspace_context` | `UNAVAILABLE` only if that call itself raises |

Every category is real -- none is a placeholder or a hardcoded "OK". A
profile with no data at all (no active league) reports all seven as
`UNAVAILABLE` rather than silently omitting them (verified directly by
`tests/test_desktop_facade_architecture_wiring.py`).

**Not yet done this pass:** a compact health indicator on the primary
owner UI (directive section 6 says this pass "can keep it minimal") --
genuinely not built; `/league/:key/data-health` (via the League bucket)
remains the only place to see this. Disclosed as a real gap, not
overclaimed.

## Draft-time hashing (unchanged, referenced for context)

`redraft_decision_bundle{,_v2}` already compute `leagueProfileHash`,
`rosterStateHash`, `availablePlayerHash`, `universeHash`,
`marketSnapshotHash`, `bundleHash` via `provenance_hash`/
`build_score_provenance` (`score_provenance_service.py`). This pass's
`LeagueWorkspaceContext`/`LeagueSnapshot` hashing (see `LEAGUE_CONTEXT.
md`) reuses the same `provenance_hash` helper and extends the same
pattern to the in-season surface, which had none of this before -- the
two hashing schemes are deliberately parallel, not merged (different
inputs, different purposes: draft-time provenance vs. in-season decision
identity), and neither was changed.
