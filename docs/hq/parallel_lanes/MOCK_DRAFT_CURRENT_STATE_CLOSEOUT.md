# Mock Draft Current State Closeout

## Lane

- Repo: `C:\NWR\Niners-War-Room-mock-draft`
- Branch: `work/mock-draft-simulator`
- Latest HEAD before this closeout runway: `9d7f432fd9fbbe5711cfb6c878ba10a820b43861`
- Current verdict: GREEN infrastructure / YELLOW real draft-use readiness.

## Complete

- Deterministic draft-state validation and smoke coverage.
- Input readiness contracts and fixture schemas.
- Manifest, schema diagnostics, header aliases, redaction, and real-input
  preflight scaffolding.
- Read-only operator docs and handoff packets.
- ADP/market separation checks.

## Missing Before Draft Use

- Local-only real manifest.
- Frozen rookie input.
- Dropped/available veteran pool.
- Final pick order and NWR/my picks.
- Rosters/keepers.
- Team needs/opponent tendencies.
- NWR private value source.
- ADP/market behavior context.

## Latest Successful Validation

```powershell
$uv = "C:\Users\codex-agent\.local\bin\uv.exe"
$env:PYTHONDONTWRITEBYTECODE="1"
& $uv run --locked python -B scripts/mock_draft_state_smoke.py
& $uv run --locked python -B scripts/mock_draft_input_readiness_check.py
& $uv run --locked python -B scripts/mock_draft_real_input_preflight.py
& $uv run --with pytest --with ruff pytest tests/test_draft_state_service.py tests/test_mock_draft_input_contract.py
& $uv run --with pytest --with ruff ruff check src/services scripts tests/test_mock_draft_input_contract.py
```

Recent results: state smoke passed `9/9`; readiness script passed with
aggregate YELLOW, fixture GREEN, real input YELLOW; real-input preflight
reported missing manifest as YELLOW; focused lane-local pytest and Ruff passed.

## No-Simulation Gate

No mock draft simulation may run until real inputs are supplied, validated
GREEN, and explicitly approved. Missing real inputs are YELLOW readiness gaps.
Schema contamination or ADP/market mixing into NWR private value is RED.

## ADP / Market Separation

ADP/market context is opponent behavior, availability, and likely pick timing
only. It must never become NWR private quality, value, ranking, sorting key,
probability, band, or promoted artifact.

## Next Step

When real inputs are supplied, run the real-input validation prompt and
preflight script read-only. Create a local-only manifest only if explicitly
approved, and never commit real files or manifest paths.

## Stop Conditions

Stop for wrong branch, dirty unexpected files, `uv.lock` changes, staged real
data, any app/production/Outcome/Rookie/Drop Decision cross-lane edit, any
simulation path, or ADP/market-to-private-value mixing.
