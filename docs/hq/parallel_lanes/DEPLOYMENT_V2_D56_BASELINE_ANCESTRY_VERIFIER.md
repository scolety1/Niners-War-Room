# Deployment V2 D56 Baseline Ancestry Verifier

Deployment V2 now has a read-only helper that verifies the current HEAD descends from a supplied accepted baseline commit.

## Command

```powershell
python scripts/verify_deployment_v2_baseline_ancestry.py <baseline-commit>
```

Optional JSON output:

```powershell
python scripts/verify_deployment_v2_baseline_ancestry.py <baseline-commit> --json
```

Optional clean-worktree requirement:

```powershell
python scripts/verify_deployment_v2_baseline_ancestry.py <baseline-commit> --require-clean
```

These commands are validation-only. They run local read-only git checks and do not deploy, create deploy commands, expose public ports, create credentials, add CI/CD, create containers/images, or change app behavior.

## Verdicts

- `GREEN`: current HEAD descends from the supplied baseline.
- `YELLOW`: the baseline is missing or cannot be resolved.
- `RED`: current HEAD does not descend from the baseline, or clean status was required and the worktree is dirty.

## Deployment Stance

V1 remains `local_only`.

Hosted deployment remains blocked.

No deploy command exists.

Normal operator path remains `C:\NWR\Niners-War-Room-outcome`, and the normal operator branch remains `main`.

Deployment V2 is not the operator app path.
