# Consumer Generation Resolution

The refresh writer, refresh CLI, scheduled wrapper, market display service, and
refresh orchestrator were inventoried.

The builder and refresh CLI now publish the exact five in-memory CSV byte
payloads through the transactional generation service and require an explicit
safe root. They do not publish to the tracked opaque directory.

`market_baseline_service` resolves one authenticated generation snapshot and
parses CSVs from the verified in-memory payload map. It never independently
opens five mutable latest files.

The refresh orchestrator passes `--safe-root`, expects all five files, resolves
the pointer after subprocess completion, and reports the generation ID and
manifest hash metadata. A subprocess exit 0 without a valid current generation
is reported `RED` and `FAILED`.

The scheduled wrapper passes the explicit safe root to the CLI, rejects
non-canonical/device/reparse paths, and no longer imports the live freshness
CSV for status reporting.

Legacy research/audit scripts that refer to the tracked opaque evidence packet
were not converted into runtime consumers and were not admitted as model
evidence. Production rankings, V2, Outcome Columns, navigation, and UI remain
disconnected.

The static Data Health display-only guardrail row remains visible when the
generation pointer is absent; passive-read semantics are unchanged and missing
refresh data still fails closed.
