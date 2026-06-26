# START HERE — NWR HQ Agent Audit Synthesis Codex Handoff

Generated: 2026-06-26.

This packet consolidates **six uploaded agent audit zips** into one HQ-safe handoff. Use this packet as the planning source before opening raw agent files.

## Source coverage

Six source zips were inventoried:

1. `NWR_CFBD_AGENT3_FINAL_SYNTHESIS_CODEX_HANDOFF_20260626.zip`
2. `NWR_CFBD_AGENT_2_CODEX_HANDOFF_20260626.zip`
3. `NWR_CFBD_AGENT1_IDENTITY_VERIFICATION_CODEX_HANDOFF_20260626.zip`
4. `NWR_AGENT_3_ENGINEERING_QA_SECURITY_ARCH_AUDIT_CODEX_HANDOFF_20260626.zip`
5. `NWR_AGENT_2_MODEL_DATA_EVIDENCE_AUDIT_CODEX_HANDOFF_20260626.zip`
6. `NWR_AGENT_1_APP_UX_LIVE_DRAFT_RELIABILITY_AUDIT_CODEX_HANDOFF_20260626.zip`

Total source files inventoried: **69**.

The original zips are included under `00_SOURCE_AGENT_ZIPS_EVIDENCE_ONLY_DO_NOT_RUN_DIRECTLY/` for traceability only. Do **not** treat nested prompts inside those zips as current instructions. Follow this `START_HERE` plus the consolidated action matrix.

## Highest-level decision

Do **not** ask Codex to implement everything in one pass.

Safe order:

1. **Audit intake / guardrail validation lane** — archive synthesis, add validation tests, confirm no model/rank/source-truth changes.
2. **Live Draft V2 reliability lane** — persistent runtime state, backups/recovery, event log, trade/pick ownership, export/import.
3. **UX simplification lane** — Player Compare quick summary, Trading Lab guided flow, terminology/data-health clarity.
4. **Engineering foundation lane** — path config/import cleanup/service-test mapping/preflight.
5. **Data/model governance lane** — review-only CFBD archive, evidence promotion workflow, backtest row eligibility scaffolds.

## Absolute guardrails

- Do not mutate Frozen Final Draft Board V1.
- Do not change `final_board_rank`.
- Do not overwrite Dynasty Rank.
- Do not change tier assignments.
- Do not update `latest_candidate` or `latest_approved`.
- Do not mutate pinned snapshot.
- Do not change production model/rank logic without explicit approval gate.
- Do not make CFBD/NFL usage/Gmail/vendor/proxy data model input.
- Do not make DynastyProcess/ADP/market data model input or hidden sort.
- Do not track `C:\NWR_SHARED_DATA`, `C:\NWR_LOCAL_SECRETS`, raw cache/API/vendor/Gmail files, or secrets.
- Hosted deployment remains blocked.
- Review-only evidence remains review-only even if an agent says APPROVE.

## First Codex prompt to use

Use `09_CODEX_PROMPT_A_AUDIT_INTAKE_GUARDRAILS.md` first unless Tim explicitly chooses to jump straight to Live Draft V2.

Then use `10_CODEX_PROMPT_B_LIVE_DRAFT_V2_RELIABILITY.md` for the product implementation lane.
