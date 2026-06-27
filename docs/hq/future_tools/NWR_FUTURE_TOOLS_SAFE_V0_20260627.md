# NWR Future Tools Safe V0 - 2026-06-27

## Verdict

GREEN as a safe display/manual implementation lane. This does not launch model outputs, rankings, recommendations, projections, trade targets, pick valuation, playoff odds, rookie class strength, or source-truth decisions.

## Tools Promoted To Safe V0

### Roster Weakness Tracker V0

Status: Safe V0 display/manual.

What it does:

- Accepts optional manual roster rows in the format `Player, Position, Age, Dynasty Rank, Notes`.
- Shows position counts.
- Shows simple starter-threshold coverage notes.
- Shows age buckets if age was manually supplied.
- Shows Dynasty Rank buckets if rank was manually supplied.

Guardrails:

- Display-only roster structure.
- Not a recommendation.
- Not model input.
- Missing age/rank remains `Not enough information`.
- No add/drop, trade, start/sit, waiver, or roster-action advice.

### Future Pick Planning V0

Status: Safe V0 display/manual.

What it does:

- Reads future pick assets from the local Live Draft runtime trade event log if present.
- Accepts optional manual future pick notes.
- Exports a planning CSV from the browser if the user wants a local copy.

Guardrails:

- Planning ledger only.
- Runtime events are manual/local, not official source truth.
- No pick valuation.
- No trade valuation.
- No class-strength prediction.
- No DynastyProcess/ADP/market use.

### Deadline Prep Toolkit V0

Status: Safe V0 display/manual.

Includes:

- Keeper Deadline Prep
- Drop Deadline Prep
- Trade Deadline Prep

What it does:

- Shows checklist rows.
- Accepts manual deadline dates/notes.
- Exports checklist CSVs from the browser.
- Uses status text such as `Not Started`.

Guardrails:

- Manual checklist only.
- No keeper recommendation.
- No drop recommendation.
- No trade target.
- No hidden scoring.
- No model output.

## Tools Kept Blocked

- Who Should I Start? - blocked pending weekly projections, injury/status, matchup/schedule, and model gate.
- Waiver Wire Rankings - blocked pending current free-agent/waiver data and recommendation gate.
- In-Season Rankings - blocked pending in-season model gate.
- Trade Targets - blocked pending trade target policy/model gate.
- Upcoming Rookie Class Preview - blocked pending CFBD/unified human approval.
- Draft Class Strength - blocked pending class-strength model gate.
- Position Strength by Class - blocked pending position-level class model gate.
- Position Target Plan - blocked pending roster/class/model gates.
- Playoff Push Planner - blocked pending standings/schedule/projection source gate.

## Data Used

- Committed Future Tools R&D matrix and specs under `docs/hq/future_tools/`.
- Optional manual user input typed into `/future-tools`.
- Local Live Draft runtime trade event log, read only, for future pick ledger display.

## Data Explicitly Not Used

- DynastyProcess, ADP, or market values for value logic.
- CFBD or NFL usage as model input.
- Vendor/RotoWire/FantasyPros/Gmail automation.
- Projections, injuries, matchup forecasts, playoff odds, or rookie class grades.
- Frozen board, latest candidate, latest approved, pinned snapshot, source-truth, or model/rank artifacts.

## Persistence

Safe V0 does not add new persistence. Manual notes are page inputs only. Browser download buttons can export CSVs without tracking repo files. Live Draft runtime state is read-only here and remains local/untracked under `C:\NWR_SHARED_DATA`.

## Remaining Caveats

- Roster Weakness Tracker V0 requires manual roster input to display summaries.
- Future Pick Planning V0 shows runtime trade-event future picks only if they were manually recorded in Live Draft.
- Deadline Prep Toolkit V0 is a checklist shell; it does not make decisions.
- All blocked/gated tools need separate approval before product implementation.

## Guardrails

- No rank/tier/model/source-truth mutation.
- No model input promotion.
- No CFBD/NFL usage promotion.
- No decision-page wiring.
- No data refresh.
- No hosted deployment.
- No raw/shared/local/secret files tracked.

## Validation

- Focused pytest: `31 passed`.
- Ruff on touched Python/tests: passed.
- Python compile on touched Python/tests: passed.
- CSV load validation: Future Tools status matrix 14 rows; tool inventory 14 rows.
- `git diff --check`: passed.
- Browser smoke on port 8611: `/future-tools`, `/live-draft-room`, `/mock-draft`, `/draft-analyzer`, `/rankings`, and `/settings-data-health` rendered without traceback.
- Frozen baseline board row count: 66.
- Protected artifact diff paths: none.
