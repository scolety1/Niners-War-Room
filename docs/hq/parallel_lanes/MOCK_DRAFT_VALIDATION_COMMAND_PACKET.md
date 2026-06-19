# Mock Draft Validation Command Packet

Run from `C:\NWR\Niners-War-Room-mock-draft` on
`work/mock-draft-simulator`.

```powershell
$uv = "C:\Users\codex-agent\.local\bin\uv.exe"
$env:PYTHONDONTWRITEBYTECODE="1"
```

## Core Checks

```powershell
git diff --check
& $uv run --locked python -B scripts/mock_draft_state_smoke.py
& $uv run --locked python -B scripts/mock_draft_input_readiness_check.py
```

## Preferred Locked Gates

```powershell
& $uv run --locked pytest tests/test_draft_state_service.py tests/test_mock_draft_input_contract.py
& $uv run --locked ruff check src/services tests scripts/mock_draft_state_smoke.py scripts/mock_draft_input_readiness_check.py
```

## Approved Ephemeral Fallback

Use only when locked pytest/Ruff are unavailable and confirm `uv.lock` remains
clean afterward.

```powershell
& $uv run --with pytest --with ruff pytest tests
& $uv run --with pytest --with ruff ruff check src/services tests scripts/mock_draft_state_smoke.py scripts/mock_draft_input_readiness_check.py
git status --short -- uv.lock
```

## Cleanup And Status

```powershell
Get-ChildItem -Recurse -Directory -Force |
  Where-Object {
    $_.FullName -notmatch '\\.venv\\' -and
    $_.Name -in @("__pycache__", ".pytest_cache", ".ruff_cache", "niners_war_room.egg-info")
  } |
  Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

git status --short
git status --short -- uv.lock
```

No simulations run in this packet.
