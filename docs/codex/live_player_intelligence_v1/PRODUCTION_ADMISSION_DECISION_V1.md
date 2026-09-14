# NWR Live Player Intelligence — Production Admission Decision V1

Worker 4, Work Unit 8, branch `upgrade/nwr-live-player-intelligence-v1-
20260913`, worktree `C:\NWR\live-player-intelligence-v1`. This is the real
production-admission decision the whole cycle (Workers 1-4) has been
building toward, made against the preregistered
`LIVE_PLAYER_INTELLIGENCE_ADMISSION_CONTRACT.md` gates, using ALL real
evidence gathered this cycle: `CANDIDATE_SOURCE_ACQUISITION_V1.md`
(Worker 1), `OFFICIAL_TRUTH_BENCHMARK_V1.md` /
`IDENTITY_MAPPING_V1.md` (Worker 2), `SOURCE_QUALITY_EVALUATION_V1.md`
+ its Worker-4 addendum (Worker 3 + Worker 4 step 1), and this session's
own shadow-consumer plumbing test (`shadow_consumer_test_v1/summary.json`).

**Nothing in this document changes any live recommendation's actual
output.** It is a written verdict, per field/source, using the vocabulary
the directive specified. Where a verdict allows a future wiring pass, that
wiring is explicitly NOT performed in this document or this pass — see
"Work Unit 9" at the bottom.

---

## The honest headline conclusion

**No source/field pair evaluated this cycle clears the full admission bar
for recommendation-affecting integration.** This is a valid, expected, and
fully evidence-based outcome, not a failure of this cycle's work: every
gate that FAILED, failed with real, current, disclosed evidence (Sleeper's
`injury_status`); every gate that could not be measured is honestly
reported as unmeasured rather than assumed or estimated (nflverse's Gate
3/5); and every small-sample finding is flagged as too small for a
confident verdict rather than rounded up into one (Sleeper `ir_pup_nfi`,
n=3; Sleeper `current_team`, n=9).

Two fields — nflverse `injury_designation`/`practice_state` and nflverse
depth-chart `depth_chart_position`/`depth_chart_context` — have real,
clean provenance/identity/rights standing and are judged safe for
**disclosed, non-recommendation-affecting CONTEXT DISPLAY only**, if a
future, separate pass chooses to wire them in that way (this pass does
not). Every other field/source stays at `NO_SOURCE_PASSED`.

---

## Per-field/source verdicts

