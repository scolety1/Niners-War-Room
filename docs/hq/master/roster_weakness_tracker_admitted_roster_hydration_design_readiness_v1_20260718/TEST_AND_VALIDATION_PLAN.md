# Test and Validation Plan

## Design-lane validation

- Fetch/prune and verify live HQ commit/tree.
- Confirm no intervening commit or stop-scope conflict.
- Confirm isolated clean worktree.
- Parse source registry and detect duplicate source/table keys.
- Inspect exact Sleeper admission rows.
- Inspect current roster and player schema.
- Check tracked synthetic roster/player uniqueness and cross-table coverage.
- Record that the synthetic fixture has no populated Sleeper crosswalk IDs.
- Confirm active LocalData pack is absent without searching arbitrary disk.
- Confirm tracker route registration and page path.
- Run focused repository tests using fake/synthetic inputs only.
- Inspect Data Health, receipt, and Decision Trust contracts.
- Scan relevant tracked code/docs for private-data boundaries without reading credentials.
- Hash protected blobs and frozen/prospective paths.
- Parse every new CSV and JSON document.
- Validate manifest membership, duplicate keys, and hashes.
- Run git diff --check and git diff --cached --check.
- Verify primary DynastyProcess hashes before and after.
- Verify one docs-only commit and a clean worktree.

## Future implementation tests

### Identity

- exact unique source ID joins;
- missing source ID;
- missing NWR mapping;
- duplicate source ID;
- duplicate NWR mapping;
- conflicting asset types;
- rookie without assigned ID;
- inactive/retired player;
- kicker;
- DST unsupported/excluded behavior;
- taxi and IR status on an exact player;
- draft-pick inclusion/exclusion rule;
- assertion that no name join function is invoked.

### Snapshot

- closed schema and type validation;
- schema version compatibility;
- source/league/roster matching;
- UTC timestamp ordering;
- source-as-of distinct from hydration time;
- integrity pass/fail;
- oversized/corrupt input;
- current, stale, no usable, and not enough information;
- partial identity resolution;
- latest attempt versus latest success;
- matching and nonmatching last-known-good.

### Presentation

- missing is never healthy;
- stale is never current;
- partial is never complete;
- unresolved count appears in summary and detail;
- failed attempt preserves last-known-good;
- rankings-only and roster-only states;
- descriptive/advisory label;
- keyboard and compact-width checks;
- page-open performs no refresh or write.

### Privacy

- reject credentials, tokens, cookies, raw headers, provider payloads, messages, absolute paths, traversal, unknown nested metadata, and private identifiers in receipts;
- verify snapshot root is approved, ignored, bounded, and nontracked;
- verify fixtures contain synthetic identifiers only.

## Provider boundary

All design and initial implementation tests use synthetic/fake inputs. No provider call or production roster hydration belongs in either lane.
