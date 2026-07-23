# Hermetic and LocalData results

Independent adoption verification used:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify-repository.ps1 -Tier Hermetic -RepoRoot <ADOPTION_ROOT>
```

Hermetic result:

- bootstrap checks: 13/13 pass;
- security automation regressions: 20/20 pass;
- Python tests: 2,798 passed;
- owned/changed-file Ruff: pass;
- terminal marker: `HERMETIC_TIER_PASS`;
- exit code: `0`.

LocalData was invoked separately without importing or synthesizing a pack:

- result: `BLOCKED_MISSING_LOCAL_TEST_PACK`;
- native exit code: `4`;
- wrapper verification: pass.

Static follow-up:

- Python compileall: pass;
- changed-file Ruff: pass;
- whole-tree Ruff candidate: 4,443 pre-existing findings;
- live-HQ baseline: 4,443 findings;
- no-new-Ruff differential: pass;
- changed PowerShell parse gate: not applicable because no PowerShell file
  changed;
- new skip/xfail/xpass count: zero.
