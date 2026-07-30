# Validation Results

| Gate | Result |
|---|---|
| Focused foundation tests | 39/39 PASS IN IMPLEMENTATION AND REVIEW |
| Mutation sensitivity | 28/28 PASS IN IMPLEMENTATION AND REVIEW |
| Deterministic regeneration | PASS 35/35 ACROSS TWO CLEAN ROOTS |
| Hermetic | PASS 2934/2934 IN IMPLEMENTATION AND REVIEW; 13/13 BOOTSTRAP; 20/20 CONTROLS |
| LocalData | BLOCKED_MISSING_LOCAL_TEST_PACK EXIT 4 IN IMPLEMENTATION AND REVIEW |
| Security regressions | PASS REQUIRED FINDING REGRESSIONS; NO SECURITY SCAN RUN |
| Data Health passive reads | 63/63 PASS IN IMPLEMENTATION AND REVIEW |
| Python compilation | PASS ALL CHANGED PYTHON |
| PowerShell parsing | NOT_APPLICABLE_NO_CHANGED_PS1 |
| Changed-file Ruff | PASS ZERO CHANGED_FILE_FINDINGS |
| No-new-Ruff differential | PASS HQ 4443 CANDIDATE 4443 NEW 0 |
| Git whitespace | PASS |
| Preservation | PASS BOARD FROZEN OPAQUE 5/5 PERSISTENT RECOVERY |
| Scheduled task | DISABLED ENABLED_FALSE; ZERO MATCHING REFRESH PROCESSES |

No skip, xfail, or xpass is allowed. LocalData must return exactly
`BLOCKED_MISSING_LOCAL_TEST_PACK` with exit 4.
