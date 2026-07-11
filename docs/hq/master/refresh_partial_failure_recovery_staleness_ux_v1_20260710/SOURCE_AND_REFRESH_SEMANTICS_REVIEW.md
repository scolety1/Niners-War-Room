# Source and Refresh Semantics Review

The implementation reuses `RefreshSourceResult`, serialized refresh rows, `load_latest_refresh_status`, and `HealthDashboardReport.refresh_health`. It does not read sources or manifests directly. No new freshness threshold exists. Explicit `stale` is the sole stale-retained trigger. `blocked_policy`/`BLOCKED` is gated; `blocked_config`/`NOT_CONFIGURED` is unavailable; policy skip remains skipped; failure remains failed. Missing evidence resolves to `NOT_ENOUGH_INFORMATION`.

The adapter performs no I/O, writes, calls, retries, matching, promotion, source substitution, or input mutation.
