# NWR Draft Room V2 — Owner Feedback Closure, Pass V3 (2026-09-06)

## 0. Build state recovered before editing

- Worktree: `C:\Users\codex-agent\orca\workspaces\Niners-War-Room\draft-upgrade-hq`
- Branch: `work/nwr-draft-upgrade-hq-v1-20260903`
- HEAD at close of this pass: `04d8d5905de3ed82114380dabe3789f41e42ff22`
  ("feat: Draft Room V2 owner-feedback pass -- disclosure, filters, Action/Value split"),
  preceded by `aebea94b` ("fix: need-aware shortlist diversity, honest Make-It-Back trials, real position filter").
- Frontend route under test: Vite dev server, `http://127.0.0.1:1422/#/draft-room-v2`
  (HashRouter; confirmed the real, GUI-rendered Draft Room V2, not Legacy `pages.tsx`).
- Backend under test: standalone `scripts/run_nwr_desktop_api.py`, port 18742, `--mode redraft`,
  `NWR_REDRAFT_HOME=C:\Users\codex-agent\AppData\Local\Temp\nwr_gui_test_root`. Restarted mid-pass
  to load this pass's backend changes; the standalone launcher requires a bounded, single-line JSON
  `{"apiToken": "...", "startupProofKey": "..."}` on stdin (a real, pre-existing hardening gate,
  `read_startup_credentials` in `scripts/run_nwr_desktop_api.py`) — supplied the same
  `nwr-desktop-development-token-only-000000000000` default dev token the browser API client falls
  back to (`desktop/packages/api-client/src/index.ts`) plus a distinct proof key, both piped via a
  single `echo '{...}' | python scripts/run_nwr_desktop_api.py ...` invocation. Verified live via
  `curl` with the matching `X-NWR-Desktop-Token` header (200) before any GUI re-check.
- Active profile at verification time: `TEMPORARY_QA_CONFIG_UNVERIFIED_REAL_LEAGUE_SETTINGS`
  (10-team, Half-PPR, 1QB — the owner-directed temporary QA config from the unresolved 403 N 18th
  ESPN league; see memory `nwr-403-n-18th-espn-league-unresolved`). Draft state: on the clock at
  overall pick 69 (round.pick "7.09"), QB unfilled, RB 2/2, WR 2/2, TE 1/1, FLEX 1/1 — the exact
  roster shape from the owner's original bad-recommendation screenshot (section 1 of the directive).
- Legacy Draft Room (`pages.tsx`), real league boards, historical datasets, and frozen model
  artifacts: untouched this pass (no diffs touch those files or any `src/model_v4` scoring
  coefficients).

This pass continues directly from `NWR_DRAFT_ROOM_CONSOLIDATION_V1_REPORT_20260906.md` and
`NWR_DRAFT_ROOM_STABILIZATION_RECONSTRUCTION_V2_REPORT_20260906.md`. It does not repeat their
findings; see those reports for the original candidate-collapse bug, the Raw Action Value wiring,
and the P0 self-contained-workflow rescue. This report covers only what changed in this pass.

## 1–2. Repeated-score root cause (traced, not re-tuned)

Reproduced the owner's screenshot directly: a Round-7, 10-team practice draft, pick 69, with QB the
only open need. Traced the pipeline candidate-by-candidate:

- Candidate identity and eligibility: correct (all 8 shortlisted candidates were real, legally
  draftable players).
- Current roster: correctly read (QB 0/1, RB/WR/FLEX filled, TE 1/1).
- Candidate-conditioned completion (`evaluate_pick_candidates` / `simulate_pick_now`): each
  candidate is forced, then the **entire rest of the draft** is completed via the same market/CPU
  logic. This is a full 16-round projection, not an isolated single-pick delta — already disclosed
  via UI tooltips from the prior pass, re-confirmed unchanged this pass.
