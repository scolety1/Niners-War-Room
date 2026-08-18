# Global snapshot storage

One snapshot is stored under `state/redraft/adp_provider_cache/owner_platform_snapshot/` using the provider-cache architecture:

- `snapshot.json`: normalized rows, all four columns, parser mode, source label, imported time, format, season, hash, match report, coverage, and activation state.
- `snapshot.txt`: the original pasted text.
- `leagues/<profile-id>.json`: only the per-league selection metadata.

The raw text is not duplicated for every league.
