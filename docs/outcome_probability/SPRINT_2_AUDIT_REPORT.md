# Build Sprint 2 Audit Report

Verdict: **PASS WITH TODOs**

Sprint 2 is safe as a point-in-time training row contract and validator scaffold. It does not create player probabilities, app percentages, rankings, base rates, model training output, or materialized real feature rows.

The only TODOs are for Sprint 3, when a real historical row factory starts reading source files:

- Add explicit stale-prior-row reuse checks at the factory/export layer.
- Emit row-level leakage audit exports from actual source manifests.
- Verify real source timestamps and parser versions once historical files are wired.

## Files Audited

Sprint 2:

- `src/services/nwr_outcome_training_row_service.py`
- `tests/test_nwr_outcome_training_row_service.py`
- `docs/outcome_probability/BUILD_SPRINT_2_POINT_IN_TIME_CONTRACTS.md`

Sprint 1 still checked:

- `src/services/nwr_outcome_scoring_service.py`
- `tests/test_nwr_outcome_scoring_service.py`
- `docs/outcome_probability/BUILD_PROCESS_PACKET.md`
- `tests/test_outcome_probability_build_packet.py`

Prior-prep outcome-column files were inspected as separate work and remain outside Sprint 2.

## Audit Answers

1. Supported row families are limited to:
   - `rookie_post_draft`
   - `all_player_pre_week1`
   - `offseason_carryover`

2. Unsupported row types are rejected by `_require_supported_row_type`. The test suite covers `rookie_pre_draft`. In-season row types and stale/reused prior-row behavior should remain rejected unless explicitly added later. A dedicated stale-row reuse detector belongs in Sprint 3's real row factory because Sprint 2 does not ingest rows.

3. `row_id` is deterministic from stable business keys:
   - row type
   - player id
   - position
   - cutoff id
   - input snapshot date
   - target season
   - target horizon

4. `snapshot_hash` is deterministic from canonicalized row payload.

5. Changing feature payload changes `snapshot_hash`; covered by test.

6. The source allowlist uses explicit allowed and blocked source families.

7. The legality validator rejects:
   - post-cutoff source timestamps
   - forbidden feature names
   - forbidden upstream sources
   - future-data flags
   - target-window overlap
   - incomplete lineage

8. `player_id` and `player_name` are preserved for identity/display and blocked from `feature_vector`.

9. Missingness mask preserves `None` and blank strings as missing instead of zero-filling.

10. Training rows are blocked before `label_available_date`.

11. Forbidden-source detection covers:
   - FantasyPros
   - ADP
   - public consensus
   - startup rankings
   - trade calculators
   - public projections
   - RotoWire projections/rankings/outlooks/values
   - market rank
   - league rank
   - prior `private_score`
   - prior model outputs
   - prior fantasy draft history
   - acquisition cost
   - same-season final stats
   - hindsight notes
   - post-cutoff updates

   Audit fix applied: forbidden-name detection now normalizes spaces, punctuation, hyphens, and slashes, so variants like `same-season final stats` and `RotoWire projections/outlooks/values` are caught.

12. Sprint 2 did not ingest or materialize real feature paths.

13. Sprint 2 did not create probabilities, rankings, model training outputs, base rates, or app percentage values.

14. Prior-prep outcome-column files remain separate. They are not imported by Sprint 2 and should not be included in a Sprint 2-only commit.

15. Sprint 1 and Sprint 2 are safe to commit as separate layers. Sprint 1 is already committed; Sprint 2 can be committed separately after review.

## Tests Run

Command run with the bundled Codex Python runtime because `python` on PATH points to the Windows Store alias in this shell:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_nwr_outcome_training_row_service.py tests/test_nwr_outcome_scoring_service.py tests/test_outcome_probability_build_packet.py -q
```

Result:

- `27 passed`

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m py_compile src/services/nwr_outcome_training_row_service.py tests/test_nwr_outcome_training_row_service.py
```

Result:

- passed

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m ruff check src/services/nwr_outcome_training_row_service.py tests/test_nwr_outcome_training_row_service.py
```

Result:

- passed

## Legality / Hash / Timestamp Issues

No failing legality, hash, or timestamp issues remain in the scaffold.

One audit hardening fix was made:

- Forbidden feature detection now canonicalizes separators before matching prohibited input families.

## Leakage Concerns

No leakage from Sprint 2 itself. The service defines allowlist/blocklist rules and validators only. It does not read historical source files or emit model rows.

Future leakage risk moves to Sprint 3, where real file ingestion must prove:

- each feature has complete lineage
- each source timestamp is on or before the prediction snapshot
- no target-window data enters features
- no stale prior rows are silently reused

## Forbidden-Source Coverage Gaps

No known Sprint 2 coverage gap remains after the separator-normalization hardening.

## Sprint 2-Only Commit Safety

Sprint 2 files are safe to commit separately:

```powershell
git add -- `
  src/services/nwr_outcome_training_row_service.py `
  tests/test_nwr_outcome_training_row_service.py `
  docs/outcome_probability/BUILD_SPRINT_2_POINT_IN_TIME_CONTRACTS.md `
  docs/outcome_probability/SPRINT_2_AUDIT_REPORT.md
```

Do not include prior-prep files in the Sprint 2 commit:

- `docs/model_v4/OUTCOME_COLUMN_INTEGRATION_CONTRACT_20260610.md`
- `tests/test_outcome_column_integration_contract.py`
- `scripts/validate_outcome_column_package.py`
- `src/services/outcome_column_package_service.py`
- `tests/test_outcome_column_package_service.py`

## Proceed To Sprint 3?

Yes, after a Sprint 2-only commit is reviewed/approved.

Sprint 3 should create a read-only historical row factory that emits point-in-time rows and row-level legality reports. It should not train models or create probabilities until the factory outputs are audited.

## Remaining Blockers

- No real historical feature rows are materialized yet.
- No row-level source manifests have been validated against actual files yet.
- Stale/reused prior-row prevention must be implemented in the Sprint 3 row factory.
- Probability models, base rates, and app percentage display remain intentionally blocked.
