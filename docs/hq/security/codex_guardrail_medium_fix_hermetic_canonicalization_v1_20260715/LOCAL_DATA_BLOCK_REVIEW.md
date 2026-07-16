# LocalData Block Review

The only approved LocalData root is the ignored repository-local `local_exports/` directory and the only admitted manifest is `LOCAL_TEST_PACK_MANIFEST.json` with the exact ID/version/rights contract.

No such manifest or pack was present. Independent invocation produced:

```text
LOCALDATA_TIER_BEGIN
BLOCKED_MISSING_LOCAL_TEST_PACK
```

Exit code: `4`. Collection count: `0`. The 89 LocalData files were not run, skipped, xfailed, or described as Hermetic. No arbitrary disk fallback, discovery, copy, check-in, or private/licensed data access occurred.
