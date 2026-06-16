# Sprint 5CQ: Human Review Packet, No App Output

Outcome lane: veteran outcome probability column path only

Verdict: `GREEN_HUMAN_REVIEW_PACKET_NO_APP_OUTPUT`

Sprint type: `REVIEW_PACKET_NO_PRODUCTION_NO_DISPLAY`

## 1. Scope

Sprint 5CQ prepares a human-review packet for the local-only shadow evaluation findings from 5CN through 5CP. This sprint did not create player-facing probabilities, current board outputs, app-readable files, exact display percentages, coarse display bands, app wiring, rankings/sorting, hidden sort keys, promoted model artifacts, rookie files, `data/` edits, `local_exports/` commits, push, or deploy.

No local-only export was required for 5CQ.

## 2. Review Inputs

5CQ reviewed:

- `docs/outcome_probability/BUILD_SPRINT_5CN_LOCAL_SHADOW_MODEL_PREFLIGHT_DESIGN_GATE.md`
- `docs/outcome_probability/BUILD_SPRINT_5CO_LOCAL_ONLY_AGGREGATE_SHADOW_MODEL_EVALUATION.md`
- `docs/outcome_probability/BUILD_SPRINT_5CP_BACKTEST_CALIBRATION_SANITY_AUDIT.md`
- local-only 5CO aggregate metrics under `local_exports/outcome_probability/sprint_5co_local_only_aggregate_shadow_model_evaluation/`

All reviewed outputs remain local-only and aggregate-only.

## 3. Head Tiers For Human Review

Viable heads for continued human review:

- `same_year_qb_t12`
- `same_year_qb_t18`
- `same_year_qb_t24`
- `same_year_rb_t12`
- `same_year_rb_t24`
- `same_year_wr_t12`
- `same_year_wr_t24`
- `same_year_wr_t36`
- `same_year_te_t12`
- `same_year_te_t18`
- `same_year_te_t24`

Weak heads requiring caution:

- `same_year_rb_t36`
- `same_year_rb_t48`
- `same_year_wr_t48`

Blocked/not evaluated heads:

- `same_year_qb_t6`
- `same_year_rb_t6`
- `same_year_wr_t6`
- `same_year_te_t3`
- `same_year_te_t6`

These tiers are internal review labels only. They are not app display labels, probability bands, ranking signals, hidden sort keys, or release claims.

## 4. Human Review Questions

For every viable head, the reviewer should answer:

1. Does the head have enough practical football meaning to justify continued local shadow work?
2. Does the rolling-holdout performance look stable enough across holdout seasons?
3. Are calibration-bin thinness and class imbalance acceptable for internal research only?
4. Does the source-safe feature set explain the result without relying on leakage or market information?
5. Would the head create misleading user expectations if later translated to display language?
6. What abstention conditions would be required before any player-facing proposal?

Additional questions for QB heads:

- Are prior passing volume and prior NWR rank driving plausible outcomes?
- Do backup/low-games rows create misleading signals?

Additional questions for RB heads:

- Are RB Top 36/48 too broad or too usage-sensitive for reliable display?
- Do low-games and committee usage rows need stricter abstention rules?

Additional questions for WR heads:

- Does WR Top 48 become too broad for user-facing semantics?
- Are deep-position thresholds still meaningful without target-share features?

Additional questions for TE heads:

- Are TE Top 18/24 too broad for useful display?
- Do sparse TE scoring patterns require stronger calibration gates?

## 5. Qualitative Sanity Checks

Required next-review sanity checks:

- Prior high production should generally support stronger outcome likelihood.
- Prior low production should not systematically receive strong model support without an explainable source-safe reason.
- Prior games played and games active should behave as availability signals, not as hidden status outputs.
- Prior NWR finish rank and prior NWR PPG must remain historical source-safe signals, not rankings/sorting outputs.
- Multi-position and position-transition cases, including the accepted Taysom Hill exclusion, must remain explicitly governed.
- Rookies must not be scored through veteran heads.

## 6. Risk Register

| Risk | Current status | Required mitigation before Phase 5 |
| --- | --- | --- |
| Leakage | No leak found in 5CO/5CP | Re-run forbidden feature scan in any Phase 5 proposal |
| Support | 14 heads evaluated; 5 constrained heads not evaluated | Keep constrained heads out unless HQ reopens them |
| Calibration | Several thin calibration bins | Require aggregate calibration audit and abstention policy |
| Temporal drift | 2010-2019 historical-only window | Use time-aware validation and document era drift |
| Position quirks | Taysom Hill 2018 QB to 2019 TE excluded | Preserve accepted-exclusion contract or create explicit multi-position policy |
| Return scoring | Granular return yards/TDs unavailable | Keep return scoring excluded unless source coverage is approved |
| Display overclaiming | No display created | User-facing copy review required before any app proposal |
| Ranking misuse | No ranking/sorting output created | Prove no probability/band/status sort key in any future app sprint |
| Production artifact drift | No production model artifact created | Keep local-only outputs quarantined until separate promotion review |

## 7. Display-Readiness Warning

Human review does not approve:

- app wiring
- player-facing probabilities
- exact display percentages
- coarse display bands
- app-readable probability outputs
- app-readable band outputs
- app-readable status tables from this research lane
- rankings/sorting
- hidden sort keys
- promoted artifacts

Existing status-only Outcome Model Status copy remains safe, but this sprint creates no app-readable status table and changes no app files.

## 8. What Phase 5 Would Need To Prove

A future Phase 5 proposal would need to prove:

1. the exact head list is approved before any new modeling run
2. constrained heads remain excluded or receive explicit HQ constraints
3. the rolling split or a stricter time-aware split is locked
4. calibration stability is acceptable at aggregate level
5. abstention rules prevent weak/sparse heads from emitting display candidates
6. human sanity review does not find misleading examples
7. no output can become app-readable without a separate display contract
8. no rankings/sorting or hidden sort keys are introduced
9. rollback and quarantine procedures are documented

## 9. Verdict

5CQ verdict: GREEN.

The packet is complete, review-only, non-app-readable, and preserves viable/weak/blocked separation. 5CR is approved to run next as a Phase 5 readiness verdict only.

## 10. Checks

Checks run:

- 5CO/5CP aggregate review packet inspection completed
- `git diff --check` passed

No Python files changed in 5CQ, so `python -m py_compile`, Ruff, and pytest are not required.
