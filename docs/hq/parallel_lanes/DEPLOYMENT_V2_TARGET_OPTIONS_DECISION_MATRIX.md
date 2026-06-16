# Deployment V2 Target Options Decision Matrix

## Scope

This document evaluates hosted-app and local-only deployment paths for Niners
War Room. It is planning-only. It does not approve implementation, create a
deploy command, create secrets, expose ports publicly, change app behavior, or
alter Outcome/Rookie/model artifacts.

## Current Baseline

- Worktree: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2`
- Branch: `work/deployment-v2-discovery`
- Charter commit: `8b3faf6 Add deployment v2 discovery charter`
- Default stance: `local_only`
- V1 status: Outcome Numeric Columns V1 is GREEN for local/main readiness
- Deployment status: YELLOW because no hosted target, owner, secrets policy,
  data policy, rollback policy, or deploy command is approved

## Decision Matrix

| Option | Fit For This App | Setup Complexity | Data/Secrets Risk | Cost/Risk Category | Rollback Story | Local Development Impact | Repo Changes Required | Credentials Required | Data Policy Approval Required | Appropriate Now Or Later |
|---|---|---|---|---|---|---|---|---|---|---|
| Stay local-only for V1 | Best fit for current policy. Matches local-first docs, private league data, local data packs, and current no-deploy stance. | Low | Low, because data remains on Tim's machine and no hosted secrets are needed. | Lowest cost and lowest exposure risk. | Revert to prior local commit or keep using known-good local branch. No hosted rollback needed. | None. Current workflow stays intact. | No | No | No new hosted-data policy needed. Existing no-commit policy remains enough. | Appropriate now. Recommended for V1. |
| Manual local Streamlit run as official supported mode | Strong fit. Formalizes the known good local command and local smoke process without changing deployment posture. | Low | Low, assuming `.env`, `data/`, `local_exports/`, and `.venv/` remain uncommitted. | Low cost, low operational risk. | Use previous local commit, stop/restart local Streamlit, or switch branches/worktrees. | Minimal. Could add a runbook later. | Later docs-only runbook may be useful. No app code required. | No new credentials beyond existing optional local `.env`. | No hosted policy needed; local data policy should still be stated. | Appropriate now as the next path. |
| Private hosted Streamlit-style deployment | Possible fit if Tim wants browser access away from the local machine, but it conflicts with current local-first policy until private data, auth, and secrets controls are approved. | Medium | Medium to high. Hosting must prevent public access to private league data, data packs, and local exports. | Platform cost may be low, but privacy risk is meaningful. | Redeploy previous approved commit or disable the hosted app. Requires platform-specific rollback runbook. | Moderate. Dev remains local, but hosted parity and dependency pinning become important. | Yes. Likely needs config/runbook and possibly dependency/runtime metadata. | Yes, platform credentials and possibly app secrets. | Yes. Must approve what data can be uploaded, persisted, cached, or displayed. | Later only, after policy approval. |
| General app hosting with controlled secrets | Flexible option for a private web service on a platform with secret manager, auth, logs, and rollback controls. Better for a hardened private deployment than ad hoc hosting. | Medium to high | Medium to high. Secret storage, data upload, platform logs, and access controls all need review. | Moderate cost and operational risk. | Roll back by pinning/redeploying previous release artifact or commit. Requires documented release identifiers. | Moderate. May require environment parity, config files, and release discipline. | Yes. Likely platform config and release docs. | Yes, platform credentials and secret-manager entries. | Yes. Must decide whether data packs are bundled, mounted, uploaded manually, or excluded. | Later, if hosted deployment becomes a real need. |
| Containerized deployment option | Useful if reproducibility, platform portability, or rollback by immutable image becomes important. Heavier than needed for V1. | High | Medium. Secrets can stay outside image, but data-bundling mistakes could expose private files. | Higher setup cost; lower drift once established. | Roll back to prior tagged image or prior commit/image digest. Requires registry and tag policy. | Medium to high. Adds container build/test path alongside local Streamlit. | Yes. Dockerfile/container config, `.dockerignore`, image policy, and runbook. | Usually yes for registry/platform; app secrets still external. | Yes. Must ensure `data/`, `local_exports/`, `.venv/`, caches, and private PDFs are excluded from images. | Later only if portability/reproducibility becomes worth the complexity. |
| CI/CD deployment option | Not a target by itself. Useful only after a hosted target, secrets policy, tests, rollback, and release gates exist. | High | High if misconfigured, because deploy-on-push can expose unreviewed app or data. | Highest automation risk until governance is mature. | Revert/redeploy previous release. Requires protected branches, manual approvals, and audit trail. | Medium. Adds CI requirements to every release branch. | Yes. Workflows, protected environments, and release checks. | Yes, CI secrets and platform tokens. | Yes. CI must prove it cannot package private local artifacts. | Later only. Blocked now. |

## Recommendation

Recommended next path: make `manual_local_streamlit_supported_mode` the official
Deployment V2 next step while keeping V1 `local_only`.

This means:

- Keep the app private and local by default.
- Treat the current local Streamlit smoke process as the supported release path.
- Add a future docs-only local runbook if HQ wants one.
- Do not select a hosted target yet.
- Do not create deployment commands, platform configs, CI/CD deploy workflows,
  containers, or secrets yet.

## Required Approvals Before Any Hosted Implementation

Before any hosted implementation may begin, HQ must approve:

1. Hosted stance: `private_hosted` or `public_hosted`.
2. Deployment owner and release branch/worktree.
3. Hosting target and account owner.
4. Access policy: who can open the app and how access is controlled.
5. Secrets policy: where tokens/API keys live and how they are rotated.
6. Data policy: whether data packs, private rosters, local exports, PDFs, and
   generated artifacts may ever leave the local machine.
7. Persistence policy: whether the hosted app can write files, caches, logs, or
   databases.
8. Runtime policy: whether live APIs stay disabled or may be enabled.
9. CI/manual policy: whether deploys are manual only or CI-gated.
10. Rollback policy: previous release identifier, revert strategy, and emergency
    disable procedure.
11. Static guardrails proving no `data/`, `local_exports/`, `.venv/`, caches,
    secrets, promoted artifacts, unapproved Outcome heads, hidden sort keys, or
    ranking/sorting effects enter the release.
12. Human privacy review confirming hosted output is safe for the intended
    audience.

## What Remains Blocked

- Hosted deployment target selection
- Deploy commands
- Release scripts
- Public port exposure
- Platform account setup through this repo
- Secrets or credential creation
- CI/CD deployment workflows
- Containers or images
- Uploading private data packs or local exports
- App behavior changes
- Outcome model behavior changes
- Outcome displayed-head changes
- Sorting, ranking, hidden-key, or promoted-artifact changes
- Rookie file changes
- `data/`, `local_exports/`, `.venv/`, generated database, cache, or market-data
  commits

## Implementation Approval

Implementation is not approved. This is a proposal only.

The only recommended near-term implementation candidate is a future docs-only
local runbook that documents the supported local Streamlit workflow and smoke
checks. Even that runbook should be separately requested or approved by HQ.

## D2 Verdict

GREEN to keep Deployment V2 in planning mode.

YELLOW for hosted deployment because target, owner, secrets policy, data policy,
CI/manual policy, and rollback policy remain undefined.

Recommended next action: approve or reject `manual_local_streamlit_supported_mode`
as the official V1 deployment stance before considering hosted options.
