# Failure and Trust-State Review

The source failure matrix parses as 24 unique scenarios. It explicitly covers current and stale retained data; a failed latest attempt with matching last-known-good; partial and one-row-unresolved identity; duplicate source/canonical identity; unsupported asset; missing ownership and league settings; unavailable, gated, and skipped sources; invalid schema; integrity and corrupt-snapshot failure; missing LocalData; source rights failure; no usable roster; rankings without roster; roster without rankings; not enough information; DST mismatch; draft-pick scope; and absent taxi/IR state.

The presentation contract uses the existing Decision Trust Strip labels exactly: Valid / current, Stale, Missing, Gated, Unavailable, Identity exception, Source exception, and Not enough information. It also reuses Refresh Recovery and retained-data vocabulary including Refresh succeeded, Partial success, Stale retained data, Source skipped, Source unavailable, Source gated, Refresh failed, `CURRENT_RETAINED_DATA`, `STALE_RETAINED_DATA`, and `NO_USABLE_RETAINED_DATA`.

Tracked service inspection and focused tests confirm those vocabularies are repository-governed. No competing positive state is introduced.

Missing, unresolved, partial, duplicate, stale, retained, unavailable, gated, corrupt, or unknown evidence cannot appear current or complete. A failed latest attempt cannot overwrite or relabel a prior validated snapshot. Resolved rows in a partial snapshot require a visible numerator, denominator, unresolved count, and limitation.
