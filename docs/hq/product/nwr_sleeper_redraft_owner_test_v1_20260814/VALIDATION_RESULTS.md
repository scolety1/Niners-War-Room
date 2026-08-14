# Validation results

- Existing `SleeperHttpClient` used for the real read-only response: pass.
- League, owner user ID, roster 9, unique 2026 draft and no draft slot: pass.
- Exact core scoring and roster mapping with non-zero unknown settings surfaced: pass.
- Local profile creation and active-profile ranking attempt: pass/fail-closed.
- Combined rookie + veteran board: blocked by governed K/DST projection-depth gate.
- Mock three-run QA and owner receipt: not run; blocked, not simulated.
- Python compile check: pass.
- Desktop TypeScript and production build: pass after the workspace's offline-locked dependencies were restored.
- Pytest: blocked in the bundled runtime because `pytest` is unavailable; tests are included for a normal project environment.
