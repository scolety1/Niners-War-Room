# Test Results

Green gates:

- Phase 0/1 expanded Python gate: 134 passed; targeted tier/draft-room rerun: 6 passed.
- Draft Room service: slots 2, 5, and 9; 150 unique legal picks each; deterministic replay; persistence/undo; ADP validation; Beat ADP and make-it-back states.
- Desktop HTTP/application contracts: strict start, advance, ADP import, pick, undo, and read-only Sleeper event routes.
- Frontend: 14 files, 58 tests passed.
- TypeScript: Dynasty and Redraft project references passed.
- Desktop resource allowlists: passed.
- Vite production builds: Dynasty passed; Redraft passed.
- Ruff on every touched Python file: passed.
- Tauri Redraft bundle: passed; NSIS and MSI emitted.

An attempted unscoped repository-wide sweep was stopped after unrelated legacy generators modified five tracked documentation outputs in-place. Those side effects were fully excluded (zero diff), and the bounded product/reconciliation suite was used as the release gate.
