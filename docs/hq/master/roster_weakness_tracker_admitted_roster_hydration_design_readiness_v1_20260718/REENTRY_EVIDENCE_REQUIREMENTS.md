# Re-entry Evidence Requirements

Implementation remains blocked until all mandatory evidence below is accepted.

## Product

1. Human-approved V1 scope states whether draft picks and DST are included or explicitly excluded.
2. V1 confirms descriptive facts only and names every permitted output.
3. Taxi and IR treatment is explicit; unsupported states are not silently omitted.

## Identity

1. Approved canonical statement that NWR player_id is the target identity and Sleeper player ID joins only through exact dim_players.sleeper_id.
2. Approved local test pack with every in-scope roster asset represented.
3. Aggregate audit shows:
   - zero blank source IDs for supported assets;
   - zero duplicate source IDs;
   - zero duplicate canonical IDs;
   - zero ambiguous mappings;
   - zero name-only or composite joins;
   - explicit unresolved and unsupported denominators.
4. Kicker and inactive/retired coverage is demonstrated.
5. DST and draft picks have stable contracts or accepted exclusions.

## Roster fields

1. Versioned normalized snapshot schema.
2. Explicit starter/bench, taxi, IR, eligibility, ownership, validation, resolution, retention, timestamp, and integrity behavior.
3. Field provenance and privacy classification accepted.
4. Partial and duplicate behavior tested.

## League context

1. Typed configuration migrated from docs/model_v4/LEAGUE_RULES_LOCK.md with provenance.
2. Starter slots, flex eligibility, bench, phase-specific IR, kicker, DST, scoring labels, and taxi missingness represented.
3. The hard-coded future-tools STARTER_FORMAT is not used as authority.

## Freshness and trust

1. Roster stale threshold has a named owner and rationale.
2. Existing receipt family fit is approved, or a bounded separate family is approved.
3. Latest attempt, latest success, retained data, last-known-good, partial identity, unavailable, gated, and unknown tests pass.
4. Decision Trust Strip mapping is reviewed with no new vocabulary.

## Privacy and LocalData

1. Approved LocalData manifest is present under the allowed root.
2. noCopy, noCheckIn, and no arbitrary disk fallback are enforced.
3. Private IDs are redacted from diagnostics and docs.
4. Provider payloads, credentials, messages, transactions, and waiver data are excluded.
5. User deletion and rollback procedures are approved.

## Reproducibility and tests

1. Clean checkout passes synthetic exact-ID and failure-state tests.
2. LocalData tier runs separately and reports its true result.
3. Route/page-open smoke proves no write or refresh.
4. Protected/frozen paths and primary CSV hashes remain unchanged.
5. A new implementation work order identifies exact allowed paths and rollback.

No workaround, manual name match, plugin result, or locally discovered file satisfies these requirements.
