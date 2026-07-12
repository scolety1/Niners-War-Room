# Post-Rookie-Registry Roadmap Reassessment V1 Report

## Controlling verdict

`GREEN_POST_ROOKIE_REGISTRY_ROADMAP_READY_WITH_SAFE_NEXT_LANE`

The single highest-value safe next lane is **Trading Lab Saved Manual Scenario Workspace V1**.

This is a documentation-only reassessment from verified live HQ. It does not execute the lane.

## Repository state

| Item | Verified value |
|---|---|
| Controlling remote branch | `origin/work/hq-parallel-control` |
| Expected HQ | `794b6cd64ffdc673936d0a1f6c8f4bdfe0fc863e` |
| Actual remote HQ | `794b6cd64ffdc673936d0a1f6c8f4bdfe0fc863e` |
| Remote advance | None |
| Intervening commits | None |
| Isolated branch | `work/post-rookie-registry-roadmap-reassessment-v1-20260711` |
| Isolated worktree | `C:\Users\codex-agent\Documents\Niners War Room\Niners-War-Room-post-rookie-registry-roadmap-reassessment-v1-20260711` |
| Allowed write scope | `docs/hq/master/post_rookie_registry_roadmap_reassessment_v1_20260711/` |

All remotes were fetched before the branch was created. The remote branch was queried directly after the fetch. Because the actual head equals the expected head, there were no intervening commits to reconcile and no live-HQ conflict.

## Method

The reassessment used repository evidence only. No external research was needed, so no external research ledger is created. No external fantasy ranking, projection, proprietary data, provider, Flaim, or FantasyBot was consulted.

The scan covered:

- 18 visible navigation specifications and 41 hidden/compatibility specifications (59 total);
- 46 tracked `app/pages` Python files;
- 271 tracked `src/services` Python files;
- 407 tracked `tests/test_*.py` files;
- `docs/hq`, current roadmaps, backlogs, no-recreate indexes, recent lane packets, source/data-health systems, rankings, Player Compare, Trading Lab, Live Draft, Mock Draft, rookie tools, Development Lab, Refresh Data, Settings/Data Health, Future Tools, roster/league context, historical research, plugins, prospective tracking, and registry systems;
- known focused failures, fixture assumptions, warnings, route aliases, and operational conventions.

Every proposed item appears in `REMAINING_PRODUCT_GAP_MATRIX.csv` or `CANDIDATE_LANE_SCORECARD.csv` with one of the required classifications. Completed and forbidden work is reconciled in `NO_RECREATE_AND_COMPLETED_WORK_INDEX.csv`.

## What remains important

### 1. Manual work loss in Trading Lab

Trading Lab is already a capable human-review tool. It has manual give/get rows, a neutral comparison summary, roster-impact context, notes, checklists, evidence receipts, and CSV/memo downloads. It does not, however, have a durable scenario lifecycle. Current state is held in `st.session_state`; users can lose an unfinished scenario when a browser session or process ends.

This is the strongest product gap because it affects a frequent decision workflow and can be solved using only human-entered state. The Development Lab already demonstrates a repository-local pattern for versioned state, backups, quarantine, and reset. A Trading Lab implementation can adopt that lifecycle shape while keeping a separate schema and storage namespace.

### 2. Player Compare compact and accessibility depth

Player Compare already provides a Visible Context Summary, two-to-four-player review, uncertainty and caveats, trust/provenance context, and multiple evidence tabs. Rebuilding summaries or adding winner logic would recreate or violate existing work. The remaining bounded opportunity is to harden the existing dense surface at compact widths and through keyboard/screen-reader paths.

### 3. Operational safety claims and receipt durability

The data-health dashboard currently derives changed paths from a narrow unstaged diff command, swallows Git failures as an empty list, and emits a hard-coded green no-model/rank-mutation claim. Staged and untracked protected changes may therefore be omitted. Separately, latest refresh status and source-manifest files are written directly, and a corrupt latest status returns no validated archive fallback.

These are meaningful reliability gaps: they affect the truth and recoverability of operational evidence. They are not a reason to recreate the recently completed partial-failure/staleness UX.

### 4. Roster re-entry and league-context readiness

The repository has a manual Roster Weakness Tracker and admitted Sleeper roster structures where the active pack supplies them. Users still re-enter roster context. Hydration is promising, but implementation is not ready: a clean checkout lacks the ignored active pack, exact lineup slots are not canonical in league rules, a starter format is hard-coded elsewhere, and stale/ambiguous identity behavior needs a contract.

The safe later lane is design/readiness only. It must not infer team strategy, lineup structure, or replacement level.

### 5. Hermetic validation and route ownership

The test corpus is substantial but source-text heavy. A clean-checkout draft slice can fail or skip when ignored local pack/history fixtures are absent. Route inventory contains 59 specifications over 46 page files, with aliases and reused wrappers. One transient Live Draft direct-route not-found state appeared after restart and then cleared; that is evidence for a reproduction task, not permission to change draft routing.

## Completed, partial, parked, blocked, and obsolete work

### Complete and do not recreate