| Source | Field | Gate 1 (provenance) | Gate 2 (identity) | Gate 3 (agreement) | Gate 4 (coverage) | Gate 5 (freshness) | Gate 9 (rights) | **VERDICT** |
|---|---|---|---|---|---|---|---|---|
| Sleeper `SLEEPER_PUBLIC_PLAYERS_CATALOG` | `injury_designation` | Pass (source/fetched_at/freshness derivable) | Pass (GSIS_DIRECT + `_identity` fallback) | **FAIL — 28.57% vs ≥99%, 1 real hard contradiction (Zay Flowers)** | **FAIL — 32.69% vs ≥95%** | Mixed/contaminated, not cleanly computable | Pass (free, non-commercial) | **NO_SOURCE_PASSED (REJECTED — active failure evidence)** |
| Sleeper | `ir_pup_nfi` / `on_injured_reserve` / `on_pup` / `on_nfi` | Pass | Pass | Not measurable at scale (n=3 real overlap cases, 0 contradictions — directionally clean, not a real measurement) | Not measured (no benchmark list-state field) | Not measured | Pass | **NO_SOURCE_PASSED (insufficient evidence, not a failure — genuinely untested at scale)** |
| Sleeper | `current_team` | Pass | Pass | n=9 non-circular pairs: 88.89% raw / **100% alias-adjusted** | 90.38% broader identity coverage of the 52-player population (a different, looser claim than Gate 4's injury-flag coverage) | Not measured | Pass | **NO_SOURCE_PASSED (n=9 too small for a confident verdict — directionally the strongest finding of this whole cycle, but this cycle's own discipline refuses to round a 9-sample result up into a threshold pass)** |
| Sleeper | `active_inactive` | Pass (field exists, schema-ready) | Pass | Not evaluated (no benchmark concept exists for this cycle) | Not evaluated | Not evaluated | Pass | **NO_SOURCE_PASSED (untested — a future cycle needs its own ground truth for this concept)** |
| nflverse `NFLVERSE_OFFICIAL_INJURY_REPORT` | `injury_designation` / `game_status` (report_status) | Pass | Pass (direct `gsis_id`) | **Not independently measurable this cycle** (the only available benchmark IS this same file — circular; best real independent evidence is Worker 2's 8/8 manual NFL.com spot-check, positive but far too small for a ≥99% claim) | 100% of its own real, narrow official-report population (52/52); 9.22% of the full canonical pool by design (a precise, narrow source, not a broad one) | **Not computable** (no in-row timestamp; ~14.95h of confirmed asset-level stability observed this cycle, still zero captured update events) | Pass (public GitHub release, no restrictive ToS found) | **FREE_SOURCE_CONTEXT_ONLY** for `injury_designation`/`practice_state` (display-only, disclosed, NOT wired this pass) — **`game_status`/the game-day-inactive use case specifically is `PAID_SOURCE_REQUIRED_FOR_GAME_DAY`, see below** |
| nflverse `NFLVERSE_DEPTH_CHARTS` | `depth_chart_position` / `depth_chart_context` | Pass | Pass (direct `gsis_id`) | N/A — structurally not an injury/agreement field | 100% (52/52) of the official-report population; 88.5% of the full canonical pool (Worker 1) — the broadest real coverage of any source this cycle | Real near-daily cadence (177 snapshots, Worker 1), precise P95 not re-measured this pass | Pass | **FREE_SOURCE_CONTEXT_ONLY** (role/context display, NOT wired this pass) |

### The game-day inactive determination (`game_status`) — a separate, decisive call

Gate 5's 10-minute game-day bar is structurally different from the rest of
this table: it is not merely "not yet measured," it is **not measurable
from either free source examined this cycle even in principle, as they
are currently built**. nflverse's injuries file carries no per-row update
timestamp at all (confirmed independently by three different workers).
Sleeper's only candidate timestamp (`news_updated`) is proven CONTAMINATED
(only 12.7% of flagged values fall within 24h; a real 15.1% tail is 180+
days old) — even if Sleeper's `injury_status` itself had passed Gate 3/4
(it did not), this timestamp could never support a 10-minute freshness
claim. No paid vendor was fetched or tested this cycle (out of scope,
consistent with the directive's instruction not to force new paid access)
but Worker 1's historical bakeoff record already identifies named vendors
(RotoWire/SportsDataIO/Sportradar) with solved licensing as the realistic
path for a genuine sub-10-minute, game-day-authoritative feed.

**VERDICT: `game_status` → `PAID_SOURCE_REQUIRED_FOR_GAME_DAY`.** This is
a real, decisive, evidence-based call, not a placeholder: it says plainly
that hard game-day inactive/active determination should not be attempted
on free sources without first re-evaluating a real paid vendor's own
timestamp guarantees against Gate 5's 10-minute bar. The `game_status`
schema field (Work Unit 4) remains populated by ZERO sources today —
correctly unknown, never guessed.

### Why NOT a plain `PAID_SOURCE_REQUIRED` for the ordinary (non-game-day) use case

The 2-hour ordinary-context freshness bar is NOT given the same decisive
paid-source call, because — unlike the 10-minute game-day bar — nothing
this cycle found rules out a free source clearing it in principle; the
real blocker is that no worker has yet run a multi-week polling cadence
long enough to observe a real update event and compute an honest P95 (see
`SOURCE_QUALITY_EVALUATION_V1.md`'s open issue #3 and this session's own
addendum). Declaring `PAID_SOURCE_REQUIRED` here would overclaim what this
cycle actually tested. The honest verdict for ordinary-context
`injury_designation`/`practice_state` freshness specifically is: still
unproven, not yet disqualifying, real path forward exists (multi-week
polling next season/next cycle).

---

## What `FREE_SOURCE_CONTEXT_ONLY` means here, precisely

For nflverse `injury_designation`/`practice_state`/`depth_chart_position`/
`depth_chart_context`: these fields have clean Gate 1/2/9 standing (real
provenance, real identity resolution, real usable rights) and real,
disclosed, non-fabricated evidence on Gates 3/4/5 — they are NOT rejected,
they simply have not cleared the specific numeric bars this contract
requires for anything that would affect a recommendation, roster
eligibility, or automatic pick/suggestion logic. A future, SEPARATE,
deliberate pass COULD wire these in as disclosed, informational-only
display context (e.g., "nflverse reports: Questionable — Ankle" as a label
on Player Drawer, clearly captioned as unverified-for-recommendation
context) without violating this contract, PROVIDED:
  1. The label never feeds any ranking, score, eligibility, or automatic
     recommendation calculation (Gate 10 discipline).
  2. The label visibly discloses it is a free, unverified-for-
     recommendation, automated context signal (never presented with the
     same visual weight as a manual verified override).
  3. Freshness (`fetched_at`) is shown alongside the value so an owner can
     judge its own staleness risk.

**This pass does NOT perform that wiring.** It is explicitly Work Unit 9
territory (a later, separate, more consequential step per the directive)
and is not attempted here — see below.

---

## Composition/precedence engine's real relationship to this decision

`live_player_intelligence_composition_v1_service.py` (Work Unit 6) is
built and tested against ALL fields with ANY real standing (every row in
the table above except Sleeper `injury_designation`, which is structurally
excluded). It implements the exact precedence this decision's verdicts
imply — manual override always wins; a reserved, currently-EMPTY
`ADMITTED_AUTOMATED_FACTUAL_SOURCE` tier for the day a field like
`current_team` or `depth_chart_context` gathers enough evidence to
actually earn that tier; and a `SUPPLEMENTARY_SHADOW_SOURCE` tier for
everything in this table marked `NO_SOURCE_PASSED` or
`FREE_SOURCE_CONTEXT_ONLY` today. The engine is real, tested, and
functionally correct — but it remains entirely unwired to any consumer,
exactly matching this document's verdicts (nothing here cleared the bar
to be wired for real).

---

## Work Unit 9 (hard game-day availability integration affecting recommendations)

**NOT ATTEMPTED.** Per the directive's own explicit instruction: "do NOT
proceed to Work Unit 9 ... unless a field genuinely, clearly passes all
applicable gates with real evidence." No field in the table above clears
Gates 3 AND 5 together with real, independent, threshold-level evidence.
The closest candidate (Sleeper `current_team`) is directionally excellent
but statistically tiny (n=9); the next closest (nflverse `depth_chart_*`)
is the broadest, cleanest real data of the whole cycle but is structurally
a different question (role/context, not availability) and was never
claimed otherwise. This is exactly the "no field cleared the bar this
cycle" outcome the directive said would be a completely valid, expected,
honest conclusion — that is the real, honest conclusion reached here.

---

## What would change this decision in a future cycle

1. **nflverse Gate 3/5**: a genuinely independent, non-circular official
   benchmark (blocked this cycle by NFL.com/PFR's own ToS for automated
   use — Worker 1/2's finding, unchanged), OR a disclosed, explicit,
   owner-accepted risk call to treat the 8/8 NFL.com manual spot-check as
   the practical ceiling of available evidence (a real, different kind of
   decision than this document makes — an owner-level risk acceptance,
   not a technical finding).
2. **nflverse Gate 5**: a multi-week polling cadence (this cycle only had
   Week 1 to observe) to actually catch a real update event and compute
   an honest P95, now cheaply automatable via the real GitHub release-
   asset `updated_at` metadata check this pass added.
3. **Sleeper `current_team`/`ir_pup_nfi`-class fields**: simply more real
   overlap cases — n=9 and n=3 are the actual limiting factor, not a
   quality problem; a larger benchmark (more weeks, or a dedicated
   roster-snapshot ground truth) would likely resolve this quickly given
   how clean the existing small samples already are.
4. **`game_status`/game-day**: a real paid-vendor evaluation against this
   contract's actual 10-minute Gate 5 bar (not attempted this cycle,
   deliberately out of scope per the directive).
5. **Sleeper `active_inactive`**: needs its own dedicated ground-truth
   source; the injury-report benchmark has no comparable concept.
