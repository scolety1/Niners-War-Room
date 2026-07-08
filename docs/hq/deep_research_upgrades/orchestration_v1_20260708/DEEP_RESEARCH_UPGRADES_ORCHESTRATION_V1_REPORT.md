# Deep Research Upgrades Orchestration V1 Report

Date: 2026-07-08

Branch: `work/lane-deep-research-upgrades-orchestration-v1-20260708`

Base HQ HEAD: `d0dc3eb5e553558884521100303df3ab03b2f372`

## Verdict

`GREEN_DEEP_RESEARCH_UPGRADES_ORCHESTRATION_READY`

## Clear Answer

The two Deep Research upgrade workstreams can be separated safely if HQ 1 owns broad feature/source discovery and future tournament architecture, while HQ 2 owns the immediate prior-year baseline challenger and model-failure response. Neither workstream should touch production rankings, runtime formula code, app pages, source-truth registries, or source promotion gates.

This packet creates the coordination rules, ownership boundaries, starter prompts, and merge-order guidance needed to prevent overlapping Codex lanes.

## Workstream Separation

| Workstream | Primary Mission | Owns | Does Not Own |
| --- | --- | --- | --- |
| Deep Research HQ 1 | Broad feature discovery and future research architecture | Public source map, metric idea backlog, route/YPRR/TPRR proxy research, source status matrix, future candidate metric registry, validation methodology, long-term roadmap | Immediate prior-year baseline challenger, production tuning, production formula changes, rankings changes, app/UI integration |
| Deep Research HQ 2 | Immediate model-failure response and prior-year baseline challenger | Prior-year finish champion baseline, source-safe first-down/opportunity/role-stability challenger tournament, miss taxonomy reduction, review-only comparison to Production Rankings Backtest V1 | Broad metric backlog, route/YPRR source discovery, general source map, future registry beyond immediate tournament, production tuning, rankings/app changes |

## Why Separation Matters

The Production Rankings Backtest V1 result found that the current formula-family proxy had real signal but did not beat prior-year finish overall:

- Rank MAE was worse than prior-year finish by about `0.26`.
- Spearman was worse by about `0.006`.
- Startable precision was worse by about `0.1 percentage points`.
- Known miss taxonomy: `424/560`, or `75.7%`, were prior-production-decline false positives.
- Known low-prior-opportunity breakout misses: `136/560`, or `24.3%`.

HQ 2 should respond directly to that finding with a controlled challenger lane. HQ 1 should continue broader source-safe discovery without crowding the immediate benchmark response.

## Overlap Risks Identified

| Risk | Why It Matters | Prevention Rule |
| --- | --- | --- |
| Both agents create feature registries | Duplicate or contradictory candidate feature names could poison later tournament setup. | HQ 1 owns broad registry; HQ 2 may create only a tournament-local candidate list. |
| Both agents edit backtest/tournament scripts | Parallel script changes can produce incompatible scorecards. | No shared script paths in parallel; HQ 2 owns immediate tournament runner only when assigned. |
| Broad route/YPRR research leaks into immediate challenger | Route data may not be source-admitted or historically safe yet. | HQ 2 uses only source-safe prior-year/opportunity/first-down/role features. |
| Immediate challenger becomes production tuning | Review-only tournament evidence could be mistaken for formula approval. | No production model, rankings, UI, source-truth, or source-promotion changes. |
| App/rankings files drift while research lanes run | Research artifacts must not change draft-day behavior. | App, rankings, runtime services, default sort, hidden sort, and decision logic are protected. |

## Artifact Index

- `DR_HQ1_FEATURE_DISCOVERY_CHARTER.md`
- `DR_HQ2_PRIOR_YEAR_CHALLENGER_CHARTER.md`
- `WORKSTREAM_BOUNDARY_MATRIX.csv`
- `FILE_OWNERSHIP_MATRIX.csv`
- `LANE_QUEUE_AND_DEPENDENCIES.csv`
- `PARALLEL_WORK_RULES.md`
- `MERGE_ORDER_PLAN.md`
- `SHARED_GUARDRAILS.md`
- `DR_HQ1_STARTER_PROMPT.md`
- `DR_HQ2_STARTER_PROMPT.md`
- `artifact_manifest.csv`

## Recommended Lane Order

1. HQ 2 Source-Safe Feature Tournament V1 / Prior-Year Baseline Challenger.
2. HQ 1 Experimental Feature Discovery Registry V1.
3. HQ 1 Future Feature Tournament Registry V1.
4. Later Feature Tournament Runner V1.
5. Later position-specific candidate formula lanes, only after review evidence and human gate acceptance.

## Merge Recommendation

Merge evidence packets before review-only scripts. Merge review-only scripts before any production proposal. Production changes and source promotions require separate approval and must never be bundled with research artifacts.

## Guardrail Result

This lane created only docs/CSV orchestration artifacts under `docs/hq/deep_research_upgrades/orchestration_v1_20260708/`. It did not run a feature tournament, change formula logic, change rankings, touch UI/runtime behavior, promote sources, merge, or push.
