# Trust-Banner Contract Review

## What failed

The two failures are static checks in `tests/test_trust_banner_ui.py`. Both first stop at `app/pages/05_rankings.py`, a four-line app-shell wrapper. They do not execute a banner, parse a state, inspect accessibility text, or supply fixture vocabulary.

## Current trust owners

- Legacy review-only pages: `app/components/trust_status.py` and `render_page_trust_banner`.
- Canonical Dynasty Rankings: `app/components/decision_trust_strip.py` plus `src/services/decision_trust_strip_service.py`.
- Legacy Draft Prep: its explicit `Scouting Only / Legal Pool Pending` gate and planning-only copy.

The canonical Decision Trust Strip preserves these eight mechanically distinct states:

- `VALID_CURRENT`
- `STALE`
- `MISSING`
- `GATED`
- `UNAVAILABLE`
- `IDENTITY_EXCEPTION`
- `SOURCE_EXCEPTION`
- `NOT_ENOUGH_INFORMATION`

The six-field order remains evidence/source, freshness, identity/join, completeness, material caveats, and receipts/details. No component or service code changed.

## Harness repair

The repaired tests:

1. retain the one-old-banner assertion for pages that still own the old component;
2. assert exactly one shared Decision Trust Strip call on the routed rankings implementation;
3. retain the Draft Prep scouting/legal-pool gate;
4. retain the old component's collapsible review-only details test; and
5. retain the current Decision Trust Strip heading assertion.

This preserves interface validation and prevents the original violations. It does not replace rendered coverage with a weaker unit-only check; `tests/test_decision_trust_strip_render.py` still exercises the representative Streamlit fixture.

## Negated-status security overlap

The exact two failures do **not** reveal or exercise negated status parsing. They contain no `not valid` or `not current` input and never call `state_from_existing_status`. Therefore they are not identical to the low-severity negated-status finding associated with scan `85b6913f-ffcf-437e-bd3a-3597d75eb8c5`.

That separate finding was neither fixed nor broadened into this lane. The repaired assertions do not treat a negative phrase as a positive state, and no Decision Trust Strip semantics changed.

Classification for both failures: `FIXTURE_OR_HARNESS_DEFECT`. Confidence: `HIGH`. Unresolved ambiguity: none.
