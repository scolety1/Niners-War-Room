# Sprint 5BQ: Outcome Internal Status Policy and Larger-Universe Feasibility

Outcome lane: veteran outcome probability column path only

Verdict: `INTERNAL_STATUS_POLICY_AND_LARGER_UNIVERSE_FEASIBILITY_ONLY`

Sprint type: `NOT_A_DISPLAY_SPRINT_NOT_A_RELEASE_SPRINT`

## 1. Scope

Sprint 5BQ defines a research-governance status policy and evaluates whether a larger historical universe is the safest path toward trustworthy future percentages. It does not create app-readable probabilities, app-readable bands, app-readable status tables, app wiring, rankings/sorting hooks, hidden sort keys, model release artifacts, or rookie-framework changes.

Evidence reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5BH_CONSTRAINED_PROTOTYPE_CALIBRATION_REVALIDATION.md`
- `docs/outcome_probability/BUILD_SPRINT_5BI_INTERNAL_HOLDOUT_CALIBRATION_PACKAGE.md`
- `docs/outcome_probability/BUILD_SPRINT_5BJ_5BI_HOLDOUT_CALIBRATION_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5BK_CALIBRATION_INSTABILITY_ROOT_CAUSE.md`
- `docs/outcome_probability/BUILD_SPRINT_5BL_CALIBRATION_BIN_SENSITIVITY_ABSTENTION_POLICY.md`
- `docs/outcome_probability/BUILD_SPRINT_5BM_THRESHOLD_GROUPING_POOLED_CALIBRATION_RESEARCH.md`
- `docs/outcome_probability/BUILD_SPRINT_5BN_GROUPED_CALIBRATION_LOCAL_PACKAGE_AUDIT_PLAN.md`
- `docs/outcome_probability/BUILD_SPRINT_5BO_GROUPED_CALIBRATION_PACKAGE_ADVERSARIAL_AUDIT.md`
- `docs/outcome_probability/BUILD_SPRINT_5BP_OUTCOME_COLUMN_RELEASE_PATH_DECISION_MATRIX.md`

## 2. Executive Decision

The Outcome Column lane can continue internal research, but it cannot release numbers.

Current decision:

| Area | Decision |
| --- | --- |
| Existing status-only Outcome Model Status copy | safe to remain unchanged |
| New app-readable status table | blocked |
| Exact percentages | blocked |
| Coarse bands | blocked |
| App wiring for real probabilities/bands | blocked |
| Rankings/sorting usage | blocked |
| Hidden sort keys | blocked |
| Promoted artifacts | blocked |

The next safe path is a data inventory/feasibility audit for pre-2020 historical expansion, paired with continued internal-only status governance.

## 3. Internal Status Policy

The following statuses are research governance labels. They are not player-facing probabilities, bands, rankings, sorting keys, or release claims.

| Status | Meaning | Allowed use | Display/release stance |
| --- | --- | --- | --- |
| `non_viable_current_evidence` | Current evidence is too sparse or unstable to support release research for the head/group. | Docs and local research review only. | No percentages, bands, app-readable output, sorting, or promotion. |
| `calibration_blocked` | Monotonicity or mechanics may be acceptable, but calibration stability fails. | Docs and internal audit notes. | No numeric display or release artifact. |
| `internal_diagnostic_candidate_only` | Candidate passes a limited internal diagnostic screen but not release gates. | Internal research prioritization. | No player-facing output and no app-readable table. |
| `needs_larger_universe` | Current 2020-2024 support appears insufficient; more legal history may be required. | Planning for data inventory and feasibility work. | No release implication. |
| `release_blocked` | Candidate is explicitly blocked from release/display/promotion. | Default gate label for all current outcome probability work. | Blocks exact percentages, bands, app wiring, sorting, hidden sort keys, and promoted artifacts. |

Policy rules:

1. Statuses must not contain exact percentages.
2. Statuses must not imply a coarse probability band.
3. Statuses must not be used as ranking or sorting signals.
4. Statuses must not be placed in a new app-readable output table in this sprint.
5. Statuses must not score rookies through veteran heads.
6. Statuses must not override calibration, population, forbidden-feature, monotonicity, or artifact-quarantine gates.
7. Statuses may guide internal research sequencing only.

## 4. Existing App Copy Decision

Existing status-only Outcome Model Status copy remains safe to keep unchanged.

This means the existing app-facing status language can continue if it does not expose:

- exact probabilities
- coarse bands
- app-readable outcome columns
- real probability/band wiring
- rankings/sorting usage
- hidden sort keys
- promoted artifacts

No new app-readable status table should be created in Sprint 5BQ. No app code should be touched.

## 5. Current Evidence Classification

| Candidate | Current status | Evidence basis |
| --- | --- | --- |
| RB T6 | `non_viable_current_evidence` | Sparse historical and holdout positives; pooling did not resolve T6 scarcity. |
| WR T6 | `non_viable_current_evidence` | Sparse historical and holdout positives; pooling did not resolve T6 scarcity. |
| RB T12 | `needs_larger_universe` and `release_blocked` | Fails support/bin-stability screens under current universe. |
| WR T12 | `needs_larger_universe` and `release_blocked` | Fails support/bin-stability screens under current universe. |
| RB T24 | `calibration_blocked` | Support exists, but validation stability fails. |
| RB T36 | `internal_diagnostic_candidate_only` | Only individual head passing strict 2-bin validation/test screen; not release-grade. |
| RB T48 | `calibration_blocked` | Support exists, but test large-gap check fails. |
| WR T24 | `calibration_blocked` | Sparse-bin/gap checks fail. |
| WR T36 | `calibration_blocked` | Sparse-bin/gap checks fail. |
| WR T48 | `calibration_blocked` | Sparse-bin/gap checks fail. |
| RB T36/T48 grouped | `internal_diagnostic_candidate_only` | Grouped diagnostic pass with threshold-semantics risk. |
| RB T24/T36/T48 grouped | `internal_diagnostic_candidate_only` | Grouped diagnostic pass with broader threshold-semantics risk. |
| RB+WR pooled T24 | `internal_diagnostic_candidate_only` | Pooled diagnostic pass but can hide position-specific calibration differences. |
| RB+WR pooled T36 | `internal_diagnostic_candidate_only` | Pooled diagnostic pass but can hide position-specific calibration differences. |
| RB/WR T24/T36/T48 grouped | `internal_diagnostic_candidate_only` | Broad diagnostic pass with highest interpretability risk. |

All rows remain `release_blocked` for app display, exact percentages, coarse bands, rankings/sorting, hidden sort keys, and promotion.

## 6. Larger-Universe Feasibility Read

The current 2020-2024 historical universe appears too small for trustworthy player-facing percentages across the RB/WR threshold grid.

Evidence:

- 5BI found every RB/WR head unstable on validation and test for raw, clamped, and constrained methods.
- 5BK identified sparse positives, thin per-bin holdout samples, and large observed-vs-predicted gaps as root causes.
- 5BL found only RB T36 survives strict 2-bin internal criteria, and no head survives 3+ bins on both validation and test.
- 5BM through 5BO showed grouping can improve internal diagnostics, but grouped semantics are not clean player-facing probabilities.

A larger universe would likely need:

| Need | Why it matters |
| --- | --- |
| More historical seasons | Increases total player-years and rare positive outcomes. |
| More RB/WR player-years | Reduces per-head and per-bin sampling noise. |
| More positives per threshold | Especially important for T6/T12 and low-probability bins. |
| More holdout examples | Enables validation/test checks that are less dominated by a few events. |
| Consistent legal preseason features | Prevents feature drift and leakage while expanding history. |
| Reconstructable point-in-time labels | Keeps same-season outcomes as labels only, not preseason features. |

The feasibility question is not just whether older seasons exist. The question is whether older seasons can be reconstructed with the same legal, point-in-time feature policy.

## 7. Risks Of Expanding Historical Data

Pre-2020 expansion is promising but risky. The next sprint should inventory these risks before generating any new model or display artifact.

| Risk | Why it matters | Required audit |
| --- | --- | --- |
| Rule/scoring drift | League rules, fantasy scoring, and stat conventions may shift outcome meaning over time. | Document scoring comparability by season. |
| Player usage era drift | RB/WR workloads and passing environments may differ materially across eras. | Check whether older data changes calibration or creates era bias. |
| Feature availability drift | Older seasons may lack the same legal preseason feature set used in 5BI. | Inventory feature coverage before modeling. |
| Identity/team mapping issues | Older player IDs, team changes, and name collisions can corrupt labels/features. | Build a player/team mapping QA checklist. |
| Leakage risk | Older data reconstruction can accidentally use final-season stats as preseason features. | Re-run forbidden-feature and same-season leakage scans. |
| Label-definition drift | Top-N outcome labels must mean the same thing across seasons. | Reconfirm label construction and tie handling. |
| Survivorship bias | Missing fringe players can inflate calibration confidence. | Audit coverage for low-priority, waived, blocked, and replacement-level rows. |
| Source contamination | ADP, rankings, projections, market, trade values, and RotoWire-derived content remain forbidden. | Re-run source and feature provenance scans. |

## 8. Release Path Implications

Exact percentages eligible now: `no`.

Coarse bands eligible now: `no`.

App wiring eligible now: `no`, except existing status-only Outcome Model Status copy can remain unchanged.

Rankings/sorting usage eligible now: `no`.

Promoted artifacts eligible now: `no`.

Before percentages can be reconsidered, the lane would need:

1. Larger-universe feasibility pass for legally reconstructable historical seasons.
2. Stable feature provenance across added seasons.
3. No forbidden feature/source contamination.
4. No same-season final stats used as preseason features.
5. Population policy pass for veterans, rookies, kickers, blocked, waived, and unscored rows.
6. Validation/test calibration stability under a predeclared binning policy.
7. Enough positives per head and per bin, especially for T6/T12.
8. Monotonicity pass for top-N-or-better semantics.
9. Honest Brier/log-loss reporting without overclaiming small deltas.
10. Artifact quarantine pass.
11. Separate adversarial audit.
12. Separate HQ release/display approval.

## 9. Recommended Next Safe Sprint

Recommended next safe sprint:

`Sprint 5BR - Pre-2020 Historical Universe Inventory And Feasibility Audit`

Scope:

- Docs and inventory only unless HQ explicitly authorizes local-only export generation.
- Identify candidate pre-2020 seasons that can be legally reconstructed.
- Inventory required preseason features by season.
- Check player identity, team mapping, scoring, and label comparability risks.
- Define go/no-go criteria for expanding the 5BI-style holdout package.
- Keep exact percentages, coarse bands, app wiring, rankings/sorting, hidden sort keys, and promoted artifacts blocked.

Do not proceed to release, display, app wiring, ranking/sorting, or promoted artifacts.

## 10. Final Gate Label

Final gate label:

`OUTCOME_INTERNAL_STATUS_POLICY_DEFINED_LARGER_UNIVERSE_FEASIBILITY_NEXT_RELEASE_BLOCKED`

Meaning:

- Internal status labels are governance labels only.
- Existing status-only Outcome Model Status copy remains safe unchanged.
- No new app-readable status table is approved.
- The current 2020-2024 universe appears too small for trustworthy player-facing percentages.
- A pre-2020 data inventory/feasibility audit is the next safe research step.
- Exact percentages remain blocked.
- Coarse bands remain blocked.
- App wiring for real probabilities/bands remains blocked.
- Rankings/sorting and hidden sort keys remain blocked.
- Promoted artifacts remain blocked.
