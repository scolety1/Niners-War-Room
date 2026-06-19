# Deployment V2 D64 Operator Escalation Matrix

This matrix standardizes Deployment V2 HQ escalation. It is a reporting guide only.

V1 remains `local_only`. Hosted deployment remains blocked. No deploy command exists. Deployment V2 is not the operator app path.

## Matrix

| Condition | Verdict | Operator Response |
| --- | --- | --- |
| Branch is not `work/deployment-v2-discovery` before work | RED | Stop and report branch mismatch. |
| Dirty repo before work | RED | Stop and report `git status --short`. |
| Dirty repo during an in-progress allowed task | YELLOW until committed | Validate, commit only safe allowed changes, then rerun. |
| `git diff --check` fails | RED | Stop or fix whitespace within allowed scope. |
| Local-only guard fails | RED | Fix only if the cause is inside Deployment V2 docs/scripts/tests and remains local-only. |
| Guard report JSON is invalid | RED | Fix validation report mode within allowed scope. |
| Focused tests fail | RED | Fix within allowed docs/validation/test scope or stop. |
| Python unavailable | YELLOW | Continue docs-only tasks only; report skipped script/test validation. |
| Docs audit is GREEN with historical path NOTE only | GREEN | Continue; note that the legacy path is historical. |
| Docs audit has missing required local-only language | RED | Fix docs language within Deployment V2 docs only. |
| Docs audit has hosted-readiness language | RED | Remove or reword only inside Deployment V2 docs. |
| Import zip missing when optional | YELLOW or SKIPPED | Report missing optional comparison; do not invent zip exports. |
| Import zip missing when required by user | YELLOW | Stop and request/provide exact missing path in final report. |
| Hosted request | BLOCKED | State hosted deployment remains blocked pending explicit policies. |
| Request for a deploy command | BLOCKED | Do not invent the command; report blocker. |
| Request touching Outcome behavior | BLOCKED | Do not touch Outcome runtime/app behavior in this lane. |
| Generated/data artifact detection | YELLOW | Report as outside-lane note unless cleanup is explicitly approved. |
| Secret/credential request | BLOCKED | Do not create credentials or credential-shaped fixtures. |
| CI/CD or container request | BLOCKED | Do not add workflows, containers, images, or platform configs. |

## Remaining Hosted Blockers

Hosted deployment remains BLOCKED pending explicit approval of hosted target, owner, secrets policy, data policy, access policy, rollback policy, deploy command policy, CI/CD policy, public/private routing policy, and hosted smoke plan.
