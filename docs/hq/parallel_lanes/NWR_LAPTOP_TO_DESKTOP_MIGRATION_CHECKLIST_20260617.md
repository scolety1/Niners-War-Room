# NWR Laptop To Desktop Migration Checklist

## Scope

This is a Master/Main HQ docs-only migration checklist for moving Niners War
Room work from the vacation laptop to the desktop. It uses the latest Master HQ
lane checkpoint docs and current Master repo branch metadata. It does not touch
Mock Draft, Rookie, Outcome, Deployment V2, app/source files, `data/`,
`local_exports/`, or `.venv/`.

Mock Draft Codex is active, so Mock Draft is intentionally excluded from
push/migration completion in this checklist.

## Global Migration Rules

Use Git as the remote-backed source of truth for committed code/docs.

Do not manually copy blindly:

- `data/`
- `local_exports/`
- `.venv/`
- generated caches
- generated logs
- generated databases
- ad hoc exports

If generated artifacts are needed on the desktop, create a separate artifact
manifest and copy only explicitly approved folders/files.

Do not use migration to create:

- app/production rankings
- probabilities or bands
- hidden sort keys
- promoted artifacts
- simulations
- hosted deployment
- deploy commands

## Desktop Bootstrap

On the desktop, start with:

```powershell
git clone https://github.com/scolety1/Niners-War-Room.git
Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room"
git fetch --all
git status --short
```

Then create/check out lane worktrees only as needed.

## Master/Main HQ

Laptop worktree path:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room
```

Branch:

```text
work/hq-parallel-control
```

Latest remote-backed commit:

```text
31fbdc3 Record full NWR lane status scan
```

Remote-backed:

```text
yes - origin/work/hq-parallel-control
```

Local status:

```text
clean at last Master check
```

Desktop checkout:

```powershell
git fetch origin
git switch work/hq-parallel-control
git log --oneline -5
git status --short
```

Do not manually copy:

- `data/`
- `local_exports/`
- `.venv/`
- caches/logs

Lane state:

```text
complete / monitor-control
```

Recommended first desktop check:

```powershell
git rev-parse --show-toplevel
git branch --show-current
git status --short
git log --oneline -5
```

## Outcome V1

Laptop worktree path:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome
```

Branch:

```text
main
```

Latest remote-backed commit:

```text
6e47932 Record Outcome numeric columns V1 local release closeout
```

Remote-backed:

```text
yes - origin/main
```

Local status:

```text
has local-only ?? data/ on laptop; do not commit or copy blindly
```

Desktop checkout:

```powershell
git worktree add "C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome" main
Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome"
git status --short
git log --oneline -5
```

Do not manually copy:

- `data/` unless an explicit artifact-transfer manifest says so
- `local_exports/`
- `.venv/`
- caches/logs

Lane state:

```text
complete / local-use ready
```

Recommended first desktop check:

```powershell
streamlit run app/main.py
```

Then open:

```text
http://localhost:8501/rankings
```

Blocked:

- hosted deployment in V1
- Top 6/unapproved heads
- sorting/ranking effects
- hidden sort keys
- promoted artifacts

## Deployment V2

Laptop worktree path:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2
```

Branch:

```text
work/deployment-v2-discovery
```

Latest remote-backed commit:

```text
04dda41 Prepare deployment v2 branch push review hold
```

Remote-backed source of truth:

```text
origin/work/deployment-v2-discovery
```

Local status at handoff:

```text
clean
```

Desktop checkout:

```powershell
git worktree add "C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2" work/deployment-v2-discovery
Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2"
git status --short
git log --oneline -5
```

Do not manually copy:

- `data/`
- `local_exports/`
- `.venv/`
- platform config not present in Git
- caches/logs

Lane state:

```text
complete / local-only review hold
```

Recommended first desktop check:

```powershell
git log --oneline -5
```

Blocked:

- hosted deployment
- deploy commands
- public ports
- secrets
- CI/CD deploy workflows
- containers/images

## Rookie HQ

Laptop worktree path:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies
```

Branch:

```text
work/rookie-framework-path
```

Latest remote-backed commit:

```text
7884d67 Document rookie manual draft kit v2 readability pass R-ACC-7
```

Remote-backed:

```text
yes - origin/work/rookie-framework-path
```

Local status:

```text
expected local-only ?? data/; Rookie HQ is actively upgrading/refining
```

Desktop checkout:

```powershell
git worktree add "C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies" work/rookie-framework-path
Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room-rookies"
git status --short
git log --oneline -5
```

Do not manually copy:

- `data/`
- `.venv/`
- all of `local_exports/` blindly
- generated caches/logs

Important local artifact note:

- The final Rookie mock draft input lives under `local_exports/`.
- Do not copy all `local_exports/` blindly.
- If the desktop needs Rookie final exports, create a separate artifact manifest
  and copy only the approved final Rookie export folder.

