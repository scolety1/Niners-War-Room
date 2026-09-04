# NWR DRAFT UPGRADE HQ — OWNER TEST CANDIDATE V1 — final report

**Directive**: "Wire the real Draft Intelligence backend into Draft Room
V2 so the owner can test everything except historical calibration."
Starting state (verified match, accepted as-is): branch
`work/nwr-draft-upgrade-hq-v1-20260903`, HEAD `adacff9f`, prior verdict
`YELLOW_PRE_DATA_BACKEND_READY_WITH_NAMED_IMPLEMENTATION_GAPS`.

## Exact branch/HEAD/tree

- **Branch**: `work/nwr-draft-upgrade-hq-v1-20260903`
- **HEAD**: `a922517607cf7f881bb74578a740f2bf7f4e53d1`
- **Tree**: clean for everything this wave touched. 5 unrelated,
  pre-existing modified files remain uncommitted
  (`docs/model_v4/DRAFTABLE_POOL_SOURCE_READINESS_20260609.md` and four
  sibling docs) — present at the start of this wave, not touched by
  Owner Test Candidate V1 work, and left alone rather than silently
  committed under this directive's authorship.
- No push. No merge. No deploy. No production/scoring promotion.

## Preview launch command

```
desktop\launch-draft-upgrade-preview.bat
```

Builds/verifies the `nwr-desktop-api` Python sidecar
(`npm run sidecar:build`), then runs `npm run tauri:redraft` — a DEV
build against this worktree's branch, sharing the same
`%LOCALAPPDATA%\com.ninerswarroom.redraft` data root as other NWR
shortcuts. The script warns explicitly to use a **new test profile**,
never the real KHA profile, from inside the app.

**Known limitation**: this session's environment has no interactive
display/GUI, so the Tauri window itself was not launched and visually
confirmed this pass. What **was** verified for real: `npm run
typecheck` (both apps), `npm run test` (95/95 vitest), and `npm run
build` (both `dynasty` and `redraft` apps) all pass clean against the
exact code the launcher would run, and the full Python backend test
suite (documented 5-failure baseline unchanged) exercises every
facade/HTTP path the running app calls. This is the one acceptance item
(A, and by extension a live visual check of B/C) not demonstrated via a
literal running window this pass — see "Known current-data
limitations."

## Test profile / replay mode

Two honest paths, per section 12:

- **Path A — current test profile**: create a new Redraft profile from
  a built-in preset (e.g. `12_TEAM_1QB_HALF_PPR`) inside the app and
  start a Draft Room. This is the path every DecisionBundle/Suggestions/
  Team Score/Championship Equity/Pick Score test in this report
  exercises. Genuinely current, no relabeling needed.
