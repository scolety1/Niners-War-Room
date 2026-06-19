# Mock Draft Operator Quick Start

## Verify Lane

```powershell
cd C:\NWR\Niners-War-Room-mock-draft
git branch --show-current
git rev-parse --short HEAD
git status --short
git diff --check
```

## Run Readiness Checks

```powershell
$uv = "C:\Users\codex-agent\.local\bin\uv.exe"
$env:PYTHONDONTWRITEBYTECODE="1"
& $uv run --locked python -B scripts/mock_draft_state_smoke.py
& $uv run --locked python -B scripts/mock_draft_input_readiness_check.py
& $uv run --locked python -B scripts/mock_draft_real_input_preflight.py
& $uv run --locked python -B scripts/mock_draft_closeout_status.py
```

## Focused Validation

```powershell
& $uv run --with pytest --with ruff pytest tests/test_draft_state_service.py tests/test_mock_draft_input_contract.py tests/test_mock_draft_closeout_status.py
& $uv run --with pytest --with ruff ruff check src/services scripts tests/test_mock_draft_closeout_status.py
```

## Readiness Colors

- GREEN: lane infrastructure or supplied inputs validate.
- YELLOW: real inputs or local manifest are missing.
- RED: unsafe source mixing, malformed inputs, or guardrail violation.

## Paste Back To Mock Draft HQ

Report branch, HEAD, status, smoke result, readiness result, real-input
preflight result, closeout status result, focused pytest/Ruff result, and
whether any real data was copied or committed.

No simulation command belongs in this quick start.

## Fixture Operator Practice

Use fixture practice only:

```powershell
$uv = "C:\Users\codex-agent\.local\bin\uv.exe"
& $uv run --locked python -B scripts/mock_draft_operator_practice.py demo
& $uv run --locked python -B scripts/mock_draft_operator_practice.py status
& $uv run --locked python -B scripts/mock_draft_operator_practice.py available
& $uv run --locked python -B scripts/mock_draft_operator_practice.py validate
```

These commands are for fake fixture rehearsal only. They do not read real inputs
or run a real simulation.
