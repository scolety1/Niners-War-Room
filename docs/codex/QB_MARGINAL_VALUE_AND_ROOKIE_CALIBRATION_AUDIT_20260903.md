# QB marginal-value and rookie-calibration audit (2026-09-03)

Evidence-only audit, no formula changes made. Confirms two owner-reported
defects with real numbers, traces both to exact code, and stops short of
touching the live ranking formula -- see "Why no fix shipped tonight"
at the bottom.

## QB marginal-value / QB-saturation — CONFIRMED, root cause found

League: real KHA profile, 16-team, true 1QB (`roster.qb=1`, `superflex=0`,
`roster_limits.QB=2`).

The 4 named QBs (Stafford, Maye, Lawrence, Caleb Williams) are ranked
51-94 overall spots earlier than ESPN ADP, and 5.06-7.50 implied rounds
earlier than where the real 16-team room actually took them. This is not
those 4 in isolation: across all 21 QBs actually drafted in the real KHA
recap, mean implied-round gap is **-2.21 rounds**, median **-3.75
rounds** (negative = NWR ranked them earlier than the real draft did).
NWR's own top-30-overall board has 12 QBs in the top 30 (40%) and 19 in
the top 64 (29.7%), in a league that only starts 16 QBs total.

**Root cause, traced to code**: `calculate_replacement_levels()` /
`_position_roster_limit()` in `src/services/redraft_engine_v1_service.py`
derives the QB replacement baseline from how many QBs a team is *allowed
to roster* (`profile.draft.roster_limits.QB = 2` for KHA → replacement
pool depth `16 teams × 2 = 32` → replacement level = QB33, ~123.5 pts),
not from how many actually *start* (1). Roster capacity and expected
roster utilization are different things for a low-value bench position
like backup QB in a 1QB league, and the formula conflates them. On top of
that, `generate_rankings()` sorts purely by `value = projected -
replacement_points` (lines ~1178-1190) with no scarcity/starter-count
dampening layered on afterward -- so a QB10-caliber player's large raw
surplus over a too-deep replacement baseline outranks players at
genuinely scarcer positions.

Notably, `src/services/model_v4_replacement_vorp_core_service.py`
already encodes a shallower, explicitly format-aware QB baseline
(`configured_replacement_rank: 12`, comment: `"10 teams x 1QB;
conservative shallow-league fringe starter"`) but is marked
`review_only_replacement_vorp_core` and is **not** used by the live
`generate_rankings()` path. The codebase already has the right idea in
one place and doesn't use it in the path that actually produces rank.

**This is a genuine formula-structural defect, not a display-order
issue** -- fully reproducible from raw stat data + scoring settings, and
confirmed against 21 real draft outcomes, not guessed.

## Rookie redraft calibration — CONFIRMED, statistically real, uneven

Jeremiyah Love: `nwr_rank=59` (implied round 3.69) vs. real draft slot
(overall #26, round 2) -- 1.69 rounds late, `nwr_vs_espn_gap=-24.8`. Real,
but **not the largest miss in the sample** once the full picture is in.

Matched 12 of the ~14 skill-position rookies actually drafted (RB/WR
only -- no rookie QB/TE cracked the 192 picks) against 135 veterans by
name:

| Group | N | Mean gap (rounds) | Median gap (rounds) |
|---|---|---|---|
| Rookies (all) | 12 | +2.73 | +2.53 |
| Veterans (all) | 135 | +0.47 | -0.13 |
| Veteran RB | 42 | +0.33 | -0.09 |
| Veteran WR | 53 | +1.54 | +0.69 |

(positive = NWR ranked them later/worse than the real draft did)

Rookie RB is ~2.6 rounds later than veteran RB; rookie WR is ~1.1 rounds
later than veteran WR after accounting for a modest league-wide WR
under-ranking. **The pattern is real but uneven**: 4 of 12 rookies
(Jadarian Price, Makai Lemon, KC Concepcion, Jordyn Tyson) landed within
~0.5 rounds of their real slot or were ranked *better* than market;
the largest misses (Caleb Douglas +7.94, Ja'Kobi Lane +6.50, Mike
Washington Jr. +6.19, De'Zhaun Stribling +4.50, Jonah Coleman +4.25) are
mid-to-late-round rookies the real room treated as breakout/role fliers.
Jeremiyah Love's miss is directionally consistent with this pattern but
is not its most extreme instance.

Traced provenance: Love's `current.csv` row carries
`NWR_REDRAFT_2026_ROOKIE_POSITION_ROUND_MEDIAN_V1` -- a historical
outcomes-by-NFL-draft-round baseline. That kind of prior is structurally
backward-looking (what rookies picked in round N historically produced)
and will systematically understate a specific player's current-year
opportunity/buzz signal, which is exactly the shape of miss seen in the
largest-gap rookies above.

**Data-availability caveat**: FantasyPros ECR (`fantasypros_ecr`) is
`API_TIER_NOT_RETURNED` for nearly every rookie in the cheat sheet (in
fact for 599/608 rows overall -- see the Garrett Wilson finding in
`docs/codex/KHA_ANOMALY_INVESTIGATION_20260903.md`), so this audit relied
on ESPN ADP and partial UDK data only; a FantasyPros cross-check isn't
currently possible from data on disk.

## Why no fix shipped tonight

Both defects are real, quantified, and traced to exact functions. Neither
gets a same-night patch:

- `calculate_replacement_levels()` / `generate_rankings()` are the live,
  tested, production ranking formulas real users depend on right now --
  exactly what `docs/codex/CALIBRATION_PLAN.md`'s "no blind tuning" rule
  and `docs/codex/EVALUATORS.md`'s fixture-before-formula-change gate
  exist to protect. A change here is broad-blast-radius (every league's
  rankings, not just KHA's) and has more than one legitimate design
  answer -- shallow-fixed replacement rank, wiring in the existing
  `model_v4_replacement_vorp_core_service.py` baseline, or solving it
  structurally via marginal Team Score value (this lane's stated
  direction, see `docs/codex/NUMERIC_AUTHORITIES_RESEARCH_V1.md`) --
  which one is right is a design decision, not a mechanical bug fix.
- The brief this audit serves is explicit: "make marginal roster value
  solve it," not a hardcoded QB_BAD/NO_QB_EARLY rule *and* not a
  same-night reweighting of the existing formula without the fixture
  process the rest of this repo requires for formula changes.

This document is the evidence handoff for that decision, not the fix
itself.
