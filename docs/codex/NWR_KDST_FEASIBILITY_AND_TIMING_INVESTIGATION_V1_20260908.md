# NWR K/DST Historical Model Feasibility + Draft-Timing Investigation (V1)

**Date:** 2026-09-08 (overnight V4 continuation)
**Scope:** Directive V4 sections 16 (K/DST historical direct-model feasibility inventory) and 17 (investigate whether K/DST always landing at rounds 15/16 is a hidden hard rule vs. genuinely opportunity-cost-driven, test counterexamples).

## Part A — K/DST historical direct-model feasibility (section 16)

K/DST are currently `manual` assets in NWR — "NWR has no model for them" (a real, disclosed limitation, not a bug). This is an *inventory* of whether a real, direct projection model (analogous to the existing veteran persistence model) is even feasible from available historical data — not a build.

**Kicker (K)**: real nflverse `load_player_stats` carries exact, distance-bucketed FG data per player-season — `fg_made`/`fg_att`/`fg_missed`/`fg_pct` split by `0_19`/`20_29`/`30_39`/`40_49`/`50_59`/`60_`, plus per-attempt distance lists (`fg_made_list`, `fg_missed_list`) and PAT makes/attempts (`pat_made`/`pat_att`/`pat_pct`). Verified directly (2024 season, 43 K rows) — e.g. Justin Tucker: 22/30 FG, exact distance-bucket breakdown, 60/62 PAT. This is exactly the granularity almost every league's K scoring rule needs (distance-tiered FG points). **Feasibility: real and direct** — a persistence-style model (analogous to the existing veteran skill-position model) could be built from this data with no acquisition gap.

**Defense/Special Teams (DST)**: real nflverse `load_team_stats` carries team-level defensive production — `def_sacks`, `def_interceptions`, `def_fumbles`/`fumble_recovery_*`, `def_tds`, `def_safeties`, `def_pat_blocks`, `def_fg_blocks` (verified directly, 2024 season, 570 team-season rows). The one common DST scoring category not directly in that table — points-allowed tiers — is trivially derivable from `load_schedules`' real per-game `home_score`/`away_score` (the opponent's score each week is the team's own points-allowed that week; verified directly, 285 real 2024 games). **Feasibility: real and direct**, with one extra join step (schedule scores) beyond the team-stats table alone.

**Disposition**: feasible, not built. Building a real, validated K/DST model (own persistence/backtest methodology, own uncertainty bounds, own governance admission) is a real, substantial unit of work on the same scale as the existing veteran/rookie models — correctly scoped as a future candidate, not a same-night addition. This inventory closes the "is the data even there" question with a real, verified yes for both positions, which is the actual blocker this section asks to resolve.

## Part B — Is the K/DST rounds-15/16 timing pattern a hidden hard rule? (section 17)

Every multi-league mock battery this session (8/10/12/16-team 1QB + Superflex, all real 16-round leagues) observed K/DST landing at rounds 15/16 with zero exceptions. Traced the real mechanism (`_forced_position()`, `redraft_draft_room_v1_service.py:2520`) and tested real counterexamples rather than assuming from the code alone.

**Real finding: it's both, layered — not an either/or.**

1. **A genuine, position-agnostic, urgency-driven dynamic check runs first** (lines 2530-2539): whenever `picks_remaining <= count(still-unfilled required positions)`, it force-picks the FIRST unfilled required position in priority order (`QB, RB, WR, TE, K, DST`) — real opportunity-cost logic, not K/DST-specific. **Counterexample tested and confirmed**: a 16-round league where the owner is still short a required WR at round 15 (in addition to K/DST) — the function returns `'WR'` at rounds 13 through 16, never `'K'`, proving real skill needs correctly take priority over K/DST even deep into the draft when they're genuinely still short.

2. **A real, explicit, K/DST-specific hard rule also exists** (lines 2540-2544): `if round_number >= profile.draft.rounds - 1: force K, then DST`. **Counterexample tested and confirmed this is NOT redundant with #1**: a 16-round league where only K is unmet (DST already filled) — at rounds 13-14 nothing is forced (`None`, the dynamic check's own math doesn't yet require it); at rounds 15-16 the function returns `'K'` specifically because of this explicit rule, not the dynamic check (whose own condition, `picks_remaining(2 or 1) <= still_required(1)`, is FALSE at round 15). This is a real, independently-firing backstop, not dead code.

3. **It is NOT a fixed "round 15" constant.** The hard rule is `rounds - 1`, computed from the real `profile.draft.rounds`, not hardcoded. Verified directly across 4 different `rounds` configurations by calling `_forced_position` directly: a 16-round league forces at round 15 (matches every real observed mock); a 10-round league forces at round 9; a 20-round league forces at round 19; a 12-round league forces at round 11. Every mock battery this session used a real 16-round league, which is exactly why "15/16" was the only pattern ever observed — a shorter or longer league would show a different, but equally deterministic, pair of rounds.

**Conclusion**: the "K/DST at 15/16" pattern is real, correctly-designed, two-layer behavior — genuinely opportunity-cost-driven for the common case (and correctly deprioritizes K/DST behind real skill needs, per the WR counterexample), backed by a real, disclosed, round-count-relative hard deadline (not a hidden magic number) that only activates in the narrow edge case where the dynamic check's own urgency math would otherwise leave K/DST undrafted. No change proposed — this is working as designed and is now verified, not merely assumed.

## Verification

All read-only: direct `_forced_position()` calls with synthetic profiles/rosters (no real board touched), plus real `nflreadpy` pulls for the feasibility inventory. Both real boards re-verified byte-identical before and after.
