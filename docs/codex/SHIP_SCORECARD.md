# Ship Scorecard

Use this before giving a ship meaningful autonomous runtime. The goal is to prove the ship has a narrow useful job, a clear user, and a local way to evaluate progress.

## Summary

Ship name: NinersWarRoom

Primary user or buyer: The Niners co-owner using local fantasy football rankings and keeper decisions.

Weekly job this replaces: Keeper, drop, trade, and draft decisions for the league using deterministic local data.

First useful version: A local dashboard that loads roster data, shows formulas, and explains keeper/drop recommendations.

Local evaluator: build command plus configured visual or manual preview routes.

Current recommendation: ADMIT

## Admission Score

| Criterion | Weight | Score | Evidence |
| --- | ---: | ---: | --- |
| Recurring pain | 20 | 16 | Recurring job is captured by ship mission and task queue. |
| Clear buyer or user | 15 | 13 | Primary user inferred from ship identity and config. |
| Local evaluability | 20 | 18 | Build command: powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\codex-static-check.ps1; visual paths: /, /Import_Review, /Team, /War_Board, /Trade_Central, /Draft_Room, /League_Intel, /Model_Audit. |
| Thin first release | 10 | 7 | Risk tier is production-adjacent; profile is real-product. |
| Bounded scope | 10 | 7 | Project type is full-stack-web. |
| Revenue or demo speed | 10 | 8 | Local preview and iterative fleet loops can show progress quickly. |
| Demo clarity | 5 | 4 | First useful version is defined as a short local demo or workflow. |
| Fleet leverage | 5 | 4 | Design, copy, test, visual, repair, and formula passes can run separately. |
| Data and compliance safety | 5 | 3 | Risk tier and capabilities limit sensitive work. |
| Total | 100 | 80 | 70+ admit, 55-69 revise, below 55 park. |

## Red Flags

- [ ] Needs payments to be useful.
- [ ] Needs custom auth or account roles to be useful.
- [ ] Stores regulated, sensitive, payment, medical, payroll, tax, or private production data.
- [ ] Depends on many third-party integrations before v1 has value.
- [ ] Has no credible local evaluator.
- [ ] Has no named user workflow.
- [ ] Is broad, platform-shaped, or generic AI-wrapper-shaped.
- [ ] Requires live external APIs at decision time.

## Decision

Choose one:

- ADMIT: Score is 70+ and no red flags apply.
- REVISE: Score is 55-69 or the job/user/evaluator needs sharpening.
- PARK: Score is below 55, red flags apply, or the ship cannot prove local usefulness.

Decision: ADMIT

Reason: Auto-backfilled from fleet config; review and sharpen before enforcing long unattended runs.

Next action: Run product usefulness review and assign one product-shaped task.
