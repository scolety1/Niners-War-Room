# Tracking Ledger Schema

`APPEND_ONLY_TRACKING_LEDGER.csv` is administrative only. Rows may be appended; existing rows may never be edited or deleted.

Immutable columns after append: `event_id`, `event_timestamp_utc`, `event_type`, `freeze_version`, `controlling_commit`, `baseline_freeze_sha256`, `actor_or_authority`, `artifact_or_location`, `artifact_sha256`, `status`, `notes`.

Allowed event types: `HASH_INTEGRITY_CHECK`, `CANONICAL_BACKUP`, `REPOSITORY_RELOCATION`, `DOCUMENTATION_CLARIFICATION`, `SOURCE_RECEIPT_ARRIVAL`, `OUTCOME_SOURCE_READINESS`, `SEASON_COMPLETION`, `EVALUATION_AUTHORIZATION`, `EVALUATION_COMPLETION`, `SEPARATELY_VERSIONED_CORRECTION_NOTICE`.

Forbidden content includes rewritten predictions, live performance, partial outcome scores, comparator standings, altered eligibility, or any claim that an administrative event authorizes production use.
