# Validation results

| validation | command | expected | observed | status | notes |
| --- | --- | --- | --- | --- | --- |
| builder and analytical invariants | bundled-python scripts/build_nwr_dual_lens_rc1_v1_20260729.py | exit 0; 5,518 historical and 240 current rows | exit 0; 5,518 historical; 240 current; 227 scored per lens | PASS | W3 and D1 selected; both fail closed; no production integration. |
| formula, rookie, Team Window, board, mutation, and manifest contracts | pytest test_nwr_dual_lens_rc1_research.py plus Outcome display | 14 passed | 14 passed | PASS | Includes canonical Outcome manifest hashes, 19 mutation detectors, and rookie null fences. |
| named core-app, route, accessibility, and page-open safety matrix | pytest 25 named surface files | all pass | 291 passed | PASS | Compare, Trading Lab, draft tools, roster, rankings, Data Health, routes, accessibility, and no-write paths. |
| strict Hermetic repository tier | verify-repository.ps1 -Tier Hermetic | exit 0; no skip, xfail, or xpass | 13 bootstrap; 20 security regression; 2,905 Python passed; Ruff passed; exit 0 | PASS | Existing security regressions only; no new security scan. |
| LocalData boundary | verify-repository.ps1 -Tier LocalData | BLOCKED_MISSING_LOCAL_TEST_PACK; native exit 4 | BLOCKED_MISSING_LOCAL_TEST_PACK; native exit 4; zero collection | PASS_EXPECTED_BLOCK | No arbitrary-disk fallback, LocalData read, copy, or synthesis. |
| deterministic regeneration | full builder from implementation and independent review roots | 38 files; zero mismatches | 38 files; zero name, byte, or SHA-256 mismatches | PASS | Also matched across bundled and project Python runtimes. |
| Python compile | python -m py_compile builder and focused test | exit 0 | exit 0 | PASS | Bundled workspace Python. |
| Ruff | ruff check builder and focused test | zero findings | All checks passed | PASS | Hermetic also reran its owned Ruff gate. |
| PowerShell parser | Parser.ParseFile over tracked PowerShell files | zero parse errors | 25 files parsed; zero errors | PASS | No PowerShell file was changed by this lane. |
| protected changed-path allowlist | git diff --name-only remote-HQ..review-HEAD | only packet, builder, test, and LF materialization rule | 41 of 41 paths allowed; zero protected or production paths | PASS | No app, source, runtime, production ranking, Outcome payload, frozen comparator, or LocalData diff. |
| canonical baseline hashes | SHA-256 readback for Finished V1, frozen comparator, and Outcome V3 | five exact canonical matches | five of five exact matches | PASS | Outcome LF working bytes now match its unchanged committed manifest. |
| opaque and persistent preservation | check_nwr_outcome_v3_preservation.py | all exact | opaque 5/5; persistent 14 files; recovery 7 files; all digests exact | PASS | Opaque CSV contents were never opened, parsed, copied, normalized, staged, or used. |
| scheduled-task and refresh-process state | Get-ScheduledTask plus process readback | disabled; enabled false; zero refresh workers | Disabled; enabled false; last result 0; zero refresh workers | PASS | Verifier command process excluded from worker matching. |
| whitespace and repository cleanliness | git diff --check and git status --short | no whitespace errors; clean review worktree | no whitespace errors; clean review worktree | PASS | Generated packet uses stable UTF-8 LF bytes and a non-self-referential manifest. |
| dual-lens viewport acceptance | VIEWPORT_AND_ACCESSIBILITY_RESULTS.csv | not applicable when production integration is prohibited | 24 of 24 rows NOT_APPLICABLE_PRODUCTION_UI_NOT_INTEGRATED | PASS_EXPECTED_NOT_APPLICABLE | Existing surface accessibility and route tests pass; no incomplete dual-lens UI was installed. |
| provider, security-scan, and production-mutation boundaries | source and changed-path inspection | none | zero provider calls; no new security scan; zero production app or data mutations | PASS | Outcome V3 remains display-only and Finished V1 remains canonical. |
| bounded correction cycle | independent review finding and one corrected re-review | at most one cycle | one cycle used; post-correction review fully green | PASS | Corrected only Outcome LF materialization and cross-runtime deterministic serialization. |

Required interpretation:

- Hermetic must exit 0.
- LocalData must return `BLOCKED_MISSING_LOCAL_TEST_PACK` with exit 4.
- No provider is called and no new security scan is run.
- No new skip/xfail/xpass is allowed.
- The scheduled task must remain disabled.
- Production integration is absent, so dual-lens viewport controls are
  correctly `NOT_APPLICABLE_PRODUCTION_UI_NOT_INTEGRATED`, not falsely passed.
