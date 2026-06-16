# Sprint 5BM Threshold Grouping and Pooled Calibration Research

## 1. Executive verdict

Verdict: `THRESHOLD_GROUPING_POOLED_CALIBRATION_INTERNAL_ONLY_CONTINUE`

Sprint 5BM researched whether nearby thresholds or RB/WR pooling can improve calibration stability enough to define a future internal diagnostic policy. Grouping helps, but it does not authorize release.

Best internal-only signals:

- RB-only broad grouping is the strongest candidate family.
- RB T36/T48 grouped calibration passes 2-bin and 3-bin internal diagnostics.
- RB T24/T36/T48 grouped calibration passes 2-bin and 4-bin internal diagnostics.
- RB+WR pooled T24 and pooled T36 each pass 2-bin internal diagnostics.
- WR-only grouped candidates remain unstable.

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
- `docs/outcome_probability/BUILD_SPRINT_5BL_CALIBRATION_BIN_SENSITIVITY_ABSTENTION_POLICY.md`

Local-only exports reviewed, not modified and not committed:

- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/holdout_predictions_internal_only.csv`
- `local_exports/outcome_probability/sprint_5bi_internal_holdout_calibration_package/sparse_head_audit.csv`

No new local-only exports were created for 5BM.

## 3. Grouping strategy tested

All analysis used constrained/PAVA holdout predictions from 5BI. This was a read-only diagnostic pass.

Candidate groups:

- `all_rb_wr_no_t6`: RB/WR T12/T24/T36/T48.
- `all_rb_wr_broad_t24_t36_t48`: RB/WR T24/T36/T48.
- `all_rb_wr_upper_t36_t48`: RB/WR T36/T48.
- `all_rb_wr_narrow_t6_t12`: RB/WR T6/T12.
- `rb_broad_t24_t36_t48`: RB T24/T36/T48.
- `wr_broad_t24_t36_t48`: WR T24/T36/T48.
- `rb_upper_t36_t48`: RB T36/T48.
- `wr_upper_t36_t48`: WR T36/T48.
- pooled same-threshold groups: RB+WR T6, T12, T24, T36, T48.

5BL strict criteria were reused:

- at least 20 rows per bin
- at least 3 positive labels per bin
- at least 3 negative labels per bin
- maximum observed-vs-predicted gap at or below 0.15
- validation and test both pass

## 4. Threshold grouping findings

Grouped constrained/PAVA results:

| Group | Validation rows/events | Test rows/events | Stable bin counts | Finding |
|---|---:|---:|---|---|
| RB/WR no T6 | 1040 / 209 | 1044 / 214 | 2-bin only | broad support, but fails 3+ bins |
| RB/WR T24/T36/T48 | 780 / 188 | 783 / 194 | 2-bin and 3-bin | strongest cross-position broad group |
| RB/WR T36/T48 | 520 / 145 | 522 / 151 | 2-bin only | broader thresholds help, but 3+ bins fail |
| RB/WR T6/T12 | 520 / 32 | 522 / 31 | none | narrow heads remain sparse |
| RB T24/T36/T48 | 318 / 97 | 294 / 100 | 2-bin and 4-bin | strongest RB broad group |
| RB T36/T48 | 212 / 75 | 196 / 78 | 2-bin and 3-bin | strongest upper-threshold group |
| WR T24/T36/T48 | 462 / 91 | 489 / 94 | none | sparse low bins persist |
| WR T36/T48 | 308 / 70 | 326 / 73 | none | validation sparse/gap failures persist |

Grouping thresholds helps most when:

- T6 is excluded.
- RB and WR are pooled at same thresholds, or RB is kept separate.
- T36/T48 are grouped for RB only.

Grouping does not help enough when:

- T6/T12 are included as a narrow group.
- WR is grouped alone.
- 5- or 10-bin evidence is required.

## 5. Same-threshold pooling findings

RB+WR same-threshold pooling:

| Pooled threshold | Validation rows/events | Test rows/events | 2-bin result |
|---|---:|---:|---|
| T6 | 260 / 11 | 261 / 11 | fail sparse events |
| T12 | 260 / 21 | 261 / 20 | fail sparse events |
| T24 | 260 / 43 | 261 / 43 | pass |
| T36 | 260 / 63 | 261 / 65 | pass |
| T48 | 260 / 82 | 261 / 86 | fail validation large gap |

Interpretation:

- T24 and T36 are the only same-threshold pooled candidates that pass the 2-bin internal diagnostic screen.
- T6 and T12 remain too sparse.
- T48 has enough events, but the validation gap remains too large.

## 6. RB vs WR pooling strategy

RB and WR should not be blindly pooled for all future work.

RB-only grouping looks materially stronger:

| Group | 2-bin result | 3-bin result | 4-bin result | Notes |
|---|---|---|---|---|
| RB no T6 | pass | not tested as release candidate | not tested as release candidate | stable under 2-bin diagnostic read |
| RB T24/T36/T48 | pass | validation pass/test large-gap fail | pass | stronger than individual heads |
| RB T36/T48 | pass | pass | test large-gap fail | strongest upper-threshold candidate |

WR-only grouping remains unstable:

| Group | 2-bin result | Main failure |
|---|---|---|
| WR no T6 | fail | sparse low bin |
| WR T24/T36/T48 | fail | sparse low bin |
| WR T36/T48 | fail validation | sparse low bin and large gap |

Recommendation:

- Keep RB and WR separate for grouped calibration research unless a same-threshold pooled audit is explicitly testing RB+WR T24 or RB+WR T36.
- Do not use WR-only grouped outputs for release or coarse bands.

## 7. Scarce-head exclusion

RB T6 and WR T6 should be excluded from grouped calibration candidates under the current 2020-2024 universe.

Reason:

- T6 remains sparse even when RB+WR are pooled.
- Pooled T6 has only 11 validation events and 11 test events.
- It fails the 2-bin screen due to sparse events.

T12 should also remain abstained from release research:

- Pooled T12 has 21 validation events and 20 test events, but still fails the 2-bin sparse-event check.
- T12 may be useful only as an internal support context row, not as a display or band input.

## 8. Broad-head viability

Broad heads are more viable when grouped, especially for RB.

Most promising internal-only candidates:

- RB T36/T48 grouped calibration.
- RB T24/T36/T48 grouped calibration.
- RB+WR pooled T24.
- RB+WR pooled T36.

These candidates are useful for future internal diagnostics because they reduce sparse-bin failures. They still do not support exact percentages or coarse bands.

## 9. Interpretability and semantic risk

Grouping thresholds creates interpretability risk.

Individual thresholds have clear semantics:

- T24 means top-24-or-better.
- T36 means top-36-or-better.
- T48 means top-48-or-better.

Grouped calibration blends adjacent semantics. A grouped calibration result is no longer a clean player-facing probability for a specific threshold. It is a research diagnostic about a threshold family.

Risk:

- A grouped threshold family could be mistaken for a release-ready coarse band.
- Pooled RB/WR thresholds could hide position-specific calibration failures, especially WR upper-bin gaps.
- Grouped outputs could mislead if shown without the abstention and calibration warnings.

Therefore grouped/pooled outputs must remain internal-only and non-display.

## 10. Monotonicity impact

Pooled calibration research does not repair or worsen per-player monotonicity by itself because it is evaluated as aggregate calibration evidence after constrained/PAVA repair.

The 5BI constrained/PAVA holdout rows already satisfy per-player threshold monotonicity. Grouped calibration should be treated as an audit layer, not a replacement for per-player monotonic chain enforcement.

Future grouped research must preserve:

`P(T6) <= P(T12) <= P(T24) <= P(T36) <= P(T48)`

No grouped output should be used to create new per-player probabilities unless a separate monotonicity and calibration gate passes.

## 11. Strict abstention survival

Candidates surviving strict 5BL-style internal diagnostics:

| Candidate | Survives | Scope |
|---|---|---|
| RB T36 individual | yes, 2-bin only | internal diagnostic candidate |
| RB T36/T48 grouped | yes, 2-bin and 3-bin | strongest grouped internal candidate |
| RB T24/T36/T48 grouped | yes, 2-bin and 4-bin | strong but non-monotonic bin-count pattern needs audit |
| RB+WR pooled T24 | yes, 2-bin only | cross-position threshold diagnostic |
| RB+WR pooled T36 | yes, 2-bin only | cross-position threshold diagnostic |
| RB/WR T24/T36/T48 grouped | yes, 2-bin and 3-bin | broad diagnostic, interpretability risk |

Non-survivors:

- RB T6
- WR T6
- RB/WR T6 pooled
- T12 individual and pooled
- WR-only broad groups
- RB+WR pooled T48

## 12. Coarse-band implications

Grouped/pooled outputs are suitable only for internal diagnostics right now.

They could become future coarse-band candidates only after additional gates:

- grouped calibration rerun in a formal local-only package
- adversarial audit of threshold semantics
- proof that grouped outputs cannot be mistaken for exact probabilities
- explicit abstention policy attached to every group
- no app-readable path
- no ranking/sorting use
- HQ release/display approval

No coarse band is approved by Sprint 5BM.

## 13. Recommended next safe sprint

Recommended next sprint: `Sprint 5BN - Grouped Calibration Local Package and Adversarial Audit Plan`

Scope:

- Build a local-only package for grouped candidates only.
- Include RB T36/T48, RB T24/T36/T48, RB+WR T24, RB+WR T36, and RB/WR T24/T36/T48.
- Exclude T6.
- Keep T12 review-only or context-only.
- Report only aggregate diagnostics and abstention flags.
- Do not create app-readable outputs, bands, rankings, sorting, or promoted artifacts.

Alternative if HQ wants data-first work:

- `Sprint 5BN - More Seasons / Larger Historical Universe Feasibility`

Either path remains internal-only.

## 14. Final gate label

Final gate label: `THRESHOLD_GROUPING_POOLED_CALIBRATION_INTERNAL_ONLY_CONTINUE`

Meaning:

- Threshold grouping improves diagnostic stability for selected broad groups.
- RB grouped candidates are stronger than WR grouped candidates.
- T6 must remain excluded.
- T12 remains abstained from release research.
- Grouped outputs are not player-facing probabilities.
- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring remains blocked.
- Rankings/sorting remain blocked.
- Promoted artifacts remain blocked.
