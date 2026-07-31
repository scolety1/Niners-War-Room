# NWR GOLDEN LANE PHASE 1A WORK ORDER
## Existing Source, Rights, and Identity Audit

### Setup

Work only on the live canonical branch work/hq-parallel-control through a new isolated worktree and task branch. Fetch and prune first. Resolve and report the actual live HQ/tree; the prior canonical source was 18792a8bbf3f39c03086163c1f5d672b1e2ba5a6 / b91e9b41c192494fbed2facd85bd64b1a1a8d18d, followed only by the Golden Lane documentation packet if it was pushed.

Stable: C:\NWR\Niners-War-Room-V1.
Operational: C:\NWR\Niners-War-Room.
Do not update operational. Do not start the launcher. Leave the NWR DynastyProcess Market Baseline Refresh task unchanged.

Read AGENTS.md and docs/hq/master/nwr_golden_lane_v1_20260731 completely. Verify canonical, stable, operational, preservation, scheduler, and process state before auditing.

### Exact mission

Execute only Golden Lane Phase 1A. Inventory the NWR-owned local snapshots for:

1. nflverse player and team stats;
2. weekly player stats;
3. play-by-play;
4. players and IDs;
5. rosters;
6. schedules;
7. snap counts;
8. injuries;
9. depth charts;
10. participation;
11. FTN public subset.

For every source family, record exact local snapshot paths, upstream source, terms/rights evidence, seasons, row grain, identity fields, revision/correction behavior, historical as-of authority, missingness, and model eligibility. Distinguish verified facts, inferred properties, absent evidence, and owner decisions.

Do not acquire or refresh any provider. Do not treat the audit as model admission. No network is authorized except the initial Git remote fetch and a final conditional Git push. Rights claims require local evidence; when evidence is absent, record UNKNOWN_REQUIRES_OWNER_OR_SOURCE_CONFIRMATION.

### Allowed paths

- docs/hq/master/nwr_existing_source_rights_identity_audit_v1_20260731/
- docs/hq/master/nwr_golden_lane_v1_20260731/

Read-only inspection is allowed elsewhere in the repository, stable checkout, operational checkout, and approved persistent/recovery roots. Do not read opaque artifact contents; verify them by hash only.

### Prohibited paths and actions

- No src/, tests/, scripts/, application, model, ranking, formula, UI, or generated data-pack changes.
- No local_exports, active-pack, Trading Lab, opaque, persistent, recovery, or user-state writes.
- No provider acquisition, scraping, subscription, purchase, API collection, or scheduler execution.
- No Phase 1B hash repair, broad replay archaeology, feature testing, target design, formula research, market modeling, or product integration.
- Do not repeat any CLOSED_WORK_REGISTRY.csv lane.
- Never force-push.

### Required targets and source authority

Finished V1 remains production authority. Model V4 rookie review remains separate review-only authority with 73 scored and 7 blocked. The rookie-veteran common scale is formally rejected. Outcome V3 and the frozen comparator remain unchanged. Audit findings may classify future model eligibility but cannot admit a source into a model.

Create a Phase 1A packet with a source-family inventory, exact snapshot inventory, rights/terms evidence matrix, season/grain/identity matrix, revision and historical-as-of assessment, missingness summary, model-eligibility decision table, conflicts/unknowns, preservation proof, validation results, file inventory, and manifest.

Update the Golden Lane ledger mechanically:

- Phase 1A PASS only if every named family has an explicit evidence-backed classification, including UNKNOWN where necessary.
- On PASS, make Phase 1B the sole next authorized lane and replace NEXT_AUTHORIZED_LANE_PROMPT.md with a complete bounded Data Hygiene work order.
- On failure, generate only a bounded Phase 1A correction prompt.
- Recalculate completion from passed gates divided by ten.

### Validation and mutations

Require exact canonical state; mechanically generated changed-file inventory; deterministic packet hashes; registry and phase-gate consistency; documentation-only diff; no model/code/data/UI mutation; Finished V1, Rookie Board, Outcome V3, Trading Lab, active-pack, frozen comparator, opaque, persistent, and recovery preservation; scheduled-task no-change; existing security controls; passive Data Health reads; no Hermetic regression; and LocalData fail-closed behavior.

Perform real-path negative mutations against a temporary copy or test harness for missing source, unsafe path, changed snapshot hash, ambiguous identity, missing rights evidence, invalid grain, future leakage, and unauthorized eligibility. Mutations must not touch governed source artifacts or user state.

### Commits and independent review

Use documentation-only commits such as:

1. docs: audit existing NWR source authority
2. docs: close Golden Lane Phase 1A

Create a separate adoption worktree/branch from the exact same canonical parent. Independently review the packet, registry completeness, evidence claims, deterministic hashes, mutations, preservation, and next-work-order correctness. Permit at most one bounded documentation correction.

### Conditional push

Push only after a green Phase 1A gate, clean independent review, exact remote re-read, fast-forward proof, clean secret/security checks, and preservation confirmation. Push the reviewed documentation commits to work/hq-parallel-control without force. Then fast-forward stable with line-ending-safe checkout behavior. Never update operational.

### Authorized verdicts

Use exactly one:

- GREEN_NWR_GOLDEN_LANE_PHASE_1A_COMPLETE_AND_PHASE_1B_READY
- GREEN_NWR_GOLDEN_LANE_PHASE_1A_READY_FOR_HQ_REVIEW
- YELLOW_NWR_GOLDEN_LANE_PHASE_1A_NEEDS_TARGETED_REVISION
- BLOCKED_NWR_GOLDEN_LANE_PHASE_1A_SOURCE_RIGHTS_OR_IDENTITY_AUTHORITY
- RED_NWR_GOLDEN_LANE_PHASE_1A_DATA_SECURITY_OR_PRESERVATION_REGRESSION

### Required final response

Report verdict; starting and final canonical HQ/tree; Phase 1A gate result; source-family counts by eligibility and evidence status; rights and identity blockers; completed and blocked Golden Lane gates; mechanical completion percentage; next authorized lane; next prompt path; owner decisions; commits; independent review; push; stable status; operational no-change; production changes NONE; preservation; deterministic result; Hermetic/LocalData/security/Data Health results; and exact instructions for beginning the next task.
