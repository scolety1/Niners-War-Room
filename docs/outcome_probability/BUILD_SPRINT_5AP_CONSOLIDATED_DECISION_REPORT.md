# Build Sprint 5AP Consolidated Decision Report

## Verdict

`STATUS_ONLY_KEEP_RECOMMENDED`

HQ should keep the current status-only player detail section, review it in the app, and avoid any probability release. The most reasonable next path is `keep_status_only_and_review_later`, with optional UX compaction research. Coarse label research can be prepared later, but no coarse label, band, exact probability, ranking, sorting, or decision automation should be released now.

## 1. Current State In Plain English

The app shows an **Outcome Model Status** section on the player detail card. It tells users that the outcome model is in development and that no probabilities are released. It is not a prediction surface. It is a status/readiness surface.

## 2. What Is Built And Safe

- Player detail card status-only display.
- Text-only columns: `Outcome`, `Status`, `Help`.
- Same-year targets show `In development`.
- `next_year_starter` shows `Blocked by release gate`.
- Multi-year/hazard targets show `Not applicable`.
- Kicker rows resolve to `Not applicable`.
- Numeric fields stay null in the service payload.
- Rankings and sorting are not changed by outcome status.

## 3. What Is Still Blocked

- Exact probabilities.
- Percentages.
- Calibrated probabilities.
- Player-facing probability numbers.
- Probability bands.
- Hidden sortable values.
- Rankings or sorting by model output.
- Draft recommendations.
- Decision automation.
- App-readable probability tables.
- Promoted or released model artifacts.
- Production deployment.
- `next_year_starter`, multi-year, and hazard target release.

## 4. Should The Current Status-Only Section Stay?

Yes. It should stay for HQ review because it is clear, status-only, nonnumeric, and covered by tests. It is somewhat dense, so a compact or collapsible presentation can be considered later if demo users find the player card too long.

Decision option: `keep_status_only_and_review_later`.

## 5. Should A Coarse Label Or Band Path Be Considered Later?

Only as research. Same-year targets have internal aggregate support, but calibration/display readiness is not release-ready. Future labels must be non-sortable, player-card-only, and separately approved. Exact percentages and probability bands remain blocked.

Decision option: `prepare_coarse_label_research_only`.

## 6. What Must Happen Before Real Probabilities?

- Final leakage audit.
- Validation evidence.
- Calibration stability evidence.
- Confidence gate.
- Documentation/model-card gate.
- App display gate.
- Operational safety gate.
- HQ approval.
- Monotonicity checks.
- Ranking/sort block.
- Explicit approval of display scope.

## 7. Recommended Next 3 Actions

1. Keep the status-only section visible for HQ app review.
2. Run a product review on whether the seven-row table should be compacted or made collapsible.
3. Prepare research-only criteria for future coarse non-sortable labels, without creating app labels or probabilities.

## 8. Explicit Do Not Do Next List

- Do not release probabilities.
- Do not show percentages.
- Do not add probability bands.
- Do not create hidden sortable values.
- Do not sort or rank by outcome model output.
- Do not add decision automation.
- Do not wire internal model outputs into app pages.
- Do not create app-readable probability tables.
- Do not promote or release model artifacts.
- Do not deploy.
- Do not push this audit bundle until HQ reviews it.

## Consolidated Findings

| Sprint | Verdict | Key finding |
| --- | --- | --- |
| 5AM | `KEEP_STATUS_ONLY_RECOMMENDED` | Same-year targets support internal research only; release remains blocked. |
| 5AN | `STATUS_ONLY_UX_PASS_WITH_RECOMMENDATIONS` | Current UX is safe and clear, but table density may justify compaction later. |
| 5AO | `DISPLAY_GATE_AUDIT_PASS` | Current status-only scope passes; future probability-like output requires all gates and HQ approval. |
| 5AP | `STATUS_ONLY_KEEP_RECOMMENDED` | Keep status-only, review UX, and do not release probabilities. |

## Local Exports

Local-only exports were written under:

`local_exports/outcome_probability/sprint_5ap_consolidated_decision_report/`

## Final Recommendation

Keep status-only. Review compact/collapsible UX. Do not release probabilities or probability-like app output.
