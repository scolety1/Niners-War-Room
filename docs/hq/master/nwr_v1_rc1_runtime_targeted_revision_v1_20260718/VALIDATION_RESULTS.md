# Validation results

| Gate | Result | Evidence |
|---|---|---|
| HQ/RC control state | PASS | HQ `7a3d01a...`, tree `b4ab40e...`; RC direct child `c380956...` |
| Route authority | PASS | `SUPPORTED_HIDDEN_ROUTE` |
| `/draft-cockpit-root` | PASS | exact URL and H1; no dialog at all widths |
| Full endpoint matrix | PASS | 180/180 |
| Candidate repeatability | PASS | 3 x 34/34 plus three second starts |
| Post-commit clean repeatability | NOT RUN | Hermetic fail-fast stopped release sequence |
| Focused route/UI | PASS | 76 passed |
| Accessibility/UI contract | PASS | browser settled controls plus 26 tracked UI tests |
| Data Health/passive reads | PASS | 107 passed |
| CSV/trust security | PASS | 300 passed |
| Security automation | PASS | 20/20 |
| Python compilation | PASS | exit 0 |
| Changed-file Ruff | PASS | zero findings |
| No-new-Ruff differential | PASS | RC 4,443; candidate 4,443 |
| Hermetic | FAIL | 13/13 bootstrap; 20/20 security; 2,626 passed, 1 failed; exit 1 |
| LocalData | PASS AS SEPARATE BLOCK | `BLOCKED_MISSING_LOCAL_TEST_PACK`, exit 4 |
| Skip/xfail/xpass | PASS | zero new skip, xfail, or xpass |
| Protected/frozen | PASS | only admitted route/lifecycle/tests/docs paths |
| Primary preservation | PASS TO DATE | zero hash drift; exact five paths |
| Independent review | BLOCKER | required manifest path conflicts with Data Health path-name heuristic |

Final verdict: `RED_NWR_V1_RC1_RUNTIME_REVISION_REGRESSION`.

The failed assertion was `test_guardrails_report_no_shared_or_runtime_files_tracked`. The tracked file is documentation, not draft runtime state, but changing the guard or its Data Health semantics is not authorized in this targeted lane.

Commit-policy disposition: the temporary clean candidate commit was soft-reset after the failed gate. The successor branch points to RC and the 24 candidate paths remain staged; successor commit: none.
