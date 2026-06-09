# 5-26 Workdocs

This is the overnight / away-from-keyboard work queue. Use it when the user says something like:

`get started on feature 7`

Rules for every item in this file:
- Keep outputs review-only unless the user explicitly asks for promotion.
- Do not mutate active rankings, My Team, War Board, readiness gates, or app promotion.
- Do not create final cut/keep/trade/draft recommendations.
- Do not use ADP, market rankings, projections, mock drafts, big boards, or consensus as private value.
- Missing data remains missing.
- Run focused tests, Ruff, and compile/static checks where practical.
- End with paths, test results, and whether the feature is ready to test or needs patching.

## Model v4.8 Source Firewall Data Stack Sprint

Use these prompts when the user says `start source firewall phase 1`, `start source
firewall phase 2`, etc.

### v4.8 Phase 1 - Source Registry And Firewall

Prompt:

```text
Model v4.8 / Phase 1: Source Registry And Firewall

Goal:
Create and validate a source registry that separates admitted factual evidence from
display-only market/projection/ranking context before any new API/feed work.

Tasks:
1. Inspect `config/source_registry.csv`, source contract docs, and existing formula
   contract guardrails.
2. Confirm registry rows exist for nflverse, Sleeper, RotoWire, FantasyPros,
   DynastyProcess, PlayerProfiler, NFL official draft tracker, Tankathon,
   CollegeFootballData, SportsDataIO, PFF, and Pro Football Reference.
3. Add or patch a source registry service that fails closed when display-only,
   market, projection, rank, mock, big-board, consensus, salary, or expert fields
   are allowed as private value.
4. Add tests proving no private source row includes blocked source kinds or terms.
5. Produce/update `docs/model_v4/SOURCE_FIREWALL_DATA_STACK_PLAN.md`.

Constraints:
- No formula/value changes.
- No app promotion or final recommendations.
- Missing evidence remains missing.
```

### v4.8 Phase 2 - Sleeper League Truth Sync Contract

Prompt:

```text
Model v4.8 / Phase 2: Sleeper League Truth Sync Contract

Goal:
Define and, if practical, implement the Sleeper API sync lane for league truth only.

Tasks:
1. Build or patch a Sleeper sync contract for league settings, rosters, users,
   traded picks, drafts, and the players endpoint.
2. Normalize outputs into league state / identity tables only.
3. Treat Sleeper trending adds/drops as display-only market/activity context.
4. Add cache/diff requirements for the players endpoint.
5. Add tests proving league state may drive roster/pick truth, but trending fields
   cannot drive private value.

Outputs:
- docs/model_v4/MODEL_V4_8_PHASE_2_SLEEPER_LEAGUE_TRUTH_SYNC.md
- review-only local export contract or generated rows if implementation is safe.
```

### v4.8 Phase 3 - nflverse Factual Evidence Contract

Prompt:

```text
Model v4.8 / Phase 3: nflverse Factual Evidence Contract

Goal:
Make nflverse/nflreadr the factual NFL evidence backbone for production, first
downs, usage, snaps, injuries, depth charts, draft picks, combine, and IDs.

Tasks:
1. Define raw_nflverse_* tables and evidence_* outputs.
2. Include schema-drift/data-dictionary checks.
3. Keep FantasyPros/ffverse rankings from nflverse ecosystems display-only.
4. Add first-down derivation rules from factual play/stat data.
5. Add tests proving factual nflverse rows can be admitted and market/projection
   rows remain blocked.

Output:
- docs/model_v4/MODEL_V4_8_PHASE_3_NFLVERSE_FACTUAL_EVIDENCE_CONTRACT.md
```

### v4.8 Phase 4 - RotoWire Export Import Firewall

Prompt:

```text
Model v4.8 / Phase 4: RotoWire Export Import Firewall

Goal:
Use the user's RotoWire access safely through manually exported or explicitly
permitted structured extracts only.

Tasks:
1. Support factual tables: injuries, practice reports, depth charts, snap counts,
   target leaders, TE routes, player stats, combine/pro-day data.
2. Classify projections as DISPLAY_PROJECTION.
3. Classify ADP, rankings, rookie ranks, mocks, and analyst blurbs as DISPLAY_MARKET
   or MANUAL_REVIEW only.
4. Store metadata/links for news; do not ingest premium text as model input.
5. Add tests proving RotoWire factual exports can be admitted only by table/field
   allowlist and display-only rows cannot drive private value.

Output:
- docs/model_v4/MODEL_V4_8_PHASE_4_ROTOWIRE_EXPORT_IMPORT_FIREWALL.md
```

### v4.8 Phase 5 - College And Draft Capital Evidence Lane

Prompt:

```text
Model v4.8 / Phase 5: College And Draft Capital Evidence Lane

Goal:
Add the next rookie evidence lane for actual NFL draft capital and factual college
production without mock/big-board/ranking leakage.

Tasks:
1. Define evidence_draft_capital with actual draft year, round, pick, team,
   position, and school only.
2. Use NFL official draft tracker as primary completed-pick source; Tankathon only
   for completed-result verification, not mocks/big boards.
3. Define CollegeFootballData factual production/team-share ingestion contract.
4. Add tests blocking mock draft slot, big-board rank, consensus prospect rank,
   rookie ADP, and analyst rank from private value.

Output:
- docs/model_v4/MODEL_V4_8_PHASE_5_COLLEGE_DRAFT_CAPITAL_EVIDENCE.md
```

