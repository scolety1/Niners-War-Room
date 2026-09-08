# Brooks-Class Source-Gap Fix — V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 4 ("Brooks/Diggs-class
source-gap repair — systemic, not by name"), Brooks-class half. Root cause originally
identified in `docs/codex/NWR_BROOKS_DIGGS_JUDKINS_ROOT_CAUSE_V1_20260908.md`.

## Problem

A current, active NFL player (`status=ACT`/`RES`) with real NFL draft capital but no usable
own prior-season stat line (injury, missed rookie/sophomore season) is blocked entirely by
`build_current_projection_candidate` (`reason = "no prior-season NFL stat line; persistence
forecast blocked"` or `"prior-season games are zero; persistence forecast blocked"`) and is
also **not** covered by the true-rookie lane (`build_current_rookie_candidate` requires
`current_rookie_season == season`). Real example: Jonathon Brooks (CAR, RB, drafted round 2
pick 46 in 2024, real rookie-year ACL recovery, zero recorded 2024 games) — genuinely
invisible to search/rankings/compare, not merely low-ranked.

Real audit of the current admitted universe (post Diggs-class fix): **173** players blocked
for insufficient own history, of which **66** have a real, matched NFL draft record (any
year); **38** are from the 2023-2025 draft classes (the fantasy-relevant recent tail).

## Reuse-first search (per directive)

Searched existing repo infrastructure before building anything new, per the explicit
"REUSE FIRST" instruction. Found `src/services/redraft_2026_rookie_projection_model_service.py`
— an already-built, already-validated (via its own `promotion_gates`) real position+round
rookie-year cohort-median model, currently scoped only to the CURRENT year's incoming rookie
class. Its two core helpers (`cohort_projection`, `median_stats`) were private
(`_cohort_projection`, `_median_stats`); renamed to public (pure rename, no logic change,
verified via the existing rookie test suite) so a second, real caller could reuse them
directly instead of duplicating the median/component-consistency logic.

## Fix: general "insufficient-history, has draft capital" fallback category

Added `build_insufficient_history_fallback_candidate()` to the same rookie-model service file
(avoids a circular import, since the rookie service already imports one-directionally from the
veteran persistence service). It:

- Takes the veteran model's own `blocked` frame as-is (no duplicated eligibility logic) and
  keeps only the two genuine "no usable own history" reasons — a true-rookie-blocked row is
  never touched (that lane is untouched and unaffected).
- Cross-references real NFL draft-pick evidence (`load_draft_evidence`) by canonical
  `gsis_id`; a player with no real draft record stays genuinely blocked/unprojectable (no
  guess), and a real position conflict between the draft record and the current registry is
  also blocked, not coerced.
- For an eligible player, applies the exact same real position+round rookie-year cohort
  median already used for true rookies, trained on the same real
  `load_rookie_outcome_frame` pool — **no fabricated stat line for the specific player**, only
  a real median of *other* real players at the same real draft slot.
- Labeled distinctly: `source_id = NWR_REDRAFT_2026_INSUFFICIENT_HISTORY_DRAFT_CAPITAL_COHORT_FALLBACK_V1`,
  `evidence_status = MODEL_VALIDATED_REVIEW_ONLY`, `source_status = GOVERNANCE_PENDING` — same
  review-only posture as every other unpromoted projection lane in this codebase.

## Real historical spot-check (honest result)

Per the directive's "test historically where possible" and "if weak, say so": evaluated the
real historical population of players whose real rookie-year `games == 0` (2013-2023 draft
classes, 168 real cases with a real sophomore season available), comparing the same real
walk-forward cohort median (trained only on strictly-prior draft classes) against a naive
"predict zero" baseline, scored against real sophomore-season half-PPR outcomes:

```
Evaluated: 168 real historical cases
Mean challenger (cohort-median) MAE:  16.79
Mean baseline (predict-zero) MAE:      9.80
Challenger wins (lower abs error):    28/168 (16.7%)
Mean actual real sophomore points:     9.76
Mean challenger predicted points:     15.34
```

**Honest finding: the cohort-median challenger loses to the naive zero baseline on aggregate
point-estimate accuracy for this specific population.** The real "zero rookie-year games"
population is dominated by genuine real busts (never play meaningfully again), so calibrating
against the full rookie cohort (which includes players who *did* get real snaps)
systematically overestimates this specific, worse-than-typical subgroup. Real counter-examples
exist in the same table (Travis Kelce, Jordan Love, Travis Etienne, Derrius Guice, Jauan
Jennings) where a real breakout followed real lost rookie time, but they are the minority, not
the pattern.

## Disposition

**NOT promoted as a calibrated point estimate.** No gate was pre-registered claiming this
would beat a zero baseline, and the honest result says it doesn't, in aggregate MAE. Consistent
with the directive's "no coherent subgroup pattern → reference-only" discipline (also applied
in Section 5), this is kept as an **additive, review-only visibility fix**: its real value is
not point-estimate accuracy but eliminating true invisibility — a real, currently active,
drafted player (Jonathon Brooks and 65 others) becomes searchable/comparable/classifiable
(feeds Top-250 coverage as a real category instead of `PROJECTION_MISSING`) instead of being
silently absent from the entire tool. Never wired into Pick Score / RAV / recommendation
ordering, and the veteran persistence model's own universe/ranking logic is completely
untouched.

## Tests

4 new tests in `tests/test_redraft_2026_rookie_projection_model_service.py`: true-positive
(Brooks-class admission via real cohort median), true-negative (true-rookie-blocked rows
ignored), true-negative (undrafted player stays honestly blocked), true-negative (real
position conflict blocked). All pass. Full rookie-service regression: 11/11 (excluding one
pre-existing, unrelated `NWR_DATA_GOVERNANCE.json` manifest-hash failure, confirmed present
on unmodified HEAD before this change too).

## Status

Section 4 (Brooks/Diggs-class systemic source-gap repair): **DONE**. Next: rerun Top-250
coverage with both fixes applied (directive's own required follow-up), then Section 5
(Judkins/role-change).
