# Sprint 5BA Monotonicity Repair Research

## 1. Executive Verdict

Verdict: `MONOTONICITY_REPAIR_RESEARCH_CONTINUE_INTERNAL_ONLY`

Sprint 5BA reviewed the RB and WR threshold-chain monotonicity failures from Sprints 5AY and 5AZ. The violations are mostly small by magnitude, especially for WR, but they are still real structural contradictions for exact threshold probabilities.

Conservative outcome:

- Exact percentages remain blocked.
- Raw independent threshold heads remain blocked from app use.
- App display remains blocked.
- Rankings and sorting remain blocked.
- Coarse-band candidates remain internal research-only.
- Monotonic repair may continue as internal research only.
- No app-readable output, promoted model artifact, fake probability, or release artifact was created.

## 2. Inputs And Artifacts Reviewed

Reviewed committed sprint reports and local-only audit artifacts:

- `docs/outcome_probability/BUILD_SPRINT_5AY_PARTIAL_THRESHOLD_MODEL_EVALUATION.md`
- `docs/outcome_probability/BUILD_SPRINT_5AZ_THRESHOLD_EVALUATION_ADVERSARIAL_AUDIT.md`
- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/threshold_head_monotonicity_audit.csv`
- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/threshold_head_support.csv`
- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/threshold_release_decision_table.csv`
- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/forbidden_feature_scan.csv`
- `local_exports/outcome_probability/sprint_5ay_partial_threshold_model_evaluation/partial_2026_veteran_prediction_audit_internal_only.csv`
- `local_exports/outcome_probability/sprint_5az_threshold_evaluation_adversarial_audit/threshold_output_risk_audit.csv`

Baseline from 5AY/5AZ:

- QB monotonicity passed: 0 violations across 74 ready rows.
- TE monotonicity passed: 0 violations across 120 ready rows.
- RB monotonicity failed: 3 violating rows across 125 ready rows.
- WR monotonicity failed: 15 violating rows across 201 ready rows.
- Exact percentages remain blocked.
- App display remains blocked.
- Coarse-band candidates remain research-only.

The 5BA review used the internal-only 5AY player-head output to inventory violations. Those internal values remain unreleased, not app-readable, not sortable, and not player-facing.

## 3. RB Monotonicity Violation Inventory

Expected RB threshold chain:

`T6 <= T12 <= T24 <= T36 <= T48`

RB violations found:

| Player | Violating threshold pair | Internal unreleased gap | Severity read |
|---|---|---:|---|
| James Conner | `T36 > T48` | 0.012790 | Small but material enough to block exact display |
| Alvin Kamara | `T36 > T48` | 0.005405 | Small |
| Christian McCaffrey | `T36 > T48` | 0.004794 | Small |

RB summary:

- Violating adjacent pairs: 3
- Players with any RB violation: 3
- Pair involved: `same_year_rb_t36 > same_year_rb_t48`
- Gap range: 0.004794 to 0.012790
- Average gap: 0.007663
- No RB violation reached 0.020000.

Interpretation: RB failures are localized to the broadest threshold transition, T36 to T48. They do not look like catastrophic contradictions, but exact player-facing percentages cannot tolerate a case where a player is modeled as more likely to finish top 36 than top 48.

## 4. WR Monotonicity Violation Inventory

Expected WR threshold chain:

`T6 <= T12 <= T24 <= T36 <= T48`

WR violations found:

