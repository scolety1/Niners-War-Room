# Age / Lifecycle Leakage And As-Of Validation

Verdict: PASS_WITH_CAVEATS

The review-only sidecar uses stable identity metadata from the recovered
`dynastyprocess_db_playerids.csv` file and joins it to the Formula Data Mart by exact `player_id`
to `gsis_id`. It does not use target-season outcomes, same-season production, rankings, market data,
injury context, or current Model v4 scoring fields.

Age is derived as of September 1 of the target season. DOB and draft year are treated as stable
identity metadata for review-only use only, consistent with prior Outcome Probability governance notes
that identified `dynastyprocess_db_playerids` as a stable identity/DOB metadata candidate after identity
validation.

Rows generated: 5518

Leakage flags:

- NOT_USABLE_FOR_AGE_SIGNAL_WHEN_BIRTHDATE_MISSING: 8
- PASS_STABLE_DOB_AND_DRAFT_YEAR_DERIVED_ASOF_SEPT_01_NO_OUTCOME_FIELDS: 5510

Current limitations:

- This sidecar is not an exact Model v4 historical lifecycle receipt.
- This sidecar does not make same-season prediction features from future outcomes.
- This sidecar does not approve production/model-use, rankings integration, or Formula Gauntlet tournaments.
- Missing DOB/draft-year remains unknown and is never zero-filled.
