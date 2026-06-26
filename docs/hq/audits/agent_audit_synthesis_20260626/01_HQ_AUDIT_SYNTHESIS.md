# NWR HQ Synthesis of Six Agent Audits

## Bottom line

All six agent audits point in the same direction: **NWR is strong as a local, review-gated draft-day tool, but the next real product risk is Live Draft V2 reliability, not model/ranking tuning.**

The safest strategy is:

1. Preserve and validate all audit evidence.
2. Keep model input and decision-page wiring blocked.
3. Build reload-safe Live Draft V2 runtime state and trade event support.
4. Add guardrail tests so review-only evidence cannot silently become model truth.
5. Defer hosted deployment until path/config, secrets, state, and preflight issues are fixed.

## What is actually done vs blocked

### Done / strong

- App pages exist and render in the current local workflow.
- Draft board/rank guardrails are clearly established.
- DynastyProcess market baseline is display-only and hidden by default.
- CFBD pull/artifacts/identity work exists as review-only infrastructure.
- Full Safe Refresh exists as review/status infrastructure.
- Evidence registry and review queues exist.
- Testing culture is stronger than typical for a fast-moving local project.

### Blocked / not done

- Model input remains blocked.
- Decision-page wiring remains blocked.
- CFBD/NFL usage promotion remains blocked.
- True routes/TPRR/YPRR remain blocked licensed-data gaps.
- Historical drop/draftable truth remains weak/proxy-heavy.
- Live Draft V2 reliability is not done.
- Hosted deployment remains blocked.

## Top confirmed faults across all audits

### P0: Live Draft state can be lost or reset

App Agent 1 and Engineering Agent 3 both identify runtime draft state as fragile. Missing/corrupt JSON can result in empty runtime state, and reload persistence/recovery is not hardened. This directly matches the real draft-day failure: drafted/picked state was lost on reload.

**HQ decision:** This is the top product implementation lane.

### P0: In-draft trade/pick ownership support is incomplete

The app did not support the real trade: 1.04 for a 2028 1st and 2.03. Agents recommend a draft event log, trade event schema, pick ownership updates, and post-draft audit trail.

**HQ decision:** Implement manual runtime-only trade events before any model/value trade engine.

### P0: Review-only evidence could become dangerous if promotion gates are weak

CFBD, NFL usage, Outcome, DynastyProcess, proxy drop lists, Gmail/vendor evidence, and inferred historical data are useful only if their flags are enforced. Agent 2’s core warning is that missingness, proxy evidence, market fields, and unlicensed/vendor fields must not leak into features or hidden sorts.

**HQ decision:** Add guardrail validators and blocked-field scanners before model work.

### P0: Local path and import hygiene block hosted/production readiness

Engineering Agent 3 found hard-coded Windows paths, page-level `sys.path` hacks, hard-coded row/hash expectations, local runtime assumptions, and weak secret/preflight handling.

**HQ decision:** Good engineering lane, but not a reason to enable hosted deployment yet.

### P1: App UX is too heavy under pressure

Player Compare and Trading Lab are useful but too dense for on-clock use. Refresh/Data Health is cluttered. Market baseline and terminology can mislead users.

**HQ decision:** Simplify UX after/alongside Live Draft V2 state reliability.

### P1: CFBD review results are useful but still review-only

Agent 3 final synthesis approves 4 identity links for review-only carry-forward, keeps 8 blocked, and marks 3 as needs-more-info. Agent 1 has additional supplemental review-only findings, including Kevin Coleman Jr. duplicate CFBD IDs that did not appear in Agent 3 final.

**HQ decision:** Archive all; only Agent 3 final is final synthesis for its 15 rows; Agent 1/2 supplemental outputs must not be lost or promoted.

## Main contradiction / nuance to preserve

### Agent 1 CFBD has more APPROVE rows than Agent 3 final

- Agent 1 reviewed 71 rows: APPROVE=11, REJECT=52, KEEP_BLOCKED=8.
- Agent 3 final synthesis has 15 rows: APPROVE=4, KEEP_BLOCKED=8, NEEDS_MORE_INFO=3.
- Agent 1 includes Kevin Coleman Jr. duplicate CFBD IDs as review-only supportable, but Agent 3 final does not include those as final approved links.

**HQ resolution:** Preserve Agent 1 output as supplemental review evidence. Do not promote Kevin Coleman Jr. automatically. Mark it de-dupe-needed / not final-human-approved.

### Some agent CSVs are malformed for direct import

Several whole-project CSVs have delimiter drift because text fields include unquoted commas. Their Markdown reports are readable and useful, but Codex should not blindly import the malformed CSVs.

**HQ resolution:** Source zips are evidence. Consolidated action matrix is the current implementation source.

## Recommended first three Codex lanes

### Lane 1 — Audit Intake + Guardrail Validation

Goal: preserve the six audits and add validation tests. This is safe and low-risk.

Deliverables:
- audit archive folder
- source manifest/checksum
- review-only flag tests for CFBD Agent 1/2/3
- blocked-field scanner
- missingness propagation tests
- raw/secret/local path tracked-file scan
- no model/rank/source-truth changes

### Lane 2 — Live Draft V2 Reliability

Goal: fix the failure that actually hurt the draft.

Deliverables:
- atomic runtime state writes
- timestamped backups/checkpoints
- corruption/missing-state recovery flow
- append-only draft event log
- manual trade events
- pick ownership changes
- save/load/export/import with preview
- post-draft audit recap
- reload/browser smoke tests

### Lane 3 — UX Simplification

Goal: make app usable under pressure.

Deliverables:
- Player Compare quick decision summary
- Trading Lab stepper/guided flow
- inactive filter hiding
- terminology standardization
- refresh/data-health cards and confirmation

## Do later

- async refresh queue
- hosted DB state store
- hosted deployment
- full service architecture consolidation
- model tuning or model-input promotion
- licensed route metrics integration

## Do not do

- Do not wire CFBD/NFL usage/Outcome/market data into model/ranking/decision logic.
- Do not let ADP/DynastyProcess/market data drive hidden sort.
- Do not treat agent APPROVE as human approval.
- Do not use proxy/inferred drop rows as training truth.
- Do not treat missing as zero.
- Do not enable hosted deployment.
