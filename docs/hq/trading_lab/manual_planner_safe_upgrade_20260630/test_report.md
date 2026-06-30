# Trading Lab Manual Planner Safe Upgrade Test Report

## Planned Validation

- focused Trading Lab service tests
- Trading Lab manual planner guardrail tests
- existing Original Doc UX guardrail test that covers Trading Lab
- compile check for touched Python files
- Ruff check for touched Python files
- git diff --check
- route smoke for `/trading-lab`

## Expected Assertions

- Trading Lab renders as a manual planner.
- Manual Trade Away and Trade For planners are visible.
- Structured rows and editable checklist copy are present.
- No visible-score gap appears in active UI code.
- No primary market sanity panel is rendered.
- No market helper drives Trading Lab summary/status/memo output.
- Missing evidence is explicit and gated.

## Result

- Focused tests: 29 passed.
- Ruff: passed for touched app/service/test files.
- Compile: passed for touched Python files.
- git diff --check: passed.
- Browser route smoke: `http://127.0.0.1:8573/trading-lab` loaded Trading Lab with 66 frozen-board rows, source badge text, manual context sections, and no active market/verdict UI terms.
- Browser interaction smoke: Trade Away Pick Planner and Trade For Pick Planner tabs were clickable and showed structured manual rows, editable checklist, and manual memo download controls.
