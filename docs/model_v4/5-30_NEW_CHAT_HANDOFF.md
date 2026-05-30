# Niners War Room New-Chat Handoff

Date: 2026-05-30

Repo: `C:\Dev\niners-war-room`

Repair packet:
`C:\Users\codex-agent\Documents\When Low on Rate Limits\niners_model_repair_hq\niners_war_room_codex_ready_packet`

Current mode: paused / inspect-and-repair only.

Do not recalibrate football until score routing, source disclosure, and UI language are safe.

## 1. Current Repo Status

The repo is not in a clean git state. There are many modified and untracked files across app pages, services, docs, scripts, tests, configs, sample data, and generated Model v4 exports. Before any broad commit, inspect and stage intentionally.

Important dirty-state note:

- This handoff file is new and can be committed by itself if desired.
- The broader tree contains months of accumulated project work. Do not run a blind `git add .` unless the user explicitly wants to preserve the entire current workspace snapshot.
- Moving to a new chat does not require a commit because the new chat can read the same filesystem, but a small checkpoint commit for this handoff doc is safe if the user wants an anchor.

Current known blocker:

The app may be silently mixing:

- legacy active-pack values,
- Model v4 review values,
- market context,
- rookie pick baselines,
- startup-slot context,
- recommendation-like UI labels.

This makes the UI look cleaner than before, but the displayed "Model Value" and trade/draft labels may still be wrong or misleading.

## 2. Non-Negotiable Guardrails

Project format:

- 10-team dynasty
- 1QB
- non-PPR
- rushing/receiving first-down scoring
- no TE premium
- deep benches
- 23 keepers
- forced league-rank top-five release rule

Model philosophy:

- Outputs are review-only.
- Do not create final trade, cut, keep, or draft recommendations.
- Market, ADP, rankings, projections, mock drafts, startup context, consensus, and trade calculators are display-only context.
- Market context must not drive private football value, primary review score, default sort, review bands, pick labels, or trade labels.
- Weird rankings are allowed only when the admitted evidence path is clean and traceable.
- Missing evidence stays missing.
- Legacy scores may be shown only as clearly labeled comparison context.

Do not change:

- formula weights,
- veteran age curves,
- rookie weights,
- pick baselines,
- VORP,
- replacement formulas,
- market-gap thresholds,
- confidence cap magnitudes,
- startup-slot conversion,
- active rankings,
- My Team,
- War Board,
- readiness gates,
- app promotion behavior.

## 3. Implemented Work To Preserve

The project already has a large amount of useful Model v4 infrastructure. Preserve it and route it correctly before tuning.

Implemented/relevant surfaces and outputs include:

- Model v4 formula contract
- current player value checkpoint
- dynasty asset value rows
- rookie draft board review rows
- rookie pick candidate rows
- Startup Slot Simulator
- Roster Opportunity Cost Engine
- Rookie Pick Decision Lab
- Historical Similarity Engine
- Player Rank Explainer
- Source-Risk Heatmap
- Model Edge Queue
- human decision review prep
- June 15 review board
- source registry / source firewall work
- RotoWire factual import tooling
- nflverse/Sleeper data plans and partial ingestion work
- UI human-review repair passes

Important canonical Model v4 outputs:

- Current-player review source:
  `local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv`
  primary score column:
  `checkpoint_review_score`

- Cross-asset review source:
  `local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv`
  primary score column:
  `dynasty_asset_value_review_score`

- Legacy active-pack source to quarantine:
  `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks/model_outputs.csv`
  legacy score column:
  `private_score`
  legacy model version:
  `veteran_lve_stats_first_v1_0_0`

## 4. Known Sentinel Failures

These are canaries for the next chat.

Keenan Allen:

- Legacy active-pack `private_score = 82.4`
- This is too high for current dynasty review and should not appear as primary Player Board Model Value.
- Newer Model v4 dynasty asset row is much lower, around the low 40s, with substantial warnings.

Darius Slayton:

- Legacy active-pack `private_score = 78.88`
- This should not appear as primary Player Board Model Value.
- He may be absent or mismatched in newer Model v4 rows, which should fail closed rather than silently falling back to legacy.

If either Keenan `82.4` or Darius `78.88` appears as primary model value in the Player Board, the routing fix is not done.

## 5. Latest Inspect-Only Verdict

The last inspect-only pass found:

- Repo is at risk of legacy `private_score` leakage.
- Repo is at risk of market leakage in old trade/market surfaces.
- Repo still uses recommendation-like language.
- Safest first patch is a shared score-envelope/source-disclosure schema, followed by legacy active-pack quarantine.

High-risk files and paths:

- `app/pages/05_rankings.py`
  - Player Board reads active-pack `private_score`.
  - It sorts, filters, and displays this value as "Model Value".

- `src/config/constants.py`
  - Default data pack still points to `local_exports/data_packs/lve_sleeper_20260505_pdf_ranks`.

- `src/services/trade_service.py`
  - Old trade service uses `private_score`, `market_edge_score`, and buy/desirability labels.

- `src/services/market_gap_service.py`
  - Market gap creates `application_hint`, including `trade_for_candidate_review`.

- `app/pages/04_trade_central.py`
  - Still uses visible copy such as Trade Review, Buy Targets, Sell Candidates, target, and edge.

- `src/services/model_v4_sprint14c_trade_review_service.py`
  - Uses Model v4 dynasty asset scores, but still frames rows as trade-for/target context and selects top 35 external assets.

- `src/services/model_v4_startup_slot_simulator_service.py`
  - Creates hidden `_source_file` and `_score_field`, then removes them before export.

- `src/services/model_v4_rookie_pick_decision_lab_service.py`
  - Neutral pick rows can emit defer/trade labels without explicit comparison mode gating.

## 6. Report-To-Task Crosswalk

Use this as the research-to-work bridge.

| Report / Audit / Research | Useful conclusion | Actionable task |
|---|---|---|
| `reference/5-28_MODEL_VALUE_RECALIBRATION_PAUSE_PACKET.md` | Do not tune formulas yet; first prove source routing. | Freeze formulas and implement score envelope/source disclosure. |
| `research_reports/09_final_acceptance_gate_report.md` | Current app is not ready for trust if legacy/market values can leak. | Add acceptance gate around legacy quarantine, market no-leakage, and UI language. |
| `implementation_specs/01_source_of_truth_cleanup_spec.md` | There must be one canonical source per surface. | Route Player Board to `checkpoint_review_score`; cross-asset views to `dynasty_asset_value_review_score`. |
| `implementation_specs/02_data_integrity_join_spec.md` | Joins must fail closed on duplicates/missing IDs. | Add join validation and warning/quarantine rows. |
| `implementation_specs/03_score_envelope_schema_spec.md` | Every score needs lineage. | Add `source_path`, `score_column`, `lineage_class`, `model_version`, `allowed_use`, `blocked_use`. |
| `implementation_specs/04_trade_review_external_asset_reviews_spec.md` | Trade Review is not a trade-target system. | Rename/reframe to External Asset Reviews. |
| `implementation_specs/05_rookie_pick_label_gating_spec.md` | Neutral pick boards cannot say all picks should trade/defer. | Add board-mode gating for pick labels. |
| `implementation_specs/06_ui_market_language_spec.md` | Copy should not imply recommendations. | Remove buy/sell/target/edge language from review surfaces. |
| `implementation_specs/07_regression_test_plan.md` | Current tests do not fully protect score routing. | Add test-first sequence for source routing and sentinels. |
| `implementation_specs/08_codex_patch_sequence.md` | Patch order matters. | Follow the 10-patch sequence below. |
| Deep research on source stack | Better data helps, but only with source firewall. | Add nflverse/Sleeper/RotoWire/CFBD as factual layers; keep market display-only. |
| Rookie replay audits | Model may be viable; backtest/outcomes were weak. | Do not tune rookie formulas until outcome coverage/universe definition are fixed. |
| UI audits | UI can be readable but still misleading if values are wrong. | Prioritize source disclosure and language cleanup over visual polish. |
| Reddit / dynasty market examples | Elite current assets are not equal to single early rookie picks. | Keep trade reality warnings; do not let startup slot imply one-for-one trade equivalence. |

## 7. Remaining Open Findings

Open source/value findings:

- Player Board is likely still reading the old active pack.
- Legacy `private_score` is still visible in several old services.
- Old trade and market services can still derive labels from market gaps.
- Several surfaces say "Model Value" without telling the user which score column and lineage produced it.
- Some Model v4 outputs create source metadata internally but do not export it.
- Name-normalized joins may silently match or miss players without failing closed.
- Some current players have missing ages or identity fields; missing should be visible, not patched with guesses.

Open UI/language findings:

- `Trade Review` should become `External Asset Reviews` or similar.
- `Buy Targets`, `Sell Candidates`, `Trade-For Candidate`, `target`, `edge`, `Buy`, `Avoid`, and similar terms should be removed from review-only surfaces.
- Global review-only banner should be present on decision pages:
  `Review-only surface. This page does not make automatic trade, cut, keep, or draft recommendations.`

Open rookie/pick findings:

- Draft Board / Pick Decision Lab should not imply every pick should be traded or deferred.
- Neutral pick board labels should be limited to:
  - `use_pick_review`
  - `hold_pick_value_context`
  - `manual_decision_required`
- Comparative labels should require an explicit comparison object.
- `5.04` should stay manual-only if no exact admitted model baseline exists.

Open model-confidence findings:

- Historical outcome labels and similarity comps are display-only.
- Missing historical outcomes are unknown, not misses.
- 2025 outcomes are immature / rookie-year-only.
- Do not use historical similarity or outcome buckets as hidden ranking features.

## 8. Existing Tests Worth Preserving

Relevant tests already exist:

- `tests/test_model_v4_formula_contract_service.py`
  - blocks market/projection/rank fields from formula loaders.

- `tests/test_model_v4_current_value_checkpoint_service.py`
  - verifies `checkpoint_review_score` and no market/projection/ADP rows used.

- `tests/test_model_v4_sprint14c_trade_review_service.py`
  - verifies review-only trade outputs, but still accepts target naming.

- `tests/test_model_v4_startup_slot_simulator_service.py`
  - verifies sorted startup rows and pick-zone guardrails.

- `tests/test_model_v4_rookie_pick_decision_lab_service.py`
  - verifies all Niners picks, 5.04 quarantine, no obvious ADP/projection/mock words.

- `tests/test_model_v4_roster_opportunity_cost_service.py`
  - verifies review-only opportunity cost rows.

- `tests/test_legacy_label_quarantine_service.py`
  - quarantines legacy action labels, but does not yet quarantine legacy score routing.

- `tests/test_model_v4_phase5_clean_display_language.py`
  - checks some clean copy, but does not fully cover Player Board / old Trade Review.

## 9. Missing Tests To Add

Add these before or during patches:

- `test_score_envelope_requires_source_path_score_column_model_version_lineage_class`
- `test_active_pack_private_score_is_renamed_legacy_active_pack_score`
- `test_legacy_active_pack_score_cannot_drive_primary_review_score`
- `test_player_board_uses_checkpoint_review_score_as_primary_value`
- `test_player_board_does_not_show_keenan_allen_82_4_as_primary_value`
- `test_player_board_does_not_show_darius_slayton_78_88_as_primary_value`
- `test_market_gap_application_hint_cannot_drive_primary_review_label`
- `test_trade_review_renamed_external_asset_reviews`
- `test_external_asset_reviews_have_no_buy_sell_target_terms`
- `test_neutral_pick_board_allows_only_use_hold_manual_labels`
- `test_startup_slot_exports_source_file_score_field_lineage`
- `test_join_fail_closed_on_duplicate_or_unmatched_player_identity`

## 10. Next Recommended Task Queue

Patch 1: shared score envelope / source disclosure schema

- Goal: every primary score gets declared lineage.
- Likely files: new score/source envelope service, tests, small adapters.
- Acceptance: rows expose `source_path`, `score_column`, `lineage_class`, `model_version`, `allowed_use`, `blocked_use`.

Patch 2: legacy active-pack quarantine

- Goal: `private_score` from old active packs becomes `legacy_active_pack_score`.
- Acceptance: legacy scores cannot drive primary review score, sort, labels, summaries, or pick/trade comparisons.

Patch 3: Player Board Model v4 source routing

- Goal: Player Board primary value comes from `current_player_value_review_rows.csv::checkpoint_review_score`.
- Acceptance: Keenan `82.4` and Darius `78.88` are not primary Model Value.

Patch 4: cross-asset source routing

- Goal: startup, roster opportunity, and pick lab use `dynasty_asset_value_review_score` where cross-asset comparison is needed.
- Acceptance: each row discloses source and blocks one-for-one trade equivalence.

Patch 5: market no-leakage gates

- Goal: market context cannot produce primary score, default sort, review band, pick label, or trade label.
- Acceptance: market/ADP/rank/projection/mock fields appear only in display-only sections.

Patch 6: join/warning fail-closed gates

- Goal: duplicate or unmatched identity joins produce warnings/quarantine instead of silent fallback.
- Acceptance: tests prove missing Darius-style rows do not fall back to legacy values.