- Feature vector → raw Team Score (`team_score()` / `optimal_starting_lineup_value()`): **this is
  where distinctions disappear.** The formula counts only players who make the projected *optimal
  starting lineup*. A bench-tier RB/WR candidate who does not crack the starting lineup in the
  completed-draft projection is byte-identical in raw `roster_value` to any other bench-tier
  candidate, regardless of identity — verified directly by comparing raw (non-percentile)
  `roster_value` across 6+ candidates in the reproduced scenario. This is a genuine, structural
  property of the frozen, historically-validated Team Score formula (see memory
  `nwr-team-score-v1-frozen-2016-burned`), not a bug, and it is **not touched** by this pass.
- Reference population / calibration → Equity → Pick Score: `pick_score()`'s `relative_score` is
  purely a min-max normalization of `championship_equity().win_probability` within the candidate
  set. When the underlying Team Score inputs tie, the equity simulation and the resulting Pick
  Score tie too — the tie is inherited honestly, not manufactured or hidden.
- Cross-check: the RAV / Decision-Quality (V2) pipeline, built in a prior pass, **does** correctly
  differentiate in this exact scenario (QB = 100 DQP; the tied RB/WR bench options = 0 DQP),
  proving the model is semantically correct once you look past Pick Score / Team Score alone. This
  is why this pass's UI fixes lean on the existing DQ/RAV signal (via the need-aware shortlist,
  below) rather than inventing new Team Score separation.

No coefficients, reference population, or calibration were changed to produce this finding or in
response to it. Per the directive: this is reported as "the model can't distinguish these on Team
Score alone at the bench tier," not relabeled as a fixed number or a new isolated single-pick value.

**Status: VERIFIED** (root cause traced and disclosed). Explicit EVALUATED / NOT_EVALUATED /
DATA_LIMITED / UNSUPPORTED labeling beyond the existing DQ "n/a" convention (the rest of section 2)
is **OPEN** — not addressed this pass.

## 3. Make-It-Back honesty

Added `make_it_back_trials` end to end: `CostOfWaitingV2Result.trials` (a real Monte Carlo trial
count, already computed, previously discarded) → `CandidateBundle.make_it_back_trials` →
`desktop_facade` JSON (`makeItBackTrials`) → `DecisionBundleCandidate` TS contract →
`formatMakeItBack()` in the frontend, which renders a literal 100% as `"100%*"` with a tooltip
reading "Survived all N simulations — not a guarantee." The ADP-heuristic fallback path
(`historical_decision_state_service.py`, used when the real Monte Carlo path is unavailable) has no
real trial count and reports `null` rather than fabricating one.

No cap, no fabricated reach probability, no rounding change to the underlying probability — this is
purely an additive disclosure field.

**Live verification:** reproduced scenario showed `Quinshon Judkins` / `David Montgomery` /
`Ladd McConkey` / etc. at `100%*` (tooltip discloses the trial count and non-guarantee framing);
`Baker Mayfield` at `40%`; `Rhamondre Stevenson` / `Parker Washington` at `0%` (position-filtered
rows, no trial data attached to those specific candidates in this bundle).

**Status: VERIFIED.**

## 4–5. Roster-aware shortlist (the Kyle-Pitts-then-another-TE bug)

Rewrote `diversify_candidate_shortlist()` (`decision_bundle_live_service.py`, mirrored into
`decision_bundle_live_service_v2.py`) from a pure round-robin position selector to:

1. A **need-gated coverage pass** — reuses the existing `_roster_need_adjustment()` helper (already
   used elsewhere in the codebase for roster-need scoring; not a new heuristic) to decide which
   positions are worth guaranteeing shortlist coverage for. A position the current roster has
   already filled (e.g. TE at 1/1) is not artificially guaranteed a slot.
2. A **60%-of-max domination cap** (e.g. 4 of 8 candidates) replacing the old implicit ~2-per-
   position round-robin outcome — loose enough that a genuinely superior 3rd WR is never excluded
   just to hit a quota, tight enough that one position can no longer occupy 7 of 8 slots (the
   original bug).
3. A cap-relaxation fallback so the shortlist is never artificially starved if too few legal
   candidates exist at the needed positions.

**Live verification (reproduced scenario, TE 1/1 filled):** the shortlist contains **zero TE
candidates** — the two backup-TE rows from the original bug report are gone, replaced by real QB/
RB/WR options. Confirmed via the same UI render used for the section 1/2 trace: QB (`Baker
Mayfield`, the genuinely needed position) carries Pick Score 100 and DQP 100, matching the "the
model already prefers QB once you look at DQ" finding above.

