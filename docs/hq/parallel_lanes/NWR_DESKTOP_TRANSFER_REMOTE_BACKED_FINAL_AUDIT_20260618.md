# NWR Desktop Transfer Remote-Backed Final Audit

## Scope

This is a Master/Main HQ status-first audit for moving Niners War Room from the
vacation laptop to the desktop with GitHub as the remote-backed source of truth.

This audit is docs-only. It does not deploy, merge, stage, commit, create
rankings, create probabilities or bands, create hidden sort keys, create
promoted artifacts, create simulations, or touch lane worktree files outside
this Master HQ report.

## Remote

GitHub remote:

```text
https://github.com/scolety1/Niners-War-Room.git
```

Desktop bootstrap:

```powershell
git clone https://github.com/scolety1/Niners-War-Room.git
Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room"
git fetch --all
```

Do not blindly copy or commit:

- `data/`
- `local_exports/`
- `.venv/`
- caches
- logs
- generated artifacts
- secrets

## Lane Summary

| Lane | Branch | Latest Local Commit | Remote-Backed | Status | Transfer Verdict |
|---|---|---:|---|---|---|
| Master/Main HQ | `work/hq-parallel-control` | `2c575c4` | yes | clean | GREEN |
| Outcome V1 | `main` | `6e47932` | yes | `?? data/` | GREEN with local artifact note |
| Deployment V2 | `work/deployment-v2-discovery` | `04dda41` | yes | clean | GREEN |
| Rookie HQ | `work/rookie-framework-path` | `7884d67` | yes | `?? data/` | GREEN with local artifact note |
| Mock Draft HQ | `work/mock-draft-simulator` | `901fb32` | yes | clean | GREEN |
| Drop Decision | `work/drop-decision-day-review` | `ebddf8b` | yes | clean | GREEN |
| QA/Data Hygiene | `work/data-test-hygiene` | `563665c` | no | `?? data/`, untracked QD2 doc | YELLOW |

## Master/Main HQ

Laptop worktree:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room
```

Branch:

```text
work/hq-parallel-control
```

Latest commit:

```text
2c575c4 Add NWR laptop to desktop migration checklist
```

Remote-backed:

```text
yes - origin/work/hq-parallel-control matches local HEAD
```

Clean:

```text
yes
```

Tracked docs/code needing commit:

```text
none
```

Local-only artifacts:

```text
none shown by git status
```

Safe to migrate:

```text
yes
```

Desktop first check:

```powershell
git switch work/hq-parallel-control
git status --short
git log --oneline -5
```

## Outcome V1

Laptop worktree:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome
```

Branch:

```text
main
```

Latest commit:

```text
6e47932 Record Outcome numeric columns V1 local release closeout
```

Remote-backed:

```text
yes - origin/main matches local HEAD
```

Clean:

```text
no, has local-only ?? data/
```

Tracked docs/code needing commit:

```text
none
```

Local-only artifacts:

```text
data/
```

Safe to migrate:

```text
yes for Git-backed code/docs; do not copy data/ blindly
```

Desktop first check:

```powershell
git switch main
git status --short
streamlit run app/main.py
```

Use local app URL:

```text
http://localhost:8501/rankings
```

Still blocked:

- hosted deployment in V1
- Top 6/unapproved heads
- sorting/ranking effects
- hidden sort keys
- promoted artifacts

## Deployment V2

Laptop worktree:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2
```

Branch:

```text
work/deployment-v2-discovery
```

Latest commit:

```text
04dda41 Prepare deployment v2 branch push review hold
```

Remote-backed:

```text
yes - origin/work/deployment-v2-discovery matches local HEAD
```

Clean:

```text
yes
```

Tracked docs/code needing commit:

```text
none
```

Local-only artifacts:

```text
none shown by git status
```

Safe to migrate:

```text
yes
```

Desktop first check:

```powershell
git worktree add "C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2" work/deployment-v2-discovery
Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2"
git status --short
git log --oneline -5
```

Still blocked:

- hosted deployment
- deploy commands
- public ports
- secrets
- containers/images
- CI/CD deploy workflows

## Rookie HQ

Laptop worktree:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies
```

Branch:

```text
work/rookie-framework-path
```

Latest commit:

```text
7884d67 Document rookie manual draft kit v2 readability pass R-ACC-7
```

Remote-backed:

```text
yes - origin/work/rookie-framework-path matches local HEAD
```

Clean:

```text
no, has local-only ?? data/
```

Tracked docs/code needing commit:

```text
none
```

Local-only artifacts:

```text
data/
```

Safe to migrate:

```text
yes for Git-backed code/docs; do not copy data/ blindly
```

Desktop first check:

```powershell
git worktree add "C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies" work/rookie-framework-path
Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies"
git status --short
git log --oneline -5
```

Still blocked:

