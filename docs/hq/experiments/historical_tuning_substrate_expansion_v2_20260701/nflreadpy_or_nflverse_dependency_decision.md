# nflreadpy Or nflverse Dependency Decision

Decision: use the existing approved dependency declaration and the existing approved local shared pydeps path. Do not edit dependency files in this lane.

Evidence:

- `pyproject.toml` already lists `nflreadpy`.
- `requirements.txt` already lists `nflreadpy`.
- `scripts/run_nflverse_refresh_v0.ps1` uses `C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps` on `PYTHONPATH`.
- `tests/test_scheduler_runner_scripts_v0.py` asserts that runner behavior.
- `C:\NWR_SHARED_DATA\vendor_spikes\nflverse\scratch\pydeps` exists locally and contains `nflreadpy-0.1.5.dist-info`.

No package was installed globally. No package was vendored into the repo. No production runtime behavior was changed.
