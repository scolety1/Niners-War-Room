# Read-Only Runtime Boundary

The companion loader opens CSV/JSON files only for reading, returns immutable tuples, validates metadata, looks up opaque IDs, and returns fail-closed decision summaries. It contains no file-write API, network call, player-value load, identity resolution, source promotion, ranking, formula, training, scoring, migration, or application integration.

No application page, route, runtime bootstrap, ranking service, formula service, draft service, or production data path imports the loader. The scaffold is available only to tests and explicit CLI diagnostics.