### v4.8 Phase 6 - Missing Evidence Report

Prompt:

```text
Model v4.8 / Phase 6: Missing Evidence Report

Goal:
Produce a review-only missing evidence report so missing fields are visible and
never substituted with market/projection/ranking context.

Tasks:
1. For every player/prospect, show missing admitted evidence fields, source checked,
   last checked date, missing reason, confidence cap, and display-only context
   availability.
2. Add warnings when a display-only market/projection field exists but the admitted
   factual evidence is missing.
3. Add tests proving missing data is not converted to zero, average, or positive
   evidence.

Outputs:
- local_exports/model_v4/missing_evidence/latest/missing_evidence_report.csv
- docs/model_v4/MODEL_V4_8_PHASE_6_MISSING_EVIDENCE_REPORT.md
```

### v4.8 Phase 7 - Review Export Labels

Prompt:

```text
Model v4.8 / Phase 7: Review Export Labels

Goal:
Make every major UI/export table visually separate model value, admitted evidence,
display-only market context, display-only projection context, source risk, missing
evidence, and review safety.

Tasks:
1. Add/review column groups:
   - MODEL VALUE
   - ADMITTED EVIDENCE
   - MARKET CONTEXT - DISPLAY ONLY
   - PROJECTION CONTEXT - DISPLAY ONLY
   - SOURCE RISK
   - REVIEW SAFETY
2. Add the footer: Review-only. No cut/keep/trade/draft recommendation generated.
3. Ensure market ranks are not adjacent to private model value without a display-only
   label.
4. Add UI/static tests where practical.

Output:
- docs/model_v4/MODEL_V4_8_PHASE_7_REVIEW_EXPORT_LABELS.md
```

### v4.8 Phase 8 - Source Firewall Audit Packet

Prompt:

```text
Model v4.8 / Phase 8: Source Firewall Audit Packet

Goal:
Package the source firewall and data-stack plan for external audit.

Tasks:
1. Package no more than 20 files.
2. Include source registry, source firewall tests, source plan doc, formula contract,
   source trust contract, and any v4.8 phase docs produced so far.
3. Write a neutral audit prompt asking whether the registry prevents market,
   projection, ranking, mock, big-board, consensus, salary, and expert leakage into
   private value while still admitting factual nflverse/Sleeper/RotoWire/NFL/CFBD
   evidence.
4. Produce:
   - docs/model_v4/MODEL_V4_8_SOURCE_FIREWALL_AUDIT_PROMPT.md
   - local_exports/model_v4/audit_packets/model_v4_8_source_firewall_audit_YYYYMMDD.zip
```

## Feature 7 - Review-Only Trade Package Builder

Goal:
Help explore model-equivalent trade package shapes without creating final trade recommendations.

Context:
- Model v4 is a local-first dynasty fantasy football decision model.
- League: 10-team dynasty, 1QB, non-PPR, rushing/receiving first-down scoring, no TE premium.
- User team: Niners.
- June 15 roster deadline.
- Features 1-6 are built/tested/patched.
- This feature should use the existing review-only decision surfaces, especially:
  - Startup Slot Simulator
  - Roster Cut Opportunity-Cost Engine
  - Rookie Pick Decision Lab
  - Historical Similarity Engine
  - Player Rank Explainer
  - Source-Risk Heatmap
  - Model Edge Queue

Inputs:
- `local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv`
- `local_exports/model_v4/startup_slot_simulator/latest/startup_slot_review_rows.csv`
- `local_exports/model_v4/pick_trade_defer/latest/niners_pick_inventory_review_rows.csv`
- `local_exports/model_v4/decision_calibration/latest/niners_roster_state_review.csv`
- `local_exports/model_v4/rookie_draft_review/latest/rookie_draft_board_review_rows.csv`
- `local_exports/model_v4/trade_review/latest/trade_away_candidate_review_rows.csv`
- `local_exports/model_v4/pick_trade_defer/latest/pick_defer_scenario_review_rows.csv`
- `local_exports/model_v4/source_risk_heatmap/latest/source_risk_player_rows.csv`
- `local_exports/model_v4/model_edge_queue/latest/model_edge_rows.csv`

Outputs:
- `local_exports/model_v4/trade_package_builder/latest/trade_package_review_rows.csv`
- `local_exports/model_v4/trade_package_builder/latest/trade_package_component_rows.csv`
- `local_exports/model_v4/trade_package_builder/latest/trade_package_warnings.csv`
- `docs/model_v4/TRADE_PACKAGE_BUILDER.md`

Package types:
- `player_for_pick`
- `pick_for_player`
- `player_plus_pick_for_pick`
- `two_for_one_consolidation`
- `trade_down_package`
- `defer_pick_package`

Required row fields:
- `package_id`
- `package_type`
- `assets_given`
- `assets_received`
- `model_value_given`
- `model_value_received`
- `value_gap`
- `package_shape`
- `risk_note`
- `roster_pressure_context`
- `confidence_status`
- `source_risk_context`
- `model_edge_context`
- `review_label`
- `allowed_use`
- `blocked_use`
- `formula_version`

Labels:
- `model_even_review`
- `overpay_review`
- `underpay_review`
- `manual_market_check_required`
- `do_not_send_without_human_review`

