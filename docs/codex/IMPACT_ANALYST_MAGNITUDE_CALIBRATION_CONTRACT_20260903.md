# Impact Analyst — future magnitude calibration contract (section 16)

`generate_direct_impact_hypothesis`/`generate_beneficiary_hypotheses`/
`generate_role_uncertainty_hypotheses` (`src/services/ai_intelligence_backend_service.py`)
produce a **direction** (POSITIVE/NEGATIVE/NEUTRAL/UNCERTAIN), a
**confidence** (LOW/MEDIUM/HIGH), and a **horizon**
(IMMEDIATE/REST_OF_SEASON/LONG_TERM) — never a numeric point/value
adjustment. This is deliberate: **no arbitrary numeric Core adjustment
exists anywhere in this module**, and none should be added without the
calibration this contract describes.

## Why not a number today

A real magnitude (e.g., "this injury costs the player 4.2 points per
game") requires historical evidence: how much did a comparable real
event actually change comparable real players' realized output,
averaged over enough cases to be a genuine estimate rather than a guess
for one player. No such dataset exists in this repo — this is the same
substrate gap `docs/codex/HISTORICAL_REPLAY_SUBSTRATE_INVENTORY_20260903.md`
already found for redraft replay data generally. Assigning a number
without that evidence would be exactly the kind of fabrication this
session's rules forbid, dressed up as a feature.

## What a future magnitude-calibration pass would need

1. **A labeled event history**: real (event_type, severity, position)
   tuples with a real, dated occurrence, paired with the affected
   player's (and, for beneficiary/role-uncertainty hypotheses, the
   teammates') realized weekly output in the weeks immediately
   following, under a real, dated scoring format — the same shape
   `historical_replay_data_adapter_service.py`'s `OUTCOME_ONLY_FIELDS`
   already define (`realized_weekly_points`, `outcome_as_of`), reused
   rather than a new schema invented for this purpose.
2. **A leakage guard**: the calibration must never use output realized
   before the event (that would be measuring something else), and must
   never use the event's own future resolution (e.g., "how long the
   player actually missed") as an input to *predict* horizon/confidence
   at the time of the event — reuse
   `historical_replay_data_adapter_service.py`'s `validate_leakage`
   date-ordering checks rather than a new ad hoc check.
3. **A minimum sample size per (event_type, severity) cell**: the direct
   rule table currently has one row per `(event_type, severity)` pair;
   a magnitude estimate for a cell with fewer than some minimum real
   occurrences (a number this contract deliberately does not pre-commit
   to, since it depends on the real variance once real data exists)
   should stay a direction/confidence/horizon triple, not a fabricated
   point estimate from too few cases.
4. **Held-out validation**, matching this session's own established
   discipline (`docs/codex/CALIBRATION_PLAN.md`'s "tune weights only
   with fixture updates, expected-output notes, and clear reason. Do
   not tune by eyeballing one favorite player" and the rookie
   challenger's own chronological-split discipline): any fitted
   magnitude must be validated on events the fit never saw, not just
   fit and reported on the same sample.
5. **Champion/Challenger registration**: a calibrated magnitude model
   would be a CHALLENGER against the current direction/confidence/
   horizon-only CHAMPION, registered via
   `champion_challenger_registry_service.py` with its real evaluation
   evidence — never silently wired in as a numeric Core adjustment
   without that registration and an explicit owner promotion decision.

## What exists today, and is enough for now

`requires_owner_review` on every hypothesis is the current, honest
stand-in for "we don't have a calibrated magnitude yet" — every
consumer (the Explanation layer, and any future Draft Room UI surface)
is expected to show the hypothesis as a flagged, qualitative signal for
the owner to weigh themselves, not a number the system already baked
into a decision.
