# Build Sprint 3 Audit Report

Status: PASS WITH TODOs

Sprint 3 is safe as a read-only historical row factory/source-inventory scaffold. It should be committed separately from prior-prep outcome-column files, but NWR should run a Sprint 3B real-source dry-run before Sprint 4 base rates.

## Files Audited

- `src/services/nwr_outcome_historical_row_factory.py`
- `tests/test_nwr_outcome_historical_row_factory.py`
- `docs/outcome_probability/BUILD_SPRINT_3_HISTORICAL_ROW_FACTORY.md`

Sprint 1 and Sprint 2 compatibility also checked:

- `src/services/nwr_outcome_scoring_service.py`
- `tests/test_nwr_outcome_scoring_service.py`
- `src/services/nwr_outcome_training_row_service.py`
- `tests/test_nwr_outcome_training_row_service.py`
- `docs/outcome_probability/BUILD_PROCESS_PACKET.md`
- `tests/test_outcome_probability_build_packet.py`

## Audit Answers

1. Sprint 3 remains read-only. The service emits candidate objects and writes dry-run exports only to caller-provided folders. It does not mutate production data.
2. Supported row families are limited to `rookie_post_draft`, `all_player_pre_week1`, and `offseason_carryover`.
3. Unsupported row families, including pre-draft and in-season rows, are rejected. Stale prior-row reuse is rejected through `stale_prior_row` and mismatched `prior_row_cutoff_id` checks.
4. Source inventory classifies sources as `allowed`, `blocked`, `unknown`, or `display_only`.
5. Forbidden sources are blocked by path/header token detection.
6. Unknown sources are marked `manual_review_required` and are not allowed automatically.
7. Row emission uses Sprint 2 contracts directly: `PredictionSnapshot`, `FeatureSnapshot`, `TrainingRow`, `FeatureLegalityAudit`, source allowlist rules, row IDs, snapshot hashes, missingness masks, and label gates.
8. Emitted legal candidates get deterministic `row_id` and `snapshot_hash` through Sprint 2 helpers.
9. Optional missing features are preserved as `None` and marked in the missingness mask.
10. Optional missing features are not zero-filled.
11. Training rows are blocked before `label_available_date`.
12. Illegal feature snapshots are blocked by the Sprint 2 legality validator.
13. Dry-run exports write only to the requested output folder and do not touch production exports.
14. Sprint 3 did not create base rates, probabilities, rankings, model outputs, or app percentages.
15. Prior-prep outcome-column files remain separate and should not be included in a Sprint 3-only commit.
16. The listed blockers before v0 base rates are accurate: real source manifests, cutoff dates, source max timestamps, raw stat-to-label mapping, label availability dates, row-level leakage reports, identity coverage, and first-down/injury/opportunity coverage decisions.

## Read-Only Review

No read-only violation found.

`write_dry_run_exports()` can write export contracts, but only to an explicitly supplied `output_dir`. It does not target active Rankings, app data packs, or production outcome columns.

## Source Classification Review

No source-classification blocker found for the scaffold.

The current classifier is intentionally conservative:

- forbidden path/header tokens become `blocked`
- source hints become `allowed`
- prior-draft/market/comparison context becomes `display_only`
- unknown files become `unknown` and require manual review

TODO before Sprint 4: run this against real local historical source paths and review false positives/false negatives in the generated inventory.

## Leakage Review

No leakage concern found in Sprint 3 logic.

The row factory delegates feature legality to Sprint 2, which rejects:

- post-cutoff source timestamps
- source max timestamps after cutoff
- forbidden feature/source families
- future-data flags
- target-window overlap
- incomplete lineage
- identity fields used as model features

No player probabilities, app percentages, base rates, or trained model outputs were created.

## Tests And Checks

Requested shell shims were unavailable in this Windows session:

- `pytest`: not on PATH
- `python`: Windows Store alias, no interpreter
- `ruff`: not on PATH

Equivalent checks were run through the bundled Codex Python runtime:

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests/test_nwr_outcome_historical_row_factory.py tests/test_nwr_outcome_training_row_service.py tests/test_nwr_outcome_scoring_service.py tests/test_outcome_probability_build_packet.py -q
```

Result: `41 passed in 0.26s`

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m py_compile src/services/nwr_outcome_historical_row_factory.py tests/test_nwr_outcome_historical_row_factory.py
```

Result: passed

```powershell
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m ruff check src/services/nwr_outcome_historical_row_factory.py tests/test_nwr_outcome_historical_row_factory.py
```

Result: `All checks passed!`

```powershell
git diff --check
```

Result: passed with pre-existing CRLF warnings on prior-prep files:

- `docs/model_v4/OUTCOME_COLUMN_INTEGRATION_CONTRACT_20260610.md`
- `tests/test_outcome_column_integration_contract.py`

```powershell
git status --short
git diff --stat
```

Result: Sprint 3 files are untracked; prior-prep outcome-column files remain modified/untracked separately.

## Prior-Prep Separation

Prior-prep files are separate from Sprint 3 and should not be included in the Sprint 3-only commit:

- `docs/model_v4/OUTCOME_COLUMN_INTEGRATION_CONTRACT_20260610.md`
- `tests/test_outcome_column_integration_contract.py`
- `scripts/validate_outcome_column_package.py`
- `src/services/outcome_column_package_service.py`
- `tests/test_outcome_column_package_service.py`

## Safe Sprint 3 Commit List

Exact Sprint 3-only staging command:

```powershell
git add -- `
  src/services/nwr_outcome_historical_row_factory.py `
  tests/test_nwr_outcome_historical_row_factory.py `
  docs/outcome_probability/BUILD_SPRINT_3_HISTORICAL_ROW_FACTORY.md `
  docs/outcome_probability/SPRINT_3_AUDIT_REPORT.md
```

## Proceed To Sprint 3B?

Yes. Proceed to Sprint 3B before Sprint 4.

Sprint 3B should run this scaffold against real local historical source paths and create read-only inventory/dry-run outputs. Sprint 4 should wait until those source inventories and leakage/missingness reports confirm that legal historical rows exist.

## Remaining Blockers Before v0 Base Rates

- Real source manifest for each supported row family.
- Point-in-time cutoff dates for each row family.
- Source max timestamps for each feature source.
- Historical raw stat rows mapped to Sprint 1 scoring components.
- Historical label availability dates.
- Row-level leakage audit exports from actual files.
- Identity coverage reports across seasons.
- First-down and injury/opportunity coverage decisions.
- Manual review of unknown/display-only source classifications from real local files.