Hard rules:
- Do not say “make this trade.”
- Use “review package shape” language only.
- Do not use ADP, market rank, projections, consensus, mocks, or big boards as private value.
- Do not create final trade recommendations.
- Do not mutate My Team, War Board, active rankings, readiness gates, or app promotion.
- If a package includes a player or pick with red source risk, label it `do_not_send_without_human_review`.
- If a package includes orange source-limited rows, include a source-risk warning.
- Missing pick baselines must block exact value-equivalent package math.

Suggested implementation:
1. Add service:
   - `src/services/model_v4_trade_package_builder_service.py`
2. Add script:
   - `scripts/build_model_v4_trade_package_builder.py`
3. Add tests:
   - `tests/test_model_v4_trade_package_builder_service.py`
4. Add app UI:
   - Draft Room or Trade Lab tab: `Trade Package Builder`
5. Generate outputs and docs.
6. Run focused tests, Ruff, and compile/static checks.

Acceptance tests:
- Every package row is review-only.
- No package row uses final recommendation language.
- No ADP/market/projection/rank/consensus leakage.
- Red source-risk packages are blocked from send language.
- Missing pick baseline blocks exact equivalent math.
- Package values sort by model value, not market value.
- Receipts/component rows exist for every package.

## Model v4.5 Cleanup Sprint - Audit Repair And Human Review Readiness

Purpose:
Address the external audit findings from `Model v4 Audit.docx` without rebuilding the formula or tuning to consensus rankings.

Sprint verdict target:
After these phases, Model v4.5 should be ready for human final decision review with a cleaner app workflow, clearer labels, and a fresh external audit packet.

Rules for every phase:
- Keep everything review-only.
- Do not mutate active rankings, My Team, War Board, readiness gates, or app promotion.
- Do not create final cut/keep/trade/draft recommendations.
- Do not use ADP, market rankings, projections, mock drafts, big boards, or consensus as private football value.
- Do not tune rankings merely to match consensus.
- Preserve legitimate model weirdness when it is supported by admitted evidence.
- Missing data remains missing.
- Historical outcomes and comps remain context-only.
- Run focused tests, Ruff, and compile/static checks where practical.

### v4.5 Phase 1 - Safety And Admission Validation Repair

Prompt:

```text
Model v4.5 / Phase 1: Safety And Admission Validation Repair

Goal:
Patch the audit-flagged Phase 11A guard-report issue around prospect_prior inputs so factual rookie age and factual NFL draft capital are explicitly admitted, validated, and documented.

Context:
- External audit verdict is ready with cautions.
- No critical blockers were found.
- Audit flagged a guard-report failure on current_prospect_input_admitted_only for two prospect_prior inputs.
- The suspected inputs are factual rookie age and factual NFL draft capital.
- These are allowed only if admitted through the formula contract and not treated as market/ranking/projection evidence.

Tasks:
1. Inspect Phase 11A formula contract, allowed-field registry, blocked-field registry, and loader guard report.
2. Locate prospect_prior loaders and tests.
3. Confirm how rookie age and factual NFL draft capital are currently admitted.
4. Patch the validation pipeline so:
   - factual rookie age is admitted only through its approved source/lane
   - factual NFL draft capital is admitted only through its approved source/lane
   - neither can be loaded through generic JSON slurping
   - neither is confused with market rank, ADP, projection, mock draft, big board, or consensus
5. Regenerate the relevant formula contract / guard report outputs if needed.
6. Add or update tests proving:
   - rookie age passes only through admitted source
   - draft capital passes only through admitted source
   - non-admitted prospect inputs fail closed
   - market/rank/projection fields remain blocked
7. Produce:
   - docs/model_v4/MODEL_V4_5_PHASE_1_SAFETY_ADMISSION_VALIDATION_REPAIR.md
   - updated guard report CSV if applicable

Constraints:
- Review-only only.
- No score tuning.
- No app promotion.
- No active rankings, My Team, or War Board changes.

Run:
- focused tests
- Ruff on touched files
- compile/static checks where practical

End with:
- files changed
- outputs regenerated
- test results
- verdict: guard issue repaired / still needs repair
```

### v4.5 Phase 2 - Decision UI Consolidation

Prompt:

```text
Model v4.5 / Phase 2: Decision UI Consolidation

Goal:
Make the app easier to use for human review by consolidating the new decision systems into a smaller, clearer workflow.

Context:
- External audit says the systems are useful but the UI has too many surfaces.
- The user wants a usable app, not a research lab with endless tabs.
- Do not remove underlying outputs; simplify the app surface.

Primary review flow:
1. Draft Room / Main Review:
   - Startup Slot
   - Pick Decision Lab
   - Why This Rank
   - Evidence & Risk
2. June 15 Review:
   - Cut Cost
   - Roster Pressure
   - Decision Board
3. Supporting context:
   - Historical Comps
   - Source Risk
   - Model Edge Queue
   - Receipts / Warnings

Tasks:
1. Inspect the Streamlit app pages for Draft Room, June 15 Review, Trade Lab, and related Model v4 pages.
2. Propose and implement a simplified tab/page structure:
   - Surface Startup Slot, Pick Decision Lab, Cut Cost, and Why This Rank first.
   - Merge Source Risk, Historical Comps, and Model Edge Queue into an `Evidence & Risk` supporting view where practical.
   - Keep receipts/warnings accessible but not first-screen clutter.
3. Rename user-facing labels:
   - Roster Opportunity Cost -> Cut Cost
   - Model Startup Slot -> Internal Slot
   - Evidence Status -> Trust
   - Source Risk Heatmap -> Evidence Risk
   - Model Edge Queue -> Model Edges
4. Add short plain-English helper copy where it reduces confusion, but do not turn the app into a tutorial wall.
5. Ensure all tables remain explicitly review-only.
6. Do not change formulas or generated values.
7. If app code changes are made, run app/static checks and verify the relevant pages open.
8. Produce:
   - docs/model_v4/MODEL_V4_5_PHASE_2_DECISION_UI_CONSOLIDATION.md

Constraints:
- No final recommendations.
- No active ranking/My Team/War Board mutation.
- No formula tuning.

Run:
- focused UI tests/static checks if available
- Ruff on touched files
- compile/static checks
- browser verification if practical

End with:
- new page/tab structure
- URL/page to inspect first
- test results
- verdict: UI ready for human review / needs patch
```

