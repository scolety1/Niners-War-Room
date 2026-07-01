# Runtime Restoration Report

## Verdict

GREEN for local artifact generation. No repo dependency changes were needed.

## Diagnosis

The previous blocker was not that `nflreadpy` lacked repo approval. `pyproject.toml` and `requirements.txt` already declare `nflreadpy`, and `docs/hq/data_sources/nfl_usage/NWR_NFLREADPY_DEPENDENCY_APPROVAL_20260624.md` approves local installation. The actual blocker was that the bundled Python runtime did not include `nflreadpy` unless the approved shared dependency path was added to `PYTHONPATH`.

## Restored Path

- Python: bundled Codex runtime Python
- Repo path on `PYTHONPATH`: repository root
- Approved nflreadpy path on `PYTHONPATH`: `C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps`
- Observed package: `nflreadpy 0.1.5`
- Smoke: `nflreadpy.load_player_stats([2012], summary_level='reg')` returned 1,811 rows

## Generation Command

```powershell
$env:PYTHONPATH = '<repo>' + [IO.Path]::PathSeparator + 'C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps'
python scripts\build_backtest_dataset_v1.py --seasons 2012 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022 2023 2024 2025 --output-root C:\NWR_SHARED_DATA\backtests --run-label historical_tuning_substrate_expansion_v2_20260701_2012_2025
```

Output rows: `5,518`.
