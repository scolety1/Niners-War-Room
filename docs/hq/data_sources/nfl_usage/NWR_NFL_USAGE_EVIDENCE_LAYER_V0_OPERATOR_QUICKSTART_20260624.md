# NFL Usage Evidence Layer V0 Operator Quickstart

## Dry Run

Run focused tests:

```powershell
.venv\Scripts\python.exe -m pytest tests\test_nfl_usage_data_loader_service.py tests\test_nfl_usage_derived_feature_service.py tests\test_nfl_usage_validation_service.py
```

Run Ruff on touched Python:

```powershell
.venv\Scripts\python.exe -m ruff check src\services\nfl_usage_data_loader_service.py src\services\nfl_usage_derived_feature_service.py src\services\nfl_usage_schema_fingerprint_service.py src\services\nfl_usage_validation_service.py tests\test_nfl_usage_data_loader_service.py tests\test_nfl_usage_derived_feature_service.py tests\test_nfl_usage_validation_service.py
```

Compile touched Python:

```powershell
.venv\Scripts\python.exe -m compileall src\services\nfl_usage_data_loader_service.py src\services\nfl_usage_derived_feature_service.py src\services\nfl_usage_schema_fingerprint_service.py src\services\nfl_usage_validation_service.py
```

## Safe Refresh Later

Only after dependency approval:

1. Install `nflreadpy` using the project dependency workflow.
2. Set raw cache to `C:\NWR_SHARED_DATA\nfl_usage_cache\`.
3. Run the smallest field-only source smoke.
4. Generate field names, row counts, schema fingerprints, coverage summaries, and attribution summaries.
5. Commit only sanitized review artifacts.

## Paths

- Raw cache: `C:\NWR_SHARED_DATA\nfl_usage_cache\`
- Repo-safe review artifacts: `docs/hq/data_sources/nfl_usage/review_artifacts/`
- Source contract: `docs/hq/data_sources/nfl_usage/NWR_NFL_USAGE_SOURCE_CONTRACT_V0_20260624.md`
- Promotion gate: `docs/hq/data_sources/nfl_usage/NWR_NFL_USAGE_FIELD_PROMOTION_GATE_V0_20260624.md`

## Do Not Do

- Do not scrape RotoWire or blocked vendor sites.
- Do not commit raw play-by-play, snap, NGS, FTN, PFR, or participation payloads.
- Do not update Dynasty Rank, Final Board Rank, tiers, latest_candidate, latest_approved, frozen board, pinned snapshot, model files, rank files, or source-truth files.
- Do not call public participation data true routes run.
- Do not call proxy fields true TPRR or true YPRR.
