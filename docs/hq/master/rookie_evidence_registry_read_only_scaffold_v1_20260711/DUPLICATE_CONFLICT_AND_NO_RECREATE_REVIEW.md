# Duplicate, Conflict, and No-Recreate Review

The scaffold preserves 30 design relationship objects and 40 no-recreate relationships without deletion, merge, preference, or fact selection.

- `CONFLICTING_EVIDENCE`: 9
- `EXACT_DUPLICATE`: 6
- `INDEPENDENT_CORROBORATION`: 1
- `NOT_ACTUALLY_DUPLICATED`: 2
- `OVERLAPPING_POPULATION`: 2
- `SCHEMA_EQUIVALENT_DUPLICATE`: 4
- `STALE_PREDECESSOR`: 3
- `TRANSFORMED_DERIVATIVE`: 3

Artifact selectors from the design remain review references rather than guessed artifact foreign keys. Every relationship is `UNRESOLVED_REVIEW_OBJECT`; the design statuses `AUDITED_DESIGN_INPUT_NOT_IMPLEMENTED` and `NOT_CREATED_DESIGN_LANE` remain intact. Absolute no-recreate references are replaced by opaque, non-reversible locator IDs.