### v4.5 Phase 3 - Explainer De-Dupe And Context Clarity

Prompt:

```text
Model v4.5 / Phase 3: Explainer De-Dupe And Context Clarity

Goal:
Fix confusing duplicate player rows in human-facing explainers without losing useful context.

Context:
- External audit found some players appear multiple times in the Player Rank Explainer because they exist in multiple review contexts.
- This is technically valid but confusing for human review.

Tasks:
1. Inspect player rank explainer rows, component rows, warnings, and UI rendering.
2. Identify duplicate player rows caused by multiple contexts:
   - rookie board context
   - startup slot context
   - roster context
   - current value context
3. Implement a clear human-facing strategy:
   - either collapse duplicate player rows into one primary row with context chips
   - or keep context rows but label them clearly as separate contexts
4. Preferred:
   - one main row per player in the default table
   - expandable context details for alternate contexts
5. Ensure component receipts are preserved.
6. Add tests proving:
   - top-50 rookie default explainer has no confusing duplicate rows
   - duplicate contexts are not discarded
   - every displayed explanation still traces to admitted components/warnings
7. Regenerate:
   - player_rank_explainer_rows.csv
   - player_rank_explainer_component_rows.csv
   - player_rank_explainer_warnings.csv
8. Produce:
   - docs/model_v4/MODEL_V4_5_PHASE_3_EXPLAINER_DEDUPE_CONTEXT_CLARITY.md

Constraints:
- Review-only.
- No formula changes.
- No active app mutation.
- Do not hide source warnings.

Run:
- focused tests
- Ruff on touched files
- compile/static checks

End with:
- de-dupe strategy used
- regenerated output paths
- test results
- verdict: explainer clear / needs patch
```

### v4.5 Phase 4 - 5.04 Baseline Handling

Prompt:

```text
Model v4.5 / Phase 4: 2026 5.04 Baseline Handling

Goal:
Resolve or clearly quarantine the missing 2026 5.04 pick baseline so the user cannot misunderstand it during final review.

Context:
- External audit says 5.04 remains missing/manual-only.
- This is safe but needs clearer handling before human final decision review.

Decision options:
1. Conservative baseline:
   - derive a low-confidence review-only baseline from admitted pick curve / late pick history if available
   - label it conservative_manual_review_baseline
2. Manual-only quarantine:
   - keep exact baseline missing
   - make UI and outputs clearly say manual-only, no exact model equivalent

Tasks:
1. Inspect pick value baselines, pick defer rows, startup slot pick-zone rows, and rookie pick decision lab rows.
2. Determine whether an admitted conservative baseline can be derived without market/ADP/rank/projection leakage.
3. If yes:
   - create conservative review-only 5.04 baseline
   - label low confidence
   - include receipt and warning
4. If no:
   - keep 5.04 quarantined
   - make every affected row and UI table explicitly say:
     `manual_only_no_exact_model_baseline`
5. Update affected outputs:
   - startup slot pick-zone rows
   - rookie pick decision lab rows
   - roster opportunity/cut cost pick equivalents if applicable
   - June 15 decision board if applicable
6. Add tests proving:
   - missing baseline is not silently filled with zero/average
   - 5.04 cannot create exact trade/draft/cut equivalence unless admitted baseline exists
   - UI labels make manual-only status visible
7. Produce:
   - docs/model_v4/MODEL_V4_5_PHASE_4_504_BASELINE_HANDLING.md

Constraints:
- No market/ADP/ranking/projection leakage.
- No fake precision.
- Review-only only.
- No final recommendations.

Run:
- focused tests
- Ruff on touched files
- compile/static checks

End with:
- chosen handling: conservative baseline / manual-only quarantine
- affected output paths
- test results
- verdict: 5.04 clear for human review / needs patch
```

### v4.5 Phase 5 - Clean Naming And Warning Cleanup

Prompt:

