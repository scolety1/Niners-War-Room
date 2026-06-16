# Mock Draft Lane Charter

## Repo / Worktree

`C:\Users\smcol\Documents\Vacation\Niners-War-Room-mock-draft`

## Branch

`work/mock-draft-simulator`

## Mission

Build a review-only mock draft simulator for drop-day draft prep using the full
available pool: frozen rookie manual draft kit rows plus dropped, released, or
otherwise available veterans.

The simulator may model likely opponent draft behavior from pick order, team
needs, roster construction, ADP/market context, and NWR player quality/value.
It must not produce final cut/keep recommendations, production rankings, app
wiring, exact outcome probabilities, coarse probability bands, or promoted
model artifacts.

## Critical Separation Rule

ADP and market context may be used only for opponent likelihood, availability,
and draft behavior. ADP and market context must remain separate from NWR private
quality/value in columns, features, scoring explanations, and exported review
artifacts.

Required column separation:

- `nwr_quality_score` or equivalent private value column
- `market_adp_pick` or equivalent public/market behavior column
- `opponent_likelihood_score` or equivalent behavior-only column
- `availability_curve` or equivalent behavior-only column
- `separation_note` explaining that market context did not alter NWR quality

## Read-Only Inputs

- Rookie freeze commit:
  `b48085edcfd3ab4de7910158578062c39701bf59`
- Rookie kit directory:
  `local_exports/rookie_framework/final_manual_draft_kit_20260615/`
- Dropped or available veteran source files supplied for drop day
- Current pick order and pick ownership
- Current rosters and roster construction snapshots
- Public ADP/market context for opponent behavior only

## Forbidden Inputs And Actions

- Do not modify rookie framework files, rookie formulas, rookie board order,
  rookie warnings, or rookie exports.
- Do not force rookies through veteran outcome heads.
- Do not use unreleased outcome probabilities, coarse bands, outcome app wiring,
  or outcome promoted artifacts.
- Do not blend ADP, market value, public rank, projections, trade calculators,
  or prior fantasy draft history into NWR private quality/value.
- Do not modify production app or Streamlit wiring.
- Do not modify production rankings or sorting.
- Do not create app-readable probability or band outputs.
- Do not promote model artifacts.
- Do not push or deploy.
- Do not commit `data/`, `local_exports/`, generated databases, caches, market
  data files, or generated draft outputs.

## Recommended Local Artifact Paths

All generated review artifacts should stay under ignored `local_exports/`:

- `local_exports/mock_draft_simulator/input_snapshots/`
- `local_exports/mock_draft_simulator/latest/mock_available_pool_review_rows.csv`
- `local_exports/mock_draft_simulator/latest/mock_team_need_rows.csv`
- `local_exports/mock_draft_simulator/latest/mock_pick_order_rows.csv`
- `local_exports/mock_draft_simulator/latest/opponent_behavior_inputs.csv`
- `local_exports/mock_draft_simulator/latest/mock_draft_simulation_runs.csv`
- `local_exports/mock_draft_simulator/latest/mock_draft_availability_curves.csv`
- `local_exports/mock_draft_simulator/latest/nwr_pick_decision_context_rows.csv`
- `local_exports/mock_draft_simulator/latest/mock_draft_run_manifest.json`

## Safe Data Contract Sketch

The first implementation phase should define schemas before generating rows:

- available pool rows: stable player id, player name, position, asset type,
  availability source, NWR quality/value, confidence, and read-only source path
- team need rows: team id/name, current roster counts, positional need weights,
  known picks, and roster construction notes
- pick order rows: overall pick, round, pick label, current owner, original
  owner, and whether the pick is Niners-owned
- opponent behavior rows: public ADP/market rank, market source timestamp,
  market-source status, likelihood/availability features, and explicit
  separation notes
- simulation output rows: run id, pick, team, selected player, selection reason,
  remaining availability, Niners decision context, and review-only warning flags

## Recommended First Phase

1. Inventory and reuse existing draft-room state, mock storage, draft pool,
   market isolation, and source-readiness services.
2. Add schema-only tests for the mock available pool, team needs, pick order,
   opponent behavior inputs, and simulation output contracts.
3. Build a review-only local artifact generator that writes only under
   `local_exports/mock_draft_simulator/`.
4. Keep generated artifacts out of git and outside app/Streamlit until HQ
   explicitly approves a later review surface.
5. Validate that NWR quality/value is unchanged when ADP/market inputs are
   perturbed, while opponent behavior and availability may move.

## Required Final Response Format

- verdict
- files changed
- local-only exports created, if any
- tests/checks run and results
- `git status --short`
- commit/uncommitted summary
- confirmation that `data/` and `local_exports/` were not committed
- confirmation that no push/deploy/app wiring/rankings/sorting/outcome/rookie
  production/probability-band work occurred
