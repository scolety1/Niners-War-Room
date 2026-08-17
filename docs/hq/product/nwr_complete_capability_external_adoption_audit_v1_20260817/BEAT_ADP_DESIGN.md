# Beat ADP Design

Beat ADP is a decision surface, not a new player model.

## Required separation

### NWR View

- NWR overall/position rank and replacement-adjusted value;
- market expected pick/rank;
- signed rank gap and value/fade label;
- projection and authority confidence;
- explicit source timestamps.

### Draft Timing

- current overall pick and owner's next pick;
- expected pick plus dispersion/sample size;
- make-it-back estimate;
- same-position tier survival and recent position run;
- roster/legal-slot need;
- `Take now`, `Wait`, or `Do not reach` with reasons.

## Calculation stages

1. Phase 1A: deterministic gap and a disclosed logistic/empirical survival heuristic from ADP mean/dispersion.
2. Phase 1B: calibrate against held-out historical drafts by platform/format/team count; report Brier/calibration bins and coverage.
3. Never let the timing layer reorder the underlying NWR authority. It advises *when*, while NWR advises *how valuable*.

If ADP is stale, mismatched or missing, show `NOT_ENOUGH_INFORMATION` and fall back to NWR board/tier logic without fabricated probability.
