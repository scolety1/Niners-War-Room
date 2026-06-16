# Deployment V2 Local Streamlit Operator Runbook

## Scope

This is the official V1 local-only operator runbook for manually running Niners
War Room with Streamlit. It documents the supported local workflow only. It is
not hosted deployment approval and does not create a deployment path.

## V1 Status

- Deployment stance: `local_only`
- Official supported run mode: `manual_local_streamlit`
- Hosted deployment: blocked
- Deploy commands: blocked
- CI/CD deployment workflows: blocked
- Containers/images: blocked

Niners War Room remains a private, local-first Streamlit app using local CSV and
SQLite snapshots. Runtime should not require network access during keeper,
trade, or draft decisions.

## Official Local Run Command

Run from the repo root after local environment setup:

```powershell
streamlit run app/main.py
```

This is the exact local app command documented in `README.md` and
`docs/codex/ARCHITECTURE.md`.

## Expected Local URL

Streamlit normally opens a local browser URL after startup. For the Rankings
page, use the local app's Rankings route:

```text
http://localhost:8501/rankings
```

If Streamlit chooses a different local port because `8501` is already in use,
use the port shown in the local Streamlit terminal output and append
`/rankings`.

## Environment Setup Notes

Use the existing repo dependency docs only.

From `README.md`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Required packages are listed in `requirements.txt`:

- `numpy`
- `pandas`
- `pydantic`
- `pytest`
- `ruff`
- `streamlit`

Do not commit `.venv/`.

## Local Environment And API Policy

`.env.example` may be copied to `.env` for local runs. Do not commit `.env`.

Live API behavior stays disabled by default:

```text
MODEL_V4_LIVE_API_ENABLED=false
MODEL_V4_API_CACHE_ROOT=local_exports/api_cache
```

Sleeper is documented as public/read-only and does not require an API key.
CollegeFootballData and paid/commercial feed keys must remain blank unless live
import work is explicitly approved. Local app operation should not depend on
mandatory live API calls.

## Operator Preflight Checklist

Before starting Streamlit:

1. Confirm you are in the intended repo/worktree.
2. Confirm the branch or commit is the intended local release state.
3. Run `git status --short` and confirm no unexpected app/source/model files
   are dirty.
4. Confirm `.env` does not contain newly added secrets that should not be used.
5. Confirm `MODEL_V4_LIVE_API_ENABLED=false` unless HQ has explicitly approved
   live API work.
6. Confirm `data/`, `local_exports/`, and `.venv/` are not staged.
7. Confirm required local data packs or snapshots are present for the desired
   review workflow.
8. Confirm no hosted deployment, tunnel, public share, or external port exposure
   is running.

## Local Smoke Test Checklist

After running:

```powershell
streamlit run app/main.py
```

Check:

1. The app opens locally without a Python traceback.
2. The sidebar/navigation loads.
3. Open the Rankings page at `/rankings`.
4. The Rankings dataframe renders.
5. Select the Outcome column view that shows 2026 Outcome numeric columns, if
   needed.
6. Confirm only approved Outcome heads are displayed.
7. Confirm no Top 6 or unapproved Outcome heads are displayed.
8. Confirm Outcome columns do not change ranking order or sorting.
9. Confirm no hidden sort key appears in the visible table.
10. Confirm unavailable or inapplicable rows do not show fake precision.

## Approved Outcome Numeric Heads

Only these Outcome numeric heads are approved for V1 local use:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

No Top 6 or unapproved heads are approved.

## Explicitly Blocked

The following remain blocked:

- hosted deployment
- deploy commands
- public ports
- secrets or credentials
- CI/CD deploy workflows
- containers/images
- `data/`, `local_exports/`, or `.venv/` commits
- rookie changes
- Outcome model behavior changes
- Outcome displayed-head changes
- Outcome sorting, hidden-key, or promoted-artifact changes
- app behavior changes

## Troubleshooting

### Streamlit command is missing

Likely cause: the local virtual environment is not active or dependencies are
not installed.

Use the documented local setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then retry:

```powershell
streamlit run app/main.py
```

### Wrong Python or missing packages

Activate the local environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then reinstall from the existing dependency file:

```powershell
pip install -r requirements.txt
```

Do not add or upgrade dependencies as part of local operation unless HQ has
approved a dependency proposal.

### Local port is already in use

Streamlit may choose another local port or report the conflict. Use the local URL
printed by Streamlit. Do not expose a public port, open a tunnel, or publish the
app externally as part of V1 local operation.

### Rankings page does not load

Stop Streamlit, check the terminal traceback, and confirm local data packs and
snapshots are present. Do not repair by changing app behavior in the deployment
lane. If the issue appears to be app/model behavior, stop and route it to HQ.

## Rollback And Stop Guidance

For local-only operation:

1. Stop the Streamlit process with `Ctrl+C` in the terminal.
2. If the current branch is wrong, switch back to the last known-good local
   release branch or commit.
3. If a recent code commit caused the local app failure, use a forward revert
   workflow unless HQ explicitly approves another git action.
4. Do not delete or overwrite frozen data packs. Create a new dated local
   snapshot only when the data workflow explicitly calls for one.
5. Rerun the local smoke checklist before using the app for decisions.

There is no hosted rollback path in V1 because hosted deployment is not
approved.

## Not A Hosted Deployment Approval

This runbook supports manual local Streamlit operation only. It does not approve:

- hosted deployment
- deploy commands
- platform setup
- public access
- CI/CD deployment
- container builds
- secret creation
- uploading private league data

Hosted deployment remains blocked until HQ separately approves target, owner,
secrets policy, data policy, CI/manual deployment policy, and rollback policy.