| Player | Violating threshold pair | Internal unreleased gap | Severity read |
|---|---|---:|---|
| David Moore | `T6 > T12` | 0.002894 | Small numerical contradiction |
| Laquon Treadwell | `T6 > T12` | 0.002489 | Small numerical contradiction |
| Laquon Treadwell | `T12 > T24` | 0.002235 | Small numerical contradiction |
| David Moore | `T12 > T24` | 0.002225 | Small numerical contradiction |
| Parris Campbell | `T6 > T12` | 0.002045 | Small numerical contradiction |
| Justin Watson | `T12 > T24` | 0.001932 | Small numerical contradiction |
| Justin Watson | `T6 > T12` | 0.001900 | Small numerical contradiction |
| Trent Sherfield | `T12 > T24` | 0.001873 | Small numerical contradiction |
| Trent Sherfield | `T6 > T12` | 0.001829 | Small numerical contradiction |
| Mecole Hardman | `T6 > T12` | 0.001797 | Small numerical contradiction |
| Parris Campbell | `T12 > T24` | 0.001685 | Small numerical contradiction |
| Mecole Hardman | `T12 > T24` | 0.001414 | Small numerical contradiction |
| Chris Blair | `T6 > T12` | 0.001359 | Small numerical contradiction |
| Chris Blair | `T12 > T24` | 0.001282 | Small numerical contradiction |
| Tim Jones | `T6 > T12` | 0.001009 | Small numerical contradiction |
| Tim Jones | `T12 > T24` | 0.000901 | Tiny numerical contradiction |
| Marquez Valdes-Scantling | `T12 > T24` | 0.000775 | Tiny numerical contradiction |
| Malik Cunningham | `T6 > T12` | 0.000644 | Tiny numerical contradiction |
| Malik Cunningham | `T12 > T24` | 0.000594 | Tiny numerical contradiction |
| Tom Kennedy | `T12 > T24` | 0.000514 | Tiny numerical contradiction |
| Mason Kinsey | `T6 > T12` | 0.000347 | Tiny numerical contradiction |
| Simi Fehoko | `T12 > T24` | 0.000338 | Tiny numerical contradiction |
| Simi Fehoko | `T6 > T12` | 0.000309 | Tiny numerical contradiction |
| Jason Brownlee | `T6 > T12` | 0.000293 | Tiny numerical contradiction |
| Jason Brownlee | `T12 > T24` | 0.000176 | Tiny numerical contradiction |
| Mason Kinsey | `T12 > T24` | 0.000089 | Tiny numerical contradiction |
| Michael Bandy | `T12 > T24` | 0.000014 | Tiny numerical contradiction |

WR summary:

- Violating adjacent pairs: 27
- Players with any WR violation: 15
- Pair counts:
  - `same_year_wr_t6 > same_year_wr_t12`: 12
  - `same_year_wr_t12 > same_year_wr_t24`: 15
- Gap range: 0.000014 to 0.002894
- Average gap: 0.001221
- All WR violations are below 0.005000.

Interpretation: WR failures appear to be mostly small numerical contradictions in low-probability fringe cases. They are not major magnitude conflicts, but they still break the expected threshold ordering and block exact player-facing probabilities.

## 5. Root-Cause Analysis

Most likely causes:

1. Independent one-vs-threshold heads

   Each threshold was modeled independently. Independent heads do not guarantee `T6 <= T12 <= T24 <= T36 <= T48` for a player, even if each head is individually reasonable.

2. Unstable calibration

   Sprint 5AY found `unstable_bins_present` for all evaluated heads. Unstable bins make small adjacent-threshold reversals more likely and prevent release claims.

3. Sparse top-threshold labels

   RB T6 and WR T6 were sparse:

   | Head | Historical rows | Events | Train events | Validation events | Test events |
   |---|---:|---:|---:|---:|---:|
   | `same_year_rb_t6` | 538 | 28 | 16 | 6 | 6 |
   | `same_year_wr_t6` | 817 | 26 | 16 | 5 | 5 |

   WR violations cluster around T6/T12 and T12/T24, where the rare-event boundary is most fragile.

4. Position and sample-size limitations

   RB and WR have wider player pools and more mid-depth threshold heads than QB and TE. The broad pools make small tail-ordering issues easier to produce.

5. Feature instability

   The reviewed artifacts do not prove feature instability as a direct cause. However, a compact prior-season feature set and partial 2026 coverage can amplify head-to-head variance when thresholds are modeled separately.

Less likely based on current evidence:

1. Identity or coverage gap as the immediate violation cause

   Violating rows came from ready feature snapshots. The five waived high-priority players remained unscored, blocked rows remained unscored, rookies remained excluded, and kickers remained not applicable.

2. Implementation or schema issue

   The 5AY forbidden-feature scan passed for all 14 evaluated legal feature names. 5AZ found no app/source references to the 5AY local outputs and no display/sort flags enabled. No evidence currently indicates a schema leak or implementation bug as the direct cause of the monotonicity failures.

## 6. Repair Options Evaluated

