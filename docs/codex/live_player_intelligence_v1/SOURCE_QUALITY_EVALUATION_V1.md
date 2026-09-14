# NWR Live Player Intelligence — Source Quality Evaluation V1

Work Unit 5, branch `upgrade/nwr-live-player-intelligence-v1-20260913`,
worktree `C:\NWR\live-player-intelligence-v1`. Computes REAL Gate 3
(official factual agreement), Gate 4 (coverage), and Gate 5 (freshness)
numbers against `LIVE_PLAYER_INTELLIGENCE_ADMISSION_CONTRACT.md` (the
preregistered gates, unweakened here even where a source falls short),
using Worker 2's real 182-row `official_truth_benchmark_v1/` and
`identity_mapping_v1/` build. Reproducible via
`python scripts/build_live_player_intelligence_source_quality_v1.py`
(reads only already-fetched local files, no network I/O of its own); the
exact machine-readable numbers are committed at
`source_quality_evaluation_v1/summary.json`.

**THIS DOC IS PRELIMINARY EVIDENCE, NOT A PRODUCTION ADMISSION DECISION.**
Work Unit 8 (a later, separate worker) makes the actual promotion call
after shadow-mode consumer testing. Nothing here is wired into
`PlayerAvailabilityStatus`, any consumer of it, or any recommendation
path.

---

## Real data this pass added (beyond what Worker 2 left)

To get a real, non-degenerate Gate 5 data point for nflverse injuries,
this pass performed **two additional real polls** on top of Worker 1's
original 2026-09-13 pull and Worker 2's 2026-09-14 02:52:46Z pull:
another fresh pull at `2026-09-14T03:19:59Z` (preserved alongside the
prior two as
`local_exports/.../nflverse_injuries/{wu1_snapshot_20260913,
wu2_snapshot_20260914_0303,latest}/`). **Zero rows changed across all
three polls** (spanning ~27 minutes). Real, honest evidence of stability
at *this specific point* in Week 1 — not proof the file never revises
(Worker 1's own two-day-apart diff already showed it does, `Out` 27→31
between 2026-09-11 and 2026-09-13) — and NOT sufficient to derive a P95
latency figure, since no update *event* occurred inside the observed
window (see Gate 5 below).

---

## GATE 4 — Coverage

**Population**: the real official-report, fantasy-relevant players this
pass can identify inside NWR's own governed 564-player pool. Of the
benchmark's 182 rows, 53 carry a fantasy-relevant position
(QB/RB/WR/TE/K); of those, 52 resolve to exactly one canonical NWR
`player_id` via direct `gsis_id` match (`MATCHED_GSIS_DIRECT`, same
identity resolver as everywhere else in this codebase). The 53rd,
**Jonathon Brooks (RB, CAR)**, is real and correctly on the official
report but is **not a member of NWR's governed pool at all** — a
different, already-documented exclusion (this project's own
"Brooks-class" evidence-backed holdout finding, unrelated to Gate 4) —
so he is reported separately, not folded into the population: no source
in NWR's pipeline could ever "cover" a player NWR itself doesn't track.

**Population size = 52.**

| Candidate | Covered | Coverage ratio | ≥95% gate |
|---|---|---|---|
| **Sleeper `injury_status`/`status` (flagged subset)** | 17 / 52 | **32.69%** | **FAIL** |
| nflverse depth charts (role/context only — not an injury field, directional) | 52 / 52 | 100.00% | PASS (not a Gate-3-relevant field) |

Sleeper's shadow-record builder (`build_sleeper_shadow_records`, existing
production-adjacent code, unmodified) only emits a record for a player
carrying a real `injury_status` or a non-`Active` `status` — i.e. "does
Sleeper surface *any* status for this player at all" is exactly what Gate
4 asks. Of the 52 real official-report players, Sleeper surfaces a
flagged record for only 17 — **35 of the 52 (67.3%) have no Sleeper
signal whatsoever this week**, a hard, real, far-below-threshold failure.
14 of the 17 matched via the existing `NAME_POSITION_TEAM` identity
fallback, not `GSIS_DIRECT` — Sleeper's own `gsis_id` field is frequently
empty even on flagged rows (e.g. Zay Flowers, BAL, confirmed empty in the
raw pull), consistent with this codebase's already-documented Sleeper
`gsis_id` sparsity.