Lane state:

```text
active / refining
```

Recommended first desktop check:

```powershell
git log --oneline -5
git status --short
```

Blocked:

- Master HQ touching Rookie files/artifacts
- production/app ranking integration unless explicitly approved
- probabilities/bands
- hidden sort keys
- promoted artifacts

## Mock Draft HQ

Laptop worktree path:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-mock-draft
```

Branch:

```text
work/mock-draft-simulator
```

Latest laptop branch commit known from Master metadata:

```text
cc3b23d Add openpyxl test dependency
```

Remote-backed:

```text
not yet confirmed / leave out while Mock Draft Codex is active
```

Local status:

```text
active work in progress; do not migrate yet from Master HQ
```

Desktop checkout:

```text
Do not create this desktop worktree from Master HQ yet.
Wait for Mock Draft Codex to finish, commit, push, and provide final handoff.
```

Do not manually copy:

- active modified docs/code
- `data/`
- `local_exports/`
- `.venv/`
- generated caches/logs

Lane state:

```text
active / excluded from this migration checklist until lane handoff
```

Recommended first desktop check:

```text
Wait for Mock Draft HQ final pushed branch and handoff.
```

Blocked:

- Master HQ touching active Mock Draft worktree
- simulations from Master HQ
- production/app rankings
- probabilities/bands
- hidden sort keys
- promoted artifacts

## Drop Decision Lane

Laptop worktree path:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-drop-decision
```

Branch:

```text
work/drop-decision-day-review
```

Latest remote-backed commit:

```text
ebddf8b Repair drop decision full-board bridge validation
```

Remote-backed:

```text
yes - origin/work/drop-decision-day-review
```

Local status:

```text
clean at last Master migration push check
```

Desktop checkout:

```powershell
git worktree add "C:\Users\smcol\Documents\Vacation\Niners-War-Room-drop-decision" work/drop-decision-day-review
Set-Location "C:\Users\smcol\Documents\Vacation\Niners-War-Room-drop-decision"
git status --short
git log --oneline -5
```

Do not manually copy:

- `data/`
- `local_exports/`
- `.venv/`
- generated review artifacts unless separately approved

Lane state:

```text
review lane / remote-backed
```

Recommended first desktop check:

```powershell
git status --short
git log --oneline -5
```

Blocked:

- app/ranking changes unless separately approved
- committing local artifacts

## QA / Data Hygiene Lane

Laptop worktree path:

```text
C:\Users\smcol\Documents\Vacation\Niners-War-Room-qa-data
```

Branch:

```text
work/data-test-hygiene
```

Latest local commit known:

```text
563665c Document QA data hygiene artifact risk
```

Remote-backed:

```text
not currently visible as origin/work/data-test-hygiene
```

Local status at last Master scan:

```text
?? data/
?? docs/hq/parallel_lanes/QA_DATA_HYGIENE_AUDIT_QD2.md
```

Desktop checkout:

```text
Do not migrate from Master HQ yet.
Needs lane cleanup/commit/push or explicit decision to ignore.
```

Do not manually copy:

- `data/`
- `local_exports/`
- `.venv/`
- generated caches/logs

Lane state:

```text
needs human review / not remote-backed
```

Recommended first desktop check:

```text
Wait for QA/Data Hygiene lane handoff or explicit approval.
```

Blocked:

- committing `data/`
- blind artifact copy

## Legacy / Non-Primary Branch Note

Branch:

```text
nwr-outcome-build-sprint-1-scoring-labels
```

Status from Master metadata:

```text
local branch ahead of origin by 18 commits
```

Migration stance:

```text
Do not treat as a primary desktop migration lane unless HQ explicitly requests
legacy prototype preservation.
```

Recommended action:

- Leave alone for now.
- If needed later, run a separate legacy-branch preservation audit.

## Overall Migration Status

Remote-backed and ready to recreate on desktop:

- `main`
- `work/hq-parallel-control`
- `work/deployment-v2-discovery`
- `work/drop-decision-day-review`
- `work/rookie-framework-path`

Not safe to migrate yet from Master HQ:

- `work/mock-draft-simulator` because Mock Draft Codex is active
- `work/data-test-hygiene` because it is not remote-backed and has untracked
  local files
- `nwr-outcome-build-sprint-1-scoring-labels` because it is a legacy/non-primary
  branch ahead of origin

## Final Recommendation

On desktop, start with the remote-backed lanes only. Leave Mock Draft out until
Mock Draft Codex finishes and pushes a clean branch. Leave QA/Data Hygiene out
until it has a clean handoff or explicit ignore decision.

Do not copy `data/`, `local_exports/`, `.venv/`, caches, logs, or generated
artifacts blindly. If local exports are needed, create a separate artifact
transfer manifest with exact source and destination folders.

This checklist is docs-only coordination and does not perform migration,
deployment, feature work, artifact transfer, or lane cleanup.