This does not ban all backup TEs outright — a TE that independently ranks well enough to survive
the domination cap can still appear (covered by a new unit test); it only stops TE from being
*force-included* to satisfy a stale round-robin quota once the position is filled. No hardcoded
age penalty or player-specific exclusion was added for Kelce/Goedert/Pitts.

**Tests:** `tests/test_decision_bundle_live_service.py` — 5 new tests (need-gating excludes a filled
position; an unneeded position still surfaces if it independently ranks well; `needed_positions=None`
falls back to full coverage for backward compatibility; the position filter returns real eligible
players rather than a false "no candidates"; `ALL` behaves like no filter) plus 2 updated assertions
(the old `<=3`/`<=2`-per-position round-robin bound loosened to the documented `<=4`, a real,
intentional design choice — still a major improvement over the original 7-of-8 QB-dominated bug).
All 17 tests in the file pass.

**Status: VERIFIED** (live-reproduced and unit-tested).

## 6. "Take RB now, wait on QB" counterfactual reaching the live UI

**Status: OPEN.** Not verified this pass. The existing Compare tab and cost-of-waiting pipeline are
unchanged and structurally capable of this comparison (Compare already surfaces `costOfWaiting` and
`makeItBackProbability` per candidate using the same lookahead), but no live run was performed this
pass to confirm the lookahead actually reaches the specific later turn the owner's Maye-at-47/
Stafford-later example requires, or to disclose a horizon miss if it doesn't. Flagging as a
concrete remaining gap rather than claiming it works.

## 7. Action vs. Value split

Added `splitActionValue(action, nwrRank, marketExpectedPick, currentPick, teamCount)` — a pure
function reusing the exact existing `label_pick_decisions()` action string and the already-available
NWR rank / market ADP fields (no second scoring system). It returns:

- **Action** ("what to do"): a straight relabel of the existing action enum — Pick now / Consider
  now / Queue for later / Wait until next turn / Review data.
- **Value** ("how the market sees this player right now"): Falling / Reach / Value / Fair /
  Unknown, derived from comparing the current pick against the player's own cited ADP (Falling /
  Reach describe this draft's real-time behavior — has this specific player actually gone later or
  earlier than their own market expectation so far), with a distinct Value label for a real
  ≥10-spot NWR-vs-ADP discount. Missing ADP or current-pick context always renders Unknown, never a
  guessed label.

Applied to both the Suggestions table and the Compare table (each supplies its own real
`currentPick`/`teamCount` from board state — not a stale snapshot).

**Bug caught and fixed before commit:** writing the new unit tests surfaced that the Falling/Reach
branches were inverted in the first draft of this function (a player taken well *before* their own
ADP was mislabeled "Falling" instead of "Reach"). Fixed in the same change, verified via the
corrected tests, not silently re-asserted.