nflverse depth charts (which carries **no injury field of its own** — see
Gate 3) maps all 52/52 of the same population by role/depth-chart
context, real and notable as a broad, reliable identity/context source,
but this is a coverage number for a *different concept* (role, not
injury), reported here only because it is directly measurable from the
same population and relevant to the `depth_chart_position`/
`depth_chart_context` factual fields added in Work Unit 4.

---

## GATE 3 — Official factual agreement

### (a) nflverse injuries vs. the benchmark — CIRCULAR, disclosed as such

The benchmark **is** `injuries_2026.csv` (Worker 2's own disclosed
caveat). Comparing the 52 matched benchmark rows' `reportStatusCategory`
against itself trivially returns:

| | |
|---|---|
| Comparable pairs | 52 |
| Exact agreements | 52 |
| Agreement ratio | **100.00%** (by construction) |
| Hard contradictions | 0 |

**This is not real evidence of nflverse's factual accuracy** — it proves
only that the computation logic is correct on identical inputs. The best
*real*, independent evidence for nflverse's designation accuracy remains
Worker 2's 8/8 manual NFL.com spot-check (`OFFICIAL_TRUTH_BENCHMARK_V1.md`)
— real, positive, but a small sample, not a ≥99%-threshold-shaped
measurement. **Gate 3 cannot be honestly scored PASS/FAIL for nflverse
injuries against an independent benchmark this cycle** — the benchmark
methodology this project's own rights constraints allow does not produce
one. This is a real, disclosed limitation, not a gate result.

### (b) Sleeper `injury_status` vs. the benchmark — THE MEANINGFUL COMPARISON

For the 17 benchmark players Sleeper covers (Gate 4 above), Sleeper's
`injury_status` is normalized into the SAME `OUT`/`DOUBTFUL`/
`QUESTIONABLE`/`CLEARED_OR_NOT_LISTED` vocabulary the benchmark uses
(`normalize_sleeper_designation`). 3 of the 17 carry a Sleeper value that
is a real but *different* concept — a roster-list state (`IR`) — and are
excluded from the exact-agreement denominator (a different question, not
a miss) but ARE still checked for hard contradiction:

| | |
|---|---|
| Comparable pairs (both sides carry a real weekly designation) | 14 |
| Exact agreements | 4 |
| **Agreement ratio** | **28.57%** |
| **≥99% gate** | **FAIL — badly** |
| **Zero-hard-contradiction floor** | **VIOLATED — 1 real case found** |

**The real hard contradiction**: Zay Flowers (WR, BAL) — benchmark
`reportStatusCategory = CLEARED_OR_NOT_LISTED` (no designation — the
official report treats him as healthy this week) vs. Sleeper
`injury_status = "Out"`. Sleeper's own `news_updated` for this exact
player is `2026-09-14T02:00:58Z`, only ~52 minutes before this pass's
`fetched_at` (`02:52:46Z`) — i.e. this is a genuinely *recent* Sleeper
value, not visibly stale, which makes the contradiction more concerning,
not less: this is evidence of a real, current factual disagreement
between the two sources at the same point in time, not an artifact of
comparing a fresh benchmark against a stale candidate snapshot.

**Full disagreement table** (14 comparable pairs; ✓ = exact agreement):

| Player | Team | Benchmark | Sleeper `injury_status` | Agree? |
|---|---|---|---|---|
| Tua Tagovailoa | ATL | OUT | Out | ✓ |
| Brock Bowers | LV | OUT | Out | ✓ |
| TreVeyon Henderson | NE | OUT | Out | ✓ |
| Oscar Delp | NO | OUT | Out | ✓ |
| Zay Flowers | BAL | CLEARED_OR_NOT_LISTED | Out | ✗ (hard contradiction) |
| Devontez Walker | BAL | QUESTIONABLE | Out | ✗ |
| Ty Johnson | BUF | QUESTIONABLE | Out | ✗ |
| Tyson Bagent | CHI | QUESTIONABLE | Out | ✗ |
| Alec Pierce | IND | CLEARED_OR_NOT_LISTED | Questionable | ✗ |
| Alvin Kamara | NO | QUESTIONABLE | Out | ✗ |
| Kene Nwangwu | NYJ | DOUBTFUL | Out | ✗ |
| Tory Horton | SEA | QUESTIONABLE | Out | ✗ |
| Sean Tucker | TB | DOUBTFUL | Out | ✗ |
| Jalen McMillan | TB | DOUBTFUL | Out | ✗ |

