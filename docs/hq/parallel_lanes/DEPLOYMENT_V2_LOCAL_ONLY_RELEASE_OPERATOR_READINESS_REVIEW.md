# Deployment V2 Local-Only Release Operator Readiness Review

## Scope

This is a docs/review-only readiness review for V1 local-only operation. It
reviews whether the existing Deployment V2 discovery docs and repo docs are
clear enough for manual local Streamlit operation.

This review does not approve hosted deployment, create a deploy command, create
secrets, expose public ports, change app behavior, or alter Outcome/Rookie/model
artifacts.

## Reviewed Files

- `docs/hq/parallel_lanes/DEPLOYMENT_V2_DISCOVERY_CHARTER.md`
- `docs/hq/parallel_lanes/DEPLOYMENT_V2_TARGET_OPTIONS_DECISION_MATRIX.md`
- `docs/hq/parallel_lanes/DEPLOYMENT_V2_LOCAL_STREAMLIT_OPERATOR_RUNBOOK.md`
- `README.md`
- `RUN_POLICY.md`
- `docs/codex/ARCHITECTURE.md`
- `requirements.txt`
- `.env.example`

## Readiness Questions

### 1. Is local-only operation documented clearly enough for V1?

Yes for a technical or semi-technical operator. The reviewed docs consistently
state that V1 is local-first/local-only, uses local CSV and SQLite snapshots,
and has no hosted deployment approval.

For a non-technical operator, the documentation is close but not fully turnkey.
It still assumes comfort with PowerShell, virtual environments, repo paths, and
reading terminal output.

### 2. Is the official local run command documented?

Yes. The official command is documented in `README.md`,
`docs/codex/ARCHITECTURE.md`, and the D3 runbook:

```powershell
streamlit run app/main.py
```

The D3 runbook correctly avoids turning this into a hosted deployment command.

### 3. Are dependency setup notes clear enough?

Mostly yes. `README.md` and the D3 runbook document:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt` is short and understandable. The remaining gap is that a
non-technical operator may not know how to confirm Python is installed or how to
recognize that the virtual environment is active.

### 4. Are environment / `.env.example` expectations clear enough?

Yes for V1. `.env.example` says to copy to `.env` for local runs and not commit
`.env`. The runbook reinforces that `.env` is local-only.

The remaining gap is operational: a non-technical operator may need a short
"when you do not need `.env`" note, because local Streamlit operation may work
without editing API keys.

### 5. Are live API/secrets rules clear enough?

Yes. The docs consistently say:

- runtime must not require mandatory live APIs
- `MODEL_V4_LIVE_API_ENABLED=false` by default
- Sleeper is public/read-only and does not require an API key
- CFBD and paid/commercial keys remain blank unless explicitly approved
- `.env`, API keys, and credentials must not be committed

### 6. Are public port and hosted deployment prohibitions clear enough?

Yes. The charter, decision matrix, runbook, `RUN_POLICY.md`, and architecture
doc all block hosted deployment or production deploys. The D3 runbook explicitly
blocks hosted deployment, deploy commands, public ports, tunnels, public shares,
and external exposure.

### 7. Are local smoke checks clear enough?

Mostly yes. The D3 runbook gives a manual smoke checklist for app startup,
navigation, Rankings page render, Outcome column view, approved heads, Top 6
absence, no sorting/ranking effects, no hidden sort key, and no fake precision.

The remaining gap is that the checklist is observational. A non-technical
operator may need screenshots or expected visible labels for "2026 Outcomes"
and the exact Rankings control to select.

### 8. Are Outcome numeric columns mentioned correctly and safely?

Yes. The runbook lists only approved V1 heads:

- QB T12
- RB T12
- RB T24
- WR T12
- WR T24
- WR T36
- TE T12

It explicitly blocks Top 6 and unapproved heads, and it states Outcome columns
must not change ranking order, sorting, hidden keys, promoted artifacts, or
model behavior.

### 9. Are rollback/stop instructions clear enough?

Mostly yes. The runbook says to stop Streamlit with `Ctrl+C`, return to the last
known-good branch/commit, prefer forward revert for bad commits unless HQ
approves otherwise, avoid overwriting frozen data packs, and rerun smoke checks.

The remaining gap is that a non-technical operator may not know how to find the
terminal running Streamlit or identify the current branch/commit without help.

### 10. What remains missing before a non-technical operator could run this reliably?

Remaining operator-readiness gaps:

1. A one-page quick-start checklist with no branching decisions.
2. A "how to know the virtual environment is active" cue.
3. A "how to know Streamlit started successfully" cue with expected terminal
   output and local URL.
4. Screenshots or exact UI labels for the Rankings page and Outcome column view.
5. A simple stop/restart guide for when the app is already running on another
   local port.
6. A clear statement of which repo/worktree path a non-technical operator should
   use for normal V1 local operation after HQ chooses the release worktree.
7. A reminder that local data readiness is separate from app startup readiness.

These are documentation/handholding gaps, not blockers for a technical operator.

### 11. GREEN / YELLOW / RED readiness verdict for V1 local-only operator use

Verdict: `YELLOW_GREEN_FOR_TECHNICAL_OPERATOR`

Reason:

- GREEN for technical local operation. The command, environment setup, local URL,
  smoke checks, Outcome head limits, and no-hosting boundaries are documented.
- YELLOW for non-technical operation. A non-technical operator could still get
  stuck on PowerShell, virtualenv activation, choosing the right local path,
  interpreting Streamlit terminal output, or finding the exact UI controls.

No RED blocker was found for keeping V1 local-only.

### 12. Hosted deployment remains blocked

Hosted deployment remains blocked.

No hosted target, owner, secrets policy, data policy, CI/manual deployment
policy, or hosted rollback policy has been approved. No deploy command should be
created or run.

## D4 Summary

V1 local-only operation is documented well enough for technical operator use.
The official run mode remains manual local Streamlit. Hosted deployment remains
blocked. The next documentation improvement, if HQ wants a smoother
non-technical handoff, should be a one-page operator quick-start with
screenshots or exact visible UI labels.

## D4 Guardrail Confirmation

- No deploy command was created.
- No hosted deployment was approved.
- No secrets or credentials were created.
- No public ports were exposed by this review.
- No app behavior changes were made.
- No Outcome model behavior, displayed heads, sorting, hidden keys, or promoted
  artifacts were changed.
- No rookie files were changed.
- No `data/`, `local_exports/`, or `.venv/` files were committed.
