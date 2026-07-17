# LocalData and Hermetic Results

## Hermetic

Command:

```powershell
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File scripts/verify-repository.ps1 -Tier Hermetic -RepoRoot C:\NWR\Niners-War-Room-csv-formula-whitespace-revision-v1-20260717
```

Authoritative final result:

- bootstrap controls: `13/13`;
- focused security controls: `20/20`;
- strict Python collection: `2513 passed`;
- skipped, xfailed, xpassed: zero;
- owned Ruff check: pass;
- marker: `HERMETIC_TIER_PASS`;
- exit: `0`.

The prior expected total was 2271. The increase is attributable to the added
focused regression nodes; no prior test was removed.

## LocalData

The approved pack is absent. The LocalData command emitted:

```text
LOCALDATA_TIER_BEGIN
BLOCKED_MISSING_LOCAL_TEST_PACK
```

The child-process exit was captured as `4`. No LocalData test was collected,
passed, skipped, xfailed, xpassed, or counted as Hermetic.
