# Numeric authorities research V1 — Player/Team/Championship/Pick scores

Design/research pass for Draft Upgrade HQ section 4 (four numeric
authorities) and section 5 (look-ahead optimizer). This is a design
document, not a calibrated ship — nothing here may be presented to the
owner as decision-ready. Follows this repo's existing governance:
`docs/codex/CALIBRATION_PLAN.md` (no blind tuning), `docs/codex/
ANALYTICAL_NUMBER_PROVENANCE.md` (no hardcoded user-facing numbers),
`docs/codex/EVALUATORS.md` (fixtures + golden values before any formula
ships).

## What already exists and must not be duplicated

Checked before writing this (see agent survey, 2026-09-03):

- **Pick value already exists**: `src/models/pick_values.py` implements
  `FinalPickValue` on a 0-1000 scale (`BRIEF_PICK_VALUE_CURVE_1000`,
  `pick_value()`), wired into `src/services/draft_service.py`. This is a
  **draft-capital** value (what a slot in the draft order is worth), not
  the per-decision "should I take this player right now" concept this
  brief calls PICK SCORE. Reuse, don't replace: PICK SCORE below treats
  `FinalPickValue`/`pick_value_review_score` as one input signal among
  several, not something to reimplement.
- **Replacement level / VORP already exists**: `src/services/
  model_v4_replacement_vorp_core_service.py` defines `REPLACEMENT_DEFAULTS`
  per position (required-starter-rank, configured-replacement-rank) and a
  versioned VORP core. TEAM SCORE's replacement-level component (section 4B)
  should call into this rather than re-deriving replacement thresholds.
- **TEAM SCORE, CHAMPIONSHIP EQUITY, and any Monte-Carlo/look-ahead
  optimizer do not exist anywhere in this repo** (docs or code) — confirmed
  by grep across `src/` and `docs/codex/`. This is genuinely new scope, not
  covered by PROJECT_GOLD's 18-phase roadmap (which is dynasty
  keep/drop/trade decisioning, a different lane this HQ does not own the
  underlying asset-valuation formulas of — dynasty and redraft are
  explicitly separate apps per `desktop/packages/contracts/src/index.ts`
  per `RECONCILIATION_CONFLICTS.md`).
- **Existing "review only" / unvalidated-output convention**:
  `src/services/trust_status_service.py`'s `TrustStatus(status, severity,
  title, message, next_action)` shape, and string labels like
  `REVIEW_ONLY_NGS_CONTEXT`, `review_only_startup_slot_context_not_final_
  recommendation`. The brief's requested `RESEARCH_ONLY_PICK_SCORE` label
  is semantically the same kind of gate this repo already uses elsewhere
  under the `REVIEW_ONLY_*` naming — proposal below uses both: the owner's
  requested literal string as the visible UI label, and a `TrustStatus`-
  shaped object under the hood so it composes with existing gating code
  (e.g. `legacy_label_quarantine_service.py`'s freeze-driven demotion
  pattern) instead of being a one-off.

## A. PLAYER SCORE

Standalone, league-format-specific football value for THIS redraft league
(scoring rules, roster requirements) — distinct from the Dynasty lane's
multi-year asset value (`player_scores.py` / `veteran_scores.py` /
`rookie_scores.py`), which answers a different question over a different
time horizon and is out of this lane's scope to alter.

Proposed shape (research, unvalidated):

```
PlayerScore(player, league_format) =
    project_season_points(player, league_format.scoring_rules)   # from projections/2026/current.csv fields
    adjusted for:
      - format-specific scoring weight (PPR/half/standard, TE premium, etc.)
      - games/availability_probability already present in the projections schema
      - position-specific floor/ceiling spread (projection_low/projection_high already present)
