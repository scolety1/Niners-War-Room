# Model Refinement External Audit Prompt

Copy this prompt into a ChatGPT Pro audit thread with repo/file access or with
the relevant files attached.

```text
You are auditing the Niners War Room dynasty fantasy football analyzer.

Repo:
C:\Dev\niners-war-room

Mode:
External audit only. Review-only refinement prep. Evidence first, no formula tuning.

Read first:
1. docs/model_v4/POST_AUDIT_READINESS_HANDOFF_20260531.md
2. docs/model_v4/POST_AUDIT_CLEANUP_QUEUE_20260531.md
3. docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md
4. docs/model_v4/MODEL_REFINEMENT_EXTERNAL_AUDIT_PACKAGE_20260605.md
5. docs/model_v4/FORMULA_CANDIDATE_PROPOSAL_PACKET_20260605.md
6. docs/model_v4/DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md
7. docs/model_v4/SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md
8. docs/model_v4/NON_FORMULA_SANITY_FIXTURE_TEST_NOTES_20260605.md

Then inspect the evidence reports listed in:
docs/model_v4/MODEL_REFINEMENT_EXTERNAL_AUDIT_PACKAGE_20260605.md

Hard guardrails:
- Do not tune formulas.
- Do not change model weights, veteran age curves, rookie weights, pick baselines,
  VORP, replacement formulas, market-gap thresholds, confidence cap magnitudes,
  or startup-slot conversion.
- Do not add ADP/rankings/projections/consensus/market/startup/trade-calculator
  logic to private value.
- Do not turn review labels into final trade/cut/keep/draft/buy/sell/defer/target
  recommendations.
- Do not mutate active rankings, My Team, War Board, readiness gates, app
  promotion, active data packs, generated model outputs, or user-entered draft
  state.

Audit questions:
1. Does the packet keep all formula candidates proposal-only?
2. Are source/data gaps separated from formula candidates?
3. Are Keenan Allen legacy 82.4 and Darius Slayton legacy 78.88 still
   comparison-only sentinels?
4. Do blank current-player score rows remain fail-closed/manual-only?
5. Does 2026 5.04 remain manual-only with no invented baseline/equivalence?
6. Are market, ADP, rankings, projections, consensus, startup, and
   trade-calculator context display-only or excluded from private value?
7. Do QB/TE/RB/WR/veteran/rookie/pick reports avoid final recommendations?
8. Is the packet ready for cautious human review, or does it need repair first?

Optional focused checks, if pytest and ruff are available:
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest tests\test_non_formula_sanity_fixtures.py tests\test_suspicious_ranking_triage_report.py tests\test_data_source_gap_triage_report.py tests\test_formula_candidate_proposal_packet.py tests\test_model_refinement_external_audit_package.py -q
& 'C:\Users\codex-agent\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m ruff check tests\test_non_formula_sanity_fixtures.py tests\test_suspicious_ranking_triage_report.py tests\test_data_source_gap_triage_report.py tests\test_formula_candidate_proposal_packet.py tests\test_model_refinement_external_audit_package.py

Return exactly one top-level verdict:
- refinement_packet_ready_for_human_review_only
- needs_repair_before_human_review
- needs_source_cleanup_before_formula_tuning
- formula_tuning_not_ready

Then list:
- Blockers
- High-priority issues
- Medium/low issues
- Missing evidence or unclear assumptions
- Exact file/test references for every finding
- A final short note on whether formula work should remain blocked
```
