# Data Hygiene Source Trace Requirements

Data Hygiene cannot mark an artifact usable for any later lane until the minimum source trace is recorded or the missing fields are explicitly blocked.

## Minimum Required Fields

- source exists
- raw file/artifact exists
- source path or URL recorded
- acquisition method recorded
- row count recorded
- column count recorded
- schema recorded
- hash/checksum recorded where possible
- seasons covered
- row grain
- identity keys
- join keys
- source status
- admission status
- licensing status
- identity status
- leakage status
- missingness status
- coverage status
- rebuild instructions
- use gate
- validation tests

## Additional Required Fields When Applicable

- weeks or dates covered
- positions covered
- team coverage
- field dictionary path
- join method
- unmatched rows
- duplicate key rows
- collision/conflict rows
- source retrieval timestamp
- source version/release
- normalized output hash
- decision date/as-of rule
- local_exports dependency
- missing-file blocker

## Usability Rule

If a required field is missing, the artifact may still be preserved as evidence, but its status must be limited to `REVIEW_ONLY`, `DISPLAY_ONLY`, `MISSING_RECEIPT`, `REBUILD_BLOCKED`, `JOIN_BLOCKED`, `NOT_ENOUGH_INFORMATION`, `IDENTITY_UNSAFE`, or `LEAKAGE_UNSAFE`.
