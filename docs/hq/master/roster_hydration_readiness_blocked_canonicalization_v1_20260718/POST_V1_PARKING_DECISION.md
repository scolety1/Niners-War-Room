# Post-V1 Parking Decision

## Formal status

`AUTOMATED_ROSTER_HYDRATION_PARKED_POST_V1_PENDING_STABLE_ADMITTED_IDENTITY`

## V1 treatment

- The current manual/display-only Roster Weakness Tracker may remain unchanged.
- Automated roster hydration is not included in V1.
- Hidden, partial, opportunistic, or page-open hydration is prohibited.
- Name matching and every display-derived fallback are prohibited.
- The surface must not imply admitted live roster coverage where none exists.
- Missing automated hydration is a documented post-V1 limitation, not a failed V1 release gate.

## Re-entry rule

Automated roster hydration may re-enter only after all ten requirements in `REENTRY_TRIGGER_MATRIX.csv` are evidenced and approved. A partial set does not authorize design implementation, provider calls, data population, schema changes, page wiring, or scoring. No shortcut, locally discovered file, manual match, plugin result, or inferred identifier satisfies a trigger.

This parking decision clears the project to proceed to the separately governed final V1 release-readiness lane without beginning that lane here.
