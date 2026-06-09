# Model Refinement Queue

Date: 2026-06-05

Mode: review-only refinement prep.

Purpose: get Niners War Room to a solid football-evaluation point for external
audit and human judgment before any formula tuning. This queue should produce
evidence, sanity checks, suspicious-ranking lists, and audit packets. It should
not change formulas.

## Current Baseline

Start from the post-audit green state:

- `docs/model_v4/POST_AUDIT_READINESS_HANDOFF_20260531.md`
- Full test suite observed green: `1214 passed`
- Full lint observed green: `ruff check app src tests`
- Source-routing and review-only safety gates are complete.

## Hard Guardrails

- Do not tune formulas.
- Do not change model weights, veteran age curves, rookie weights, pick
  baselines, VORP, replacement formulas, market-gap thresholds, confidence cap
  magnitudes, or startup-slot conversion.
- Do not add ADP, rankings, projections, consensus, market, startup, or
  trade-calculator logic to private value.
- Do not turn review labels into final trade, cut, keep, draft, buy, sell,
  defer, target, or start/sit recommendations.
- Do not mutate active rankings, My Team, War Board, readiness gates, app
  promotion, active data packs, generated model outputs, or user-entered draft
  state.
- Do not run blind `git add .`.
- If a task discovers a likely formula issue, document it as a candidate only.
  Do not patch the formula.

## Repeatable Refinement Prompt

```text
You are working on the Niners War Room dynasty fantasy football analyzer.

Repo:
C:\Dev\niners-war-room

Current mode:
Review-only refinement prep. Evidence first, no formula tuning.

Read first:
1. docs/model_v4/POST_AUDIT_READINESS_HANDOFF_20260531.md
2. docs/model_v4/POST_AUDIT_CLEANUP_QUEUE_20260531.md
3. docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md
4. The next queued refinement task marked Pending or In progress

Implement exactly one queued refinement task.

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
- Do not run blind `git add .`.

Before editing, briefly confirm:
1. current queued task,
2. allowed scope,
3. forbidden scope,
4. tests/checks you will add or run.

Then:
1. Implement only that task.
2. Prefer docs/reports/tests over code changes.
3. Add/update focused readback tests when the task creates docs or reports.
4. Run focused tests/checks.
5. Update docs/model_v4/MODEL_REFINEMENT_QUEUE_20260605.md with task status and audit notes.
6. End with changed files, tests/checks run, results, remaining risks, and next recommended queued task.
```

## Queue