- **Path B — historical replay preview**: the new **Historical Replay**
  tab in Draft Room V2, labeled **"HISTORICAL REPLAY — 2026-09-02"**,
  never presented as current. Serves the real, checked-in
  `docs/codex/KHA_SHADOW_OPTIMIZER_REPLAY.csv` (real pick
  identity/round/team/NWR-rank-at-time-of-pick; Team Score/Championship
  Equity columns are an explicitly-labeled `RANK_DERIVED_PROXY_NOT_REAL_MAGNITUDE`,
  not the real backend magnitude, because the governed projection
  snapshot needed for the real magnitude is expired — see "Known
  current-data limitations"). No expiry was manually extended, no stale
  data was pretended current, and no self-approval occurred to make this
  path available — the CSV was already real, tested, disclosed output;
  this wave only added a route and a read-only viewer for it.

## DecisionBundle live endpoint

`POST /api/v1/redraft/draft/{profileId}/decision-bundle` (body:
`{"speed": "FAST" | "STANDARD" | "DEEP"}`, defaults to `FAST`) →
`DesktopBackendFacade.redraft_decision_bundle()` →
`decision_bundle_live_service.build_live_decision_bundle()` →
`decision_bundle_service.build_decision_bundle()`, composing real
`team_score()` / `championship_equity()` / `evaluate_pick_candidates()`
/ `evaluate_cost_of_waiting_v2()` / `label_pick_decisions()` from
`shadow_numeric_authorities_service` — the same functions the rest of
NWR's SHADOW/RESEARCH numeric authority uses, never a second
implementation.

Every field the directive's section 2 names is present: current team
score/championship equity, per-candidate Player Score/Team Score
before-after-delta/Championship Equity before-after/Equity Gain/Cost of
Waiting/Make-It-Back/Raw Decision Utility/Pick Score/Action taxonomy
(TAKE NOW/GOOD VALUE/WAIT/DEEP TARGET/WAIVER WATCH)/warnings/
uncertainty, plus provenance, simulation metadata, and
`latencySeconds`. When a value cannot be calculated, the payload is
`{"available": false, "reason": "<the real reason>"}` — never a
placeholder number (proven by
`test_redraft_decision_bundle_reports_unavailable_not_a_placeholder_when_no_room_started`
and the owner's-turn guard tests in `test_decision_bundle_live_service.py`).

## Suggestions V2

`draft-room-v2.tsx`'s Suggestions tab renders `decisionBundle.candidates`
directly (`buildSuggestionsRows`), default-sorted by Pick Score
descending. Columns: Pick Score — EXPERIMENTAL / Player / NWR / Market /
Team Score — RESEARCH (with delta) / Champ Eq — SIMULATED RESEARCH (with
gain) / Wait Cost / Make It Back / Action / Alert. Candidate generation
respects drafted state and roster-position-maximum legality
(`_roster_candidate_allowed`, proven by
`test_build_live_decision_bundle_respects_position_maximum_legality`).
`max_candidates` is capped per speed preset (8/10/12), not by raw ADP
gap, so a deep market target cannot dominate the list just by having a
large ADP gap — it must actually clear the roster-legal, ranking-eligible
candidate selection. Returns `[]` (never fabricated rows) when the
bundle is unavailable; the UI renders the real `reason`.

## Team Score

Label **"TEAM SCORE — RESEARCH"**. Current roster score shown
prominently in the My Team tab (`buildCurrentRosterScores`, real
`currentTeamScore.percentile` from the bundle). Every Suggestions
candidate shows Team Score Before → After and the Delta. Recomputes on
every real draft-state change (see "Recalculation behavior").

## Championship Equity

Label **"SIMULATED CHAMPIONSHIP EQUITY — RESEARCH"**. Before/after/gain
shown per candidate; compact uncertainty (`currentChampionshipEquity.standardError`,
`seasonsSimulated`) surfaced. `assumedFormat: true` is always set on the
live endpoint's current equity (Monte Carlo comparable-league simulation
stands in for exact league-vs-league dynamics) and rendered as an
**"ASSUMED FORMAT"** eyebrow on the My Team panel, per section 5's
explicit visibility requirement.

## Pick Score

Label **"PICK SCORE — EXPERIMENTAL"** everywhere it's rendered
(Suggestions column header, Compare column, Player Drawer). Backend-only
(`shadow_numeric_authorities_service.pick_score()`), reproducible from
provenance (`test_redraft_decision_bundle_never_shows_a_static_zero_it_computes_a_real_percentile`
proves an identical call with identical inputs returns identical
scores). Relative-quality semantics only — no historical-accuracy claim
anywhere in the UI copy.

## Cost of Waiting

Real per-candidate value from `evaluate_cost_of_waiting_v2`
(ADP-distance-aware, layered onto Pick Score —
`test_evaluate_cost_of_waiting_v2_layers_survival_onto_pick_score`,
pre-existing and re-verified this session). Changes with market/draft
state because it's recomputed inside the same live bundle build every
call — never cached independently of the roster/market state that
produced it.

## Player drawer

Rewritten this wave to accept a real `DecisionBundleCandidate`. Sections:
**NWR** (Player Score, rank, tier), **Draft** (market ADP, expected
round, Cost of Waiting, Make-It-Back), **Roster Impact — Pick Score
EXPERIMENTAL / Team Score & Championship Equity RESEARCH** (full real
breakdown — Team Score Delta, Championship Equity Gain, Pick Score, Raw
Decision Utility with its Team Score/Equity components named, Action,
Uncertainty, warnings — or an honest "not among the top ranked
Suggestions candidates this pick" note when the clicked player isn't a
current bundle candidate, never a fabricated impact), **Current**
(status/injury alert from NWR's own admitted external-intelligence
feed, UDK context when available). This is also this wave's
implementation of section 7 ("Score Details/Why") — clicking a
Suggestions row opens this drawer with the full structured breakdown;
there is no separate concise generated-explanation surface yet (see
"Known current-data limitations" — the AI Explanation API).

## Compare

Real backend values for every selected player that is a current bundle
candidate (`evaluated: true`); a compared player who isn't one of this
pick's evaluated candidates shows `null` fields honestly rather than a
fabricated number (`evaluated: false`). Columns: Player Score / Market /
Team Score Δ — RESEARCH / Champ Eq Δ — SIMULATED RESEARCH / Wait Cost /
Make It Back / Pick Score — EXPERIMENTAL / Action / Warnings / Status.
The AI Compare Summary is a real, deterministic, template-based sentence
generator (`generateCompareSummary`) built only from structured fields
already on screen — no invented reasoning, no LLM call, and it now leads
with the highest-Pick-Score candidate when evaluated data exists.

## Rapid capture

Rapid capture (fast keyboard-driven pick entry) already exists and is
**GREEN** in the **production** Draft Room (`pages.tsx`) — 23/23 KHA
replay keystroke-accuracy test passing, re-verified this session
(`npm run test`, all 95 vitest cases including that suite). Draft Room V2
is deliberately a **decision-support surface layered on the same draft
state**, not a second pick-entry UI — it has no "record this pick"
control of its own. The intended owner test flow: record picks via
production Draft Room's rapid capture (or the correction/Catch-Up/
Sleeper-sync flows below), then watch Draft Room V2 react live off the
same underlying room state. This is a deliberate scope choice (the
directive says "do not duplicate numerical logic in TypeScript/frontend
… backend computes, frontend renders" — the same spirit applies to not
duplicating an already-working input UI), not a gap, but it means the
owner needs both surfaces open (or switches between the two routes) to
exercise the full loop.

