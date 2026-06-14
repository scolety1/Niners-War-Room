# Sprint 5BP: Outcome Column Release Path Decision Matrix

Outcome lane: veteran outcome probability column path only

Verdict: `NO_RELEASE_PATH_APPROVED_CONTINUE_INTERNAL_RESEARCH`

Decision checkpoint stance: `NOT_A_RELEASE_SPRINT`

## 1. Scope

Sprint 5BP turns the Outcome Column evidence from Sprints 5BH through 5BO into a release-path decision matrix. This document does not create, promote, or approve probabilities, coarse bands, app display, app loaders, rankings, sorting, or model artifacts.

Evidence reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5BH_CONSTRAINED_PROTOTYPE_CALIBRATION_REVALIDATION.md`
- `docs/outcome_probability/BUILD_SPRINT_5BI_INTERNAL_HOLDOUT_CALIBRATION_PACKAGE.md`
- `docs/outcome_probability/BUILD_SPRINT_5BJ_5BI_HOLDOUT_CALIBRATION_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5BK_CALIBRATION_INSTABILITY_ROOT_CAUSE.md`
- `docs/outcome_probability/BUILD_SPRINT_5BL_CALIBRATION_BIN_SENSITIVITY_ABSTENTION_POLICY.md`
- `docs/outcome_probability/BUILD_SPRINT_5BM_THRESHOLD_GROUPING_POOLED_CALIBRATION_RESEARCH.md`
- `docs/outcome_probability/BUILD_SPRINT_5BN_GROUPED_CALIBRATION_LOCAL_PACKAGE_AUDIT_PLAN.md`
- `docs/outcome_probability/BUILD_SPRINT_5BO_GROUPED_CALIBRATION_PACKAGE_ADVERSARIAL_AUDIT.md`

Local-only exports under `local_exports/outcome_probability/` were used as evidence only where prior docs cite them. They remain uncommitted and not app-readable.

## 2. Executive Decision

No Outcome Column release path is approved today.

| Decision area | Current decision | Reason |
| --- | --- | --- |
| Exact percentages | blocked | All individual RB/WR heads fail release-grade calibration evidence. |
| Coarse bands | blocked | Grouped diagnostics reduce instability but introduce semantic risk and are not display-approved. |
| App display | blocked | No app-readable table, band table, loader, player card, or release service is approved. |
| Rankings/sorting | blocked | Outcome probabilities and grouped diagnostics are not allowed as visible or hidden sort keys. |
| Promoted artifacts | blocked | No model, calibration layer, probability table, or grouped package may be promoted. |
| Rookie scoring through veteran heads | blocked | Rookies remain excluded from veteran outcome heads. |

Current safe app display stance: existing status-only Outcome Model Status copy remains safe.

All numeric outcome columns remain blocked. This includes exact percentages, coarse bands, app-readable outcome columns, app wiring for real probabilities/bands, rankings/sorting usage, hidden sort keys, and promoted artifacts.

## 3. Individual Head Decision Matrix

| Head | Evidence status | Current decision | Display eligibility |
| --- | --- | --- | --- |
| RB T6 | sparse historical and holdout positives | clearly non-viable under current universe | none |
| RB T12 | fails positive-label support and bin stability | non-viable for current release path | none |
| RB T24 | passes support, fails validation stability | internal research only, abstain for display | none |
| RB T36 | only individual head passing strict 2-bin validation/test screen | internal diagnostic only | none |
| RB T48 | passes support, fails test large-gap check | internal research only, abstain for display | none |
| WR T6 | sparse historical and holdout positives | clearly non-viable under current universe | none |
| WR T12 | fails positive-label support and bin stability | non-viable for current release path | none |
| WR T24 | passes support, fails sparse-bin/gap checks | internal research only, abstain for display | none |
| WR T36 | passes support, fails sparse-bin/gap checks | internal research only, abstain for display | none |
| WR T48 | passes support, fails sparse-bin/gap checks | internal research only, abstain for display | none |

Conclusion: no individual RB/WR head is eligible for exact percentages, coarse bands, app display, ranking, sorting, or promotion.

## 4. Clearly Non-Viable Heads

Clearly non-viable under the current 2020-2024 evidence:

- RB T6
- WR T6

Reason:

- Very sparse historical positives.
- Only 5-6 holdout positives per validation/test split.
- Sparse-bin failures persist even under reduced bin counts and pooling attempts.

Non-viable for current release/display:

- RB T12
- WR T12
- RB T24
- RB T36
- RB T48
- WR T24
- WR T36
- WR T48

Reason:

- T12 heads fail support and bin-stability screens.
- RB T24/RB T48 and WR T24/T36/T48 fail validation/test bin stability or large-gap checks.
- RB T36 is the best individual diagnostic candidate, but only under a 2-bin internal screen, which is insufficient for display.

## 5. Internal Diagnostic-Only Candidates

Individual head:

| Candidate | Diagnostic status | Release reason blocked |
| --- | --- | --- |
| RB T36 | passes strict 2-bin validation/test screen | fails stricter bin-count evidence and has no release-grade calibration policy |

Grouped/pooled candidates from 5BM-5BO:

| Candidate | Diagnostic status | Release reason blocked |
| --- | --- | --- |
| RB T36/T48 grouped | internal grouped diagnostic candidate | blends threshold semantics |
| RB T24/T36/T48 grouped | internal grouped diagnostic candidate | blends broader RB threshold semantics |
| RB+WR pooled T24 | internal pooled diagnostic candidate | can hide position-specific calibration differences |
| RB+WR pooled T36 | internal pooled diagnostic candidate | can hide position-specific calibration differences |
| RB/WR T24/T36/T48 grouped | internal broad diagnostic candidate | highest semantic risk from pooling positions and thresholds |

These candidates are suitable only for internal policy research and adversarial review. They are not player-facing probability, band, ranking, sorting, or display candidates.

## 6. Grouped And Pooled Research-Only Matrix

| Group | 5BN/5BO result | Current release-path decision |
| --- | --- | --- |
| RB T36/T48 grouped | passes internal 2-bin diagnostic with validation/test evidence | research-only, no display |
| RB T24/T36/T48 grouped | passes internal 2-bin diagnostic with validation/test evidence | research-only, no display |
| RB+WR pooled T24 | passes internal 2-bin diagnostic with validation/test evidence | research-only, no display |
| RB+WR pooled T36 | passes internal 2-bin diagnostic with validation/test evidence | research-only, no display |
| RB/WR T24/T36/T48 grouped | passes internal 2-bin diagnostic but has highest semantic risk | research-only, no display |
| RB T6, WR T6, pooled T6 | explicitly excluded | blocked |
| T12 individual/pooled release research | explicitly excluded/context-only | blocked |
| WR-only broad groups | explicitly excluded as unstable | blocked |
| Pooled T48 | explicitly excluded for validation large-gap failure | blocked |

Grouped and pooled outputs may inform future internal diagnostics, but they are not eligible for exact percentages or coarse bands today.

## 7. Exact Percentage Decision

Decision: `BLOCKED`

No candidate is eligible for exact percentages now.

Reasons:

- 5BI found all 10 RB/WR heads unstable on validation and test for every method.
- 5BK found the 2020-2024 historical universe too small for player-facing exact probabilities across the RB/WR threshold grid.
- 5BL found only RB T36 survives strict 2-bin internal criteria, and no head survives stricter bin counts.
- 5BM-5BO grouped diagnostics improve aggregate stability but weaken individual threshold semantics.

## 8. Coarse-Band Decision

Decision: `BLOCKED`

No candidate is eligible for coarse bands now.

Reasons:

- Coarse bands would still derive from unstable or semantically blended evidence.
- Grouped/pooled candidates are explicitly internal-only and not player-facing.
- A safe band system would require a separate display gate, semantic audit, calibration audit, abstention policy, and app-readiness review.

## 9. App Display Decision

Decision: `APP_DISPLAY_BLOCKED`

Current safe app display stance: existing status-only Outcome Model Status copy remains safe.

Do not display:

- exact percentages
- coarse bands
- app-readable outcome columns
- grouped diagnostic labels
- hidden rank/sort keys
- release-service outputs

Do not wire:

- real probabilities or bands into the app
- rankings/sorting usage
- hidden sort keys
- promoted artifacts

The only currently safe app-facing copy is the existing status-only Outcome Model Status copy. All numeric outcome probability release paths remain blocked.

## 10. Gates Required Before Any Future App Display

Before any future display discussion, a separate HQ-approved sprint would need all of the following:

1. A formal display proposal specifying exact UI language and scope.
2. A release artifact design that remains separate from research-only local exports.
3. Calibration evidence that passes validation and test under a predeclared policy.
4. Abstention rules for sparse and unstable heads.
5. Semantic proof that grouped/pooled outputs cannot be confused with individual probabilities.
6. Population policy audit confirming no rookies, kickers, blocked, waived, or unscored rows are incorrectly scored.
7. Forbidden feature scan reconfirming no ADP, rankings, projections, consensus, market, trade-value, RotoWire, prior draft-history, private-score, or same-season final-stat leakage.
8. Monotonicity audit preserving top-N-or-better semantics.
9. Artifact quarantine audit for the proposed release package.
10. App/import isolation audit before wiring.
11. Separate app display approval from HQ.
12. Separate rankings/sorting approval if that ever becomes a goal.

None of these gates are passed for app display today.

## 11. Rankings, Sorting, And Promotion Decision

Rankings/sorting decision: `BLOCKED`

Outcome probabilities and grouped diagnostics cannot be used for:

- visible rankings
- visible sorting
- hidden sort keys
- value pipelines
- draft recommendations
- player-card ordering

Promoted artifact decision: `BLOCKED`

Do not create or promote:

- app-readable probability tables
- app-readable coarse-band tables
- model packages
- calibration-layer artifacts
- release-service inputs
- player-card inputs
- ranking/sorting artifacts

## 12. Recommended Next Safe Sprint

Recommended next safe sprint:

`Sprint 5BQ - Outcome Column Internal Status Policy And Larger-Universe Feasibility`

Scope:

- Keep all work internal-only.
- Define a non-display internal status taxonomy for outcome research evidence.
- Decide whether the lane should continue grouped-diagnostic policy work or pivot to legally reconstructing additional historical seasons.
- Estimate whether more seasons could materially improve T6/T12 support and WR upper-threshold calibration.
- Preserve all release blocks unless a later HQ gate explicitly changes them.

Alternative safe sprint:

`Sprint 5BQ - Larger Historical Universe Feasibility`

This is the cleaner path if HQ wants to address the main root cause before refining grouped display semantics.

## 13. Final Decision Label

Final gate label:

`OUTCOME_COLUMN_RELEASE_PATH_DECISION_NO_DISPLAY_CONTINUE_INTERNAL_RESEARCH`

Meaning:

- RB T6 and WR T6 are clearly non-viable under current evidence.
- RB T36 individual is internal diagnostic only.
- Grouped/pooled candidates remain research-only.
- No exact percentages are eligible.
- No coarse bands are eligible.
- No app display is approved.
- Rankings/sorting remain blocked.
- Promoted artifacts remain blocked.
- The next safe path is internal policy work and/or larger-universe feasibility, not release.
