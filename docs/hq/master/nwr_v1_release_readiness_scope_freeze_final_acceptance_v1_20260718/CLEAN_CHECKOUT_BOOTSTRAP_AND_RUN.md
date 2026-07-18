# Clean-checkout bootstrap and run

## Prerequisites

- Git 2.54.0 was used for this lane.
- PowerShell 5.1.26100.8875 was used.
- Python 3.12 or newer is supported; the isolated verification runtime resolved Python 3.14.6.
- `uv 0.11.22` and its already available offline cache were used for deterministic dependency isolation.
- No provider credentials, private league data, LocalData, or sibling-worktree copying is required.

## Commands and observations

| Step | Command | Duration | Exit |
|---|---|---:|---:|
| Offline runtime/dependencies | `uv run --offline --no-project --with pytest --with ruff --with nflreadpy --with numpy --with pandas --with pydantic --with streamlit python -c <version-check>` | 5.483 s | 0 |
| Hermetic bootstrap clean | `powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File .\scripts\bootstrap-hermetic-test-pack.ps1 -RepoRoot . -OutputRoot .\local_exports\hermetic_test_pack_v1 -Clean` | 0.868 s | 0 |
| Hermetic bootstrap repeat | same command | 0.513 s | 0 |
| Cold application startup/HTTP | isolated `uv ... streamlit run app/main.py --server.headless true --server.port 8518` then local HTTP GET | 2.18 s upper bound | HTTP 200 |
| Warm application startup | isolated `uv ... streamlit run app/main.py --server.headless true --server.port 8519` | 2.01 s to process yield/server start | 0 while serving |
| Route discovery/smoke | local in-app browser plus CDP; 60 endpoints Ã— 3 widths | bounded matrix; slowest endpoint 4.097 s | 180/180 pass |
| Clean shutdown | Ctrl+C; listener/process verification | 1.09 s | process shell reports 1 after interrupt; server prints â€œStoppingâ€ |
| Repeat run | second server and full corrected matrix | completed | pass |

Resolved packages were numpy 2.5.1, pandas 3.0.3, pydantic 2.13.4, Streamlit 1.59.2, and pytest 9.1.1.

## Determinism and isolation

Both bootstrap runs produced SHA256SUMS hash `6e7e2ff88de7e1fc8bd620657a619e16d1d183bb117d9c9c631477ab811ad98f` and PACK_MANIFEST hash `3cc8da45be5ddc2ce2b2c3a719e3ee0ec7bc365e607a97bb3667a9a090a3f842`.

The correction removes the two runtime fallbacks that referenced other developer worktrees. Optional rankings and outcome files now resolve only inside the active checkout. Missing optional data produces explicit unavailable/caveat behavior, not a crash. After shutdown, no test listener or candidate app process remained.
