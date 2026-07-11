# Provider Change Reentry Gate

## Default state

Both plugins remain manual-only. No immediate Flaim rerun is authorized, and the original long battery must not be rerun unchanged.

## Flaim reentry triggers

The Flaim path may reopen only when at least one concrete trigger exists:

- Release notes or written acknowledgement addressing standings semantics.
- Corrected add/drop filtering.
- Explicit trade-side mapping.
- Complete or paginated relevant free-agent retrieval.
- Provider or API source-as-of or version fields.
- Explicit FLEX, phase-specific roster, keeper, or playoff settings.
- Written persistent-use, display, and retention permission.
- Relevant upstream-platform downstream-use clarification.

A future regression lane must test only the corrected surfaces plus minimum controls. The trigger permits a narrow test; it does not authorize production integration.

## FantasyBot reentry triggers

The FantasyBot path may reopen only after documented new capability for at least one of:

- Exact or bounded custom NWR scoring.
- Dynasty or keeper horizon.
- Roster or league context.
- Draft picks.
- A documented numerical value scale.
- Provider version and data-as-of.
- Underlying source attribution.
- Persistent output-display and evaluation rights.

## Gate sequence after a trigger

1. Document the triggering provider change and its source.
2. Preregister only the corrected surface and minimum control cases.
3. Recheck privacy, retention, display, and downstream-use rights.
4. Test semantic fidelity, completeness, freshness, provenance, and stability.
5. Keep production influence at `0%` unless a separate numerical-signal and source-admission gate passes.

Absent a documented trigger, do not rerun or recreate the completed audit.
