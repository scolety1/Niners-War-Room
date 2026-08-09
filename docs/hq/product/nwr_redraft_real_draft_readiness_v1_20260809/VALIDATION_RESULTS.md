# Validation Results

- Starting HQ: `e0b5ef89082b565a6dd2c6862239e45f9d67037f`; tree `936fa643d26c6d5ac4571e53642f5b3e6102c88f`.
- Focused after cycle 3: 27/27 passed.
- Selected Redraft/Dynasty regressions: 138/138 passed.
- Ruff owned paths: passed. `git diff --check`: passed.
- Browser: three viewports, Redraft primary surfaces, Draft Cockpit, Mock Draft, Player Compare, seven Dynasty routes passed settled checks.
- Console classification: two cold-start Streamlit deep-link messages and one expected WebSocket close during owned restart; zero settled blocking console errors.
- Three correction cycles used; no projection/model/source changes.
- Disposable profiles, backup, restore copy, processes, browser tabs, and listening port cleaned.
