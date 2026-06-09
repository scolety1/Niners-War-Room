# Phase 10K Post-Download Move Preservation Check

Date: 2026-05-17

## Reason

The user reorganized files out of `Downloads`. This check verifies that Model v4 does not rely on `Downloads` as a permanent source of truth and that project-preserved copies survived.

## Checks Run

- Confirmed Phase 10A-10J docs exist.
- Confirmed canonical first-down, return, identity, and evidence-matrix outputs exist.
- Confirmed the Phase 10I data-spine audit zip exists.
- Confirmed `local_exports/model_v4/raw_user_exports` contains preserved raw/source copies.
- Hash-checked every path controlled by raw-user-export manifests/indexes.
- Hash-checked the Phase 10 external research report bundle.
- Ran focused preservation-sensitive tests:
  - `tests/test_model_v4_fantasypros_advanced_intake_service.py`
  - `tests/test_model_v4_fantasypros_identity_mapping_service.py`
  - `tests/test_model_v4_evidence_matrix_service.py`

## Results

- Raw user export file count under `local_exports/model_v4/raw_user_exports`: 307
- Phase 10 external research reports preserved: 8
- Manifest-controlled missing files: 0
- Manifest hash failures: 0
- Focused tests: 15 passed
- Phase 10G evidence matrix status: `ready_for_formula_design_review`
- Market leakage violations in latest evidence matrix summary: 0
- Fake-zero missing violations in latest evidence matrix summary: 0
- Duplicate entity rows in latest evidence matrix summary: 0
- Ambiguous join rows in latest evidence matrix summary: 0

## Cleanup Performed

Two legacy FantasyPros advanced per-batch manifests had stale `archived_path` values after the earlier 2017/2018 duplicate split. The raw files themselves were present and the canonical intake index was already clean. The manifest paths were updated to point at the actual preserved project copies:

- `local_exports/model_v4/raw_user_exports/fantasypros_advanced/2017_confirmed_20260517T034242Z/MANIFEST.csv`
- `local_exports/model_v4/raw_user_exports/fantasypros_advanced/2018_received_20260517T033626Z/MANIFEST.csv`

No raw data files were edited.

## Notes

Some generated evidence rows still record original `Downloads` filenames inside provenance fields. Those are historical source labels embedded in processed outputs, not live read dependencies. Future regeneration should prefer project-controlled raw paths in provenance where practical, but the current model-ready files do not require the original `Downloads` files to exist.

## Verdict

The project-preserved Model v4 data spine survived the Downloads reorganization. The project is safe to continue from the controlled raw/source folders and latest Phase 10 outputs.

