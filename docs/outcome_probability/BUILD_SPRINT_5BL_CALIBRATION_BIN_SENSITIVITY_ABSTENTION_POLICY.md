# Sprint 5BL Calibration Bin Sensitivity and Abstention Policy

## 1. Executive verdict

Verdict: `CALIBRATION_BIN_SENSITIVITY_INTERNAL_ONLY_ABSTENTION_REQUIRED`

Sprint 5BL studied whether calibration instability from Sprint 5BI can be managed by changing bin counts and applying abstention rules. The answer is: partially for internal diagnostics, not for release.

Bin sensitivity confirms the 5BI/5BK finding. Fewer bins reduce some instability, but sparse positives and large observed-vs-predicted gaps persist. Under strict support and 2-bin stability criteria, only `RB T36` survives both validation and test as an internal diagnostic candidate. No head survives strict criteria at 3, 4, 5, or 10 bins.

Release stance remains unchanged:

- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting remain blocked.
- Promoted artifacts remain blocked.

## 2. Evidence reviewed

Documents reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5BI_INTERNAL_HOLDOUT_CALIBRATION_PACKAGE.md`
- `docs/outcome_probability/BUILD_SPRINT_5BJ_5BI_HOLDOUT_CALIBRATION_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5BK_CALIBRATION_INSTABILITY_ROOT_CAUSE.md`

Local-only exports reviewed, not modified and not committed:

- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/holdout_predictions_internal_only.csv`
- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/calibration_bins.csv`
- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/calibration_bin_stability.csv`
- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/sparse_head_audit.csv`

No new local-only exports were created for 5BL.

## 3. Candidate abstention policy tested

5BL tested a strict internal diagnostic policy:

1. Minimum historical positives per head: `>=100`.
2. Minimum validation positives per head: `>=20`.
3. Minimum test positives per head: `>=20`.
4. Minimum holdout rows per bin: `>=20`.
5. Minimum positive labels per bin: `>=3`.
6. Minimum negative labels per bin: `>=3`.
7. Maximum absolute observed-vs-predicted gap per bin: `<=0.15`.
8. Must pass both validation and test on the same bin-count setting.

This policy is not a release policy. It is a research screen for whether a head is stable enough to keep studying without showing probabilities or bands.

## 4. Bin sensitivity findings

Read-only binning simulations were run from the 5BI constrained/PAVA holdout predictions.

| Bin count | Stable constrained split-heads | Total split-heads | Main failures |
|---:|---:|---:|---|
| 2 | 4 | 20 | sparse events, large gaps |
| 3 | 2 | 20 | sparse events, large gaps |
| 4 | 0 | 20 | sparse events, large gaps |
| 5 | 0 | 20 | sparse events, low row count, large gaps |
| 10 | 0 | 20 | low row count |

Interpretation:

- 10 bins is unusable for the current universe; every constrained split-head fails low row-count checks.
- 5 bins is too aggressive for current holdout sample sizes.
- 4 bins still fails every split-head.
- 3 bins leaves only two stable split-heads, neither forming a validation+test pair for the same head.
- 2 bins is the least-bad diagnostic view, but even then only one head survives both splits.

## 5. Stable split-heads by bin count

Stable constrained/PAVA split-heads:

| Bin count | Stable split-heads |
|---:|---|
| 2 | Test RB T24; Test RB T36; Validation RB T36; Validation RB T48 |
| 3 | Test RB T36; Validation RB T48 |
| 4 | none |
| 5 | none |
| 10 | none |

Heads stable on both validation and test:

| Bin count | Heads stable on both splits |
|---:|---|
| 2 | RB T36 |
| 3 | none |
| 4 | none |
| 5 | none |
| 10 | none |

## 6. Minimum positive-label threshold findings

Support screen:

| Head | Historical events | Validation events | Test events | Support result |
|---|---:|---:|---:|---|
| RB T6 | 28 | 6 | 6 | fail |
| RB T12 | 54 | 10 | 11 | fail |
| RB T24 | 103 | 22 | 22 | pass |
| RB T36 | 159 | 33 | 34 | pass |
| RB T48 | 204 | 42 | 44 | pass |
| WR T6 | 26 | 5 | 5 | fail |
| WR T12 | 54 | 11 | 9 | fail |
| WR T24 | 106 | 21 | 21 | pass |
| WR T36 | 155 | 30 | 31 | pass |
| WR T48 | 209 | 40 | 42 | pass |

T6 and T12 fail the minimum positive-label screen. They should be abstained from any release path unless additional legal historical data materially changes support.

## 7. Strict abstention result by head

Strict criteria require both support and bin stability.

| Head | Support screen | 2-bin validation/test stability | Strict result |
|---|---|---|---|
| RB T6 | fail | fail | abstain |
| RB T12 | fail | fail | abstain |
| RB T24 | pass | fail validation | abstain |
| RB T36 | pass | pass | internal diagnostic candidate only |
| RB T48 | pass | fail test large-gap check | abstain |
| WR T6 | fail | fail | abstain |
| WR T12 | fail | fail | abstain |
| WR T24 | pass | fail sparse-bin checks | abstain |
| WR T36 | pass | fail sparse/gap checks | abstain |
| WR T48 | pass | fail sparse/gap checks | abstain |

Only `RB T36` survives the strict 2-bin diagnostic screen. It does not survive any stricter bin-count setting, so it is not release-eligible.

## 8. Non-viable head findings

Permanently non-viable for release under the current 2020-2024 universe:

- RB T6
- WR T6

Reason:

- Too few total historical positives.
- Too few validation/test positives.
- Bin-level positive counts remain sparse even with 2 bins.

Non-viable for exact probabilities under the current universe:

- RB T12
- WR T12
- RB T24
- RB T48
- WR T24
- WR T36
- WR T48

Reason:

- They either fail the positive-label threshold, fail validation/test bin stability, or show large observed-vs-predicted gaps.

Internal diagnostic candidate only:

- RB T36

Reason:

- It passes 2-bin validation/test stability and support thresholds, but fails stricter bin counts and therefore cannot support release.

## 9. Can abstention support status-only diagnostics?

Yes, abstention can support status-only internal diagnostics.

Allowed internal status-only language could be limited to non-numeric research states such as:

- `insufficient_evidence`
- `calibration_unstable`
- `internal_diagnostic_candidate`
- `not_release_ready`

Those statuses must not include probabilities, bands, hidden sort keys, ranking use, player-facing display, or app-readable output. Status-only diagnostics should remain documentation/local-export research until HQ separately approves a display gate.

## 10. Coarse-band and exact-probability implications

Exact probabilities remain blocked after abstention.

Reason:

- Only one head survives the least-strict 2-bin screen.
- No head survives 3+ bins on both validation and test.
- Sparse and large-gap failures remain widespread.

Coarse bands remain blocked after abstention.

Reason:

- Coarse bands would still be derived from unstable head behavior.
- A single RB T36 diagnostic candidate is not enough to justify a band framework.
- WR upper thresholds show large gap failures even with fewer bins.

## 11. Safe policy recommendation

Recommended internal-only abstention policy for future research:

| Policy item | Recommended threshold |
|---|---|
| Historical positives per head | at least 100 |
| Validation positives per head | at least 20 |
| Test positives per head | at least 20 |
| Minimum rows per bin | at least 20 |
| Minimum positive labels per bin | at least 3 |
| Minimum negative labels per bin | at least 3 |
| Maximum absolute calibration gap | 0.15 |
| Required split agreement | validation and test must both pass |
| Minimum bin-count evidence | 2-bin pass for internal diagnostics; 3+ bin pass required before any future release discussion |

This policy should be treated as a floor, not a release approval.

## 12. Recommended next safe sprint

Recommended next sprint: `Sprint 5BM - Threshold Grouping and Pooled Calibration Research`

Goal:

- Test whether grouped thresholds or pooled RB/WR calibration can reduce sparse-bin failures without releasing probabilities or bands.
- Keep T6 permanently abstained under current evidence.
- Keep all outputs internal-only and not app-readable.

Alternative if HQ prefers data-first work:

- `Sprint 5BN - More Seasons / Larger Historical Universe Feasibility`

That would test whether additional legal seasons can be reconstructed before investing in pooled calibration.

## 13. Final gate label

Final gate label: `CALIBRATION_BIN_SENSITIVITY_INTERNAL_ONLY_ABSTENTION_REQUIRED`

Meaning:

- Bin-count sensitivity does not clear release gates.
- Strict abstention leaves only RB T36 as an internal diagnostic candidate.
- T6 heads are non-viable under current evidence.
- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting remain blocked.
- Promoted artifacts remain blocked.
