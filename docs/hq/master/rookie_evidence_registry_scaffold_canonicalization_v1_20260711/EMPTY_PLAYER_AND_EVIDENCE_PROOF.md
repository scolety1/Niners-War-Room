# Empty Player and Evidence Proof

The player registry, alias registry, identity-assertion ledger, and evidence-observation registry each contain one schema header and zero data rows. Real player rows, aliases, identity assertions, evidence observations, player values, draft/UDFA facts, rankings, scores, formula inputs, training rows, and production rows are all 0.

Exactly one fixture row exists under `tests/fixtures/rookie_evidence_registry_v1/`. It uses impossible synthetic IDs and `SYNTHETIC_VALIDATION_FIXTURE`, is outside the registry root, and is excluded from exports and real-row counts.

Result: `PASS_ZERO_REAL_PLAYER_AND_EVIDENCE_ROWS`.