| ID | Task | Allowed Scope | Checks | Status | Audit Notes |
|---|---|---|---|---|---|
| R01 | Create refinement evidence map | Inventory current value, dynasty asset, rookie board, pick lab, external asset, Decision Board, and Player Board sources; map source file, score column, entity type, lineage, warnings, and UI surface | Docs readback test | Done | Added `REFINEMENT_EVIDENCE_MAP_20260605.md` covering core score sources, UI surfaces, warning fields, legacy/display-only lanes, and the missing current external asset generated CSV with compatibility fallback noted. |
| R02 | Build named-player audit roster | Create a balanced audit list of 60-80 players/assets: elite young WR/RB, aging vets, injured players, low-evidence players, QB/TE in format context, rookies, and picks | Docs readback test | Done | Added `NAMED_PLAYER_AUDIT_ROSTER_20260605.md` with 80 review subjects across current players, rookies, picks, position/age/evidence risk categories, and inclusion reasons. |
| R03 | Current-player value extraction report | Read current-player review rows and produce a report of selected named players with score, rank/order, source, warnings, trust cap, and manual-review flags | Report/readback test | Done | Added `CURRENT_PLAYER_VALUE_EXTRACTION_REPORT_20260605.md` covering 68 current-player audit roster rows, checkpoint rank/order, score, confidence cap/status, warning flags, and warning-derived manual-review flags; excluded rookie/pick subjects for later tasks and preserved no-score-change guardrails. |
| R04 | Legacy-vs-current sentinel expansion | Expand Keenan/Darius-style sentinel report to 15-25 legacy-risk veterans where active-pack score could mislead if leaked | Report/readback test plus existing sentinel tests | Done | Added `LEGACY_VS_CURRENT_SENTINEL_EXPANSION_20260605.md` with 25 comparison-only legacy active-pack leak sentinels, including mandatory Keenan Allen `82.4` and Darius Slayton `78.88`; documented current checkpoint comparisons, missing-current fail-closed handling, and no-routing/no-formula-change guardrails. |
| R05 | Top/bottom current-player sanity scan | Generate top 50 and bottom 50 current-player review rows with warnings and reason fields; flag obvious surprise rows for human review | Report/readback test | Done | Added `TOP_BOTTOM_CURRENT_PLAYER_SANITY_SCAN_20260605.md` sorted by numeric `checkpoint_review_score`, with top/bottom 50 rows, warning previews, reason labels, blank-score manual-review rows, and explicit `review labels do not mean wrong` guardrails. |
| R06 | RB/WR cross-position balance report | Compare RB and WR score distributions, top tiers, age bands, warning rates, and named-player examples | Report/readback test | Done | Added `RB_WR_CROSS_POSITION_BALANCE_REPORT_20260605.md` comparing RB/WR counts, score bands, top-tier presence, warning rates, age-window rows, and named review prompts while explicitly preserving no-balance-tuning guardrails. |
| R07 | QB 1QB discipline report | Audit QB values against 1QB/no-superflex assumptions; flag QBs near RB/WR tiers or picks where context may be confusing | Report/readback test | Done | Added `QB_1QB_DISCIPLINE_REPORT_20260605.md` covering 9 QB rows, 1QB warning coverage, nearby RB/WR score neighborhoods, owned-pick context, blank QB handling, and explicit no-QB-cap/no-trade-equivalence guardrails. |
| R08 | TE no-premium discipline report | Audit TE values against no-TE-premium assumptions; flag TEs near RB/WR values and warning coverage | Report/readback test | Done | Added `TE_NO_PREMIUM_DISCIPLINE_REPORT_20260605.md` covering 11 TE rows, no-premium warning coverage, nearby RB/WR score neighborhoods, owned-pick context, blank TE handling, and explicit no-TE-discipline/no-trade-equivalence guardrails. |
| R09 | Veteran age-window audit | Review older productive veterans, age-warning coverage, and score bands; classify potential over/under-confidence candidates | Report/readback test | Done | Added `VETERAN_AGE_WINDOW_AUDIT_20260605.md` covering 18 veteran/age-warning rows, exported RB age guardrails, confidence/identity warnings, score bands, and review-only classifications while preserving no-age-curve-tuning guardrails. |
| R10 | Young-player evidence audit | Review young players with high scores and limited evidence; ensure warnings and manual-review flags explain uncertainty | Report/readback test | Done | Added `YOUNG_PLAYER_EVIDENCE_AUDIT_20260605.md` covering 35 young/volatile/low-evidence rows, high-score young prompts, limited-history/source-gap rows, blank-score manual-review rows, and no-young-prior-tuning guardrails. |
| R11 | Injury/status risk audit | Identify players with injury, status, or stale-team warnings and verify score presentation makes those risks visible | Report/readback test | Done | Added `INJURY_STATUS_RISK_AUDIT_20260605.md` covering 30 status-risk rows, team/identity warning visibility, injury/status roster prompts, confidence caps, and no-injury-penalty-tuning guardrails. |
| R12 | Rookie board top-cluster audit | Inspect top rookie rows, evidence components, trust caps, and warning groups; flag rankings that need human scouting | Report/readback test | Done | Added `ROOKIE_BOARD_TOP_CLUSTER_AUDIT_20260605.md` covering top-20 rookie rows, evidence/band counts, warning group counts, named rookie anchors, Daniel Sobkowicz low-evidence routing, and no-rookie-weight/no-draft-recommendation guardrails. |
| R13 | Rookie low-evidence/watchlist audit | Inspect watchlist/data-incomplete rookies and verify low-confidence rows do not masquerade as confident draft options | Report/readback test | Done | Added `ROOKIE_LOW_EVIDENCE_WATCHLIST_AUDIT_20260605.md` covering 43 watchlist/data-incomplete rows, including 21 explicit `watchlist_data_incomplete` rows and Daniel Sobkowicz; verified every reviewed row carries review-only/final-pick blocked-use and no score reaches the 50+ top-cluster band. |
| R14 | Pick value ladder audit | Inspect 1.03, 1.04, 2.04, 2.08, 5.04 and nearby pick baselines; verify source disclosure and manual-only handling | Report/readback test | Done | Added `PICK_VALUE_LADDER_AUDIT_20260605.md` covering admitted ladder rows around 1.03/1.04/2.04/2.08, owned-pick inventory matches, Decision Lab context, comparison-row counts, and 5.04 manual-only/no-exact-baseline quarantine; no pick baselines changed. |
| R15 | Pick-vs-player neighborhood audit | Review nearby model-value neighborhoods for picks, rookies, current players, and available assets; flag one-for-one trade-equivalence risks | Report/readback test | Done | Added `PICK_VS_PLAYER_NEIGHBORHOOD_AUDIT_20260605.md` covering 72 Decision Lab comparison rows, closest rookie/current neighborhoods for owned picks, 14 elite-current one-pick risk flags, 5.04 blank-gap quarantine, and the compare-export source-disclosure gap; no startup-slot or pick conversion changed. |
| R16 | External Asset Reviews sanity audit | Inspect external asset rows for top context assets, warnings, lineage, and whether UI/report framing stays review-only | Report/readback test | Done | Added `EXTERNAL_ASSET_REVIEWS_SANITY_AUDIT_20260605.md` covering repaired in-memory External Asset Review rows, 35 external context rows, 24 roster-pressure rows, source/lineage disclosure, review-only UI framing, and stale compatibility fallback naming; no buy/sell/target logic or generated outputs changed. |
| R17 | Decision Board coherence audit | Trace a sample of Decision Board rows back to source rows and receipts; verify areas, warning flags, and blocked-use fields | Report/readback test | Done | Added `DECISION_BOARD_COHERENCE_AUDIT_20260605.md` tracing representative pick, 5.04, roster-pressure, and rookie-window rows to receipts/components/source CSVs; verified 105 rows, 105 receipts, 315 components, blocked-use coverage, and no Decision Board output mutation. |
| R18 | Player Board UX smoke checklist | Create a manual smoke-test checklist for Player Board filters, score disclosure, warnings, and named-player traceability | Docs readback test | Done | Added `PLAYER_BOARD_UX_SMOKE_CHECKLIST_20260605.md` covering filters, score disclosure, warnings, named-player traceability, Keenan/Darius sentinels, display-only market checks, fail conditions, and evidence capture; no frontend implementation or generated output mutation. |
| R19 | Draft Room UX smoke checklist | Create a manual smoke-test checklist for owned picks, rookie rows, source disclosure, warning groups, and receipt expanders | Docs readback test | Done | Added `DRAFT_ROOM_UX_SMOKE_CHECKLIST_20260605.md` covering owned picks, rookie filters, source disclosure, warning groups, receipt expanders, 5.04 manual-only guardrails, live-draft observe-only state safety, and evidence capture; no draft-state mutation. |
| R20 | External Asset/Decision Board UX smoke checklist | Create manual smoke-test checklist for External Asset Reviews and Decision Board review-only framing | Docs readback test | Done | Added `EXTERNAL_ASSET_DECISION_BOARD_UX_SMOKE_CHECKLIST_20260605.md` covering External Asset Reviews, War Board Decision Snapshot, Decision Board artifacts, source disclosure, blocked-use guardrails, market display-only framing, 5.04 manual-only sentinel checks, and evidence capture; no UI feature work or generated output mutation. |
| R21 | Build ordered sanity fixture spec | Define expected ordering fixtures without exact numeric targets: elite tiers, replacement tiers, pick ladders, format caps, and warning expectations | Docs/readback test | Done | Added `ORDERED_SANITY_FIXTURE_SPEC_20260605.md` defining review-only fixture families for elite tiers, replacement/depth tiers, pick ladders, format caps, warning expectations, source/blocked-use checks, and R22 automation guidance without exact numeric targets or formula-enforcing assertions. |
| R22 | Add non-formula sanity fixture tests | Add tests that assert source/risk behavior and broad ordering only where already true; skip or document candidates that would fail | Focused tests | Done | Added `test_non_formula_sanity_fixtures.py` plus `NON_FORMULA_SANITY_FIXTURE_TEST_NOTES_20260605.md`; tests assert source/risk guardrails, legacy fail-closed behavior, rookie watchlist suppression, admitted pick-ladder ordering, Pick Decision Lab equivalence guardrails, and Decision Board traceability without exact score targets or new football-opinion enforcement. |
| R23 | Suspicious ranking triage report | Consolidate suspicious rows from prior reports into buckets: likely data issue, source-missing issue, formula candidate, UI/explanation issue, human-review-only | Report/readback test | Done | Added `SUSPICIOUS_RANKING_TRIAGE_REPORT_20260605.md` consolidating suspicious rows into likely data, source-missing, formula-candidate, UI/explanation, and human-review-only buckets with tomorrow review order; no formula tuning or final recommendations. |
| R24 | Data/source gap triage report | Identify missing source patterns, duplicate/mismatched identities, stale rows, and warning coverage gaps that should be fixed before tuning | Report/readback test | Done | Added `DATA_SOURCE_GAP_TRIAGE_REPORT_20260605.md` covering missing primary scores, identity/team mismatches, rookie evidence gaps, source-disclosure gaps, and stale compatibility lanes; no external data import or generated output mutation. |
| R25 | Formula candidate proposal packet | Summarize candidate formula issues with evidence, impacted players, risks, and proposed future experiments; no implementation | Docs readback test | Done | Added `FORMULA_CANDIDATE_PROPOSAL_PACKET_20260605.md` with proposal-only candidate areas for TE ceiling, 1QB spread, RB/WR balance, veteran age/status, young-player evidence, rookie source limits, and pick-neighborhood explanation; no implementation. |
| R26 | External audit package v2 | Build an external audit packet for football-quality/readiness review, including reports, queue status, tests, and exact audit instructions | Package/readback test | Done | Added `MODEL_REFINEMENT_EXTERNAL_AUDIT_PACKAGE_20260605.md` and `MODEL_REFINEMENT_EXTERNAL_AUDIT_PROMPT_20260605.md` for a ChatGPT Pro/external auditor, with report index, verdict options, focused checks, and guardrails. |
| R27 | User judgment worksheet | Create a tomorrow worksheet for human judgment: player, model says, warning, your prior, agreement, disagreement reason, money-action risk | Docs/CSV readback test | Done | Added `USER_JUDGMENT_WORKSHEET_20260605.md` and `USER_JUDGMENT_WORKSHEET_20260605.csv` with review-only rows, warning context, money-action risk notes, and blank human-prior/final-decision fields for manual use. |
| R28 | Final overnight readiness rerun | Run focused refinement tests plus full repo tests/lint if time; update queue and handoff with exact results | Existing tests/lint | Done | Added `FINAL_OVERNIGHT_READINESS_RERUN_20260605.md`; pytest/ruff unavailable in current runtime, direct readback runner passed 121 assertions across 27 refinement test files, and py_compile passed for all 27 files. |
| R29 | Tomorrow morning handoff | Write concise handoff with what changed, what passed, what to inspect first, and which rows require your judgment | Docs readback test | Done | Added `TOMORROW_MORNING_HANDOFF_20260605.md` with what changed, what passed, blocked full-suite/lint tooling notes, first inspection order, and which rows require human judgment. |
| R30 | Optional archive/export bundle | Create a zip/package of the refinement reports, audit prompt, worksheet, queue, and readiness handoff | Package/readback test | Done | Added `MODEL_REFINEMENT_EXPORT_BUNDLE_MANIFEST_20260605.md` and `MODEL_REFINEMENT_EXPORT_BUNDLE_20260605.zip` containing refinement reports, audit prompt, worksheet, queue, readiness rerun, and handoff; no source code staging or commits. |

## Definition Of Done

This queue is done when:

- The model has an evidence-backed suspicious-ranking list.
- Named players, positions, rookies, picks, and external asset rows have
  readable audit reports.
- Broad sanity fixture expectations are documented.
- Formula work is separated into proposal-only candidates.
- External audit packet and user judgment worksheet are ready.
- Full tests/lint have been rerun or any failure is documented with exact scope.

## Recommended Run Count

Send the repeatable prompt **30 times** to complete every queued task once.

If time is limited, send it **26 times** to reach the external audit package.
Then send tasks R27-R30 tomorrow before or after your own judgment pass.