(Excluded from the ratio, but hard-contradiction-checked and clean:
Malik Davis/DAL, Tim Patrick/NYJ, Eli Stowers/PHI — all Sleeper `IR`
against a benchmark `OUT`/`OUT`/`OUT`, a real, consistent, non-contradictory
relationship — IR implies OUT, no conflict.)

**Real, disclosed pattern** (observation only, not a causal claim this
pass can prove): in every disagreement, Sleeper's value is the SAME OR
MORE SEVERE than the benchmark's (`Out` where the benchmark says
`Questionable`/`Doubtful`/nothing at all — never the reverse). This is
consistent with either (i) Sleeper genuinely lagging an in-week upgrade
from an earlier, worse designation, or (ii) Sleeper's `injury_status`
vocabulary meaning something systematically broader than "this week's
official game-status designation." This pass did not gather enough
evidence to distinguish between those two explanations and does not
claim to.

---

## GATE 5 — Freshness

### nflverse injuries

**Not computable this session — honestly reported as such, not
estimated.** The file carries no per-row update timestamp (confirmed by
Worker 1/2 and re-confirmed here). This pass's own three real,
successive polls (`wu1_20260913_0252 → wu2_20260914_0303 →
wu3_20260914_0319`, ~27 minutes total) show **zero changes** — real
stability evidence at this specific point in Week 1 (consistent with
Week 1 games already underway and the league's documented Friday
4:00 PM final-designation deadline having passed), but since no update
*event* occurred inside the polling window, there is nothing to time —
a P95 latency figure cannot be derived from an interval with zero
observed transitions. Worker 1's separately-disclosed two-day-apart diff
(`Out` 27→31 between 2026-09-11 and 2026-09-13) proves the file DOES
revise earlier in a week, but a ~2-day observation granularity is far too
coarse to produce a P95 figure against either of Gate 5's real bars
(2-hour ordinary-context, 10-minute game-day). **A real P95 for this
source requires either an intra-week polling cadence maintained across
multiple real weeks (this cycle only has Week 1 to observe), or a source
with an actual per-update timestamp.**

### Sleeper `injury_status`

A real, usable per-player signal exists (`news_updated`, epoch-ms) that
does not exist for nflverse — but it is **not a clean Gate-5 measurement**
and this pass does not claim a P95 from it:

| | |
|---|---|
| Flagged population (real `injury_status`, non-NA) | 722 |
| P50 latency (fetch time − `news_updated`) | ~14.2 days |
| P95 latency | ~398 days |
| Max latency | ~2,921 days (~8 years) |
| Min latency | ~26.8 minutes |

**Why this P95 is not admissible as a Gate 5 figure**: only 92/722
(12.7%) of flagged players' `news_updated` values fall within 24 hours of
this pull; a real, non-trivial tail — 109/722 (15.1%) — is **180+ days
old**, and multi-year-old values (2019/2022/2023) were directly observed
elsewhere in the same raw pull on other players. This proves
`news_updated` is a whole-record "last touched for any reason" field
(name changes, team changes, roster moves — anything), **not** a field
Sleeper specifically re-stamps every time `injury_status` changes. The
raw P50/P95 above are reported in the committed JSON artifact for full
transparency, but are explicitly **not** presented as Gate 5 evidence.
The **real, honest, directional finding** is the age-bucket distribution
itself: a genuine near-real-time subset exists (92 players updated within
24h — positive evidence SOME status changes reach Sleeper's record
quickly) alongside a genuine stale subset (109+ players 180+ days old —
positive evidence the field is unreliable as a general freshness clock
for the *whole* flagged population). Neither Gate 5 bar (2h ordinary,
10min game-day) can be honestly scored PASS or FAIL from this evidence;
it can only be honestly characterized as **mixed and field-contaminated**.

