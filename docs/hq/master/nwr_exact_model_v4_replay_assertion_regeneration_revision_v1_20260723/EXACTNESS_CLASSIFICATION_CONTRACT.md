# Exactness classification contract

The authoritative lattice contains only:

`EXACT_PRIMARY_EVIDENCE`, `EXACT_DETERMINISTIC_REGENERATION`,
`NEAR_EQUIVALENT`, `PARTIAL_REPLAY`, `APPROXIMATE`, `REVIEW_ONLY`,
`BLOCKED_MISSING_RECEIPT`, `BLOCKED_SOURCE_NOT_ADMITTED`, `DEPRECATED`, and
`FROZEN_COMPARATOR`.

Only the first two classifications are exact. An exact classification requires
nonblank provenance, schema proof, exact identity proof, and historical
availability proof. The mandatory component set is identity, outcome, lagged
production, position score, lifecycle, confidence, discipline/safety,
checkpoint, final score, and rank. Missing, duplicated, optionalized, or
unsupported components fail closed.

Full-row exactness is derived from every mandatory proof. Label-only promotion
of approximate or near-equivalent evidence fails. The unchanged frontier is
zero exact rows, no exact seasons or positions, and proxy-to-exact
`NOT TESTABLE`.
