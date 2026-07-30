# Validation results

| validation | command | expected | observed | status | notes |
| --- | --- | --- | --- | --- | --- |
| targeted builder and analytical invariants | build_nwr_dual_lens_rc1_targeted_revision_v1_20260729.py | exit 0; 5518 historical; 240 current; 20 mutations; 43 second-year | exit 0; 5518 historical; 240 current; 20/20 mutations; 43/43 second-year | PASS | W3 and D1 reselected from corrected season-aware evidence; both remain not admitted. |
| focused dual-lens research contracts | pytest test_nwr_dual_lens_rc1_research.py test_nwr_dual_lens_rc1_targeted_revision.py | all pass | 20 passed | PASS | Real-path mutations, availability semantics, nDCG, cohorts, rookie evidence, gates, boards, inventory, and manifests. |
| strict Hermetic repository tier | verify-repository.ps1 -Tier Hermetic | exit 0; no skip, xfail, or xpass | 13 bootstrap; 20 security regressions; 2915 Python passed; Ruff passed; exit 0 | PASS | Existing security regressions only; no new security scan. |
| LocalData boundary | verify-repository.ps1 -Tier LocalData | BLOCKED_MISSING_LOCAL_TEST_PACK; native exit 4 | BLOCKED_MISSING_LOCAL_TEST_PACK; native exit 4 | PASS_EXPECTED_BLOCK | No arbitrary-disk fallback, LocalData read, copy, or synthesis. |
| passive Data Health reads and page-open safety | pytest four Data Health service/route/page-open files | all pass | 59 passed | PASS | No page-open mutation. |
| deterministic regeneration | full targeted builder from implementation and independent review roots | 61 files; zero mismatches | 61 files; zero name, byte, or SHA-256 mismatches | PASS | Original 38-file packet plus additive 23-file targeted packet. |
| Python compilation | python -m py_compile two builders and two focused tests | exit 0 | exit 0 | PASS | Independent review root. |
| changed-file Ruff and no-new-Ruff differential | ruff check two builders and two focused tests; Hermetic Ruff | zero findings | All checks passed | PASS | No new Ruff findings. |
| PowerShell parser | Parser.ParseFile over tracked PowerShell files | zero parse errors | 25 files parsed; zero errors | PASS | No PowerShell file changed. |
| protected changed-path allowlist | git diff --name-only b1ed04e2..review-HEAD | only bounded builder/test/docs/LF paths | 42 of 42 paths allowed; zero protected or production paths | PASS | No app, runtime, Finished V1, Outcome V3, frozen, LocalData, or V2-2 path changed. |
| canonical baseline and preservation hashes | check_nwr_outcome_v3_preservation.py | all exact | Finished and frozen match; opaque 5/5; persistent 14; recovery 7; all digests exact | PASS | Opaque CSV contents were never opened, parsed, copied, normalized, staged, or used. |
| scheduled-task and refresh-process state | Get-ScheduledTask plus process readback | Disabled; Enabled false; zero refresh workers | Disabled; Enabled false; zero refresh workers | PASS | Scheduled refresh was neither enabled nor executed. |
| whitespace and repository cleanliness | git diff --check and git status --short | no whitespace errors; clean independent review root | no whitespace errors; clean independent review root | PASS | Stable UTF-8 LF output and non-self-referential manifests. |
| provider, security-scan, and production-mutation boundaries | source and changed-path inspection | none | zero provider calls; no new security scan; zero production/UI/data mutations | PASS | Finished V1 and Outcome V3 remain canonical. |
| second and final bounded correction cycle | independent review of targeted validation correction | one authorized final cycle; no further corrections | targeted cycle used; independent review fully green | PASS | Scope limited to real-path mutations, availability semantics, cohort completeness, season-aware nDCG, and inventory. |

The targeted builder itself requires all 20 executed mutations to fail closed,
all 240 current rows to appear exactly once in the mechanically assigned
experience cohort, separate continuous and binary availability semantics,
season-aware primary nDCG, and unchanged pinned production hashes. Hermetic
must exit 0; LocalData must remain `BLOCKED_MISSING_LOCAL_TEST_PACK` with exit
4. No provider call, security scan, scheduled-task execution, production
integration, skip, xfail, or xpass is authorized.
