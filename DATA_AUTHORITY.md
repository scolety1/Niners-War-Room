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

**CLOSURE pass update (2026-09-10):** every major owner-facing surface
now attaches this SAME authority (via a new shared facade helper,
`DesktopBackendFacade._player_availability_status_map()`, keyed by
canonical player id) to its own already-computed rows: Draft
(`redraft_decision_bundle{,_v2}`), Lineup (`redraft_weekly_lineup`),
Waivers (`redraft_waivers`), Trade Analysis (`redraft_trade_analysis`),
Trade Finder (`redraft_trade_finder`). See `tests/test_player_
availability_status_consumer_consistency.py` for the proof (byte-
identical to the standalone authority endpoint, keyed consistently, no
surface invented a competing lookup). `weekly-shared.tsx`'s `statusTone`
remains a legitimate PRESENTATION-only mapping (string -> UI tone/color)
of the engine's own already-override-derived `status` string -- it was
not, and did not need to be, replaced; the directive's "no duplicate
per-surface status transformations unless presentation-only" bar is met.
Frontend CONSUMPTION of the new `playerAvailabilityStatus` field in the
UI itself is proven for Lineup/Waivers via the new global Player Detail
drawer (see below); Draft/Trade Analysis/Trade Finder carry the field on
the wire, typed in `@nwr/contracts`, but no frontend UI reads it yet in
those three surfaces -- a real, disclosed, scoped-down remainder, not
silently claimed done.

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

## Governance reconciliation (CLOSURE pass, 2026-09-10, directive section 1)

Read-only investigation, no auto-renewal performed. Compared this worktree's
expired bundled seed (`docs/hq/model/nwr_redraft_2026_rookie_projection_
candidate_v1_20260809/NWR_DATA_GOVERNANCE.json`, `source_sha256
e483caae...`, combined 608 rows [530 veteran + 78 rookie], `valid_until
2026-09-09`) against the real-install Freeze V7 governed snapshot
(`docs/codex/NWR_PROSPECTIVE_2026_FREEZE_V7_20260908.md`, commit
`0ae4b039`, in the `draft-upgrade-hq` worktree lineage) previously
identified as valid through 2026-10-08.

**Verdict: `DIFFERENT_ARTIFACT_TEST_SEED_EXPIRED`.** These are NOT the same
governed artifact:

| | This worktree's bundled seed | Freeze V7 real install |
|---|---|---|
| Admitted universe | 608 (530 veteran + 78 rookie) | 564 (491 veteran + 73 rookie) |
| Veteran source_sha256 | `6ee6dbff...` | `29f3c2e8...` (a1505742's fresh admission) |
| Rookie source_as_of | 2026-07-30 | 2026-09-08 (independently re-governed) |
| Combined source_sha256 | `e483caae...` | not a single combined artifact -- installed via `install_projection_snapshot()` |
| valid_until | 2026-09-09 (expired) | veteran candidate `docs/codex/nwr_redraft_2026_projection_admission_CANDIDATE_v3_20260908/NWR_DATA_GOVERNANCE.json` shows `valid_until 2026-10-08`, but that candidate (`source_sha256 29f3c2e8...`) is ALSO not what `desktop_facade.REDRAFT_SEED_SHA256` (`e483caae...`) checks against |

Even if the Freeze V7 veteran candidate's approval is still nominally
valid through 2026-10-08, it covers a genuinely different artifact
(different row count, different source hashes) than the one this
worktree's `redraft_engine_v1_service` actually validates against
(`REDRAFT_SEED_SHA256` in `desktop_facade.py` is hardcoded to the OLD
608-combined snapshot's hash). Copying the Freeze V7 artifact in would
ALSO require a code change to that hardcoded constant -- a data-admission/
engineering change, not something this architecture-only pass may do
unilaterally. Per the directive, this expired seed is left as-is; it does
not block the architecture work in this pass, all of which is testable
structurally (pure-function tests, honest-degradation facade tests,
source-level wiring proofs) without live rankings data -- see
`DECISION_CONTRACTS.md`'s and `tests/test_desktop_facade_architecture_
wiring.py`'s own disclosures of this exact, unrelated, pre-existing gap.

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
