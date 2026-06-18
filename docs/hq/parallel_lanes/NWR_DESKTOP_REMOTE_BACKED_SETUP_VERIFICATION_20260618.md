# NWR Desktop Remote-Backed Setup Verification

Date: 2026-06-18

## Scope

This is a Master/Main HQ docs-only verification note for rebuilding the Niners
War Room desktop workspace from GitHub remote-backed branches.

No laptop folders were copied wholesale. No `data/`, `local_exports/`, `.venv/`,
caches, logs, generated artifacts, or secrets were copied or committed.

No deploy, merge, push, commit, staging, app ranking, probability/band, hidden
sort key, promoted artifact, or simulation occurred.

## Prior Desktop Permission Blocker

Previous official desktop root:

```text
C:\Users\smcol\Desktop\Niners War Room
```

Result:

```text
BLOCKED - this Codex session could not write to C:\Users\smcol\Desktop.
```

Observed failure:

```text
New-Item : Access to the path 'Desktop' is denied.
fatal: could not create leading directories of
'C:\Users\smcol\Desktop\Niners War Room\Niners-War-Room': Permission denied
```

## Selected Official Codex Workspace Root

New official Codex-accessible desktop workspace root:

```text
C:\NWR
```

Status:

```text
created successfully
```

GitHub remote:

```text
https://github.com/scolety1/Niners-War-Room.git
```

Source-of-truth docs read:

```text
docs/hq/parallel_lanes/NWR_DESKTOP_TRANSFER_REMOTE_BACKED_FINAL_AUDIT_20260618.md
docs/hq/parallel_lanes/NWR_LAPTOP_TO_DESKTOP_MIGRATION_CHECKLIST_20260617.md
```

## Lane Folders Created Or Fetched

Created/fetched under `C:\NWR`:

| Lane | Path | Branch | Source | Latest Commit | Status |
|---|---|---|---|---|---|
| Master/Main HQ | `C:\NWR\Niners-War-Room` | `work/hq-parallel-control` | `origin/work/hq-parallel-control` | `2fa529d Add desktop transfer remote backed final audit` | clean before this doc |
| Outcome V1 | `C:\NWR\Niners-War-Room-outcome` | `main` | `origin/main` | `6e47932 Record Outcome numeric columns V1 local release closeout` | clean |
| Deployment V2 | `C:\NWR\Niners-War-Room-deploy-v2` | `work/deployment-v2-discovery` | `origin/work/deployment-v2-discovery` | `04dda41 Prepare deployment v2 branch push review hold` | clean |
| Drop Decision | `C:\NWR\Niners-War-Room-drop-decision` | `work/drop-decision-day-review` | `origin/work/drop-decision-day-review` | `ebddf8b Repair drop decision full-board bridge validation` | clean |

Master/Main HQ is now dirty only because this verification doc is intentionally
left uncommitted for review.

## Verification Commands Run

Master/Main HQ setup:

```powershell
git fetch origin
git checkout work/hq-parallel-control
git pull --ff-only origin work/hq-parallel-control
git status --short
git log --oneline -20
```

Master/Main HQ result:

```text
branch: work/hq-parallel-control
latest commit: 2fa529d Add desktop transfer remote backed final audit
status before this doc: clean
```

Worktree list after lane recreation:

```text
C:/NWR/Niners-War-Room               2fa529d [work/hq-parallel-control]
C:/NWR/Niners-War-Room-deploy-v2     04dda41 [work/deployment-v2-discovery]
C:/NWR/Niners-War-Room-drop-decision ebddf8b [work/drop-decision-day-review]
C:/NWR/Niners-War-Room-outcome       6e47932 [main]
```

## Lanes Skipped

Skipped for now:

- Rookie HQ, because the latest user instruction said to skip unless the latest
  clean Rookie refinement handoff exists. Rookie also has known local-only
  artifact risk around `data/` and selected final exports under `local_exports/`.
- Mock Draft HQ, because the latest user instruction said to skip unless the
  latest clean handoff exists. It remains blocked from Master HQ simulations or
  production ranking work.
- QA/Data Hygiene, because the final transfer audit says it was not
  remote-backed and had untracked local files.
- Legacy/non-primary Outcome branches, unless explicitly requested.
- Any lane with active unpushed laptop work.

## Missing Local-Only Artifacts

The Git remote-backed setup does not transfer local-only artifacts. If any are
needed later, create a separate exact artifact manifest before copying:

- `data/`
- `local_exports/`
- `.venv/`
- caches
- logs
- generated databases
- generated exports
- secrets

Known notes from source-of-truth docs:

- Outcome V1 had laptop-local `data/`; do not copy or commit blindly.
- Rookie HQ had laptop-local `data/` and may need selected `local_exports/`
  only through a separate manifest.
- QA/Data Hygiene had local `data/` and untracked docs; do not recreate yet.

## Recommended First Lane To Resume

Recommended first lane to resume:

```text
Outcome V1 at C:\NWR\Niners-War-Room-outcome on main
```

Reason:

- It is remote-backed and clean.
- It is the normal local app/operator path.
- It is GREEN for local/main readiness in the source-of-truth docs.

Keep blocked:

- hosted deployment
- deploy commands
- app/production ranking changes
- probabilities or bands
- hidden sort keys
- promoted artifacts
- simulations from Master HQ
- blind local artifact copy

## Confirmation

- `C:\NWR` was created successfully.
- Master/Main HQ was cloned/fetched from GitHub.
- Outcome V1, Deployment V2, and Drop Decision were recreated as Git worktrees.
- Rookie HQ, Mock Draft HQ, QA/Data Hygiene, and legacy/non-primary branches were
  skipped.
- No deploy occurred.
- No merge occurred.
- No push occurred.
- No commit occurred.
- No staging occurred.
- No laptop local artifacts were copied.
- No `data/`, `local_exports/`, `.venv/`, caches, logs, generated artifacts, or
  secrets were copied or committed.
