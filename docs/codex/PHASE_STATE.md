# Phase State

Current Phase: repair
Audience: Niners co-owner making keeper/drop, top-five release, trade, and draft-pick decisions.
Product Promise: Local-first fantasy football drop-deadline command center with explainable keeper, pick, trade, and release scores.
Primary Action: Review table-first recommendations and inspect the formulas behind each score.
Showable Moment: Niners roster table shows official top five, forced-release pressure, keeper/drop scores, pick values, and clear recommendation labels from deterministic formulas.
What Not To Build: No live runtime APIs, scraping, auth, payments, deployments, generic fantasy blog copy, complex ML, or auto-trading/offers.
No More Features Lock: true
Complexity Budget: Formula-first: implement one deterministic model slice at a time with fixture tests before UI polish.
Before/After Judgment: A score is better only if its formula, fixture inputs, expected output, and table meaning are easier to audit.
Human Taste Note: Personal project but high trust bar; prioritize correctness and explainability over visual flash.
Phase Model Policy: balanced
Parking State: ACTIVE
Evidence Required: Static check plus hand-calculated formula tests and sample table output.
Done Signal: Core V1 formulas match the written model spec and tests assert the actual brief values.
Next Phase Criteria: Move to fixture-tests/engine-build only when formula specs and expected outputs are explicit.
Repair Trigger: BUDGET_STOP: pause ship and inspect results
Repair Return Phase: formula-spec
Updated At: 2026-05-03 03:40:03

## Phase Order

Website loop: brief -> foundation -> shape -> simplicity -> polish -> proof -> parked

Website stage contract source: docs/codex/WEBSITE_STAGE_RULES.md when present. Use leet-website-stages.ps1 -Project NinersWarRoom -WriteReference from the fleet control room to write or refresh it.

Analytical software loop: problem-brief -> data-contract -> formula-spec -> fixture-tests -> engine-build -> calibration -> dashboard -> scenario-tools -> analysis-proof -> parked

repair is an interrupt lane, not a normal destination. Any phase can enter repair when RED review gates, build/runtime failures, quarantine, stale/idle lock problems, or visual blockers stop safe progress. After the repair passes, return to the previous product phase.

## Phase Locks

- Brief must define audience, promise, primary action, and what not to build.
- Foundation may add missing structure and core behavior.
- Shape may reorganize pages and flows, but should avoid feature sprawl.
- Simplicity should remove, combine, shorten, hide, or demote before adding.
- Polish should refine visual/copy details without changing the core flow.
- Proof should fix blockers only.
- Parked means review-ready; do not generate new work unless a human moves the phase.
- Repair must address only the named blocker, keep No More Features Lock true, and avoid fresh feature work.
- Problem Brief defines the decision, user, outputs, and what not to predict.
- Data Contract defines CSV schemas, database tables, IDs, missing-data behavior, and snapshot/version rules.
- Formula Spec writes deterministic formulas, weights, defaults, confidence rules, and examples before coding.
- Fixture Tests creates tiny known datasets with obvious expected answers before full app work.
- Engine Build implements loaders, validators, scoring, ranking, probabilities, and exports.
- Calibration compares model outputs against history, known sanity checks, and confidence behavior.
- Dashboard builds table-first review UI only after formulas and fixtures are trustworthy.
- Scenario Tools adds what-if controls, weight changes, strategy modes, and comparison workflows.
- Analysis Proof fixes blockers only: tests, import validation, reports, deterministic outputs, and no live-data dependency.

## Upgrade Rules

- One primary action above the fold.
- No more features after Foundation unless a human moves the phase backward.
- Track whether each task makes the product clearer, simpler, more useful, or more beautiful.
- Keep one sentence product promise visible to the planner.
- Respect complexity budgets for sections, CTAs, choices, and visible copy.
- Protect the showable moment.
- Honor human taste notes.
- Use stronger judgment for Shape, Simplicity, and Polish.
- Park review-ready ships instead of continuing to generate improvements.