Patch 7: rename Trade Review to External Asset Reviews

- Goal: remove buy/sell/target framing.
- Acceptance: UI and exports use neutral review-language.

Patch 8: rookie pick label mode gating

- Goal: neutral board cannot say every pick should trade/defer.
- Acceptance: neutral board emits only `use_pick_review`, `hold_pick_value_context`, `manual_decision_required`.

Patch 9: UI copy lint and score disclosure

- Goal: users can see what value they are looking at.
- Acceptance: each main table has visible score lineage and review-only language.

Patch 10: final sentinel regression gate

- Goal: lock the fix.
- Acceptance: Keenan/Darius sentinels pass, no market leakage tests fail, no banned UI terms remain on main review pages.

## 11. Paste-Ready Prompt For Next Codex Chat

```text
You are working on the Niners War Room dynasty fantasy football analyzer.

Repo:
C:\Dev\niners-war-room

First read this handoff:
C:\Dev\niners-war-room\docs\model_v4\5-30_NEW_CHAT_HANDOFF.md

Then inspect the Codex-ready repair packet:
C:\Users\codex-agent\Documents\When Low on Rate Limits\niners_model_repair_hq\niners_war_room_codex_ready_packet

Read at minimum:
1. README_CODEX_START_HERE.md
2. 00_PROJECT_GUARDRAILS.md
3. PACKET_MANIFEST.md
4. reference/5-28_MODEL_VALUE_RECALIBRATION_PAUSE_PACKET.md
5. research_reports/09_final_acceptance_gate_report.md
6. implementation_specs/01_source_of_truth_cleanup_spec.md
7. implementation_specs/02_data_integrity_join_spec.md
8. implementation_specs/03_score_envelope_schema_spec.md
9. implementation_specs/04_trade_review_external_asset_reviews_spec.md
10. implementation_specs/05_rookie_pick_label_gating_spec.md
11. implementation_specs/06_ui_market_language_spec.md
12. implementation_specs/07_regression_test_plan.md
13. implementation_specs/08_codex_patch_sequence.md
14. checklists/ACCEPTANCE_CRITERIA.md
15. checklists/INSPECTION_CHECKLIST.md

Current project mode:
Paused / inspect-and-repair only.

Do not tune formulas.
Do not change model weights, veteran age curves, rookie weights, pick baselines, VORP, replacement formulas, market-gap thresholds, confidence cap magnitudes, or startup-slot conversion.
Do not add ADP/rankings/projections/consensus/market/trade-calculator logic to private value.
Do not turn review labels into final trade/cut/keep/draft recommendations.
Do not mutate active rankings, My Team, War Board, readiness gates, or app promotion.

Known sentinel failures:
- Keenan Allen legacy active-pack private_score = 82.4 must not be primary Player Board Model Value.
- Darius Slayton legacy active-pack private_score = 78.88 must not be primary Player Board Model Value.

Canonical sources:
- Player Board current-player primary value should use:
  local_exports/model_v4/current_value/latest/current_player_value_review_rows.csv
  column: checkpoint_review_score
- Cross-asset review surfaces should use:
  local_exports/model_v4/dynasty_asset_value/latest/dynasty_asset_value_review_rows.csv
  column: dynasty_asset_value_review_score
- Legacy active-pack private_score may be shown only as legacy comparison context:
  local_exports/data_packs/lve_sleeper_20260505_pdf_ranks/model_outputs.csv

First task:
Start Patch 1 from the handoff: shared score envelope / source disclosure schema.

Before editing, briefly confirm:
1. current blocker,
2. canonical source-routing rules,
3. first patch scope,
4. tests you will add.

Then implement Patch 1 only.
Run focused tests.
End with changed files and test results.
```

## 12. Commit Guidance Before Moving Chats

Moving to a new chat does not require committing. The next chat can read the same files.

However, the worktree is heavily dirty. Recommended options:

Option A - safest for continuity:

- Commit only this handoff doc as a small checkpoint if the user wants a clean anchor.
- Do not stage the entire repo.

Option B - preserve everything:

- Create a broad WIP commit only if the user explicitly wants to snapshot the entire current workspace.
- Review `git status --short` first because there are many untracked generated files and docs.

Option C - no commit:

- Start the new chat and point it to this handoff.
- This is acceptable because the same workspace persists.

Recommended: do not commit the whole tree blindly. If committing before the move, commit only:

- `docs/model_v4/5-30_NEW_CHAT_HANDOFF.md`

