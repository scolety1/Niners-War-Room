# Niners War Room Repair Task Queue

Date: 2026-05-30

Mode: paused / inspect-and-repair only.

Use one task per repeatable run. Each task must end with changed files, tests run,
failures, and remaining risks. Do not tune formulas until all source, routing,
market, join, label, and copy gates pass.

## Repeatable Task Prompt

```text
You are working on Niners War Room in paused / inspect-and-repair mode.

Read:
1. docs/model_v4/5-30_NEW_CHAT_HANDOFF.md
2. docs/model_v4/REPAIR_TASK_QUEUE_20260530.md
3. the current task only

Implement exactly one queued task.

Do not tune formulas, weights, age curves, rookie weights, pick baselines, VORP,
replacement formulas, market thresholds, confidence caps, or startup-slot conversion.
Do not add market/ADP/rank/projection/consensus/trade-calculator logic to private value.
Do not create final trade, cut, keep, draft, buy, sell, or target recommendations.
Do not mutate active rankings, My Team, War Board, readiness gates, or app promotion.

Before editing:
- summarize the current task
- summarize allowed scope
- summarize forbidden scope
- list tests to add/run

Then implement only that task.
Run focused tests.
Update this queue status and audit notes.
End with changed files, tests run, failures, and remaining risks.
```

## Queue

| ID | Task | Allowed Scope | Tests | Status | Audit Notes |
|---|---|---|---|---|---|
| 01 | Shared score envelope / source disclosure schema | Central DTO, classifier, resolver, validation, export contract | `tests/test_review_score_envelope_service.py` | Done | Added `ReviewScoreEnvelope`; no formulas changed. |
| 02 | Legacy active-pack quarantine service | Rename `private_score` to `legacy_active_pack_score` on load; legacy comparison-only envelope rows | Add legacy score quarantine tests for Keenan/Darius | Done | Player Board service quarantines active-pack legacy scores as comparison-only. |
| 03 | Player Board Model v4 current-player routing | Route Player Board primary value to `checkpoint_review_score`; keep legacy lane separate | Add Player Board sentinel tests | Done | Keenan routes to Model v4 `41.6097`; Darius fails closed instead of falling back to `78.88`. |
| 04 | Cross-asset source resolver enforcement | Shared resolver for cross-asset tools; reject legacy/unknown primary inputs | Add resolver/cross-asset tests | Done | Shared resolver declares cross-asset canonical source; deeper call-site wiring remains queued. |
| 05 | Market display-only payload gate | Keep market/ADP/rank/projection context under display lanes; prevent primary score assignment | Add market no-primary tests | Done | Added display-only market payload helper; broader market service repair remains queued. |
| 06 | Legacy active-pack call-site quarantine | Replace direct active-pack primary score use in old services where safe | Existing trade/asset service tests plus new sentinel tests | Done | Old asset/trade services now expose active-pack private scores through quarantine metadata (`legacy_active_pack_score`, blank `primary_review_score`, lineage/source flags) while preserving compatibility math for later cleanup. |
| 07 | Join identity fail-closed gates | Duplicate/unmatched identity warning helpers; manual decision state | Add duplicate/unmatched tests | Done | Added shared identity join gate helpers and wired Player Board Model v4 current-value joins to fail closed on duplicate/unmatched identity keys without falling back to legacy scores. |
| 08 | Team/status and role evidence fail-closed gates | Shared warning classifiers for stale team/status and missing role evidence | Add gate tests | Done | Added shared Model v4 evidence gate for stale team/status and missing role evidence; Player Board now exposes gate flags and requires manual review when they fire without changing score math. |
| 09 | Partial/quarantined join gate | Detect quarantined contribution and force manual state | Add quarantined contribution tests | Done | Extended shared Model v4 evidence gate to flag partial/quarantined joins or contributions; Player Board now exposes the flag and requires manual review without hiding source warnings or falling back to legacy. |
| 10 | Market no-leakage service repair | Repair `market_gap_service` labels and payload separation | Market gap tests | Done | Market gap rows now expose explicit display-only metadata, blank primary/review label fields, stronger blocked-use scope, and neutral context labels with action-like hint terms removed. |
| 11 | Old Trade Central language quarantine | Remove buy/sell/target/edge recommendation copy from old trade service/page | Trade copy lint tests | Done | Old Trade Central service/page now use neutral review-context labels for roster, external asset, market-gap, and package rows; added service/page copy tests for action-like label quarantine without changing score math. |
| 12 | External Asset Reviews service rename | Sprint 14C trade-for rows become external asset context rows | Sprint 14C tests | Done | Sprint 14C now exposes canonical `external_asset_rows`, neutral external-asset context bands, and `external_asset_context_review_rows.csv` export while preserving compatibility aliases; no value formula or acquisition realism layer changed. |
| 13 | External Asset Reviews UI rename | Page title/copy and exported names use External Asset Reviews | UI copy tests | Done | Navigation, command-center copy, old context page title, and June 15 advanced source rows now use External Asset Reviews / external asset context wording and the new `external_asset_context_review_rows.csv` export path; no value formula changed. |
| 14 | Cross-asset export disclosure | Startup, roster opportunity, pick lab, external review exports preserve source fields | Export header tests | Done | Startup Slot, Roster Opportunity Cost, Rookie Pick Decision Lab, and External Asset Review exports now include `source_path`, `source_column`, and `lineage_class`; focused exporter tests and ruff pass. |
| 15 | Rookie pick neutral label mode gate | Neutral board allows only use/hold/manual labels | Pick label tests | Done | Rookie Pick Decision Lab neutral board now emits only `use_pick_review`, `hold_pick_value_context`, or `manual_decision_required`; 5.04 keeps no-baseline evidence fields while using the neutral manual label. |
| 16 | Rookie comparison-mode gates | Trade-down/future/current-player labels require concrete comparator | Pick comparison tests | Done | Rookie Pick Decision Lab compare rows now disclose `comparison_mode`, `comparator_key`, and concrete comparator source status; future-pick and current-player comparison modes require loaded comparator rows, while absent trade-down comparators emit no trade-down mode. |
| 17 | UI review-only banner rollout | Main model pages show required review-only banner | UI text tests | Done | Added the required review-only surface banner to the shared trust banner and the standalone June 15 review page; static UI tests confirm main model pages route through the banner without changing readiness or promotion gates. |
| 18 | UI score disclosure rollout | Visible source/version/type/confidence/warning disclosure on score tables/cards | Disclosure tests | Done | Player Board default table now exposes score source file, column, type, model version, lineage, trust cap, and warnings; Draft Room score tables/cards now surface exported source/column/lineage/version metadata. |
| 19 | Final sentinel regression gate | Keenan/Darius, market, copy, source routing, pick labels, cross-asset tests | Focused suite plus selected full tests | Done | Added final sentinel gate covering Keenan/Darius legacy leakage, market display-only rows, neutral copy/banner/disclosure, pick label/comparator gates, and cross-asset source disclosure; selected focused suite passed, full repo suite remains a residual risk. |
| 20 | External audit package and Pro-agent prompt | Bundle docs, changed-file summary, tests, acceptance checklist, prompt | Package existence/readback test | Done | Added external audit package overview, Pro-agent prompt, and acceptance checklist with readback tests; package references final sentinel gates, changed surfaces, test commands, guardrails, residual risks, and verdict format for ChatGPT Pro audit. |