```text
Model v4.5 / Phase 5: Clean Naming And Warning Cleanup

Goal:
Make labels, warning text, and table columns human-readable and consistent across Draft Room, June 15 Review, and new decision systems.

Context:
- External audit found minor naming inconsistency and warning overload.
- The user wants to understand the app without decoding internal function names.

Tasks:
1. Inventory user-facing labels and warnings across:
   - Startup Slot Simulator
   - Cut Cost / Roster Opportunity Cost
   - Rookie Pick Decision Lab
   - Historical Similarity
   - Player Rank Explainer
   - Evidence Risk / Source Risk Heatmap
   - Model Edges / Model Edge Queue
   - Rookie Draft Board
2. Create a label mapping for UI display:
   - `allowed_use` -> `Use`
   - `blocked_use` -> `Blocked`
   - `confidence_cap` -> `Trust Cap`
   - `market_share_score` -> `College Team Share`
   - `draft_capital_score` -> `NFL Draft Pick Signal`
   - `source_risk_level` -> `Evidence Risk`
   - `model_edge_weirdness` -> `Model Edge`
   - `source_shape_warning` -> `Data Shape Warning`
   - `format_discipline_case` -> `Format Discipline`
3. Summarize repeated warnings into plain-English warning groups:
   - Data incomplete
   - Low draft investment
   - No-premium TE caution
   - 1QB QB caution
   - Source-limited role data
   - Manual review required
4. Preserve raw warning codes in drilldowns or exports.
5. Make default app tables use clean labels.
6. Add tests or static checks proving:
   - raw warning codes are still available
   - display labels do not alter underlying values
   - no final recommendation language appears
7. Produce:
   - docs/model_v4/MODEL_V4_5_PHASE_5_CLEAN_NAMING_WARNING_CLEANUP.md

Constraints:
- No formula changes.
- No score changes.
- Review-only only.
- No active app mutation.

Run:
- focused tests/static checks
- Ruff on touched files
- compile/static checks
- browser check if practical

End with:
- label changes
- warning group changes
- test results
- verdict: naming clear / needs patch
```

### v4.5 Phase 6 - Final Audit Packet And Audit Page

Prompt:

```text
Model v4.5 / Phase 6: Final Audit Packet And Audit Page

Goal:
Package the Model v4.5 cleanup sprint for external audit and create a concise audit/readiness page for the app or docs.

Context:
- Phases 1-5 repaired audit cautions:
  - safety/admission validation
  - UI consolidation
  - explainer de-dupe
  - 5.04 handling
  - clean naming and warning cleanup
- This phase should not implement new model logic.

Tasks:
1. Produce a concise Model v4.5 readiness/audit page:
   - preferred app page or doc: `docs/model_v4/MODEL_V4_5_FINAL_AUDIT_READINESS_PAGE.md`
   - include what changed, what remains review-only, what to inspect first, known cautions, and test results.
2. Package an external audit zip with no more than 20 files.
3. Include:
   - v4.5 phase docs
   - formula contract
   - updated guard report if available
   - key decision outputs
   - cleaned UI/readiness doc
   - relevant rookie board / pick lab / startup slot / cut cost / explainer / source risk / model edge rows
4. Write a neutral audit prompt asking whether:
   - the v4.5 fixes resolved the prior audit cautions
   - guard/admission validation is now safe
   - UI workflow is understandable
   - duplicate explainer contexts are clear
   - 5.04 is safely handled
   - naming/warnings are human-readable
   - review-only and no-market-leakage constraints still hold
   - the model is ready for human final decision review
5. Produce:
   - `docs/model_v4/MODEL_V4_5_EXTERNAL_AUDIT_PROMPT.md`
   - `local_exports/model_v4/audit_packets/model_v4_5_cleanup_audit_YYYYMMDD.zip`

Constraints:
- No new recommendations.
- No app promotion.
- No active rankings/My Team/War Board mutation.
- Keep packet to 20 files max.

Run:
- focused tests/static checks if any files changed
- verify zip file count

End with:
- audit page path
- audit prompt path
- zip path
- file count
- test results
- verdict: ready for external audit / needs repair
```

## Model v4.6 Post-Audit Usability Sprint - Five Prompt Queue

Purpose:
Address the non-blocking findings from `Model v4 Audit (1).docx` after the v4.5 cleanup sprint. The audit verdict was ready for human final decision review, so these prompts are usability, readability, and export-clarity improvements only.

Rules for every prompt:
- Keep everything review-only.
- Do not mutate active rankings, My Team, War Board, readiness gates, or app promotion.
- Do not create final cut/keep/trade/draft recommendations.
- Do not use ADP, market rankings, projections, mock drafts, big boards, or consensus as private football value.
- Do not tune rankings to match consensus.
- Preserve legitimate model weirdness when supported by admitted evidence.
- Missing data remains missing.
- Run focused tests, Ruff, and compile/static checks where practical.

### v4.6 Prompt 1 - Guided Human Review Flow

Prompt:

```text
Model v4.6 / Prompt 1: Guided Human Review Flow

Goal:
Add a lightweight, review-only guided flow so a first-time user knows exactly what to inspect first without decoding every tab.

Context:
- The v4.5 audit says the system is ready, but the workflow may still feel heavy.
- Draft Room currently spans Internal Slot, Pick Decision Lab, Prospect Board, explainers, Evidence & Risk, scout/research, and receipts.
- June 15 Review should focus first on the top-five drop decision, then pick/roster review and Cut Cost.

Tasks:
1. Inspect the Draft Room and June 15 Review Streamlit pages.
2. Add a concise "Start Here" / progress-style review guide for:
   - Draft Room
   - June 15 Review
3. The guide should show:
   - Step number
   - What to inspect
   - Why it matters
   - Which tab/table to open
   - What decision the human needs to make later
4. Do not add final recommendations.
5. Keep helper copy short and practical.
6. Add tests/static checks if page helpers or display helpers are changed.
7. Produce:
   - `docs/model_v4/MODEL_V4_6_GUIDED_HUMAN_REVIEW_FLOW.md`

Acceptance checks:
- Draft Room clearly tells the user where to start.
- June 15 Review clearly calls out top-five drop review before supporting tables.
- All language remains review-only.
- No active app data is mutated.
```