```

Output: a continuous points-based number, not yet bounded to 0-100 — bounding
to a fixed scale before there is real outcome data to calibrate against
would itself be the "arbitrary weighting called validated" failure mode
this brief explicitly prohibits. Keep it in points (or a points-derived
VORP figure, see Team Score) until a calibration pass like
`CALIBRATION_PLAN.md`'s exists for it specifically.

**Not building this from scratch as a black box.** `projections/2026/
current.csv` already carries per-market stat lines (`passing_yards`,
`rushing_tds`, `receptions`, etc.) — scoring-rule-weighted point totals are
a deterministic, auditable transform of columns that already exist and are
governed (see `current.manifest.json`'s `admission_policy`/`approval_*`
fields). No new data source required for the skill-position case; K/DST
and universe-gap players (see `KDST_AND_UNIVERSE_GAP_EVIDENCE_20260903.md`)
stay outside PLAYER SCORE entirely and remain `EXTERNAL_UNMODELED_BY_NWR`
per section 17 — do not force a score onto them to make Team Score math
convenient.

## B. TEAM SCORE (0-100, ~50 = league-average finished roster)

Composite of roster construction quality **for this exact league format**,
explicitly not using universal position weights (section 4B is explicit
about this, and the KHA QB-saturation finding in the reconciliation work
is direct evidence why: a fixed QB weight would keep recommending QB3 in a
1QB league regardless of format).

Proposed structure (research, unvalidated — every weight below is a
placeholder for what calibration must set, not a proposed final value):

```
TeamScore(roster, league_format) = f(
    starting_lineup_VOR,       # sum of (starter PlayerScore - replacement_vorp_core baseline) per starting slot, FLEX-aware
    bench_contingent_value,    # bench PlayerScore, discounted by realistic play probability
    positional_scarcity,       # replacement_vorp_core's per-position thresholds, driven by actual league roster/starter counts
    weekly_floor,              # low end of projection_low/projection_high band, lineup-aggregated
    upside,                    # high end of the same band
    availability_resilience,   # availability_probability-weighted, already in the projections schema
    starting_holes,            # count/severity of unfilled or replacement-level starting slots
    redundancy_penalty,        # diminishing marginal value for repeated near-duplicate assets at one position
    concentration_risk,        # roster value concentrated in few injury-prone/low-availability assets
)
```

`league_format` (team count, scoring rules, starter layout, FLEX count,
bench size, playoff structure where known) is a required input, not a
default — this is what makes the composite format-aware instead of
universal-weighted. `replacement_vorp_core_service`'s `REPLACEMENT_DEFAULTS`
already varies required-starter-rank by position; extending it to read the
league's actual starter/FLEX/bench counts (rather than the defaults) is the
concrete integration point, not a new replacement-level system.

50 = league-average is a **normalization target, not a formula input** —
it means whatever raw composite comes out of the weighted sum above must be
centered/scaled against a reference distribution (e.g. simulated
replacement-level rosters for that exact format, or historical replay
rosters once section 9/10's replay pipeline exists), not hardcoded so that
today's specific KHA roster happens to land near 50.

## C. CHAMPIONSHIP EQUITY

`P(win this league | roster + league rules)`, with the during-draft variant
conditioning on a plausible optimized remaining draft and the after-draft
variant conditioning on the actual completed roster.

This is a genuinely unmodeled concept in this codebase (confirmed above) —
proposing a bounded approach rather than a from-scratch win-probability
model, because a real one needs either (a) simulated seasons against
simulated opponent rosters and a scoring/playoff format, or (b) enough
historical replay outcomes (section 9/10) to fit against. Neither exists
yet. Sequenced dependency, not parallel-buildable to the same maturity as
Team Score:

1. **Phase 0 (buildable now)**: Team Score is itself a leading proxy —
   `CHAMPIONSHIP_EQUITY_PROXY = rank_percentile(TeamScore, all_rosters_in_league)`,
   explicitly labeled a proxy, not a probability. This is the "AcceptanceChance is
   a deterministic score for review bands, not a calibrated probability" pattern
   already established in `FORMULA_SPEC.md` — same honesty framing, new
   concept.
2. **Phase 1 (needs section 9/10 replay + simulated season/playoff
   engine)**: simulate the rest of the season for every roster in the
   league under the league's actual scoring/playoff rules (weekly matchup
   simulation from each roster's projected points distribution, not just a
   single point estimate — the `projection_low`/`projection_high` band
   already in the schema is exactly the input a variance-aware weekly sim
   needs), then estimate P(win) from simulated playoff outcomes across many
   trials.
3. Only after Phase 1 has been checked against **real** completed-season
   outcomes (once any exist via section 9/10 historical replay) does this
   stop being purely simulated and start being calibratable in the
   `CALIBRATION_PLAN.md` sense.

Never report Phase 0's proxy number as if it were Phase 1's simulated
probability — different units, different confidence, and conflating them
is exactly the "hiding value in one blended score" failure mode
`CALIBRATION_PLAN.md` already warns about for a different formula.

## D. PICK SCORE (0-100, `RESEARCH_ONLY_PICK_SCORE` until calibrated)

Owner-facing "how good is taking this player, right now, at this exact
pick" number. Explicitly a composite over the other three, not a
from-scratch formula:

```
PickScore(candidate, pick_context) = g(
    TeamScore(roster_after_pick) - TeamScore(roster_before_pick),   # marginal roster value
    ChampionshipEquity(after) - ChampionshipEquity(before),         # marginal equity (Phase 0 proxy initially)
    CostOfWaiting(candidate, pick_context),                         # section 6 — expected loss from passing now
    make_it_back_probability(candidate, pick_context),              # derived from platform ADP/market context vs. picks until this owner's next turn
    scarcity_at_position(candidate, pick_context),                  # from replacement_vorp_core, format-scoped
    uncertainty(candidate),                                         # projection_low/high spread, availability_probability
)
```

This is the number the brief explicitly forbids shipping with "arbitrary
fixed weighting... called validated." Concrete gate before it can lose the
`RESEARCH_ONLY_` label, matching this repo's existing evaluator pattern
(`EVALUATORS.md`'s data/formula evaluator: fixtures + documented golden
values required before any formula change ships):

- hand-calculated fixtures for known-obvious cases (clear best-player-
  available at pick 1.01; a clearly-should-wait deep bench player like the
  Troy Franklin pathological case in section 6) must pass before any weight
  is treated as more than a placeholder;
- sensitivity testing (the `CALIBRATION_REPORT.md` pattern: perturb one
  input by a small amount, confirm the score doesn't swing wildly) before
  any weight change is accepted;
- the historical KHA replay (once built per the reconciliation-ledger
  resolution, from `official_recap_192picks_clean.csv`) is the first real
  regression surface once it exists, not before.

UI label: literal `RESEARCH_ONLY_PICK_SCORE` (owner's requested string),
implemented as a `TrustStatus`-shaped object (`status="review_only"`,
matching this repo's existing convention) so it can be forcibly demoted
under the same freeze mechanism `legacy_label_quarantine_service.py`
already uses for other not-yet-ready labels, rather than a one-off string
check.

## Look-ahead / Monte Carlo optimizer (section 5) — scope note only

No simulation engine exists in this repo today (confirmed by grep — zero
Monte Carlo, zero forward game-tree search anywhere in `src/`). This is a
genuinely new subsystem, sequenced behind Team Score / Cost of Waiting
existing in at least Phase-0 form (the optimizer's objective function is
literally "maximize expected Team Score / Championship Equity across
candidate branches" — it has nothing to optimize against until those
exist even at proxy fidelity). Not attempting a full design in this pass;
flagging the dependency order so this and the numeric-authority work don't
get built out of sequence. `practical_redraft_mock_service.py` (existing
mock-draft session state) is a plausible substrate for "simulate opponent
picks" once PLATFORM MARKET BEHAVIOR sourcing (section 5) is designed, but
that's next-pass scope, not this one.

## What this document does not do

Does not ship any of the above as running code, does not assign a single
concrete number to any real player, and does not claim any weight here is
calibrated. Every formula above is a structural proposal for what the
V1 build should compute from and how it should compose with existing
services — not a finished, validated model.