- Formula Gauntlet, ingredient work, accuracy reconciliation, and temporal validation.
- Prospective PYF, GAUNTLET_081, and current-board freezes.
- Freeze operational closeout and formula research pause.
- Decision Trust Strip and Evidence Consistency V1.
- Refresh Partial-Failure Recovery and Staleness UX V1.
- Live and Mock Draft Accessibility / Compact-Width Hardening V1.
- Flaim and FantasyBot capability audits and sanitized closeout.
- Rookie workspace design, authority normalization, read-only registry scaffold, deterministic linkage audit, metadata queue, triage plan, and batch 836e blocked closeout.
- Trading Lab manual asset rows, neutral summary, notes, checklists, evidence receipts, and CSV/memo export.
- Player Compare core comparison, context, caveats, uncertainty, and evidence tabs.

### Partial existing implementation

- Future Tools and Development Lab expose status and research artifacts, but canonical navigation can drift.
- Data Health shows guardrail/source state, but its protected-change claim is not fully evidence-derived.
- Roster support has services and a manual tracker, but not safe admitted-roster hydration.
- The test suite is broad, but clean-checkout and rendered-route coverage are uneven.
- Streamlit width migration is partially absorbed by recent lanes, but warnings remain elsewhere.

### Parked or gated

- Player Compare saved worksheet/export: design first and keep separate from compact hardening.
- Roster hydration implementation: design first; missing-pack and identity contracts required.
- League lineup slots: human-confirmed authority and migration required.
- Contender/rebuilder labels: human-owned neutral semantics required.
- Replacement-level presentation: formula/data gate required.
- Broad route cleanup: deterministic reproduction and ownership map required.
- Broad Streamlit deprecation cleanup: compatibility policy and focused lane required.
- Development Lab artifact navigator: canonical ownership and stale-link inventory required.

### Obsolete or superseded

- The old post-formula roadmap order is consumed by completed lanes and is not a current queue.
- The previous batch 836e ready-to-paste proof direction is superseded by its blocked closeout.
- The prior apparent rookie pytest teardown hang was not reproduced in later controlled runs and is not a current roadmap item.

## Current-state surface conclusions

Detailed per-surface records, including purpose, implemented/recent features, admitted/review-only/blocked data, user and reliability gaps, accessibility, tests, debt, risk, dependencies, and bounded-lane feasibility, are in `CURRENT_SURFACE_STATE_MAP.csv`.

The decisive conclusions are:

| Surface | Current conclusion | Highest-value unresolved issue |
|---|---|---|
| Dynasty Rankings | Mature, protected, high-risk | Preserve; fix only a reproduced defect |
| Player Compare | Mature core; bounded UX work available | Compact-width/accessibility hardening |
| Trading Lab | Mature manual tool; incomplete lifecycle | Save/resume/backup/recovery for manual scenarios |
| Live Draft | Recent hardening complete | Reproduce restart/alias issue before route work |
| Mock Draft | Recent hardening complete | Hermetic fixtures as separate reliability work |
| Rookie tools | Foundation complete; governance paused | No safe material implementation now |
| Development Lab | Useful review boundary | Canonical artifact navigation after design |
| Refresh Data | Recent UX complete | Atomic receipt writes and archive recovery |
| Settings/Data Health | Useful but can overstate green | Evidence-derived fail-closed guardrail status |
| Future Tools | Gated status surface | Prevent documented link/status drift |
| Source/provenance | Mature and protected | Strengthen diagnostics, not source admission |
| Prospective 2026 | Frozen and waiting | Defer until outcomes |
| Rookie registry | Metadata-only and blocked | Defer until exact endpoint metadata |
| Roster/league context | Manual and partially data-ready | Hydration design/readiness |
| Tests/reliability | Broad but static-heavy | Truthful guardrails, then hermetic fixtures |

## Candidate-family reassessment

### A. Player Compare

Core comparison summaries, context, uncertainty, and evidence already exist. `READY_NOW_MODERATE_RISK`: compact-width/accessibility hardening. `NEEDS_DESIGN_FIRST`: saved review worksheet/export. `BLOCKED`: automated winner logic.

### B. Trading Lab

Core manual scenario organization, notes, grouping/rows, receipts, checklists, and export already exist. `READY_NOW_MODERATE_RISK`: saved manual scenario workspace. `BLOCKED`: trade calculator, fairness verdict, winner, automated offer, plugin output.

### C. Roster construction and team strategy

Manual tracker and admitted roster structures exist. `NEEDS_DESIGN_FIRST`: admitted-roster hydration. `NEEDS_DATA_OR_SOURCE_GATE`: exact lineup coverage and replacement-level presentation. `NEEDS_HUMAN_REVIEW`: contender/rebuilder scenario labels. Flaim cannot be canonical league truth.

### D. Data and operational reliability

`READY_NOW_MODERATE_RISK`: fail-closed guardrail truth and atomic/recoverable refresh receipts. `READY_NOW_MODERATE_RISK`, but lower priority: hermetic draft/local-artifact fixtures. `NEEDS_DESIGN_FIRST`: route alias/restart repair. `PARTIAL_EXISTING_IMPLEMENTATION`, parked: broad deprecation cleanup.

