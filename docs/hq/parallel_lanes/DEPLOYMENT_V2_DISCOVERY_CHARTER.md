# Deployment V2 Discovery Charter

## Repo / Worktree

`C:\Users\smcol\Documents\Vacation\Niners-War-Room-deploy-v2`

## Branch

`work/deployment-v2-discovery`

## Source Baseline

- Source worktree: `C:\Users\smcol\Documents\Vacation\Niners-War-Room-outcome`
- Source branch: `main`
- Baseline commit: `6e47932 Record Outcome numeric columns V1 local release closeout`

## Discovery Verdict

Niners War Room remains local-only until HQ explicitly approves a hosted-app
target and release owner. Outcome Numeric Columns V1 is GREEN for local/main
readiness, but deployment remains YELLOW because the repo has no documented
deploy target, no deployment owner, no deploy command, and a current run policy
that blocks production deploys.

This lane may define requirements for Deployment V2. It must not deploy, expose
ports publicly, create secrets, invent a deploy command, or change app/model
behavior.

## Current Deployment Assumptions Found

- `RUN_POLICY.md` states the project is local-first and production deploys are
  not allowed at runtime.
- `README.md` documents local setup and local Streamlit execution only:
  `streamlit run app/main.py`.
- `.env.example` contains local/API safety knobs and keeps live APIs disabled
  by default.
- `pyproject.toml` and `requirements.txt` describe a small Python/Streamlit app
  dependency surface.
- No `.github` workflow, Dockerfile, Streamlit Cloud config, Procfile,
  platform manifest, release script, deploy script, or deployment runbook was
  found in this discovery pass.
- Outcome V1 closeout states no deploy command exists and deployment is not
  applicable until a documented deploy target exists.

## Deployment Owner And Repo Recommendation

Deployment should not belong to the Outcome feature lane. Outcome owns the
approved numeric-column behavior only.

Recommended owner:

- HQ-controlled release/platform lane
- Separate worktree and branch, such as this lane
- Final deployment work must start from `main` after any approved feature merge

Recommended repo:

- The Niners War Room repo on `main`
- Not a generated local export
- Not a feature-only worktree as the long-term deploy owner

## Hosted Target Recommendation

No hosted target is approved yet.

Deployment V2 should choose one of these explicit stances before any command is
created:

1. `local_only`: keep NWR as a private desktop/local Streamlit app.
2. `private_hosted`: host behind authentication with private repo/data handling.
3. `public_hosted`: blocked unless HQ approves stripping or excluding private
   league data, private roster context, local exports, and any sensitive notes.

Default recommendation for now: `local_only`.

If hosted deployment is later approved, the target must be selected in a new
approval packet before any deploy command is documented or run.

## Secret And Credential Policy

- Do not commit `.env`, API keys, platform tokens, service-account files, paid
  feed paths, or generated secret material.
- Keep `MODEL_V4_LIVE_API_ENABLED=false` by default for hosted review unless HQ
  separately approves live API use.
- Store hosted secrets only in the selected platform's secret manager after HQ
  approves the platform.
- Treat private league data, data packs, local exports, and roster snapshots as
  private deployment inputs, not public repo content.
- Do not require mandatory live API calls for hosted startup.

## CI/CD Or Manual Deployment Policy

Until HQ approves otherwise:

- CI may run tests and static guardrails only.
- No automatic deployment on push.
- No deployment from feature branches.
- No deploy command or release script may be created in this discovery lane.
- Any future deploy must be manual, named, logged, and tied to an approved
  release commit or tag.

## Rollback Policy

Deployment V2 must define rollback before deployment:

- Identify the previous known-good commit or tag.
- Prefer a forward revert commit for bad deploy changes.
- If using a hosting platform, define redeploy of the previous approved release
  as the operational rollback.
- Rollback must remove unauthorized app-readable artifacts, secrets, or exposed
  routes.
- Rollback must rerun tests and static no-leakage checks before a replacement
  deploy.

## Required Gate Before Any Deploy Command Exists

No deploy command may be created or run until all items pass:

1. HQ chooses `local_only`, `private_hosted`, or `public_hosted`.
2. HQ names the deployment owner and branch.
3. HQ approves the hosting target, or confirms no hosted target.
4. Secrets policy is written for the selected target.
5. Private data policy is written for data packs, local exports, and roster
   snapshots.
6. CI/manual deployment policy is written.
7. Rollback policy is written and tested at the command/runbook level.
8. Local tests and Outcome no-leakage/static guardrails pass on the release
   commit.
9. App smoke passes on a local-only address before hosted exposure.
10. Outcome displayed heads remain limited to the approved heads.
11. No sorting/ranking effects, hidden sort keys, Top 6/unapproved heads,
    promoted artifacts, rookie file changes, `data/`, `local_exports/`, or
    `.venv/` commits are present.
12. Human review confirms the hosted app will not expose private data beyond
    the intended audience.

## Forbidden In This Lane

- Do not deploy.
- Do not push.
- Do not create a deploy command.
- Do not create secrets or credentials.
- Do not expose ports publicly.
- Do not change app wiring or Streamlit behavior.
- Do not change Outcome model behavior, displayed heads, sorting, hidden keys,
  or promoted artifacts.
- Do not touch rookie files.
- Do not commit `data/`, `local_exports/`, `.venv/`, generated databases,
  caches, or release artifacts.

## Required Final Response Format

- verdict
- worktree and branch
- files changed
- checks run and results
- current git status
- committed files, if any
- uncommitted files, if any
- confirmation that no deploy/push/app/model/ranking/rookie/data/export work
  occurred