---

## PRELIMINARY SOURCE × FIELD VERDICTS

Preliminary only — Work Unit 8 (a later worker, after shadow-mode
consumer testing) makes the real production-admission call. No
`RIGHTS_BLOCKED` verdict applies to any source/field evaluated here
(Worker 1's NFL.com/PFR rights finding affects only the *benchmark's* own
independence, already disclosed — it does not itself rights-block
nflverse's public GitHub release data or Sleeper's public API, both
already separately characterized as free/keyless with no restrictive
terms found for nflverse, and free-for-non-commercial-use for Sleeper).

| Source | Field | Gate 3 | Gate 4 | Gate 5 | Preliminary verdict |
|---|---|---|---|---|---|
| nflverse injuries | `injury_designation` / `game_status` (report_status) | Not independently measurable this cycle (circular — IS the benchmark) | 100% of official-report population by definition; 9.22% of full canonical pool (expected — narrow, precise source) | Not computable this session (no per-row timestamp; 0 real update events observed) | **SHADOW** — real, precise, narrow signal; best available evidence (8/8 NFL.com spot-check) is positive but not a ≥99%-threshold measurement; cannot be promoted on Gate 3/5 evidence that doesn't yet exist |
| nflverse injuries | `practice_state` | Same as above (not independently measurable) | Same as above | Same as above | **SHADOW** |
| Sleeper | `injury_designation` (`injury_status`) | **FAIL** — 28.57% exact agreement vs ≥99%; 1 real zero-tolerance hard contradiction found (Zay Flowers) | **FAIL** — 32.69% vs ≥95% | Mixed/field-contaminated, not cleanly computable | **REJECT** for this field — fails two hard gates with real, current-week evidence, including the zero-contradiction floor Gate 3 treats as non-negotiable |
| Sleeper | `ir_pup_nfi` / `on_injured_reserve` / `on_pup` / `on_nfi` (roster-list state) | Not measured this pass (benchmark has no comparable list-state field — only 3 real overlap cases observed, all non-contradictory with the benchmark's OUT designation) | Same population as above; small n | Same as above | **SHADOW** — too little independent evidence yet either way; the 3 real overlap cases (Malik Davis/Tim Patrick/Eli Stowers, all Sleeper `IR` against benchmark `OUT`, zero conflicts) are directionally reassuring but not a real measurement |
| Sleeper | `current_team` / `active_inactive` (roster fields) | Not evaluated this pass (no benchmark field to compare against — team/active-inactive isn't part of the injury-report benchmark) | Not evaluated this pass | Not evaluated this pass | **NOT EVALUATED** — needs its own benchmark/ground-truth, out of this pass's scope |
| nflverse depth charts | `depth_chart_position` / `depth_chart_context` | **N/A** — carries no injury field at all, nothing to compare | 100% (52/52) of the official-report population, role/context only | Near-daily cadence, real per-snapshot `dt` (characterized by Worker 1, not re-measured here) | **SHADOW** — strong coverage/cadence, but Gate 3 is structurally inapplicable to this field and Gate 5's precise P95 wasn't re-measured this pass |

---

## What this pass did NOT do

- Did not compute Gate 4/3 for `current_team`/`active_inactive`/roster
  fields (no benchmark exists for those concepts — a future worker's
  job, needs its own ground-truth source, not the injury-report
  benchmark).
- Did not re-measure nflverse depth charts' Gate 5 cadence precisely
  (Worker 1 already characterized it as near-daily/177 snapshots; this
  pass did not repeat that measurement).
- Did not attempt to resolve WHY Sleeper's `injury_status` disagreements
  are directionally more-severe-than-benchmark (real, disclosed pattern,
  not explained).
- Did not wire anything into `PlayerAvailabilityStatus`, any consumer, or
  any recommendation path — this remains a preliminary evaluation only.