### E. Development Lab and research visibility

The production/research separation and prospective status already exist. A display-only artifact navigator is `NEEDS_DESIGN_FIRST`; it must never expose frozen comparators as recommendation logic.

### F. Rookie workspace follow-on

Administrative reporting is technically possible but low value, and current artifacts already document the pause. Queue closure, player rows, identity resolution, source promotion, and endpoint work are `DEFER_UNTIL_CANONICAL_ENDPOINT_METADATA` or `BLOCKED`. No rookie lane is selected.

## Prioritization model

Each candidate receives a 1–5 score, where 5 is favorable, on thirteen criteria. For effort, regression risk, production risk, and dependency count, the score is expressed as **fit**: 5 means low effort/risk/dependency.

Weights:

| Criterion | Weight |
|---|---:|
| Direct user value | 14 |
| Frequency of use | 8 |
| Confidence in benefit | 9 |
| Implementation-effort fit | 8 |
| Data readiness | 8 |
| Source readiness | 8 |
| Testability | 8 |
| Reversibility | 7 |
| Regression-safety fit | 7 |
| Production-safety fit | 5 |
| Dependency fit | 5 |
| Alignment with current goals | 7 |
| Independence from formula/source blockers | 6 |

The weights sum to 100. The score is `sum(weight * criterion / 5)`. Numerical ranking is advisory. A governance stop can only lower or eliminate a candidate; it can never be overcome by points.

Top eligible result:

1. Trading Lab Saved Manual Scenario Workspace V1 — 95.0.
2. Player Compare Compact-Width and Accessibility Hardening V1 — 90.6.
3. Data Health Guardrail Truth and Refresh Receipt Durability V1 — 84.2.
4. Roster Weakness Tracker Admitted-Roster Hydration Design and Readiness V1 — 79.4, design-only.

Player Compare worksheet/export has a competitive raw score but is parked because it needs a separate redaction/authority contract and would overlap the immediate persistence pattern. Full inputs, classifications, overrides, and decisions are in `CANDIDATE_LANE_SCORECARD.csv`.

## Why the immediate lane is safe

The selected lane:

- creates direct value by preventing loss of human work;
- uses existing Trading Lab controls and admitted identity keys;
- needs no source, formula, plugin, registry, or prospective artifact;
- is reversible because it adds an isolated local store and explicit controls;
- can be verified with focused serialization, corruption, backup, overwrite, accessibility, and draft-isolation tests;
- fits one implementation lane and one merge-review lane;
- has an explicit stop boundary against derived facts, scores, winners, recommendations, and cross-surface state.

The lane is bounded moderate rather than low risk because persistence introduces file lifecycle, schema migration, corruption, privacy, and session-overwrite hazards. `IMMEDIATE_NEXT_LANE_CONTRACT.md` makes those hazards testable.

## Work that must remain paused

- All formula and challenger work until season-complete 2026 outcomes and explicit authorization.
- Any use of frozen prospective artifacts in rankings, recommendations, trades, or draft logic.
- Flaim/FantasyBot integration until a documented provider change satisfies reentry and a separate governance decision authorizes more than review.
- Rookie queue closure until every exact canonical endpoint metadata element exists.
- New source endpoints or source promotion until a distinct source-governance proposal is approved.
- Automated trade evaluation, roster strategy classification, and replacement-level logic until their product/model/data contracts exist.

## Technical-debt judgment

The audit does not elevate cleanup simply because it is easy. The most important debt is false-green operational evidence and non-atomic receipts because those can mislead a user and weaken incident recovery. Broad Streamlit warning cleanup, wrapper deduplication, numbering normalization, documentation-link centralization, and worktree administration remain parked or human-review items.

The 500 registered worktrees observed in the controlling clone are an operational concern, but this lane must not remove or alter any existing worktree. Root workflow-document drift likewise needs owner review rather than incidental edits.

## External research

None used. Repository evidence was sufficient, and external fantasy data would have violated the lane boundaries. Consequently, `EXTERNAL_RESEARCH_LEDGER.csv` is intentionally absent rather than empty.

## Final roadmap

Immediate:

1. Trading Lab Saved Manual Scenario Workspace V1.

Next three, sequentially:

1. Player Compare Compact-Width and Accessibility Hardening V1.
2. Data Health Guardrail Truth and Refresh Receipt Durability V1.
3. Roster Weakness Tracker Admitted-Roster Hydration Design and Readiness V1.

Parking and exact reentry triggers are in `PARKING_LOT_AND_REENTRY_TRIGGERS.md`. Hard stops and no-recreate boundaries are in `STOP_AND_NO_RECREATE_LIST.md`.

## Reassessment conclusion

The repository does have a safe immediate implementation lane. It is not another research, plugin, registry, draft, ranking, or source lane. It is a narrow improvement to an existing manual decision workflow: preserve the user's own Trading Lab scenario safely and transparently, without asking the application to decide the trade.