| Repair option | Leakage risk | Calibration risk | Interpretability | Exact percentage effect | Coarse-band research effect | Could ever be app-safe? | Required future validation |
|---|---|---|---|---|---|---|---|
| Post-hoc monotonic clamping across thresholds | Low if applied only to same-player threshold outputs and kept internal | Medium to high because it can distort independently estimated calibration | Moderate; easy to explain as enforcing threshold order | Not sufficient by itself; exact percentages remain blocked | Useful as internal benchmark | Possible only after calibration and holdout validation | Re-run validation/test metrics after clamping, bin calibration, player-chain audits, and release-gate audit |
| Ordinal/cumulative model approach | Low if trained only on legal features and direct labels | Medium; still needs calibration proof | Good; threshold ordering is part of the model design | Best long-term candidate for exact readiness, but not ready now | Strong candidate for internal research | Possible if support, calibration, and coverage gates pass | Train-only design, validation/test comparison, calibration audit, monotonicity audit, leakage audit |
| Shared-head or constrained-threshold approach | Low if feature whitelist is preserved | Medium; constraints reduce contradictions but do not prove calibration | Moderate to good | Candidate path, not release-ready | Good internal research path | Possible after adversarial validation | Compare against independent heads, test stability by position, confirm no degraded rare-head behavior |
| Isotonic-style monotonic correction | Low to medium; can leak if fit on validation/test/current rows | Medium to high if overfit or fit post hoc to current pool | Moderate; correction is understandable but can look mechanical | Not enough alone for exact readiness | Useful research comparator | Possible only if fit strictly on train/calibration folds and validated out of sample | Strict split discipline, no current-row fitting, calibration drift audit, release-gate review |
| Coarse-band-only output without exact probabilities | Low display precision risk if not app-readable | Medium; bad calibration can still produce misleading bands | Good for product language if gates pass | Does not unblock exact percentages | Can continue as quarantined research | Maybe later, but not from 5AY raw heads | Define bands, test stability, prove no hidden sortable values, run display-gate audit |
| Abstention or no display for violating positions/thresholds | Lowest | Lowest | High; simple and conservative | Keeps exact percentages blocked | Preserves research without release pressure | Already app-safe as status-only/no-display policy | Continue status-only gate until model and coverage improve |

## 7. Recommended Repair Path

Recommended path: `INTERNAL_RESEARCH_ONLY_ORDINAL_OR_CONSTRAINED_FIRST`

1. Keep current independent 5AY heads blocked from app, exact display, rankings, and sorting.
2. Use post-hoc clamping only as an internal benchmark, not as a release mechanism.
3. Prioritize a future ordinal/cumulative or shared constrained-threshold modeling sprint.
4. Preserve the legal feature whitelist and split discipline.
5. Add a formal monotonicity gate that must pass by player, position, and adjacent threshold pair.
6. Re-run calibration and holdout validation after any repair. Do not assume monotonicity repair preserves calibration.
7. Keep coarse-band candidates internal-only until a separate display-gate audit approves them.

Rationale: post-hoc clamping is the fastest way to remove contradictions, but it risks hiding calibration problems rather than solving them. A cumulative or constrained model better matches the structure of threshold labels and is more defensible for future release-gate review.

## 8. Release-Gate Implications

Current release gate remains closed:

- Exact probabilities: blocked.
- App-readable probability output: blocked.
- Player-facing probability display: blocked.
- Rankings-table probability display: blocked.
- Sorting by model output: blocked.
- Decision automation: blocked.
- Promoted model artifacts: blocked.

Explicit confirmations:

- No exact probabilities are released.
- No app-readable output was created.
- No rankings or sorting artifact was created.
- No waived or unscored players were scored.
- Rookies remain excluded from veteran heads.
- Kickers remain not applicable.
- Coarse-band candidates remain internal research-only.

## 9. Next Safe Sprint Recommendation

Recommended next sprint: `Sprint 5BB - Internal Monotonic Repair Prototype`

Safe scope for 5BB:

- Research-only.
- No app wiring.
- No app-readable probability tables.
- No promoted model artifact.
- No exact or player-facing probabilities.
- No rankings or sorting changes.
- No fake values for blocked, waived, rookie, or kicker rows.

5BB should compare:

- Original independent heads.
- Post-hoc clamped heads as a benchmark.
- Ordinal/cumulative threshold modeling.
- Shared-head or constrained-threshold modeling.
- Strict abstention policies for sparse or unstable heads.

Required gates before any later release discussion:

- Monotonicity pass across every adjacent threshold pair.
- Calibration stability by head and position.
- Holdout validation/test performance not degraded in misleading ways.
- Coverage policy for blocked and waived players.
- Leakage/schema audit.
- Display-gate audit proving no hidden sortable values or app-readable probability tables.
