# Age / Lifecycle Identity And Missingness Validation

Verdict: PASS_WITH_CAVEATS

Join rule: Formula Data Mart `player_id` to DynastyProcess `gsis_id` by exact ID only. No fuzzy name match
was used. Duplicate and missing identity conditions are preserved as row-level flags.

Duplicate sidecar keys: 0

Identity flags:

- IDENTITY_REVIEW_REQUIRED_DUPLICATE_GSIS_DOB_CONFLICT: 3
- JOIN_MISSING_DP_GSIS: 8
- PASS_GSIS_ID_JOIN: 5507

Missingness flags:

- missing_birthdate|missing_draft_year|missing_identity_join: 8
- source_columns_present: 5510

Age missingness: 8/5518 (0.14%)

Lifecycle missingness: 8/5518 (0.14%)

Policy:

- Missing age is unknown, not zero.
- Missing draft year is unknown, not zero.
- Review-only derived age buckets and lifecycle buckets are transparent bins, not Model v4 formula weights.
- Any later formula test must report missingness and position-level effects separately.
