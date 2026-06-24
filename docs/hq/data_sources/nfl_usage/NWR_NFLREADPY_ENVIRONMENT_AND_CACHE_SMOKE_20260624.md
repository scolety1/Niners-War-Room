# NFLReadpy Environment And Cache Smoke

## Verdict

YELLOW. The environment is safe, but live smoke is blocked.

## Environment

- Project dependency style: `pyproject.toml` plus `requirements.txt`.
- Python used for checks: `.venv\Scripts\python.exe`.
- Detected Python version: 3.14.6.
- `pandas`: available.
- `nflreadpy`: not available.
- `nfl_data_py`: not available.

## Existing Infrastructure

The repo already has nflverse local/scheduled pull and normalization scripts:
- `scripts/nflverse_scheduled_pull_v0.py`
- `scripts/nflverse_normalize_snapshot_v0.py`
- `src/services/nflverse_player_stats_import_service.py`
- `src/services/nflverse_raw_import_service.py`

Those scripts already keep raw scheduled ingest outside normal tracked repo paths and enforce review-only semantics.

## Dependency Recommendation

Defer dependency change until project-approved dependency workflow. If approved later, add `nflreadpy` consistently to `pyproject.toml` and `requirements.txt`, then run a tiny source smoke with raw cache outside the repo.

## Cache Policy

Raw cache path: `C:\NWR_SHARED_DATA\nfl_usage_cache\`

This path is outside the repo. Do not commit raw play-by-play, snap counts, NGS, FTN, PFR, or participation payloads.

## Smoke Status

Smoke attempted: no live pull. Status: `DRY_RUN_BLOCKED_NFLREADPY_NOT_INSTALLED`.

Raw data tracked: no.

Next recommended build path: keep V0 as dry-run/source-inventory infrastructure, then run exact field introspection after dependency approval.
