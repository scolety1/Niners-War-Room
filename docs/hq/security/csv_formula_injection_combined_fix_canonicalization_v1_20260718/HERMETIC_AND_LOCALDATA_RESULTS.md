# Hermetic and LocalData Results

## Hermetic

Command:

```powershell
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File scripts/verify-repository.ps1 -Tier Hermetic -RepoRoot C:\NWR\Niners-War-Room-csv-formula-final-hq-adoption-v1-20260718
```

Authoritative adoption rerun:

- bootstrap controls: `13/13`;
- focused security controls: `20/20`;
- strict Python collection: `2513 passed`;
- skipped, xfailed, xpassed: zero;
- owned Ruff check: pass;
- marker: `HERMETIC_TIER_PASS`;
- process exit: `0`.

## LocalData

The same verifier was invoked with `-Tier LocalData`. The approved repository-
local pack was absent, so output stopped before test collection with:

```text
LOCALDATA_TIER_BEGIN
BLOCKED_MISSING_LOCAL_TEST_PACK
```

The child-process exit was explicitly captured as `4`. No LocalData test was
collected, passed, skipped, xfailed, xpassed, or represented as Hermetic.
