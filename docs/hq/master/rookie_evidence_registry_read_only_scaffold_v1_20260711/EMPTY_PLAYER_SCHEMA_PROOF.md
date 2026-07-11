# Empty Player Schema Proof

`PLAYER_IDENTITY_REGISTRY.csv`, `PLAYER_ALIAS_REGISTRY.csv`, `IDENTITY_ASSERTION_LEDGER.csv`, and `EVIDENCE_OBSERVATION_REGISTRY.csv` contain exactly one header row and zero data rows. They define keys and orthogonal state fields but contain no player names, provider IDs, aliases, identity assertions, values, draft/UDFA facts, measurements, outcomes, rankings, scores, or model inputs.

The single unmistakable synthetic fixture lives only under `tests/fixtures/rookie_evidence_registry_v1/`, uses impossible synthetic IDs and the marker `SYNTHETIC_VALIDATION_FIXTURE`, and is outside every registry export and real-row count.
