# Artifact Manifest

Verdict: `YELLOW_DRAFTED_ONLY_FEATURE_POLICY_SAFE_UPGRADE`

Branch: `work/lane-rookie-outcomes-upgrade-20260630`

Worktree: `C:\NWR\Niners-War-Room-lane-rookie-outcomes-upgrade-20260630`

Base HEAD checked before implementation: `e598249a2a9915366fc2087991bb0519be7c8403`

This packet implements the safe-now policy/spec portion of the Rookie Outcomes drafted-only safe-upgrade lane. It does not train, tune, score, app-wire, release, or approve active rookie outcome columns.

## Inputs Used

| Input | Purpose | Review-only status |
|---|---|---|
| `NWR_DEEP_RESEARCH_05_ROOKIE_OUTCOMES_20260630.md` from the handoff zip | Findings and recommended classifications | Research input only |
| `docs/hq/rookie_model/rookie_entry_status_hygiene_v1_20260630/historical_rookie_entry_status_v1.csv` | Entry-status counts and drafted-only boundary | review-only |
| `docs/hq/rookie_model/rookie_outcome_drafted_only_review_v1_20260630/drafted_only_outcome_player_audit.csv` | Drafted-only coverage counts | review-only |
| `docs/hq/rookie_outcomes/udfa_review_application_v1_20260630/rookie_display_artifact_v5_coverage_matrix.csv` | Current display/UDFA status counts | review-only/display-only |
| `docs/hq/rookie_model/rookie_source_availability_reconciliation_20260630/source_availability_matrix.csv` | Depth-chart and UDFA/CFBD source-policy status | review-only policy |

## Output Artifacts

| Artifact | Rows | Purpose | Status |
|---|---:|---|---|
| `rookie_outcomes_safe_upgrade_status_matrix.csv` | 10 | Classifies RO-001 through RO-010 recommendations | review-only/spec |
| `drafted_only_admission_gate_contract.csv` | 6 | Machine-readable drafted-only gate contract | review-only/spec |
| `gate_e_feature_policy_manifest.csv` | 31 | Reconciles the nine replay-service fields, six Gate E features, and blocked candidates | review-only/spec |
| `label_source_partition_matrix.csv` | 5 | Separates Outcome V2, model_v4/RotoWire, nflverse sidecar, CFBD, and display gaps | review-only/spec |
| `artifact_manifest.md` | n/a | This manifest | docs-only |
| `deep_research_intake_summary.md` | n/a | Research intake and classification | docs-only |
| `drafted_only_admission_gate_contract.md` | n/a | Human-readable admission gate | docs-only |
| `synthetic_draft_capital_quarantine_policy.md` | n/a | Round/pseudo-capital quarantine | docs-only |
| `label_source_partition_policy.md` | n/a | Label-source policy | docs-only |
| `historical_replay_leakage_guardrail.md` | n/a | Replay leakage controls | docs-only |
| `depth_chart_source_reaudit.md` | n/a | Current depth-chart source status | docs-only |
| `udfa_cfbd_blocker_update.md` | n/a | UDFA/CFBD blockers | docs-only |
| `gate_f_display_artifact_policy.md` | n/a | Gate F display-only policy | docs-only |
| `gate_g_blocker_policy.md` | n/a | Gate G blocker policy | docs-only |
| `next_safe_upgrade_plan.md` | n/a | Safe/WAIT/model-gate/blocked plan | docs-only |
| `codex_final_work_order.md` | n/a | Work-order receipt | docs-only |
| `merge_safety_report.md` | n/a | Guardrail merge receipt | docs-only |
| `README.md` | n/a | Folder overview | docs-only |

## Key Counts

- Historical entry-status rows: `4653`
- Historical drafted rows: `1999`
- Historical likely UDFA / needs-review rows: `2514`
- Historical confirmed UDFA rows: `0`
- Drafted-only review audit rows: `1999`
- Drafted rows with any label linkage: `897`
- Rookie-year labels: `818`
- 2Y labels: `737`
- 3Y labels: `501`
- 5Y labels: `319`
- Current display V5 rows: `157`
- V5 review-only display-field rows: `117`
- V5 confirmed UDFA review-only status rows: `28`
- V5 Not enough information rows: `10`
- V5 wrong-universe blocked rows: `2`

## What This Packet Approves

- Drafted-only review-only policy/spec work.
- Positive `draft_picks` evidence as the drafted-only admission contract.
- Conservative display-only/review-only label-source partitioning.
- Guardrail tests for no model/training/source-truth promotion.

## What This Packet Does Not Approve

- Active rookie probabilities.
- Gate G.
- Rankings, Player Compare, Live Draft Room, or Gate F/G app behavior.
- Model/training/source-truth use.
- UDFA modeling or UDFA inference from draft absence.
- CFBD as model input or training truth.
- Fake round 8, fake T12/T24/T36, or missing-as-zero output.
