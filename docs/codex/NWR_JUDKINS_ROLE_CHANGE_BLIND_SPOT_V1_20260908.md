# Judkins/Role-Change Blind-Spot Experiment — V1 (2026-09-08)

**Context:** NWR class-time autonomous hardening directive, Section 5. Per explicit
instruction, Quinshon Judkins was **not manually changed** at any point in this
investigation — he is used only as the real regression example that originally surfaced this
question.

## Real facts established (not assumptions)

1. Judkins IS already `FULLY_MODELED` by the veteran persistence model (real 2025 rookie-year
   stat line: 230 carries, 827 rushing yards, 7 TDs, 26 receptions over **14 games** —
   substantial, real lead-back-level volume, not a real committee afterthought as the
   original "role change" framing assumed).
2. NWR's real 2026 persistence projection for Judkins: **154.8 half-PPR points**
   (`games: 14.0` in the projected row -- see finding 3).
3. The real, current external market (FFA, admitted 2026 pack) projects **185.0 points**,
   overall rank 24, RB rank 19, ADP 49.6 -- a real, honest **~16.7% gap** between NWR and the
   current market.
4. Root mechanism (verified directly, not inferred): `_project_persistence` carries the
   player's own **prior-season real games total verbatim** into the projected row
   (`games: 14.0`, matching his real 2025 games exactly) rather than assuming a healthy
   17-game season. This is a real, structural, **games-availability** behavior of the
   persistence formula -- not evidence of a "role change" signal specifically. Judkins missed
   3 real 2025 games; if those were short-term (not season-ending) and he is currently
   healthy for 2026, persisting last year's real games count as this year's forecast
   understates him independent of any change in his real role.

## Searched existing current inputs (per directive, before building anything)

- `lve_role_usage_service.py` (`role_security`, `role_fragility_risk_score`,
  `depth_chart_role_score`) exists but reads from a `local_exports` CSV lane that is not
  populated in this worktree (the known, pre-existing ~323-failure gap — see
  `nwr-full-suite-preexisting-failures` project memory) -- not usable without first building
  that export lane, out of scope for this unit.
- Real, staged `depth_charts` nflverse snapshot only covers seasons through the archive's
  most recent completed season -- no real 2026 preseason depth-chart data exists yet (the
  2026 season has not started), so a true "current preseason role" signal is not available
  from this source today.
- The real, current, ALREADY-ADMITTED FFA 2026 pack **is** available and is exactly the kind
  of "current external projection" source the directive names -- used above for finding 3.

## Disposition: reference-only, not promoted to a challenger

A real disagreement exists (NWR 154.8 vs FFA 185.0), but the root mechanism identified
(games-count persistence, not a role-change-specific signal) means the directive's proposed
challenger framing -- *"historical persistence confidence should reduce when independent
current role evidence materially disagrees"* -- is not the most direct real explanation for
this specific case, and no true current-role-evidence source (depth chart, roster
transaction) is actually available for 2026 yet to build and calibrate such a feature against.
Building a role-change-disagreement feature without a real current-role input to feed it
would mean fabricating the very evidence the directive explicitly forbids substituting for
(ESPN ADP as the "answer target" was explicitly disallowed for exactly this reason).

Per the directive's own explicit fallback ("If no valid historical calibration can be
completed, leave as reference-only evidence"): **left as reference-only.** Player Score,
Team Score, Championship Equity, and Pick Score formulas are untouched. No code change this
unit. The real, distinct, testable question this surfaced -- whether persisting a player's
own prior-season real games total (vs. assuming a healthy full season) is well-calibrated in
aggregate -- is a legitimate, separate, structural follow-up for a future session, not
addressed here (out of scope for a role-change-specific directive section, and not something
to decide on a single regression example).

## Status

Section 5: **DONE (reference-only disposition)**. Next: Section 6, status/risk live intake
path.
