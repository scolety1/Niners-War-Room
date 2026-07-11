# Decision Trust Strip Schema

The shared schema is a display adapter over facts already loaded by each surface. It performs no file reads, source queries, identity joins, freshness calculations, score calculations, or recommendation logic.

Canonical order:

1. `evidence_source` — Evidence / source
2. `as_of_freshness` — As of / freshness
3. `identity_join` — Identity / join
4. `missingness_completeness` — Completeness
5. `material_caveats` — Material caveats
6. `receipt_details` — Receipts / details

Each field contains a canonical key, fixed label, state code, original existing value, and optional display detail. State mapping is lexical and deterministic over explicit existing status text. Unrecognized or absent text becomes `NOT_ENOUGH_INFORMATION`; it is never inferred as current, missing, gated, stale, or unavailable.

The compact view shows icon-plus-text status. The expandable view uses the existing Streamlit disclosure component and lists state, original value, and detail. Full receipts remain in their existing surface disclosures.

This schema is review-only and cannot influence rankings, values, filters, sorting, eligibility, recommendations, trades, or drafts.
