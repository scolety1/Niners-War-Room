# Coding Restart Board

Date: 2026-06-18

## Scope

This Master/Main HQ board restarts coding after the desktop migration while
preserving lane isolation.

No deploy, simulation, production ranking, probability/band, hidden sort key,
promoted artifact, QA/Data Hygiene activation, `.env` import, broker API,
credential use, real-money trading, or automated execution is approved by this
board.

QA/Data Hygiene remains inactive/HOLD. The full recovery archive stays
local-only at:

`C:\NWR_LOCAL_ARCHIVE\laptop_retirement_20260618\qa_data_hygiene_full_lane\`

## Restart Gate

All active desktop lanes were verified clean with:

```powershell
git branch --show-current
git rev-parse --short HEAD
git status --short
git diff --check
git remote -v
git ls-remote origin refs/heads/<current-branch>
```

Each lane's current local HEAD matches the corresponding `origin` branch ref.

## Post-Push Status Update

After the restart board was committed and pushed, final lane sweeps found Mock
Draft HQ and Trading Lab dirty:

```text
C:\NWR\Niners-War-Room-mock-draft
 M src/services/draft_state_service.py
 M tests/test_draft_state_service.py
?? docs/hq/parallel_lanes/MOCK_DRAFT_SIMULATOR_SERVICE_CONTRACT.md

C:\NWR\Niners-War-Room-trading-lab
?? docs/trading_lab/TRADING_LAB_SAFE_RESEARCH_FOUNDATION_20260618.md
?? src/trading_lab/
?? tests/test_trading_lab_source_inventory.py
?? tests/test_trading_lab_watchlist_contract.py
```

`git diff --check` still passed in both lanes, but these dirty files change the
restart gate. Mock Draft HQ and Trading Lab are now HOLD for new agents until
the owner of each workstream either commits, shelves, or explicitly reports the
files as that lane agent's controlled active change.

## Lane Board

| Lane | Repo path | Branch | HEAD | Clean status | Current approved coding task | Blocked tasks | Guardrails | Validation commands | Separate Codex agent may proceed |
|---|---|---|---|---|---|---|---|---|---|
| Master HQ | `C:\NWR\Niners-War-Room` | `work/hq-parallel-control` | `d200598` | clean; `git diff --check` pass; remote matches | Coordination docs and lane status control only | Feature coding, deploy, simulations, data import, QA/Data Hygiene activation | Do not touch lane code owned by Rookie, Mock Draft, Drop Decision, Outcome, Deployment V2, or Trading Lab; do not commit `data/`, `local_exports/`, `.env`, `.venv`, caches, logs, generated artifacts, or archives | `git status --short`; `git diff --check`; `git log --oneline -5`; `git ls-remote origin refs/heads/work/hq-parallel-control` | Yes, for Master coordination docs only |
| Mock Draft HQ | `C:\NWR\Niners-War-Room-mock-draft` | `work/mock-draft-simulator` | `901fb32` | HOLD: final post-push sweep found `M src/services/draft_state_service.py`; `git diff --check` pass; remote matches | Reconcile existing local `draft_state_service.py` change before new work | Real ADP import, app wiring, simulations, rankings/probabilities/bands, hidden sort keys, promoted artifacts; no new agent starts from this dirty tree | Manual-use mixed rookie plus dropped-veteran mock draft simulator/review lane; ADP/market may not become NWR private value | `git status --short`; `git diff --check`; targeted service tests only after dirty file is owned/reconciled | No new agent until dirty file is reconciled or explicitly claimed by Mock Draft HQ |
| Rookie HQ | `C:\NWR\Niners-War-Room-rookies` | `work/rookie-framework-path` | `7884d67` | clean; `git diff --check` pass; remote matches | Docs or validation guards only | Rookie rankings, formula, order, manual kit changes, generated artifacts | Frozen manual kit remains protected unless Master explicitly approves a scope change | `git status --short`; `git diff --check`; docs/guard tests only if explicitly scoped | Yes, only for docs/validation guard work; no ranking/formula/order edits |
| Drop Decision HQ | `C:\NWR\Niners-War-Room-drop-decision` | `work/drop-decision-day-review` | `ebddf8b` | clean; `git diff --check` pass; remote matches | Read-only validation/reporting improvements only | Outcome/display changes, production decision changes, simulations, generated artifacts | Improve auditability without changing production model behavior or fantasy lane outputs | `git status --short`; `git diff --check`; targeted validation/report tests only | Yes, limited to read-only validation/reporting |
| Outcome V1 | `C:\NWR\Niners-War-Room-outcome` | `main` | `6e47932` | clean; `git diff --check` pass; remote matches | Read-only verification only | Numeric display/model logic, probability/band changes, deploy, simulations | Outcome is sealed unless explicitly approved later | `git status --short`; `git diff --check`; read-only inspection commands | No coding; read-only verification only |
| Deployment V2 | `C:\NWR\Niners-War-Room-deploy-v2` | `work/deployment-v2-discovery` | `04dda41` | clean; `git diff --check` pass; remote matches | Discovery/docs/validation only | Deploy, merge, production config mutation, secrets import, generated artifacts | No deployment action or production environment change is approved | `git status --short`; `git diff --check`; docs/validation checks only | Yes, limited to discovery/docs/validation |
| Trading Lab | `C:\NWR\Niners-War-Room-trading-lab` | `work/trading-lab` | `7c137c7` | HOLD: final sweep found untracked docs, `src/trading_lab/`, and tests; `git diff --check` pass; remote matches | Reconcile or explicitly claim existing local Trading Lab files before new work | Fantasy lane edits, broker APIs, credentials, real-money trading, automated execution, investment advice; no new agent starts from this dirty tree | Keep Trading Lab isolated from fantasy lanes; use paper/research abstractions only | `git status --short`; `git diff --check`; docs/research validation only after dirty files are owned/reconciled | No new agent until dirty files are reconciled or explicitly claimed by Trading Lab |

## Restart Order Recommendation

1. Drop Decision HQ: read-only validation/reporting improvements only.
2. Deployment V2: discovery/docs/validation only, no deploy.
3. Rookie HQ: docs or validation guards only; frozen manual kit stays protected.
4. Outcome V1: read-only verification only.
5. Master HQ: coordination and status docs only.
6. Mock Draft HQ: HOLD until the dirty service/test/doc files are reconciled or
   explicitly claimed by the active Mock Draft owner; after that, service/test
   hardening only, no real ADP import and no app wiring.
7. Trading Lab: HOLD until the dirty docs/src/tests are reconciled or
   explicitly claimed by the active Trading Lab owner; after that,
   research/paper-only infrastructure only.

## Agent Prompt Template

Each lane agent should start by rerunning:

```powershell
git branch --show-current
git rev-parse --short HEAD
git status --short
git diff --check
```

If clean and on the lane's approved branch, the agent may work only inside that
lane's repo path and only on the approved task listed above.

If `git status --short` shows unexpected files, the agent must stop and report
before editing.
