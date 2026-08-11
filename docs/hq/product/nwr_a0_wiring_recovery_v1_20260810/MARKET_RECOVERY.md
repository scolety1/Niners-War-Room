# Market Recovery

## Before

The desktop launcher placed refresh artifacts under AppData and exposed a repository junction. The hardened generation reader rejected that junction, while the market service ignored `NWR_REFRESH_DATA_ROOT`. Result: zero runtime matches.

## After

The reader resolves the launcher-owned physical root. Transactional generations retain pointer/manifest/hash verification. Existing complete pre-generation `latest` bundles are read only through the same absolute-path, same-volume, and no-reparse guards; all five required payloads must exist.

Observed recovery: 232 market matches across the 240 structural Finished V1 rows. The eight kickers remain unmatched because they are outside ranked skill-position coverage. The upstream evidence date is 2026-07-17 and is normalized to `YELLOW_STALE`; it remains external display-only context.
