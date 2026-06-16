# Sprint 5EI - App-Readable Numeric Artifact Contract And Generator

## Purpose

Sprint 5EI creates the narrow app-readable numeric Outcome display artifact contract and generator allowed by Sprint 5EH.

This sprint creates the approved app-readable artifact path only. It does not edit Rankings UI, change rankings/sorting, create hidden sort keys, create Top 6 or unapproved heads, create promoted artifacts outside the approved path, commit `data/`, commit `local_exports/`, touch rookie files, push, deploy, release, merge, or push main.

## Files Created

Tracked files:

- `docs/outcome_probability/BUILD_SPRINT_5EI_APP_READABLE_NUMERIC_ARTIFACT_CONTRACT_AND_GENERATOR.md`
- `src/services/nwr_outcome_numeric_probability_display_service.py`
- `scripts/outcome_probability/build_phase11_numeric_outcome_display_artifact_v1.py`
- `app/generated/outcome_probability/numeric_outcome_display_v1.csv`
- `tests/test_nwr_outcome_numeric_probability_display_service.py`

The files match the Sprint 5EH allowlist.

## App-Readable Artifact Path

Approved artifact path:

`app/generated/outcome_probability/numeric_outcome_display_v1.csv`

This is the only app-readable numeric Outcome artifact created by Sprint 5EI.

## Artifact Contract

Required columns:

- `player_id`
- `player_display_name`
- `position`
- `outcome_status`
- `qb_t12_display_pct`
- `rb_t12_display_pct`
- `rb_t24_display_pct`
- `wr_t12_display_pct`
- `wr_t24_display_pct`
- `wr_t36_display_pct`
- `te_t12_display_pct`
- `unavailable_reason_public`
- `artifact_version`
- `source_evidence_version`
- `generated_at_utc`

The artifact uses `player_id` as the stable join key. Display values are whole-number percentage strings only. Unsupported rows carry `outcome_status=unavailable` and no display percentage values.

## Approved Heads Emitted

- `qb_t12`
- `rb_t12`
- `rb_t24`
- `wr_t12`
- `wr_t24`
- `wr_t36`
- `te_t12`

Blocked/unapproved heads are absent, including:

- `qb_t6`
- `rb_t6`
- `wr_t6`
- `te_t3`
- `te_t6`
- `qb_t18`
- `qb_t24`
- `rb_t36`
- `rb_t48`
- `wr_t48`
- `te_t18`
- `te_t24`

## Row Counts

The generator preserved the Phase 10 baseline:

| Metric | Count |
| --- | ---: |
| Total rows | 240 |
| Available rows | 227 |
| Unavailable rows | 13 |

If these counts change in a future regeneration, the generator fails with a YELLOW count mismatch unless the change is explicitly explained by an updated Rankings pool in a later sprint.

## Generator Behavior

Generator:

`scripts/outcome_probability/build_phase11_numeric_outcome_display_artifact_v1.py`

Behavior:

- reads the Phase 10 5ED local-only dry-run evidence;
- emits only the 5EH-approved app artifact path;
- converts probability audit units to whole-number display percentages;
- emits no raw decimal probability fields;
- emits no sorting/ranking fields;
- emits no hidden keys;
- fails closed on out-of-bounds values or blocked head columns.

## Service Contract

Service:

`src/services/nwr_outcome_numeric_probability_display_service.py`

Behavior:

- loads the approved artifact path;
- validates exact columns;
- validates whole-number percentage strings;
- validates unavailable rows have no fake numeric values;
- exposes display rows joined by `player_id`;
- exposes no sortable Outcome value.

## Checks

Checks run:

- `python -m py_compile src/services/nwr_outcome_numeric_probability_display_service.py scripts/outcome_probability/build_phase11_numeric_outcome_display_artifact_v1.py tests/test_nwr_outcome_numeric_probability_display_service.py`
- `python scripts/outcome_probability/build_phase11_numeric_outcome_display_artifact_v1.py`
- `python tests/test_nwr_outcome_numeric_probability_display_service.py`
- `git diff --check`

Results:

- generator returned `VERDICT=GREEN`;
- artifact path: `app/generated/outcome_probability/numeric_outcome_display_v1.csv`;
- rows: 240;
- available: 227;
- unavailable: 13;
- seven focused service tests passed.

## Recommendation

Verdict: GREEN for Sprint 5EJ.

Sprint 5EJ may wire the approved artifact into the Rankings page using only the Sprint 5EH UI allowlist. The wiring must remain display-only and must not change ranking order, sorting behavior, or hidden keys.
