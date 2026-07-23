# Exact replay contract final review

The authoritative exactness lattice permits an exact row only when every
mandatory component is classified as `EXACT_PRIMARY_EVIDENCE` or
`EXACT_DETERMINISTIC_REGENERATION` and carries provenance, schema, exact
identity, and historical-availability proof.

The mandatory components are identity, outcome, lagged production, position
score, lifecycle, confidence, and discipline/safety. Full-row exactness is
derived from all of them; missing components and unsupported classifications
fail closed. A label change cannot create proof.

Historical records resolve player ID, input season, target season, as-of
boundary, feature family, source authority, source season, and availability
classification. Future, target-season, current-only, contradictory, or
metadata-incomplete evidence fails closed.

Joins use exact governed `player_id`, season, and position authority. Name
fallbacks, blank or duplicate IDs, mismatched IDs, and unresolved substitutions
are rejected.

Final frontier:

- historical identities/outcomes: 5,518 rows / 1,552 players;
- exact rows: 0 / 5,518;
- exact seasons: `NONE`;
- exact position coverage: zero;
- proxy-to-exact differential: `NOT TESTABLE`.

The absence of exact rows remains a research evidence blocker, not an
assertion or reproducibility defect.
