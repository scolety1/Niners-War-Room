# Rookie Model Research Phases

These files are the local source documents for the LVE rookie-model build.

| phase | file | role |
|---|---|---|
| 1 | `PHASE_1_RESEARCH_SYNTHESIS.md` | Evidence-backed league translation and position principles. |
| 2 | `PHASE_2_IMPLEMENTATION_AUDIT.md` | Implementation audit table and feature-level rules. |
| 2 duplicate | `PHASE_2_DUPLICATE_MODEL_REPORT.md` | Alternate Phase 2 report to compare before freezing implementation details. |
| 3 | `PHASE_3_SCORING_FORMULAS.md` | Position formulas, gates, flags, and draft bands. |
| 4 | `PHASE_4_TECHNICAL_SPEC.md` | CSV schemas, formula contract, tests, UI, and migration plan. |
| 5 | `PHASE_5_MODEL_REVIEW.md` | Final review, risk list, simplified V1 order, and spec changes. |

Implementation rule: treat Phase 4 as the technical contract, then apply Phase 5's
recommended simplifications and risk controls before coding the rookie scoring engine.

Related archive: `../veteran_asset_research/` contains Phase 6-10 research for
veteran valuation, asset conversion, forced-release strategy, source confidence,
and the cross-research implementation audit.