## Corrections

`replace_redraft_pick` / `clear_redraft_pick` / `fill_redraft_pick_gap` /
`undo_redraft_pick_correction` all: (a) apply the real correction to the
real draft board, (b) append an NWR PURE correction record when that
mode is active, (c) log a real `DRAFT_STATE_CHANGED` owner-test
instrumentation event, and (d) trigger a fresh DecisionBundle on the
next fetch — the `board.updatedAtUtc` timestamp changes on every one of
these (verified at the source: `_apply_pick_correction`, `undo_pick_correction`,
`undo_room_pick` all bump `updated_at_utc`), which is exactly what Draft
Room V2's recompute `useEffect` is keyed on. Acceptance test J
(`test_redraft_decision_bundle_recomputes_after_a_pick_correction`)
proves a REPLACE correction changes `rosterStateHash` and removes the
corrected-in player from candidates.

## Catch-Up

`preview_redraft_catch_up` (pure preview, never writes) and
`apply_redraft_catch_up` (re-resolves from scratch, refuses on any
unresolved/ambiguous line). Acceptance test K
(`test_redraft_decision_bundle_recomputes_after_catch_up_is_applied`)
proves the DecisionBundle is genuinely unavailable ("not the owner's
turn") before a two-pick Catch-Up and genuinely available with real,
freshly-computed candidates immediately after — the strongest form of
this proof, since it shows the "not owner's turn" guard itself reacts to
live state, not just that scores changed.

## Sleeper sync

`sync_redraft_sleeper_picks` (bounded, read-only, GET-only against
Sleeper — never a write to the live Sleeper draft) applies at most
`MAX_SLEEPER_AUTO_SYNC_BATCH` new picks per call and logs a
`SLEEPER_SYNC_APPLIED` instrumentation event only when it actually
applied something. Feeds the same `_record_pick`/`updated_at_utc` path
as every other mutation, so the same recompute guarantee applies (not
independently re-tested against the live DecisionBundle endpoint this
wave — `test_facade_sync_redraft_sleeper_picks_wires_through_to_draft_board`,
pre-existing, proves the board-level wiring; the recompute mechanism
itself is proven generically by J/K above, since it's the identical
`updatedAtUtc` signal).

## Recalculation behavior

Section 10's "critical" requirement. Structural guarantee: Draft Room
V2's `useEffect` re-fetches `getRedraftDecisionBundle` keyed on
`board?.updatedAtUtc`, a real timestamp that changes on every real
mutation (owner pick, CPU pick, all four correction types, Catch-Up,
Sleeper sync — traced to source above). Explicitly demonstrated end to
end at the backend level for: a plain owner pick
(`test_redraft_decision_bundle_recomputes_after_a_pick_changes_the_roster`,
`test_redraft_decision_bundle_stays_available_across_owner_pick_and_cpu_advance`),
a correction (J), and Catch-Up (K) — each proves either the roster-state
hash changed, the just-affected player disappeared from candidates, or
the owner's-turn availability itself flipped correctly. Cache keys
(`comparable_leagues_key`) include `profile_id`/`ranking.projection_sha256`/
`adp.source_sha256`/`trials`/`base_seed` — provenance-bearing enough that
stale reuse across a genuinely different universe/market snapshot is
structurally impossible, per section 10's own requirement.

## Latency

Real, benchmarked (`docs/codex/DECISION_BUNDLE_LATENCY_BENCHMARK_20260903.md`,
`scripts/run_decision_bundle_latency_benchmark_v1.py`, 3-run median per
preset against a 240-player synthetic fixture):

| Speed | p50 | Worst |
|---|---|---|
| FAST (default) | 0.787s | 0.790s |
| STANDARD | 3.814s | — |
| DEEP | 9.592s | — |

FAST is the only preset comfortably under the 2-second target with
margin against the 60-second owner clock, and is the facade default.
The `comparable_leagues` Monte Carlo population is cached per
`(profile_id, ranking hash, adp hash, trials, base_seed)`, so a same-pick
re-render after a correction is materially faster than a cold call.
STANDARD/DEEP remain available (`speed` parameter) for an owner who
explicitly wants a deeper look between picks, never defaulted to during
live play.

## Provenance

`bundle.provenance` (`score_provenance_service.build_score_provenance`)
carries `leagueProfileHash` / `rosterStateHash` / `availablePlayerHash` /
`universeHash` (ranking's `projection_sha256`) / `projectionModelVersion` /
`marketSnapshotHash` (ADP's `source_sha256`) / `featureSetVersion` /
`teamScoreVersion` / `championshipEquityVersion` / `pickScoreVersion` /
`optimizerVersion` / `seed` / `simulationCount` / `timestampUtc`, plus a
`bundleHash` asserted non-empty in
`test_redraft_decision_bundle_returns_a_real_bundle_for_a_started_room`.
Reproducibility is directly proven, not just asserted present:
`test_redraft_decision_bundle_never_shows_a_static_zero_it_computes_a_real_percentile`
calls the endpoint twice with unchanged state and shows every candidate's
Pick Score is byte-identical — a displayed value can genuinely be
reconstructed from its provenance (acceptance test N).

## Known current-data limitations

- **Live GUI launch not visually verified this session** — no
  interactive display in this environment. Everything the launcher
  would run (`typecheck`, `test`, `build`, and the full backend suite)
  was verified for real; the literal window was not opened and
  screenshotted.
- **KHA Historical Replay preview is a disclosed rank-derived proxy**,
  not a real DecisionBundle replay — Team Score/Championship Equity
  columns are `RANK_DERIVED_PROXY_NOT_REAL_MAGNITUDE`, and Cost-of-Waiting/
  candidate-alternatives are `NOT_COMPUTABLE_WITHOUT_FULL_RANKING_UNIVERSE`.
  Root cause (governed projection snapshot expiry) and the exact
  substrate needed to fix it are now the explicit, bounded consumer
  contract handed to the new NWR Historical Redraft Data lane
  (`docs/codex/NWR_HISTORICAL_REDRAFT_CONSUMER_HANDOFF_CURRENT.md`).
- **AI Explanation API has no HTTP route yet.** The structured
  breakdown (section 7's evidence requirement) is fully real and shown
  in the Player Drawer; the concise natural-language generated
  explanation on top of it (`decision_bundle_explanation_service.py`,
  built and unit-tested 2 waves ago) is not yet reachable from the
  frontend. `RESEARCH_NOT_CONNECTED` remains in `draft-room-v2.tsx`
  solely for this one case.
- **The 5 pre-existing backend test failures** (documented all session:
  `test_dynasty_facade_composes_real_governed_workflows`,
  `test_desktop_rookie_veteran_bridge_is_source_separated_and_trade_aware`,
  `test_redraft_bootstrap_seeds_once_and_matches_desktop_contract`,
  `test_redraft_league_switching_isolates_draft_state_and_persists_active_profile`,
  `test_facade_has_no_streamlit_or_app_component_dependency`) are a
  hermetic-seed/environment gap unrelated to this directive's scope,
  unchanged by every check this wave ran.
- **Historical calibration is explicitly out of scope for this pass**,
  per the directive's own framing — nothing in this report should be
  read as a claim about NWR's historical prediction accuracy.

## Exact owner test checklist

Launch via `desktop\launch-draft-upgrade-preview.bat`. Use a **new test
profile** — never the real KHA profile — for every step below.

1. **Suggestions**: open `/draft-room-v2`, Suggestions tab. Confirm rows
   populate with real numbers (not the literal text "Not connected") and
   are sorted by Pick Score, highest first.
2. **Pick Score**: confirm the column header reads "Pick Score —
   EXPERIMENTAL." Click a row to open the drawer; confirm the same Pick
   Score appears under "Roster Impact."
3. **Team Score**: open My Team; confirm a real percentile is shown
   under "TEAM SCORE — RESEARCH," not a placeholder.
4. **Championship Equity**: same panel; confirm a real percentage under
   "SIMULATED CHAMPIONSHIP EQUITY — RESEARCH" with an "ASSUMED FORMAT"
   note.
5. **Player drawer**: click several different players (Suggestions,
   Players tab, Board). Confirm NWR/Draft sections always populate;
   confirm Roster Impact shows either a real breakdown or an honest
   "not among the top ranked Suggestions candidates" note — never a
   fabricated number either way.
6. **Compare**: Alt+click 2-4 players. Confirm the summary sentence
   cites real numbers already visible in the table, and confirm a
   non-candidate comparison player shows "—"/"Not evaluated," not a
   guessed value.
7. **Rapid capture**: switch to the production Draft Room (`/`), record
   a pick via rapid capture, then switch back to `/draft-room-v2` and
   confirm Suggestions/Team Score/Championship Equity all changed to
   reflect the new roster.
8. **Correction**: use the correction panel (production Draft Room or
   the API) to replace/clear/fill-gap a pick, then confirm Draft Room
   V2's Suggestions refreshed and no longer show the corrected-away
   player as a candidate if now drafted.
9. **Catch-Up**: paste a short multi-pick catch-up, apply it, and
   confirm Draft Room V2 reflects the new state without a manual page
   refresh.
10. **NWR PURE**: toggle "NWR PURE — EXPERIMENTAL" in the Draft Room V2
    header. Confirm the Player Drawer's "Current" section (UDK/external
    alerts) hides when ON; confirm Pick Score/Team Score/Championship
    Equity numbers are unaffected either way.
11. **Historical Replay**: open the "Historical Replay" tab. Confirm the
    panel is clearly labeled "HISTORICAL REPLAY — 2026-09-02" and that
    proxy/NOT_COMPUTABLE values are visibly marked as such, not shown as
    real numbers.

**Please judge**: usability, responsiveness (does a Suggestions refresh
feel comfortably faster than the 60-second clock?), score
*consistency* (does the same pick score twice in a row without a state
change?), whether scores react sensibly to a roster/state change, does
the drawer's reasoning match the numbers shown elsewhere, speed,
crashes/errors/stale-looking state, and confusing UI.

**Please do NOT judge**: whether NWR's Pick Score/Team Score/
Championship Equity are *historically accurate* or well-calibrated —
that is explicitly out of scope for this pass, pending real historical
data (tracked separately with the new Historical Redraft Data lane).

## Final verdict

**`YELLOW_OWNER_TEST_READY_WITH_NAMED_GAPS`**

The real DecisionBundle backend is genuinely wired end to end into Draft
Room V2 — no mock numbers, no static preview scores, no fake Pick Score
values anywhere in the owner-facing candidate surfaces, and every
"cannot calculate" case renders an honest reason rather than a
placeholder. Live recalculation on state change (the directive's own
"critical" requirement) is structurally guaranteed and explicitly proven
for a plain pick, a correction, and Catch-Up. NWR PURE, owner test
instrumentation, and a labeled historical replay preview are all real
and working. The gaps are named, bounded, and non-blocking for an owner
usability pass: no live GUI screenshot this session (environment
constraint, everything underneath it is verified), the KHA replay is a
disclosed proxy pending real historical data from the new lane, and the
AI Explanation API's generated-narrative layer isn't HTTP-routed yet
(the structured evidence it would explain is already fully visible in
the drawer).

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SVeKhFHk5pYE5iRihLvFxy
