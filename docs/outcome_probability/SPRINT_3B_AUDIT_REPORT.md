# Sprint 3B Audit Report - Source Manifests

Status: PASS WITH TODOs

Sprint 3B remains a source-manifest and readiness scaffold only. It does not build Sprint 3C, v0 base rates, trained models, player probabilities, app percentage values, rankings, deployment artifacts, or pushed changes.

## Files Audited

- `src/services/nwr_outcome_source_manifest_service.py`
- `tests/test_nwr_outcome_source_manifest_service.py`
- `docs/outcome_probability/BUILD_SPRINT_3B_SOURCE_MANIFESTS.md`

Sprint 1, Sprint 2, and Sprint 3 compatibility was also checked through their focused tests.

## Audit Findings

### Source Manifest Classification

PASS. Source manifests classify sources as:

- `allowed`
- `blocked`
- `unknown`
- `display_only`

Unknown sources become `manual_review_required` and are not allowed automatically. Display-only/context sources also require manual review and are not training-ready by default.

Forbidden path/header contexts are blocked through normalized path and header detection. Covered examples include ADP, FantasyPros, public rankings/projections, consensus, startup, trade calculators, market rank, league rank, RotoWire projection/ranking/outlook/value, prior fantasy draft history, prior NWR private score, same-season final stats, hindsight notes, and post-cutoff updates.

### Timestamp And Cutoff Handling

PASS. Missing source timestamps block production row emission for otherwise allowed source families.

Cutoff definitions exist for:

- `rookie_post_draft`
- `all_player_pre_week1`
- `offseason_carryover`

The current cutoff values are contract templates (`YYYY-05-01`, `YYYY-09-01`, `YYYY-02-15`) and must be resolved to concrete historical-season dates before a real dry-run or base-rate build.

### Label Availability

PASS. Label availability is handled for:

- same-year / year-1
- next-year / year-2
- next-3-year
- next-5-year

Future/censored windows remain unavailable until the label availability date has passed. Unsupported horizons return `None` and should block materialization.

### Raw Stat Mapping

PASS WITH TODO. Raw stat alias mapping covers the Sprint 1 scoring components and reports missing components as `needs_data`.

Imported fantasy totals such as `week_score_total` are not accepted as raw stat component aliases and therefore do not satisfy Sprint 1 component coverage. However, Sprint 3B does not yet have a dedicated explicit blocker/test for imported fantasy-total-only source files. Sprint 3C should add a direct test and readiness issue for files that provide imported fantasy totals without raw scoring components.

### Dry-Run Export Safety

PASS. Dry-run exports require a caller-provided output folder and write only source-manifest/readiness exports:

- row family source manifests
- source manifest entries
- row-level leakage audits
- raw stat mapping readiness
- data readiness report

No production data packs are mutated.

### Leakage Concerns

No active leakage was found in Sprint 3B logic. Forbidden source/path/header contexts are blocked, unknown sources are manual-review-required, post-cutoff source timestamps are blocked, missing timestamps block production row emission, and raw-stat coverage remains component-based.

The only TODO is the explicit imported-fantasy-total hardening noted above.

### Prior-Prep Files

Prior-prep outcome-column files remain separate and are not required by Sprint 3B:

- `docs/model_v4/OUTCOME_COLUMN_INTEGRATION_CONTRACT_20260610.md`
- `scripts/validate_outcome_column_package.py`
- `src/services/outcome_column_package_service.py`
- `tests/test_outcome_column_integration_contract.py`
- `tests/test_outcome_column_package_service.py`

Those files should not be included in a Sprint 3B-only commit.

## Tests And Checks

Passed:

```powershell
python -m pytest tests/test_nwr_outcome_source_manifest_service.py tests/test_nwr_outcome_historical_row_factory.py tests/test_nwr_outcome_training_row_service.py tests/test_nwr_outcome_scoring_service.py tests/test_outcome_probability_build_packet.py -q
```

Result: `55 passed`

Passed:

```powershell
python -m py_compile src/services/nwr_outcome_source_manifest_service.py tests/test_nwr_outcome_source_manifest_service.py
```

Passed:

```powershell
python -m ruff check src/services/nwr_outcome_source_manifest_service.py tests/test_nwr_outcome_source_manifest_service.py
```

Result: `All checks passed!`

Passed with pre-existing CRLF warnings in unrelated prior-prep files:

```powershell
git diff --check
```

## Commit Safety

Sprint 3B files are safe to commit separately after review.

Exact Sprint 3B-only add list:

```powershell
git add -- `
  src/services/nwr_outcome_source_manifest_service.py `
  tests/test_nwr_outcome_source_manifest_service.py `
  docs/outcome_probability/BUILD_SPRINT_3B_SOURCE_MANIFESTS.md `
  docs/outcome_probability/SPRINT_3B_AUDIT_REPORT.md
```

Do not include prior-prep files or other untracked outcome package files in this Sprint 3B commit.

## Proceed / Blocked Status

Proceed to Sprint 3C: YES, with the imported-fantasy-total explicit blocker test as a Sprint 3C hardening item.

Proceed to v0 base rates: NO. v0 base rates remain blocked until:

- exact real source files are selected by row family
- cutoff templates are resolved to concrete historical dates
- source timestamps are present and verified on real rows
- label availability dates are verified per target horizon
- raw stat component coverage is confirmed on actual files
- row-level leakage audits are run against selected files
- dry-run source manifest exports show readiness

