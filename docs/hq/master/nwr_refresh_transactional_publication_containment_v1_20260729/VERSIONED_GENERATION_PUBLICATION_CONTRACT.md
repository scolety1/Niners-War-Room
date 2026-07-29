# Versioned Generation Publication Contract

Canonical safe root:

`C:\NWR\Niners-War-Room\local_exports\refresh_data\dynastyprocess_market_baseline`

Layout:

```text
dynastyprocess_market_baseline/
  .staging/<generation-id>/
  generations/<generation-id>/
  current_generation.json
```

The publisher accepts exactly these five non-empty byte payloads:

1. `dp_freshness_report.csv`
2. `dp_market_baseline_context.csv`
3. `dp_nwr_join_coverage.csv`
4. `dp_pick_value_context.csv`
5. `dp_playerid_crosswalk_audit.csv`

Each payload is exclusively created in a unique staging directory. Each file
is flushed and fsynced. The deterministic manifest records the schema,
run/generation IDs, creation timestamp, exact inventory, byte sizes, SHA-256
values, completion status, and state history. Staging metadata is flushed where
supported.

The complete staging directory is renamed without replacement into
`generations`. Existing generations are never overwritten or mutated. The
candidate is fully read back and verified before pointer construction.

Only the pointer replacement changes authority. Cleanup occurs afterward,
retains the current generation unconditionally, and cannot invalidate a
successful publication. Stale staging and orphan generations are
non-authoritative.
