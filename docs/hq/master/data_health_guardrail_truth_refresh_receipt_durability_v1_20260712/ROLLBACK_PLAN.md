# Rollback Plan

1. Revert the single local implementation commit after HQ identifies its final hash.
2. Do not edit or roll back source data, production datasets, rankings, formulas, frozen artifacts, or source registries; this lane never changes them.
3. Existing untracked V1 local receipt files may remain. Legacy readers ignore added fields because the legacy top-level run keys and `results` remain present.
4. If operational cleanup is explicitly desired, stop the local app and remove only the ignored `local_exports/refresh_data/latest_refresh_status.json`, its V1 backup/archive entries, and V1 quarantine entries after independently verifying the resolved local root. Cleanup is optional and is not part of implementation rollback.
5. Restart the local app and run the pre-existing Data Health, Refresh Data, recovery, navigation, and trust-strip regressions.

Rollback requires no schema migration, provider call, source refresh, data rebuild, or external coordination. The change is one commit and no push is authorized.
