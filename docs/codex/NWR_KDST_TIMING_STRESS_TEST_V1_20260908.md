# K/DST Timing Dynamic-Policy Stress Test — V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 10. Extends the prior
session's `NWR_KDST_FEASIBILITY_AND_TIMING_INVESTIGATION_V1_20260908.md` (which already
verified the normal case and a WR-still-needed-late counterexample) across the directive's
full named-scenario list. All read-only: direct `_forced_position()`/`_roster_candidate_allowed()`
calls with synthetic profiles/rosters, no real board touched.

## Two real, distinct mechanisms (both verified)

1. **`_forced_position`** (CPU auto-pick backstop): purely a function of THIS team's own
   roster state + round number vs. `profile.draft.rounds` -- never looks at opponents' picks
   or real draft-pool depth at all (verified directly, Scenario 2 below).
2. **The general candidate-scoring path** (`_select_asset`'s market-ADP branch, same
   function `_forced_position` doesn't touch): K/DST candidates remain in the real, scored
   candidate pool throughout the draft, competing on real market ADP + need-adjustment like
   any other position -- if a real K/DST's market ADP genuinely outscores remaining skill
   options, it CAN win a pick naturally, correctly labeled `behavior="MANUAL_UNMODELED"`
   (never silently presented as an NWR-driven recommendation). This is the real "K/DST can
   move earlier when rational" pathway the directive asks to verify exists.

## Scenario results

| Scenario | Result |
|---|---|
| 1. Normal 8-team, 16 rounds, skill starters filled | K forced round 15, DST forced round 16 (baseline, matches every real mock this session) |
| 2. 12-team, opponents run early on DST | **Zero effect** on this team's own timing -- `_forced_position` never receives opponents' state at all (real, disclosed limitation, not a bug: this is a per-team deadline/need policy, not a league-wide scarcity model) |
| 3. 16-team scarcity, deep bench (bench=10, 19 rounds), skill filled | K forced exactly at round 18 (`rounds-1`), **not** before (round 17: `None`) -- deadline scales correctly with real round count, unaffected by bench depth or team count |
| 4. Shallow bench (bench=1, 10 rounds), skill filled | K forced exactly at round 9 (`rounds-1`), round 8: `None` -- same real, round-relative deadline logic holds at the opposite bench-depth extreme |
| 5. Roster starters filled EARLY (round 6), K/DST open | `None` at both round 6 and round 10 -- **K/DST never becomes a routine early recommendation** just because starters finished early; only the real deadline/urgency math triggers a force |
| 6. Owner missing 2 WR + 1 RB late (round 14-16, 16-round league) | Real skill need (`RB`, first in priority order) wins at rounds 14, 15, **and 16** -- even the final pick. Honest finding below. |
| 7. K2/DST2 in a normal 1K/1DST league | **Structurally impossible**, not merely rare: `_roster_candidate_allowed` returns `False` unconditionally once `roster[K] >= profile.roster.k` (no +1 backup allowance like QB/TE get) |
| 8. Explicit experimental 2-K format (`roster.k=2`) | A second K **is** allowed -- exactly and only because of real, explicit league configuration, never implicit |

## Honest finding from Scenario 6: real K/DST can be legally sacrificed under extreme scarcity

Because the dynamic urgency check (`still_required` in priority order `QB,RB,WR,TE,K,DST`)
runs **before** the hard K/DST deadline check and returns as soon as `picks_remaining <=
count(still_required)`, a team that is short multiple real skill positions with too few real
picks left will keep forcing skill positions even on the literal last pick of the draft --
potentially finishing with no K and no DST rostered at all. Verified directly: with RB/WR/K/DST
all short and only 1 real pick remaining, the function returns `"RB"` at round 16 of a
16-round league, never reaching the K/DST branch. This is arguably the *rational* choice
(a real roster spot filled beats an empty one under genuine scarcity) and is real, disclosed,
intentional behavior -- not a defect -- but it is a real, previously-unverified edge case worth
the owner knowing about: in a sufficiently degenerate draft, NWR's CPU auto-pick logic will
let K/DST go unfilled rather than force them ahead of a real skill shortfall.

## Disposition

No code change. All 8 named scenarios behave as designed: K/DST timing is genuinely
opportunity-cost-driven (never routine-early), backed by a real round-count-relative deadline
(never a hidden magic number), K2/DST2 is structurally blocked outside an explicit
experimental format, and a real market-driven early-K/DST pathway exists and is honestly
labeled when it fires. The one real limitation found (opponent/pool-scarcity blindness) and
the one real edge case found (skill priority can sacrifice K/DST entirely under extreme
scarcity) are both disclosed, not fixed -- neither is a bug against the mechanism's actual,
documented design intent (a per-team deadline/need policy), and "fixing" either would mean
building new, more complex scarcity-aware heuristics well beyond this section's "stress test,
don't redesign" scope.

## Status

Section 10: **DONE.** 8/8 named scenarios verified; 2 real findings disclosed.