- Master HQ touching Rookie files/artifacts
- production/app ranking integration unless explicitly approved
- probabilities/bands
- hidden sort keys
- promoted artifacts
- blind `local_exports/` transfer

Artifact note:

- Rookie final exports live under `local_exports/`.
- If the desktop needs those previews/CSV exports, create a separate exact
  artifact-transfer manifest. Do not copy all `local_exports/` blindly.

## Mock Draft HQ

Laptop worktree:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-mock-draft
```

Branch:

```text
work/mock-draft-simulator
```

Latest commit:

```text
901fb32 Document mock draft desktop transfer handoff
```

Remote-backed:

```text
yes - origin/work/mock-draft-simulator matches local HEAD
```

Clean:

```text
yes
```

Tracked docs/code needing commit:

```text
none
```

Local-only artifacts:

```text
none shown by git status
```

Safe to migrate:

```text
yes for Git-backed code/docs
```

Desktop first check:

```powershell
git worktree add "C:\Users\smcol\Documents\Vacation\Niners-War-Room-mock-draft" work/mock-draft-simulator
Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room-mock-draft"
git status --short
git log --oneline -5
```

Still blocked:

- simulations from Master HQ
- production/app rankings
- probabilities/bands
- hidden sort keys
- promoted artifacts
- Rookie artifact modifications

## Drop Decision

Laptop worktree:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-drop-decision
```

Branch:

```text
work/drop-decision-day-review
```

Latest commit:

```text
ebddf8b Repair drop decision full-board bridge validation
```

Remote-backed:

```text
yes - origin/work/drop-decision-day-review matches local HEAD
```

Clean:

```text
yes
```

Tracked docs/code needing commit:

```text
none
```

Local-only artifacts:

```text
none shown by git status
```

Safe to migrate:

```text
yes
```

Desktop first check:

```powershell
git worktree add "C:\Users\smcol\Documents\Vacation\Niners-War-Room-drop-decision" work/drop-decision-day-review
Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room-drop-decision"
git status --short
git log --oneline -5
```

Still blocked:

- app/ranking changes unless separately approved
- committing local artifacts

## QA/Data Hygiene

Laptop worktree:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-qa-data
```

Branch:

```text
work/data-test-hygiene
```

Latest commit:

```text
563665c Document QA data hygiene artifact risk
```

Remote-backed:

```text
no - origin/work/data-test-hygiene is missing
```

Clean:

```text
no
```

Current status:

```text
?? data/
?? docs/hq/parallel_lanes/QA_DATA_HYGIENE_AUDIT_QD2.md
```

Tracked docs/code needing commit:

```text
untracked docs/hq/parallel_lanes/QA_DATA_HYGIENE_AUDIT_QD2.md needs lane review
```

Local-only artifacts:

```text
data/
```

Safe to migrate:

```text
not yet
```

Desktop first check:

```text
Do not recreate this lane on desktop until QA/Data Hygiene is committed/pushed
or explicitly abandoned.
```

Recommended action:

- Ask QA/Data Hygiene lane to triage `QA_DATA_HYGIENE_AUDIT_QD2.md`.
- Do not commit `data/`.
- Push `work/data-test-hygiene` only after the lane is clean and approved.

## Other Worktrees

`git worktree list` found only these NWR worktrees:

- `C:\Users\smcol\Documents\Vacation\Niners-War-Room`
- `C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2`
- `C:\Users\smcol\Documents\Vacation\Niners-War-Room-drop-decision`
- `C:\Users\smcol\Documents\Vacation\Niners-War-Room-mock-draft`
- `C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome`
- `C:\Users\smcol\Documents\Vacation\Niners-War-Room-qa-data`
- `C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies`

## Branches To Fetch On Desktop

Fetch all remote branches:

```powershell
git fetch --all
```

Remote-backed branches to use:

- `main`
- `work/hq-parallel-control`
- `work/deployment-v2-discovery`
- `work/drop-decision-day-review`
- `work/mock-draft-simulator`
- `work/rookie-framework-path`

Not ready:

- `work/data-test-hygiene`

## Final Recommendation Before Switching To Desktop

GREEN to move the main Git-backed project to desktop for:

- Master/Main HQ
- Outcome V1
- Deployment V2
- Rookie HQ
- Mock Draft HQ
- Drop Decision

YELLOW hold:

- QA/Data Hygiene, because it is not remote-backed and has untracked local files.

Local artifact caution:

- `data/`, `local_exports/`, `.venv/`, caches, logs, generated databases, and
  generated artifacts are not covered by GitHub remote transfer.
- Do not copy them blindly.
- If needed, create a separate artifact-transfer manifest with exact paths.

Overall readiness:

```text
GREEN_FOR_GIT_REMOTE_BACKED_DESKTOP_TRANSFER_EXCEPT_QA_DATA_HYGIENE
```