**Live verification:** in the reproduced scenario (ADP not loaded this session — banner reads "ADP:
unavailable"), every row correctly renders **Value: Unknown** rather than a fabricated confident
market label — the honest-degradation path specified by the directive, actually observed live, not
just unit-tested. Action column correctly shows "CONSIDER NOW" / "WAIT UNTIL NEXT TURN" per row.

**Tests:** 6 new `splitActionValue` tests in `draft-room-v2.test.ts` (action-label mapping, missing-
evidence → Unknown, Falling, Reach, Value-discount, Fair). All 117 desktop tests pass; `npm run
typecheck` clean.

**Status: VERIFIED.**

## 8. Position filters using real eligible players

`build_live_decision_bundle()` gained `position_filter`. When set to a real position, it filters the
full legal-candidate pool directly and builds a position-specific bundle (bypassing the diversity
selector entirely), instead of re-filtering the already-diversified 8-person shortlist — which would
have falsely reported "no candidates" for any position the diversity pass didn't happen to surface
that pick. K/DST fall through to the real `manualAssets` list (Player/Status/Draft+Queue) since NWR
does not model those positions; no fabricated advanced score is shown for them.

Wired end to end: `server.py` accepts `positionFilter` as an additional allowed body field →
`desktop_facade.redraft_decision_bundle(position_filter=...)` → `build_live_decision_bundle(...)`.
Frontend: `SuggestionsTab` renders an `ALL|QB|RB|WR|TE|K|DST` chip row; selecting a position other
than ALL passes it through `getRedraftDecisionBundle(profileId, speed, positionFilter)`.

**Live verification:** chip row rendered in the Suggestions panel in the same screenshot used for
sections 1–7 above.

**Tests:** `test_position_filter_returns_real_eligible_players_of_that_position_only` and
`test_position_filter_of_all_behaves_like_no_filter` in
`tests/test_decision_bundle_live_service.py`.

**Status: VERIFIED.**

## 9–11. Three-pane layout, right roster/recent-picks pane, Board By-Picks/By-Roster toggle

**Status: OPEN.** Not addressed this pass. The current layout (as of the prior P0 pass) has a
collapsible left utility pane (Rankings/Teams/Queue) and center tabs (Suggestions/Cheat Sheets/
Draft Board/Compare/Replay), but does **not** yet have the directive's specified right-hand pane
(selected team's roster defaulting to MY TEAM, with a team-inspector dropdown that never changes
active owner/recommendation identity, followed by a recent-picks feed and next-owner-turn info), nor
a Draft Board "By Picks | By Roster" view toggle. This is the largest remaining structural gap.

## 12. round.pick formatting

`formatRoundPick(overallPick, teamCount)` implements the owner's exact formula
(`round = floor((p-1)/N)+1`, `pick = ((p-1) mod N)+1`, zero-padded to 2 digits) and is applied to the
on-clock strip, Draft Board cells, and the board record-pick panel. Verified against both of the
owner's own worked examples in tests (69 @ 10 teams → "7.09"; 47 @ 12 teams → "4.11") and confirmed
live: the reproduced Round-7/pick-69/10-team scenario renders **"7.09"** in the live UI.

**Status: VERIFIED** for the surfaces converted this pass (on-clock strip, board cells, record-pick
panel). Recent-picks list, candidate ADP, and player-detail-drawer round.pick display were not
audited for the same formatter this pass — worth a follow-up sweep before claiming full coverage.

## 13. Global nav retraction

`.sidebar--collapsed` (styles.css) now collapses to zero width (border/padding removed, all children
but the toggle hidden) instead of a permanent narrow rail; a half-pill edge arrow remains visible and
clickable to re-expand.

**Status: IMPLEMENTED_NOT_VERIFIED this pass** — the CSS change was made and typechecks/tests pass,
but no live screenshot of the collapsed state was captured in this session (screenshot tooling was
unavailable in this environment this pass — see Section 21 below); confirmed only by code inspection
carried over from before the interruption.

## 14–15, 17. Not addressed this pass

Cheat Sheets UDK-style lane audit (14), drafted-players-disappear-everywhere canonical-ID audit (15),
and porting ADP refresh/paste/import + pick-correction controls into the consolidated room (17)
remain **OPEN**, carried forward unchanged from before this pass.

## 16. Player-drawer Draft button

Carried into this pass from before the interruption: `PlayerDrawer` now renders a primary Draft
button (disabled off-clock or mid-submission) and a Queue/Queued toggle, reusing the same
`mark()`/`toggleQueue()` capture path as every other draft surface. Not re-screenshotted this pass
(the drawer wasn't opened during this session's live check), but code path is unchanged since the
prior pass's implementation.

**Status: IMPLEMENTED_NOT_VERIFIED this pass** (carried from IMPLEMENTED in the prior pass; no fresh
screenshot this session).

## 18–19. Disclosure discipline

No news/freshness gating, secret-storage handling, or approval/timestamp logic was touched this
pass. All behavioral changes above (need-aware diversify, position filter, Action/Value split) are
UI/shortlist-selection changes layered on top of the existing, frozen scoring pipeline — no
coefficients, reference population, simulation budget, or Pick-Score mapping were modified. Recorded
here per section 19's explicit versioning requirement; nothing in this pass requires re-validation
against historical holdouts.

## 20. Rendered acceptance test matrix (A–P)

**Status: OPEN — not executed as a full matrix this pass.** One live, screenshot-equivalent check
(via `get_page_text`, not a pixel screenshot — the Chrome MCP screenshot tool returned a
"0 width" error in this environment for the remainder of this session) was performed against the
real GUI-capable build at the reproduced Round-7/pick-69/10-team state, confirming sections 1–8/12
above render correctly together. The full 8/10/12/16-team, boundary, degraded-mode, and dual-
viewport (1280×900 / 1650×930) matrix was not executed.

## 21. Launcher/resource handoff

Confirmed this pass: worktree/branch/HEAD as recorded in section 0; Vite dev server on 1422 healthy
(`curl` 200) and serving the correct route; backend on 18742 relaunched with the current code and
verified authenticated (`curl` 200 with the correct `X-NWR-Desktop-Token` header) rather than
trusting a stale background-task notification (one arrived mid-restart from an earlier, already-
superseded launch attempt in this session and was correctly disregarded after independent `curl`
verification). No process was killed by port number alone without first confirming via `netstat`
that the PID was this session's own prior backend instance.

## 22. Checklist and verdict

| # | Requirement | Status |
|---|---|---|
| 0 | Build-state recovery | VERIFIED |
| 1–2 | Repeated-score root cause traced, honestly labeled | VERIFIED (trace); explicit EVALUATED/NOT_EVALUATED/DATA_LIMITED taxonomy beyond DQ's "n/a" — OPEN |
| 3 | Make-It-Back trial-count disclosure | VERIFIED |
| 4–5 | Need-aware shortlist (Pitts→TE bug, over-diversification) | VERIFIED |
| 6 | RB-now/wait-on-QB counterfactual reaches UI | OPEN |
| 7 | Action vs. Value split | VERIFIED |
| 8 | Real position filters | VERIFIED |
| 9–11 | Three-pane layout, right roster/recent-picks pane, Board By-Roster toggle | OPEN |
| 12 | round.pick formatting | VERIFIED (on-clock/board/record-pick surfaces); recent-picks/ADP/drawer surfaces not yet audited |
| 13 | Global nav full retraction | IMPLEMENTED_NOT_VERIFIED (no live screenshot this pass) |
| 14 | Cheat Sheets UDK-style audit | OPEN |
| 15 | Drafted-everywhere canonical-ID audit | OPEN |
| 16 | Player-drawer Draft button | IMPLEMENTED_NOT_VERIFIED (carried from prior pass; not re-screenshotted) |
| 17 | Port ADP refresh/paste/import + pick-correction controls | OPEN |
| 18–19 | Disclosure/versioning discipline | VERIFIED (no scoring-pipeline changes this pass) |
| 20 | A–P rendered acceptance matrix | OPEN (one live spot-check done; full matrix not run) |
| 21 | Launcher/resource handoff | VERIFIED |
| 22 | This report/checklist | VERIFIED (this document) |

Commits this pass:
- `aebea94b` — backend: need-aware shortlist diversity, honest Make-It-Back trials, real position filter.
- `04d8d590` — frontend: round.pick formatting, Make-It-Back disclosure, position filter UI, Action/Value split, player-drawer draft button (carried), fully-retracting nav (carried).

No push, merge, deploy, or model retraining performed. Both commits are local to
`work/nwr-draft-upgrade-hq-v1-20260903`.

**Final verdict: `YELLOW_OWNER_FEEDBACK_INCOMPLETE`.**

Sections 6, 9–11, 14, 15, 17, and the full section-20 test matrix remain open; sections 13 and 16
are implemented but not freshly re-verified live this pass. This pass closes sections 3, 4–5, 7, and
8 completely (root-caused, fixed/added, unit-tested, and live-verified against the owner's own
reproduced scenario), and re-confirms 12 for the surfaces it touched. The next pass should prioritize
the right-hand roster/recent-picks pane and Board By-Roster toggle (9–11, the largest structural
gap) and the full rendered acceptance matrix (20), then re-run this checklist before considering a
GREEN verdict.