### v4.6 Prompt 2 - Evidence Risk Export Consolidation

Prompt:

```text
Model v4.6 / Prompt 2: Evidence Risk Export Consolidation

Goal:
Make Evidence Risk CSV exports easier to read by clarifying why some players have multiple source-risk rows.

Context:
- The audit says duplicate player names in `source_risk_player_rows.csv` are expected because separate rows track different evidence modules.
- This is safe, but confusing for analysts reading raw CSVs.

Tasks:
1. Inspect:
   - `local_exports/model_v4/source_risk_heatmap/latest/source_risk_player_rows.csv`
   - `source_risk_feature_rows.csv`
   - source risk service/tests
   - Evidence Risk UI rendering
2. Add or regenerate a consolidated player-level export:
   - `local_exports/model_v4/source_risk_heatmap/latest/source_risk_player_summary_rows.csv`
3. Preserve module-level rows for audit.
4. The summary export should include one row per player with:
   - player_name
   - position
   - model_score
   - worst_source_risk_level
   - evidence_modules_present
   - evidence_modules_missing_or_partial
   - biggest_source_risk
   - warning_summary
   - raw_module_row_count
   - allowed_use
   - blocked_use
5. Update docs to explain that duplicate names in module-level rows are expected.
6. Add tests proving:
   - module-level rows are preserved
   - summary rows are one row per player
   - missing data stays missing
   - no market/ranking/projection leakage
7. Produce:
   - `docs/model_v4/MODEL_V4_6_EVIDENCE_RISK_EXPORT_CONSOLIDATION.md`

Acceptance checks:
- Raw evidence detail is not lost.
- Human-facing summary is one row per player.
- Documentation explains duplicate module rows.
```

### v4.6 Prompt 3 - Pick Equivalent Field Cleanup

Prompt:

```text
Model v4.6 / Prompt 3: Pick Equivalent Field Cleanup

Goal:
Split long pick-equivalent strings into cleaner fields so 2026 5.04 manual-only handling is visible without creating hard-to-read table text.

Context:
- The audit says the 5.04 handling is safe.
- It also says roster opportunity/cut-cost rows append long phrases like `manual_only_no_exact_model_baseline` into pick-equivalent fields.
- This is clear but clunky.

Tasks:
1. Inspect Cut Cost / roster opportunity cost outputs and UI:
   - `local_exports/model_v4/roster_opportunity_cost/latest/roster_opportunity_cost_rows.csv`
   - June 15 Review Cut Cost table
2. Split pick equivalent display into clearer fields:
   - `rookie_pick_equivalent`
   - `pick_baseline_status`
   - `pick_equivalent_confidence`
   - `pick_equivalent_warning`
3. Keep 2026 5.04 exact equivalence blocked unless an admitted baseline exists.
4. Preserve existing warning flags and blocked_use language.
5. Update downstream displays that show pick equivalents.
6. Add tests proving:
   - 5.04 remains manual-only/no exact model baseline
   - missing baseline is not filled with zero or average
   - exact cut/trade/draft equivalence remains blocked
   - display fields are cleaner but underlying safety is unchanged
7. Produce:
   - `docs/model_v4/MODEL_V4_6_PICK_EQUIVALENT_FIELD_CLEANUP.md`

Acceptance checks:
- Cut Cost rows are easier to scan.
- 5.04 remains safely quarantined.
- No final cut/keep recommendation appears.
```

### v4.6 Prompt 4 - Warning Code Dictionary And Display Map

Prompt:

```text
Model v4.6 / Prompt 4: Warning Code Dictionary And Display Map

Goal:
Create a warning-code dictionary so external auditors and the user can understand raw warning strings without losing audit precision.

Context:
- Phase 5 grouped warnings in the UI.
- The v4.5 audit says raw exports still contain codes like `red_manual_review|gray_missing`, which are necessary but hard to interpret.

Tasks:
1. Inventory warning codes from:
   - source risk outputs
   - model edge outputs
   - player rank explainer warnings
   - rookie draft board warnings
   - cut cost warnings
   - pick decision lab warnings
2. Produce:
   - `local_exports/model_v4/warning_dictionary/latest/warning_code_dictionary.csv`
   - `local_exports/model_v4/warning_dictionary/latest/warning_group_display_map.csv`
   - `docs/model_v4/MODEL_V4_6_WARNING_CODE_DICTIONARY.md`
3. Each dictionary row should include:
   - raw_warning_code
   - warning_group
   - plain_english_meaning
   - why_it_matters
   - human_review_action
   - severity_hint
   - allowed_use
   - blocked_use
4. Update UI helpers if a central display map already exists.
5. Preserve raw warning codes in exports and drilldowns.
6. Add tests proving:
   - every displayed warning group maps to at least one raw code
   - raw codes remain available
   - warning text does not create final recommendations
   - no market/projection/ranking leakage

Acceptance checks:
- Auditors can decode raw warnings.
- UI can show plain-English warning groups.
- Raw audit precision is preserved.
```

### v4.6 Prompt 5 - Final Human Review Brief

Prompt:

```text
Model v4.6 / Prompt 5: Final Human Review Brief

Goal:
Create a concise final human review brief that tells the user what to look at tonight and what still requires manual judgment.

Context:
- The audit verdict is `ready_for_human_final_decision_review`.
- Remaining issues are non-blocking:
  - workflow may still feel heavy
  - evidence-risk raw exports may show expected duplicate module rows
  - 5.04 is manual-only/no exact model baseline
  - raw warning codes need a dictionary
  - high evidence-risk/model-edge players need human attention

Tasks:
1. Read the latest v4.5/v4.6 docs and outputs.
2. Produce:
   - `docs/model_v4/MODEL_V4_6_FINAL_HUMAN_REVIEW_BRIEF.md`
   - optional CSV: `local_exports/model_v4/final_human_review/latest/final_human_review_checklist.csv`
3. The brief should include:
   - what to review first
   - top surfaces to trust
   - surfaces that are context-only
   - known cautions
   - specific attention list for 5.04, high evidence risk, model edges, TE/QB discipline, and top-five drop decision
   - explicit review-only/no-final-recommendation reminder
4. Do not create final roster/draft/trade recommendations.
5. Do not mutate app state or active rankings.
6. Run static checks if any code changes are made.

Acceptance checks:
- The brief is short enough for a user to actually read before reviewing.
- It points to the correct app pages and output files.
- It does not tell the user what final decision to make.
```

## Model v4.7 Post-v4.6 Audit Polish Queue

Purpose:
Address the non-blocking findings from `Model v4 Audit (2).docx`. The audit verdict was `ready_for_human_final_decision_review`, so these are polish and workflow-compression prompts only. Do not treat this as formula repair.

Rules for every prompt:
- Keep everything review-only.
- Do not mutate active rankings, My Team, War Board, readiness gates, or app promotion.
- Do not create final cut/keep/trade/defer/draft recommendations.
- Do not use ADP, market rankings, projections, mock drafts, big boards, or consensus as private football value.
- Do not tune rankings to consensus.
- Preserve legitimate model weirdness when supported by admitted evidence.
- Missing data remains missing.
- Run focused tests, Ruff, and compile/static checks where practical.

### v4.7 Prompt 1 - Review Progress Indicator And Collapsible Workflow

Prompt:

```text
Model v4.7 / Prompt 1: Review Progress Indicator And Collapsible Workflow

Goal:
Reduce first-time user overwhelm by turning the v4.6 guided flow into a clearer progress-style review checklist inside the app.

Context:
- v4.6 audit verdict: ready_for_human_final_decision_review.
- High-priority non-blocking issue: guided review flow is improved but still complex.
- The app should help the user know what to inspect first without adding final recommendations.

Tasks:
1. Inspect Draft Room and June 15 Review guided-flow sections.
2. Add a compact progress/checklist-style guide for:
   - Draft Room
   - June 15 Review
3. Use collapsible sections so the first view stays calm:
   - Start Here
   - Main Review
   - Supporting Context
   - Receipts / Advanced
4. Make each step show:
   - step number
   - page/table to open
   - why it matters
   - human question to answer later
5. Do not store completion state unless it is local/session-only and cannot mutate app data.
6. Do not create final recommendations.
7. Produce:
   - `docs/model_v4/MODEL_V4_7_REVIEW_PROGRESS_INDICATOR.md`

Acceptance checks:
- Draft Room and June 15 Review are easier to scan.
- Supporting layers are not first-screen clutter.
- All language remains review-only.
- No My Team, War Board, active ranking, readiness, or promotion mutation.
```

### v4.7 Prompt 2 - Evidence Risk Severity Labels

Prompt:

```text
Model v4.7 / Prompt 2: Evidence Risk Severity Labels

Goal:
Add plain severity labels to Evidence Risk summary exports so offline CSV review is easier.

Context:
- v4.6 audit says Evidence Risk consolidation works.
- Non-blocking issue: `worst_source_risk_level` uses codes like `red_manual_review` and `orange_source_limited`; the CSV could include a simple severity label.

Tasks:
1. Inspect:
   - `source_risk_player_summary_rows.csv`
   - source risk heatmap service/tests
   - Draft Room Evidence & Risk display
2. Add columns to the player summary export:
   - `severity_label`
   - `severity_rank`
   - `human_review_priority`
3. Suggested mapping:
   - `red_manual_review` -> `High`, rank 1
   - `orange_source_limited` -> `Medium-high`, rank 2
   - `yellow_partial` -> `Medium`, rank 3
   - `gray_missing` -> `Manual context`, rank 4
   - `green_complete` -> `Low`, rank 5
4. Update the UI display to show severity label beside Evidence Risk.
5. Preserve raw risk codes.
6. Add tests proving:
   - every summary row has a severity label
   - raw `worst_source_risk_level` remains available
   - missing data remains missing
   - no market/projection/ranking leakage
7. Produce:
   - `docs/model_v4/MODEL_V4_7_EVIDENCE_RISK_SEVERITY_LABELS.md`

Acceptance checks:
- Offline Evidence Risk review is easier.
- Raw audit precision is preserved.
- No formula or score changes.
```

### v4.7 Prompt 3 - Warning Dictionary Module Links

Prompt:

```text
Model v4.7 / Prompt 3: Warning Dictionary Module Links

Goal:
Upgrade the warning dictionary so each warning code points to the module/export where it appears and explains what receipt to inspect.

Context:
- v4.6 audit says the warning dictionary works.
- Medium/low issue: some warning codes still require cross-reference; dictionary could link directly to relevant module/evidence description.

Tasks:
1. Inspect:
   - `warning_code_dictionary.csv`
   - `warning_group_display_map.csv`
   - warning dictionary service/tests
   - source files listed in `source_files`
2. Add fields:
   - `primary_module`
   - `primary_export`
   - `receipt_or_drilldown_to_open`
   - `example_review_question`
3. Infer `primary_module` conservatively from source file path:
   - source_risk_heatmap
   - model_edge_queue
   - player_rank_explainer
   - rookie_draft_review
   - roster_opportunity_cost
   - rookie_pick_decision_lab
4. Preserve raw warning codes and source file list.
5. Add tests proving:
   - every dictionary row has a module or `multiple_modules`
   - raw warning codes remain available
   - warning text does not become a final recommendation
6. Produce:
   - `docs/model_v4/MODEL_V4_7_WARNING_DICTIONARY_MODULE_LINKS.md`

Acceptance checks:
- Auditors can trace warning codes to a useful output.
- User can tell which table to open next.
- No formula or value changes.
```

### v4.7 Prompt 4 - Pick Decision Lab Manual Question Cleanup

Prompt:

```text
Model v4.7 / Prompt 4: Pick Decision Lab Manual Question Cleanup

Goal:
Split long Pick Decision Lab manual questions into structured, scannable fields.

Context:
- v4.6 audit says Pick Decision Lab is useful.
- Medium/low issue: `manual_questions` can contain long paragraphs that clutter exports.

Tasks:
1. Inspect:
   - `rookie_pick_decision_lab/latest/pick_decision_rows.csv`
   - rookie pick decision lab service/tests
   - Draft Room Pick Decision Lab display
2. Preserve existing `manual_questions` if useful for backwards compatibility.
3. Add structured fields:
   - `manual_question_rookie_profile`
   - `manual_question_roster_fit`
   - `manual_question_pick_value`
   - `manual_question_trade_defer`
   - `manual_question_source_risk`
4. Keep labels review-only:
   - `manual_decision_required`
   - `review_candidate_cluster`
   - `review_value_gap`
5. Do not create final pick recommendations.
6. Add tests proving:
   - all owned picks still appear: 1.03, 1.04, 2.04, 2.08, 5.04
   - 5.04 remains manual-only/no exact baseline
   - structured question fields are present
   - no directive draft language appears
7. Produce:
   - `docs/model_v4/MODEL_V4_7_PICK_DECISION_MANUAL_QUESTION_CLEANUP.md`

Acceptance checks:
- Pick exports are easier to read.
- The human still makes the final decision.
- No active app mutation.
```

### v4.7 Prompt 5 - Raw Export Summary Index

Prompt:

```text
Model v4.7 / Prompt 5: Raw Export Summary Index

Goal:
Create a compact index of the large raw exports so human reviewers know which file to open first.

Context:
- v4.6 audit says extended raw exports are useful for transparency but can be time-consuming.
- This should be an index, not a replacement for raw data.

Tasks:
1. Inventory major review outputs:
   - Evidence Risk raw rows and summary rows
   - Model Edge rows
   - Warning dictionary rows
   - Pick Decision Lab rows
   - Cut Cost rows
   - Player Rank Explainer rows
   - Startup Slot rows
   - Rookie Draft Board rows
2. Produce:
   - `local_exports/model_v4/export_summary/latest/export_summary_index.csv`
   - `docs/model_v4/MODEL_V4_7_RAW_EXPORT_SUMMARY_INDEX.md`
3. Each index row should include:
   - `export_name`
   - `path`
   - `row_count`
   - `primary_use`
   - `review_first_when`
   - `key_columns`
   - `review_only_status`
   - `raw_or_summary`
4. Add tests or static checks proving:
   - listed files exist
   - row counts are populated
   - review-only status is explicit
5. Do not modify underlying model outputs.

Acceptance checks:
- User can find the right export quickly.
- Raw exports remain available.
- No recommendations or formula changes.
```

### v4.7 Prompt 6 - v4.7 Audit Packet

Prompt:

```text
Model v4.7 / Prompt 6: v4.7 Audit Packet

Goal:
Package the v4.7 polish work for an optional external audit after prompts 1-5 are complete.

Tasks:
1. Package no more than 20 files.
2. Include:
   - v4.7 docs
   - v4.6 final human review brief
   - final checklist
   - Evidence Risk summary
   - warning dictionary
   - Pick Decision Lab rows
   - export summary index
   - formula contract / loader guard report
3. Write a neutral audit prompt asking whether:
   - v4.7 improved usability without changing formulas
   - review-only constraints still hold
   - Evidence Risk severity labels help
   - warning dictionary module links help
   - Pick Decision Lab questions are clearer
   - export index is useful
   - no market/projection/ranking leakage exists
4. Produce:
   - `docs/model_v4/MODEL_V4_7_EXTERNAL_AUDIT_PROMPT.md`
   - `local_exports/model_v4/audit_packets/model_v4_7_polish_audit_YYYYMMDD.zip`
5. Verify zip file count is 20 or fewer.

Acceptance checks:
- Packet is audit-ready.
- Prompt is neutral.
- No app promotion or final recommendations.
```
